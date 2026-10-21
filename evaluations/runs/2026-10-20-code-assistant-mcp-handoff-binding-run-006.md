# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.6
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Use eigh to get the eigenvalues of the matrix with rows [4, 1] and [0, 3]."

The user's later messages in this task, verbatim: "Prompt B: yes"; "yes".

Code (S07):
```gauss
x = { 4 1,
      0 3 };

va = eigh(x);
print va;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **not_ready**; preconditions: `eigh` violated; coverage gaps: none.
Reasons: "eigh: the literal input matrix is not symmetric; eigh reads only its lower triangle and would silently return the eigenvalues of a different matrix (use eig for a general matrix)"
v0.86.0, same snippet: **handoff_candidate** (preconditions: none).
Real GAUSS (`tgauss.exe -b`): runs.

Code (S08):
```gauss
x = { 4 1,
      0 3 };

// x is not symmetric, so use eig (general matrix) rather than eigh
va = eig(x);
print va;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **handoff_candidate**; preconditions: none; coverage gaps: none; `code_sha256` e4177ffca275….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
v0.86.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs.

Expected behavior: not_ready: `eigh` violated (non-symmetric literal).

Observed behavior: not_ready with the new reason ("eigh reads only its lower triangle and would silently return the eigenvalues of a different matrix (use eig for a general matrix)"). The client explained that `eigh` would print 3 and 4 here only because the matrix is triangular (confirmed: S07 under `tgauss.exe -b` prints 3, 4), gave the true answer 4 and 3, and validated an `eig` version (handoff_candidate) without preparing it. In the same turn the user answered prompt B: "Prompt B: yes" was `unrecognized` (B's id echoed); "yes" ran B, byte-identical to direct GAUSS. v0.86.0: S07 was **handoff_candidate**.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
