# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.9
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Compute the inverse of a 3x3 positive definite matrix and check the result by multiplying it back."

The user's replies to the run prompt: "Yes approve", then "yes".

Code (S09):
```gauss
a = { 4 1 0,
      1 3 1,
      0 1 2 };

ainv = invpd(a);

print "Inverse:";
print ainv;
print "a * ainv (should be the identity):";
print a * ainv;
```

Captured output: **handoff_candidate**; precondition `invpd` **satisfied** ("the literal input matrix is symmetric
and positive definite (verified by leading-principal-minor computation)"); no gaps; `validation_id`
c52b71cbf21c4f489a8d808f42c7a8e9, `code_sha256` 35619f24….

Exact `rendered_prompt` (request_id `16dc3ef9-b3f4-44f4-919f-6b3af2c66ed6`):

````text
Ready for controlled execution.

Code:
```gauss
a = { 4 1 0,
      1 3 1,
      0 1 2 };

ainv = invpd(a);

print "Inverse:";
print ainv;
print "a * ainv (should be the identity):";
print a * ainv;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Workspace parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces
Request digest: 75b11232dbf2bb44fcdd954dfa6a39200f83bb095d7bf143692754849d67d42d

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decisions, each passed verbatim to `gauss_execution_decide`:
1. "Yes approve" -> `{"outcome": "unrecognized", "message": "Please answer exactly 'yes' or 'no'."}`. No approval
   was created and nothing ran. The parser accepts exactly `yes`/`approve`/`no`/`decline` after trim and
   lower-case (`gauss_execution_handoff.py:319-333`). The client did not shorten the reply to "yes" itself; it
   asked the user again.
2. "yes" -> approved and executed once.

Handoff result (verbatim stdout; `outcome: success`, `launched: true`, `execution_status: completed`, `exit_code: 0`, `timed_out: false`, `workspace_state: null`, `provenance: null`; result_digest `4a6ce0ba10b006ea46de8fee513f7e4694f502fedebc4cc1240207396ca1e585`; GAUSS job header `inline_jnrri7ut.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_rufo3lje\.gauss_code_execution_generated ), Mon Oct 19 07:07:13 2026`):
```
Inverse:

      0.27777778      -0.11111111      0.055555556
     -0.11111111       0.44444444      -0.22222222
     0.055555556      -0.22222222       0.61111111
a * ainv (should be the identity):

       1.0000000        0.0000000        0.0000000
  -3.4694470e-17        1.0000000    1.1102230e-16
  -1.3877788e-17    5.5511151e-17        1.0000000 
```

Workspace path: the job ran in `…\Temp\gauss_ai_handoff_rufo3lje`, a `tempfile.TemporaryDirectory` deleted after
the run, not in the "Workspace parent" the prompt showed (finding 3). The client flagged the mismatch.

Real GAUSS (S09 via `tgauss.exe -b`): **byte-identical stdout** to the handoff, including the ~1e-16 residuals.
The inverse is (1/18)·[5 −2 1; −2 8 −4; 1 −4 11], as the client computed by hand.

Diagnosis (direct `validate_code`): identical, same sha. v0.85.0: identical.

The earlier 77.1 `det` request was replaced by this prepare (single pending slot), never decided.

Expected behavior: handoff_candidate; the exact prompt shown; only the user's own words decide; an approved run matches direct GAUSS.

Observed behavior: As expected. **The first real-GAUSS execution through MCP in this project's live evaluations.** An unrecognized reply created no approval.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
