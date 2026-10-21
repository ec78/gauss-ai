# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.5
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Compute the determinant of the matrix with rows [2, 1], [1, 3] and run it."

The user's later messages in this task, verbatim: "yes".

Code (S06):
```gauss
x = { 2 1,
      1 3 };

d = det(x);
print d;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` 581ffeeda056….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Exact `rendered_prompt` (request_id `ffafa076-5e4d-4ff1-bdd2-9c58f5b3ab20`, digest `f5e78b095b1ee8c16d2e60229da9de30161299e9c589c9b2cf37bb25872bf892`):

````text
Ready for controlled execution.

Code:
```gauss
x = { 2 1,
      1 3 };

d = det(x);
print d;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: f5e78b095b1ee8c16d2e60229da9de30161299e9c589c9b2cf37bb25872bf892

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes", passed verbatim with request_id `ffafa076-5e4d-4ff1-bdd2-9c58f5b3ab20` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `ffafa076-5e4d-4ff1-bdd2-9c58f5b3ab20` and request_digest `f5e78b095b1e…` (the prompt's); result_digest `15ba12b778e42ba98484e8b7f01e4c56b4119711108427397a7ae964e3fb20eb`. Verbatim stdout:
```
       5.0000000 
```
GAUSS job header: `Job: inline_edxiehow.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_8wntqvp6\.gauss_code_execution_generated )`, Tue Oct 20 07:51:02 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: handoff_candidate; an approved run matches direct GAUSS.

Observed behavior: handoff_candidate; prepared in a third session while B was still open. With two prompts open, the client told the user in advance that the next bare yes/no would go to this prompt (C), and that B could be answered first by saying so in a separate message. "yes" ran C (5.0000000), byte-identical to direct GAUSS; B was untouched.

Notes: With several prompts open, which prompt a bare reply answers is decided by the client alone; it announced its mapping before the reply (finding 1).

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
