# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.1
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Are you connected to gauss-ai? What version is it, and can it actually run GAUSS code on this machine? Prove it without running anything."

Code (S00):
```gauss
x = 1 + 1;
print x;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **not_ready**; preconditions: none; coverage gaps: none.
Reasons: "no documented GAUSS function call was found to ground this code against -- code with no documented calls is never eligible for controlled execution"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs.

Code (S01):
```gauss
x = seqa(1, 1, 5);
print sumc(x);
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` cd1cde7b7716….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs.

Exact `rendered_prompt` (request_id `5bc7c569-a87e-4560-93fa-f9f8ea977222`, digest `debd156982f12f741f31a93b4a55e52d1ed6c287e5403f59a71b8a1170f0fd78`):

````text
Ready for controlled execution.

Code:
```gauss
x = seqa(1, 1, 5);
print sumc(x);
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: debd156982f12f741f31a93b4a55e52d1ed6c287e5403f59a71b8a1170f0fd78

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Expected behavior: The opt-in confirmed by `real_gauss_allowed` and one prepare before any task; nothing executed; claims limited to the evidence.

Observed behavior: `gauss_session_start` returned `real_gauss_allowed: true` (new in v0.87.0). The client's first snippet (`x = 1 + 1; print x;`) was not_ready (no documented call), so it validated a `seqa`/`sumc` snippet (handoff_candidate), prepared it and showed that the prompt rendered, with the new "Runs in: a new temporary directory, deleted after the run" line. It never called decide, and closed the session so the prompt could not be answered later. It also ran `gauss-ai version` (0.87.0), `gauss-ai config show`, the process list and `Test-Path` on the executable (26.1.4.5565), and said plainly that none of this proves `tgauss.exe` launches. 78.2's run later did.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
