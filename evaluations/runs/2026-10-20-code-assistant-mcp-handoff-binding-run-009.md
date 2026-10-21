# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.9
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Solve the least-squares problem y = X b, where X has rows [1, 2], [2, 4], [3, 6] and y = [1, 2, 3]."

The user's later messages in this task, verbatim: "Yes confirm result with GAUSS"; "yes".

Code (S12):
```gauss
X = { 1 2,
      2 4,
      3 6 };
y = { 1, 2, 3 };

b = y / X;
print b;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **not_ready**; preconditions: `/` violated; coverage gaps: none.
Reasons: "no documented GAUSS function call was found to ground this code against -- code with no documented calls is never eligible for controlled execution"; "/: the literal divisor is 3x2 with linearly dependent columns; GAUSS's least-squares solve stops with G0121"
v0.86.0, same snippet: **not_ready** (preconditions: none).
Real GAUSS (`tgauss.exe -b`): fails: `error G0121 : Matrix not positive definite`.

Code (S13):
```gauss
X = { 1 2,
      2 4,
      3 6 };
y = { 1, 2, 3 };

b = invpd(X'X) * X'y;
print b;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **review_required**; preconditions: `invpd` unverified; coverage gaps: `invpd` arg 1 `argument_expression`; `invpd` `runtime_dependent`.
Reasons: "runtime-dependent precondition(s) remain unverified for: invpd"; "validation coverage is minimal (incomplete: parameter roles unknown, preconditions unknown), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `invpd` argument 1 (parameter `x`): `X'X` is an expression, and expressions are never evaluated"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): fails: `error G0121 : Matrix not positive definite`.

Code (S14):
```gauss
X = { 1 2,
      2 4,
      3 6 };
y = { 1, 2, 3 };

// X is rank deficient (column 2 = 2 * column 1), so X'X is singular;
// pinv gives the minimum-norm least-squares solution
b = pinv(X) * y;
print b;

// Residual y - X*b
print y - X*b;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` 3af404e6a458….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs. **byte-identical to handoff**.

Exact `rendered_prompt` (request_id `61da338d-91c1-41cf-95f3-93dd93c2568f`, digest `e783f0f26f566b933c7cfaf1dc990cc9c0aa3b1176a838e1c1d4a673d6d63717`):

````text
Ready for controlled execution.

Code:
```gauss
X = { 1 2,
      2 4,
      3 6 };
y = { 1, 2, 3 };

// X is rank deficient (column 2 = 2 * column 1), so X'X is singular;
// pinv gives the minimum-norm least-squares solution
b = pinv(X) * y;
print b;

// Residual y - X*b
print y - X*b;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: e783f0f26f566b933c7cfaf1dc990cc9c0aa3b1176a838e1c1d4a673d6d63717

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes", passed verbatim with request_id `61da338d-91c1-41cf-95f3-93dd93c2568f` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `61da338d-91c1-41cf-95f3-93dd93c2568f` and request_digest `e783f0f26f56…` (the prompt's); result_digest `e2f8df521724e23ca5ac4f3a38559f0c7e3e4ec58b60e104b6defcb2063e20ab`. Verbatim stdout:
```
      0.20000000 
      0.40000000 

   2.2204460e-16 
   4.4408921e-16 
   8.8817842e-16 
```
GAUSS job header: `Job: inline_o1nph24s.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_toh_huq4\.gauss_code_execution_generated )`, Tue Oct 20 18:07:22 2026 (a deleted temporary directory, as the prompt said).

Expected behavior: `y / X` with literal X is not_ready (`/` violated, G0121); an approved run matches direct GAUSS.

Observed behavior: Three forms validated: `y / X` not_ready ("3x2 with linearly dependent columns; GAUSS's least-squares solve stops with G0121", new; real GAUSS G0121); `invpd(X'X)*X'y` review_required (the expression gap; the client correctly said X'X is singular and it would fail; real GAUSS G0121); `pinv(X)*y` handoff_candidate. "Yes confirm result with GAUSS" came before any prompt existed; the client treated it as a request to prepare, showed the prompt, and sent nothing to decide until the user's bare "yes". Output b = [0.2, 0.4], residuals ~1e-16, byte-identical to direct GAUSS.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
