# Evaluation Result

Date: 2026-10-20
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`d42da23b…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All sixteen tasks ran on 2026-10-20 (07:42-20:31 CDT, with breaks; the conversation hit a usage limit after 78.8 and resumed). During the tasks the client grepped `KNOWN_LIMITATIONS.md` (78.8, 78.10, 78.13) and the v0.87 plan (78.8), and read `scripts/gauss_pre_execution_validation.py` (78.13); `CLAUDE.md` was in its context from the start (v0.87 plan §11.7).
Agent Version: v0.87.0 (released; tag `v0.87.0`, commit `4103280`), editable install of this checkout (`gauss-ai version` = 0.87.0).
Prompt ID: 78.8
Prompt Category: MCP Handoff Binding and Precondition Coverage of v0.87.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.87.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: `gauss_session_start` reported `real_gauss_allowed: true` and one prepare returned a `rendered_prompt` before any other task (78.1). The client opened a new server session for most tasks (10 sessions in all). Two `gauss-ai-mcp` processes were running (PIDs 26780 and 29680, started 07:41:56 and 07:41:00); which one served the conversation was not determined, but every prompt carried v0.87.0's "Runs in" line. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.87.0 and v0.86.0, each archive's own modules asserted imported; all 21 live verdicts reproduced exactly on the v0.87.0 archive (state, reasons, every gap, every precondition, and `code_sha256` for the ten that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of every client program except S20 (a file write), each from its own new empty directory. Handoff runs through MCP: eight approved, none declined.
Prompt Text:

"Now compute the inverse of that same A, but write it as eye(2) / A instead of using inv."

The user's later messages in this task, verbatim: "continue".

Code (S11):
```gauss
A = { 1 2,
      2 4 };

Ainv = eye(2) / A;
print Ainv;
```

Captured output (live, reproduced exactly by direct `validate_code` on v0.87.0): **review_required**; preconditions: `/` unverified; coverage gaps: `/` `runtime_dependent`.
Reasons: "runtime-dependent precondition(s) remain unverified for: /"; "validation coverage is partial (incomplete: preconditions unknown), short of the broad evidence required for handoff candidacy"
v0.86.0, same snippet: **handoff_candidate** (preconditions: none).
Real GAUSS (`tgauss.exe -b`): fails: `error G0048 : Matrix singular`.

Expected behavior: review_required: `/` unverified, since `eye(2)`'s shape is not evaluated (disclosed).

Observed behavior: review_required with the `/` `runtime_dependent` gap and the designed explanation. Real GAUSS: G0048. The client grepped `KNOWN_LIMITATIONS.md` and the v0.87 plan for "dividend", and told the user the softer verdict was deliberate and disclosed, citing the plan's spot check dv03. v0.86.0: **handoff_candidate** (a literal singular solve offered for execution, 77.x finding 1).

Notes: The client read the milestone's planning doc (grep excerpts) during the tasks, which CLAUDE.md asks the testing session not to do (§11.7).

Pass/fail: Pass
Defect severity: Minor (client conduct)
Remediation: None

Overall Score: 3.6
Decision: Pass
