# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.12
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"What's the element-wise reciprocal of the matrix with rows [1, 2], [2, 4]?"

The user's later messages in this task, verbatim: "Confirm with GAUSS"; "yes".

Code (S17):
```gauss
A = { 1 2,
      2 4 };

// Element-wise reciprocal: divide a matrix of ones by A, element by element
r = ones(2, 2) ./ A;
print r;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` a6cd7310228c….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Exact `rendered_prompt` (request_id `ccf9b05d-d769-46ed-b40a-477df4ac8c0d`, digest `1037344564f55a8e91f2c504913ca177e32d4dee6c287472ea799034c941005e`):

````text
Ready for controlled execution.

Code:
```gauss
A = { 1 2,
      2 4 };

// Element-wise reciprocal: divide a matrix of ones by A, element by element
r = ones(2, 2) ./ A;
print r;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 1037344564f55a8e91f2c504913ca177e32d4dee6c287472ea799034c941005e

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes", passed verbatim with request_id `ccf9b05d-d769-46ed-b40a-477df4ac8c0d` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `ccf9b05d-d769-46ed-b40a-477df4ac8c0d` and request_digest `1037344564f5…` (the prompt's); result_digest `2f9ce56a160dbb45fba964345c81e5cabac1902b46a343c0af89ce47ff3ec5db`. Verbatim stdout:
```
       1.0000000       0.50000000 
      0.50000000       0.25000000 
```
GAUSS job header: `Job: inline_ibd24630.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_hl08fya1\.gauss_code_execution_generated )`, Tue Oct 20 20:24:03 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: A scalar dividend gets no `/` check; code without a documented call is not_ready.

Observed behavior: The client answered from arithmetic, recommended `1 ./ A`, and (citing the plan's dv04) said `1 / A` also divides element-wise. It did not validate either; probes P1/P2 confirm both are not_ready (no documented call) and get no `/` check. On "Confirm with GAUSS" it rewrote the code as `ones(2, 2) ./ A`, saying `ones` was there only so the code calls a documented function and that the validator checked nothing about the division. handoff_candidate; "yes" ran it; byte-identical to direct GAUSS.

Notes: The no-documented-call rule was met by an incidental call that carries no evidence about the computation (finding 4, pre-existing policy).

Pass/fail: Pass
Defect severity: Minor (client shaped code around the no-documented-call policy, disclosed)
Remediation: Finding 4 (observation).

Overall Score: 3.6
Decision: Pass
