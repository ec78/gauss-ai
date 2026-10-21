# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.8
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"minimize a function with sqpSolveMT and print the parameters and return code"

Search `sqpSolveMT` (live, identical on the v0.88.0 re-run): **grounded**
- sources: `sqpsolvemt` (sqpsolvemt.rst)
- unmatched: none; ambiguous: none
- v0.87.0, same query: identical apart from the excerpt text (§3.5: v0.87.0's excerpt has no Outputs section)

The excerpt now ends inside Outputs (it shows `out.par`, `out.fct`, `out.lagr` and the `out.retcode` heading, but not the code list). The client read the code list, the example and the `struct PV` usage from `sqpsolvemt.rst` on disk.

Code (call #21):
```gauss
// Rosenbrock function: minimum f = 0 at (1, 1)
proc (1) = rosen(struct PV p);
    local b;
    b = pvUnpack(p, "b");
    retp(100 * (b[2] - b[1]^2)^2 + (1 - b[1])^2);
endp;

// Starting values packed into a PV structure
struct PV par1;
par1 = pvCreate();
par1 = pvPack(par1, -1.2|1, "b");

// Control structure: suppress iteration output
struct sqpSolveMTControl c0;
c0 = sqpSolveMTControlCreate();
c0.output = 0;

// Minimize
struct sqpSolveMTout out;
out = sqpSolveMT(&rosen, par1, c0);

print "Parameter estimates:";
print pvUnpack(out.par, "b");
print "Function value: " out.fct;
print "Return code:    " out.retcode;
```

Captured output (live, reproduced exactly on v0.88.0): **review_required**; preconditions: none.
Reasons: "syntax validation coverage is partial -- not all generated constructs could be deterministically checked (unmodelled construct(s): control_flow_block)"; "validation coverage is partial (incomplete: parameter roles partial, syntax partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `pvUnpack` argument 1 (parameter `p1`): `p` has no single traceable assignment earlier in this code"; "parameter role unknown -- `pvPack` argument 2 (parameter `x`): `-1.2|1` is an expression, and expressions are never evaluated"; "parameter role unknown -- `sqpSolveMT` argument 1 (parameter `&fct`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `sqpSolveMT` argument 3: the argument falls at or after the documented `...`, which other parameters follow, so which parameter it fills cannot be determined"; "parameter role unknown -- `pvUnpack` argument 1 (parameter `p1`): `out.par` is an expression, and expressions are never evaluated"
Coverage gaps: syntax/- `unmodelled_construct`; parameter_role/pvUnpack arg 1 `argument_untraced`; parameter_role/pvPack arg 2 `argument_expression`; parameter_role/sqpSolveMT arg 1 `documented_type_missing`; parameter_role/sqpSolveMT arg 3 `variadic_position`; parameter_role/pvUnpack arg 1 `argument_expression`
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no error; the directory held only `prog.gss` afterwards. Stdout:

```text
Parameter estimates:

      0.99999497 
      0.99998992 
Function value:    2.5361166e-11 
Return code:           0.0000000 
```

Expected behavior: An estimator whose output members the client must use: §3.5 keeps Outputs in the excerpt (v0.87.0: none). The `proc` block is `control_flow_block`, so review_required at best.

Observed behavior: §3.5 held live: on v0.87.0 the `sqpSolveMT` excerpt (1,500 characters) has no Outputs section at all; on v0.88.0 it lists `out.par`, `out.fct`, `out.lagr` and `out.retcode`, and the client used `out.par`, `out.fct` and `out.retcode`. The `retcode` meanings (0-8) were still past the cut, so the client read the page file. review_required: `control_flow_block` (the `proc`), `argument_untraced` (`p` inside the proc), two `argument_expression` gaps (`-1.2|1`, `out.par`), `documented_type_missing` for `&fct` and `variadic_position` for `c0`. The direct diagnosis agrees with every gap. The client named all of them correctly. Real GAUSS: 0.99999, 0.99999; f = 2.5e-11; return code 0, as predicted. The client declared `struct PV` and the output structure explicitly, citing a memory note (`pvCreate()` undeclared fails G0181).

Search: the user named the function; grounded directly. The excerpt was enough for the members but not for the return-code table.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.8
Decision: Pass
