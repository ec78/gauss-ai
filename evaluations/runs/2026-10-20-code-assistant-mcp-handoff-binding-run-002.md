# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.2
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Compute the eigenvalues of the symmetric 3x3 matrix with rows [2, 1, 0], [1, 2, 1], [0, 1, 2] using eigh, and run it."

The user's later messages in this task, verbatim: "ye"; "yes".

Code (S02):
```gauss
x = { 2 1 0,
      1 2 1,
      0 1 2 };

va = eigh(x);
print va;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: `eigh` satisfied; coverage gaps: none; `code_sha256` 47e02f556ef6….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: **handoff_candidate** (preconditions: none).
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Exact `rendered_prompt` (request_id `6cfe61c4-5890-43ca-be40-cf4ba4524cd5`, digest `1dbd01984e7857a5f60fc41f9053f55a0401c5d544ad99cfbb121c5a1644413e`):

````text
Ready for controlled execution.

Code:
```gauss
x = { 2 1 0,
      1 2 1,
      0 1 2 };

va = eigh(x);
print va;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 1dbd01984e7857a5f60fc41f9053f55a0401c5d544ad99cfbb121c5a1644413e

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "ye", passed verbatim with request_id `6cfe61c4-5890-43ca-be40-cf4ba4524cd5` → `{"outcome": "unrecognized", "message": "Please answer exactly 'yes' or 'no'.", "request_id": "6cfe61c4-5890-43ca-be40-cf4ba4524cd5", "request_digest": "1dbd01984e7857a5f60fc41f9053f55a0401c5d544ad99cfbb121c5a1644413e"}`. No approval was created and nothing ran; the request stayed pending.

Decision: "yes", passed verbatim with request_id `6cfe61c4-5890-43ca-be40-cf4ba4524cd5` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `6cfe61c4-5890-43ca-be40-cf4ba4524cd5` and request_digest `1dbd01984e78…` (the prompt's); result_digest `98ab53aa0eb078993a02bc51e648fd1dec0f3483b7f10244f45d2357153f3bcc`. Verbatim stdout:
```
      0.58578644 
       2.0000000 
       3.4142136 
```
GAUSS job header: `Job: inline_wfam8e0s.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_02tiroq0\.gauss_code_execution_generated )`, Tue Oct 20 07:44:21 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: handoff_candidate with `eigh` satisfied; the exact prompt shown; the reply passed verbatim with the prompt's request_id; an approved run matches direct GAUSS.

Observed behavior: handoff_candidate; precondition `eigh` **satisfied** (new in v0.87.0). The user's first reply "ye" was passed verbatim with the prompt's request_id and returned `unrecognized`, echoing the request_id and digest; nothing ran and the prompt stayed pending. The client asked again rather than reading "ye" as yes. "yes" then ran it once; the response echoed the same request_id and digest. Output 2 − √2, 2, 2 + √2, byte-identical to direct `tgauss.exe -b`.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
