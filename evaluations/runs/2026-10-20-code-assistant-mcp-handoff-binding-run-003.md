# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.3
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Simulate 1,000 standard normal draws with seed 42 and print their mean and standard deviation. Run it."

The user's later messages in this task, verbatim: "yes".

Code (S03):
```gauss
// Set the seed so the draws are repeatable
rndseed 42;

// 1,000 standard normal draws
y = rndn(1000, 1);

print "Mean:";
print meanc(y);
print "Standard deviation:";
print stdc(y);
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` d44f6064e863….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Exact `rendered_prompt` (request_id `3ccb6bfe-d3a6-4940-b734-74b6c0a63370`, digest `f4b9739987e04fa69d25dfb3c236d5f314d05d03d7ddf41d21aaf8024e694df2`):

````text
Ready for controlled execution.

Code:
```gauss
// Set the seed so the draws are repeatable
rndseed 42;

// 1,000 standard normal draws
y = rndn(1000, 1);

print "Mean:";
print meanc(y);
print "Standard deviation:";
print stdc(y);
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: f4b9739987e04fa69d25dfb3c236d5f314d05d03d7ddf41d21aaf8024e694df2

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes", passed verbatim with request_id `3ccb6bfe-d3a6-4940-b734-74b6c0a63370` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `3ccb6bfe-d3a6-4940-b734-74b6c0a63370` and request_digest `f4b9739987e0…` (the prompt's); result_digest `dccfb5d11b7b53cc7722573fb728fb4e9827936676a5fe01b2a386b874b466d3`. Verbatim stdout:
```
Mean:
    0.0098225034 
Standard deviation:
       1.0085936 
```
GAUSS job header: `Job: inline_7om8_z1c.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_ak60fvwf\.gauss_code_execution_generated )`, Tue Oct 20 07:44:59 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: handoff_candidate; the user's own decision. (The suggested script planned a decline here; the user approved instead, so no decline was exercised in 78.x.)

Observed behavior: handoff_candidate; "yes" ran it once (request_id echoed). Mean 0.0098225034, SD 1.0085936, byte-identical to direct GAUSS. The client noted that `rndseed` is a statement, not a checked call.

Notes: **No decline in 78.x.** The user answered "yes" here rather than the planned "no", and never declined anything later. The decline path was exercised only by the recording session's stdio probe B1 (fake runner) and the automated tests; 77.10 remains the last live decline.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
