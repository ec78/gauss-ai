# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.4
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Estimate a simple linear IV model with gmmFit on simulated data, and set the starting values in the control structure."

Searches:
```
search_docs("gmmFit") -> grounded: gmmfit.rst (excerpt truncated inside the gCtl table)
search_docs("gmmControlCreate") -> grounded: gmmfitcontrolcreate.rst, whose example declares `struct gmmFitControl c;`
```
The client noticed that the two pages name the control structure differently, then grepped and read `gmmfit.rst`
(lines 140-219) directly: its example uses `struct gmmControl`, `gctl.bStart`, `struct gmmOut`, and the four-input
moment procedure `meqn(b, yt, xt, zt)`; its Outputs table lists `gOut.parEst`.

Code (S03, abridged): simulated `z`, endogenous `x`, `y`; `zt = ones(n, 1) ~ z;`
```gauss
struct gmmControl gctl;
gctl = gmmControlCreate();
b0 = { 0, 0 };
gctl.bStart = b0;
struct gmmOut gOut;
gOut = gmmFit(&ivMoments, y, x, zt, gctl);
print gOut.parEst;
proc (1) = ivMoments(b, yt, xt, zt);
    local ut;
    ut = yt - b[1] - b[2] * xt;
    retp(ut .* zt);
endp;
```

Captured output: `review_required`; coverage_gaps: syntax `unmodelled_construct`; `gmmFit` arg 1 `&fct`
`documented_type_missing`; arg 2 `argument_assigned_from_expression` (`y`); args 3-5 `variadic_position`.

Diagnosis (direct `validate_code`): identical. **The gaps agree**; the client's explanations were right (`&fct` is the
disclosed v0.83.0 limitation).

v0.85.0, same snippet: identical in every field (the client assigned the start values through a variable, so the 75.18
member-literal line does not occur).

Real GAUSS (S03 verbatim): **fails at compile time**, `G0504 Invalid structure member 'parEst (struct gmmOut)'` (line 25).
GAUSS's own `src/gmm.sdf` defines the member as `paramEst`; `gmmfitiv.rst` documents `gOut.paramEst`, `gmmfit.rst`
documents `gOut.parEst`. With only that one word changed (spot check e08) the program runs: `0.97506 1.9874` (truth 1, 2),
so `struct gmmControl`, `bStart`, the extra-argument order and the moment procedure were all right. This is an upstream
docs defect (finding 4); the validator does not model structure members (v0.86.0 §4, out of scope), so no verdict could
have caught it.

Client errors: it told the user "If GAUSS rejects that name, switch to `gmmFitControl`". That fallback is wrong:
`struct gmmFitControl` is undefined (`G0507`, 75.x sc10, re-confirmed as e03; 75.x finding 8). It also said "the validator
accepted it" of `gmmControl`, which implied evidence the validator does not provide (structure type names are not
checked).

Expected behavior: review_required with true gaps; a program that runs.

Observed behavior: Verdict right. The program follows the published docs and fails because of them; the client's
fallback advice for the struct name was wrong.

Pass/fail: Pass with defect recorded
Defect severity: Minor (upstream docs: `gmmfit.rst` names `parEst`; client advice error)
Remediation: Upstream: `gmmfit.rst` should document `gOut.paramEst`. Reporting it is the user's choice.

Overall Score: 3.0
Decision: Pass with defect recorded
