# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.14
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Run the sort program from earlier again."

The user's later messages in this task, verbatim: "yes".

Code (S19):
```gauss
x = { 3 1,
      1 2,
      2 3 };

// Sort the rows of 'x' by the second column, ascending
y = sortc(x, 2);
print y;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` 446b1fb82ae1….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Exact `rendered_prompt` (request_id `9c9c9838-efef-4c15-8c21-a2f593611e38`, digest `c6644e7e179c27e09c2841a5aacb0787ae55cb375e4635b1e374bdbc1f2cd5b3`):

````text
Ready for controlled execution.

Code:
```gauss
x = { 3 1,
      1 2,
      2 3 };

// Sort the rows of 'x' by the second column, ascending
y = sortc(x, 2);
print y;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: c6644e7e179c27e09c2841a5aacb0787ae55cb375e4635b1e374bdbc1f2cd5b3

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes", passed verbatim with request_id `9c9c9838-efef-4c15-8c21-a2f593611e38` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `9c9c9838-efef-4c15-8c21-a2f593611e38` and request_digest `c6644e7e179c…` (the prompt's); result_digest `fb3c7944043bfbc8e6aabacfa16d0319eeff4679a491dc7b888988287903eaa4`. Verbatim stdout:
```
       3.0000000        1.0000000 
       1.0000000        2.0000000 
       2.0000000        3.0000000 
```
GAUSS job header: `Job: inline_mtg21f7i.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_5eipvv7g\.gauss_code_execution_generated )`, Tue Oct 20 20:29:58 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: The spent approval is not reused: a new validation, a new request_id and a new approval.

Observed behavior: The client re-validated (new validation_id, identical `code_sha256`), prepared (new request_id `9c9c9838-…`, the **same digest** as 78.4's B, since the digest excludes request_id by design) and ran it on the user's "yes"; byte-identical to direct GAUSS and to 78.4's run. It explained that the earlier approval doesn't carry over. Its explanation of the different result_digest ("each run's log includes its own timestamp and job name") is wrong: the result digest covers the approval_id, which differs per approval, and not the log text.

Notes: The spent validation_id was not resubmitted live (its session was closed); probe B1 confirms the refusal.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.8
Decision: Pass
