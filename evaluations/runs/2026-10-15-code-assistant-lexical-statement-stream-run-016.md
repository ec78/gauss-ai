# Evaluation Result

Date: 2026-10-15
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. Tasks 74.1-74.7 ran on 2026-10-13 and 74.8-74.19 on 2026-10-15 (the server process restarted in between). The session did not read the planning doc, PROJECT_STATUS.md or any source until all nineteen tasks were done.
Agent Version: v0.84.0 (released; tag `v0.84.0`, commit `d19c61c`; HEAD `db80bea`), editable install of this checkout (`pip show gauss-ai` = 0.84.0). The live server's own output carries v0.84.0-only behavior (a `call_undocumented` gap in 74.10; the `"det = "` label reaching handoff_candidate in 74.2).
Prompt ID: 74.16
Prompt Category: Lexical Statement Stream (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.84.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session 352fc674f22b467fae1e3113c26898e9. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on v0.84.0 and on a `git archive` of v0.83.0 (`2740519`) for comparison.
Prompt Text:

"What gauss function can be used for optimization?"

Searches:
```
search_docs("optimization minimize a function") -> partially_grounded; minimize.rst (only because the query contains
    the token "minimize"); unmatched ["optimization"]
search_docs("optimization") -> "ungrounded"; 8 keyword candidates (truncated): maxlikmt, optmt, minimize,
    cc/optimization-and-solution, cmlmt/comt guide pages
search_docs("sqpSolveMT QNewton QProg") -> grounded; sqpsolvemt.rst, qnewton.rst, qprog.rst (prior knowledge)
```
The `minimize.rst` excerpt was cut off inside the control-structure table, so its output-structure members were never
shown; the client chose `QNewton` (fully documented outputs) for its example rather than guess them.

Code:
```gauss
proc (1) = objfun(b);
    retp((b[1] - 3)^2 + (b[2] + 1)^2);
endp;
b0 = { 0, 0 };
{ b_hat, f_min, g, ret } = QNewton(&objfun, b0);
```
(plus three `print` lines)

Captured output: `review_required`; coverage_gaps: syntax/unmodelled_construct (control_flow_block);
**parameter_role/QNewton/1/&fct/documented_type_missing** ("no documented `:type` line was matched to this parameter").

Diagnosis (direct `validate_code` plus the extractor): qnewton.rst has `:param &fct:` and `:type &fct: function pointer`.
`_PARAM_TYPE_LINE_RE` (`gauss_pre_execution_validation.py:716`) consumes the `&` and stores the type under `fct`, while
`_parse_signature_occurrence` keeps the parameter name `&fct`, so `type_by_name.get("&fct")` always misses. The gap the
client saw agrees with what the validator did, but its cause is wrong about the docs: a `:type` line exists. 114
published pages have `&`-prefixed parameters (`:type` texts: 63 "struct pointer", 23 "scalar", 12 "function pointer",
8 "pointer", 4 "struct", ...). `classify_documented_type("function pointer")` is `unknown` anyway, so this verdict would
not change; the 63 `struct pointer` and 23 `scalar` parameters do lose a real category. Same on v0.83.0.
`user_defined_symbols` omits the four `{...} =` targets, as v0.84.0 §4 accepts (multi-target assignment is out of scope).

Expected behavior: A correct answer from grounded pages; review_required for a snippet-defined `proc`, with causes named.

Observed behavior: Answer correct (`minimize`, `QNewton`, `sqpSolveMT`, `QProg`, `optmt`/`maxlikmt`). Verdict state correct. **Known limitation rediscovered live (not a new defect):** every `&`-prefixed documented parameter loses its `:type` line, so the reported cause (`documented_type_missing`) is false about the page. v0.83.0 found this in its own verdict diff (planning v0.83 §9.2 item 5) and deliberately left it unfixed, disclosed in `KNOWN_LIMITATIONS.md`: matching the names would let a literal `5` "match" a function pointer documented as `scalar`, widening candidacy in the unsafe direction. (Corrected 2026-10-15: the first version of this record called it a new defect; see planning v0.85 §1 and §2.3.)

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (known, disclosed limitation: the gap cause is false about the docs; conservative direction)
Remediation: None new. v0.85 §2.3 re-measured it (119 symbols) and recommends keeping v0.83.0's decision.

Overall Score: 3.5
Decision: Pass with limitation disclosed
