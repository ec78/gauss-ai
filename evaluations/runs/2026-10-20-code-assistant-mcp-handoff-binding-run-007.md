# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.7
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Solve A x = b where A has rows [1, 2] and [2, 4], and b = [1, 2]."

Code (S09):
```gauss
A = { 1 2,
      2 4 };
b = { 1, 2 };

x = b/A;
print x;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **not_ready**; preconditions: `/` violated; coverage gaps: none.
Reasons: "no documented GAUSS function call was found to ground this code against -- code with no documented calls is never eligible for controlled execution"; "/: the literal divisor is a singular square matrix (zero determinant); GAUSS stops with G0048"
v0.86.0, same snippet: **not_ready** (preconditions: none).
Real GAUSS (`tgauss.exe -b`): fails: `error G0048 : Matrix singular`.

Code (S10):
```gauss
A = { 1 2,
      2 4 };
b = { 1, 2 };

// A is singular (row 2 = 2 * row 1), so the '/' operator is not
// appropriate; pinv gives the minimum-norm solution
x = pinv(A)*b;
print x;

// Check the residual A*x - b
print A*x - b;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` 222c749b90f6….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs.

Expected behavior: `b / A` with a literal matrix dividend is not_ready (`/` violated, G0048).

Observed behavior: `x = b/A` not_ready with two reasons: no documented call, and "/: the literal divisor is a singular square matrix (zero determinant); GAUSS stops with G0048" (new). Real GAUSS: G0048. The client explained the system has infinitely many solutions and validated a `pinv(A)*b` minimum-norm version (handoff_candidate; prints 0.2, 0.4), not prepared. Its search "solve linear system singular matrix pinv" grounded `system.rst` (the command that exits GAUSS) and `sqpsolvemt.rst` for "solve" (the known English-word class, 75.x finding 7); it used only `pinv.rst`.

Pass/fail: Pass
Defect severity: None
Remediation: None (search items belong to v0.88.0).

Overall Score: 4.0
Decision: Pass
