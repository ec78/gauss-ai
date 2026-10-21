# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.11
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"Minimize (b1 - 3)^2 + (b2 + 1)^2 with sqpSolveMT, starting from 0, 0, with both parameters bounded between -5 and 5."

No search: the client reused 79.8's page and grepped `sqpsolvemt.rst` on disk for `bounds` ("1x2 or Kx2 matrix … If 1x2 all parameters have same bounds").

Code (call #27):
```gauss
// Objective: (b1 - 3)^2 + (b2 + 1)^2, minimum 0 at (3, -1)
proc (1) = objfn(struct PV p);
    local b;
    b = pvUnpack(p, "b");
    retp((b[1] - 3)^2 + (b[2] + 1)^2);
endp;

// Starting values (0, 0)
struct PV par1;
par1 = pvCreate();
par1 = pvPack(par1, 0|0, "b");

// Control structure: same bounds [-5, 5] on every parameter
struct sqpSolveMTControl c0;
c0 = sqpSolveMTControlCreate();
c0.bounds = -5 ~ 5;
c0.output = 0;

struct sqpSolveMTout out;
out = sqpSolveMT(&objfn, par1, c0);

print "Parameter estimates:";
print pvUnpack(out.par, "b");
print "Function value: " out.fct;
print "Return code:    " out.retcode;
```

Captured output (live, reproduced exactly on v0.88.0): **review_required**; preconditions: none.
Reasons: "syntax validation coverage is partial -- not all generated constructs could be deterministically checked (unmodelled construct(s): control_flow_block)"; "validation coverage is partial (incomplete: parameter roles partial, syntax partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `pvUnpack` argument 1 (parameter `p1`): `p` has no single traceable assignment earlier in this code"; "parameter role unknown -- `pvPack` argument 2 (parameter `x`): `0|0` is an expression, and expressions are never evaluated"; "parameter role unknown -- `sqpSolveMT` argument 1 (parameter `&fct`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `sqpSolveMT` argument 3: the argument falls at or after the documented `...`, which other parameters follow, so which parameter it fills cannot be determined"; "parameter role unknown -- `pvUnpack` argument 1 (parameter `p1`): `out.par` is an expression, and expressions are never evaluated"
Coverage gaps: syntax/- `unmodelled_construct`; parameter_role/pvUnpack arg 1 `argument_untraced`; parameter_role/pvPack arg 2 `argument_expression`; parameter_role/sqpSolveMT arg 1 `documented_type_missing`; parameter_role/sqpSolveMT arg 3 `variadic_position`; parameter_role/pvUnpack arg 1 `argument_expression`
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no error; the directory held only `prog.gss` afterwards. Stdout:

```text
Parameter estimates:

       2.9999999 
     -0.99999998 
Function value:    4.8170459e-15 
Return code:           0.0000000 
```

Expected behavior: The same review_required shape as 79.8; correct use of `ctl.bounds`.

Observed behavior: review_required with exactly 79.8's gaps; diagnosis agrees. `c0.bounds = -5 ~ 5;` matches the page. Real GAUSS: 3.0000, -1.0000; f = 4.8e-15; return code 0, as predicted.

Search: none through the tool (the page was already open from 79.8; the bounds row is past the excerpt's cut). A recording-session probe shows `sqpSolveMT bounds` grounds `sqpsolvemt`, with three `*-bounds` guide pages as candidates.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.8
Decision: Pass
