# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.4
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Write two small programs: one that inverts the matrix with rows [4, 1], [1, 3] using invpd, and one that sorts the matrix with rows [3, 1], [1, 2], [2, 3] by its second column. Prepare both to run and show me both prompts before I answer."

The user's later messages in this task, verbatim: "My answer is for the invpd prompt."; "A: yes"; "yes".

Code (S04):
```gauss
x = { 4 1,
      1 3 };

// invpd requires a symmetric, positive definite matrix
xi = invpd(x);
print xi;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: `invpd` satisfied; coverage gaps: none; `code_sha256` eab96308a85d….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Code (S05):
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

Exact `rendered_prompt` (request_id `eb20c483-eb0f-4c69-992b-b4e617489c73`, digest `9a53b8777e30251495a8cfa2dfaa01ed26174f104e6e3ebd18904badca73883f`):

````text
Ready for controlled execution.

Code:
```gauss
x = { 4 1,
      1 3 };

// invpd requires a symmetric, positive definite matrix
xi = invpd(x);
print xi;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 9a53b8777e30251495a8cfa2dfaa01ed26174f104e6e3ebd18904badca73883f

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Exact `rendered_prompt` (request_id `d845dc0d-29b3-4f31-b8b6-ea8f95bc917a`, digest `c6644e7e179c27e09c2841a5aacb0787ae55cb375e4635b1e374bdbc1f2cd5b3`):

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

Decision: "A: yes", passed verbatim with request_id `eb20c483-eb0f-4c69-992b-b4e617489c73` → `{"outcome": "unrecognized", "message": "Please answer exactly 'yes' or 'no'.", "request_id": "eb20c483-eb0f-4c69-992b-b4e617489c73", "request_digest": "9a53b8777e30251495a8cfa2dfaa01ed26174f104e6e3ebd18904badca73883f"}`. No approval was created and nothing ran; the request stayed pending.

Decision: "yes", passed verbatim with request_id `eb20c483-eb0f-4c69-992b-b4e617489c73` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `eb20c483-eb0f-4c69-992b-b4e617489c73` and request_digest `9a53b8777e30…` (the prompt's); result_digest `ed81b11ee0514e7ca90ab73f1bed82dfc90157b653c12686455c933d0319a2ad`. Verbatim stdout:
```
      0.27272727     -0.090909091 
    -0.090909091       0.36363636 
```
GAUSS job header: `Job: inline_xj2cdtns.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_g0pldi_s\.gauss_code_execution_generated )`, Tue Oct 20 07:50:08 2026 (a deleted temporary directory, as the prompt said).

Decision: "Prompt B: yes", passed verbatim with request_id `d845dc0d-29b3-4f31-b8b6-ea8f95bc917a` → `{"outcome": "unrecognized", "message": "Please answer exactly 'yes' or 'no'.", "request_id": "d845dc0d-29b3-4f31-b8b6-ea8f95bc917a", "request_digest": "c6644e7e179c27e09c2841a5aacb0787ae55cb375e4635b1e374bdbc1f2cd5b3"}`. No approval was created and nothing ran; the request stayed pending.

Decision: "yes", passed verbatim with request_id `d845dc0d-29b3-4f31-b8b6-ea8f95bc917a` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `d845dc0d-29b3-4f31-b8b6-ea8f95bc917a` and request_digest `c6644e7e179c…` (the prompt's); result_digest `246bb9f301f60e2c546a512f4d50380fed3617e8aa79c1927e610a06d9d3aae9`. Verbatim stdout:
```
       3.0000000        1.0000000 
       1.0000000        2.0000000 
       2.0000000        3.0000000 
```
GAUSS job header: `Job: inline_ifyv8fln.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_z4rgyr52\.gauss_code_execution_generated )`, Tue Oct 20 07:52:34 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: The two-prompt binding case (v0.87 plan §7 task 4): a reply aimed at a replaced prompt is `request_superseded` and runs nothing; the client then shows the pending prompt.

Observed behavior: **The binding case was not reached.** The client said "a second prepare in the same session would cancel the first prompt, so I'll give each program its own session" (knowledge from the `CLAUDE.md` bullet in its context), opened two sessions, and kept both prompts open. No prepare replaced another, so neither `replaced_request_id` nor `request_superseded` occurred live. Binding by request_id did hold for every reply: "A: yes" went to prompt A's id and was `unrecognized` (the client had itself suggested labelling answers "A: yes, B: no"); "yes" then ran A only. B stayed pending through 78.5 and was answered in 78.6. Both runs byte-identical to direct GAUSS.

Notes: The server's one-pending-request rule is per session, and sessions are free, so a client can hold several prompts open at once (finding 1). Probe B1 (recording session, real stdio transport, fake runner) confirms the server side of the planned case: the second prepare reported `replaced_request_id`; "yes" with the first prompt's id returned `request_superseded` with `pending_request_id`; a bare decide returned `request_id_required`. The client's suggested "A: yes" format caused two unrecognized replies (here and in 78.6); it apologised and asked for bare answers (finding 2).

Pass/fail: Pass
Defect severity: Minor (client conduct; binding test not reached)
Remediation: Finding 1 (disclose multi-session prompts); finding 2 (client guidance).

Overall Score: 3.5
Decision: Pass
