# Evaluation Result

Date: 2026-10-28
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`a3570b26…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-81x`), as in 80.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, answered every run prompt themselves, and answered three of the client's own numbered options ("2", "1", "1"). All tasks ran on 2026-10-28, 06:01-06:19 local (11:01-11:19 UTC). The client used only gauss-ai tools: no file read, no shell command, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.90.0 (tag `v0.90.0`, commit `1ee121c`, pushed 2026-10-24; not yet on PyPI), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.90.0).
Prompt ID: 81.6
Prompt Category: MCP Call-Form Alignment of v0.90.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.90.0 over stdio, registered at user scope with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (the 2026-10-23 fetch), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session served every task; `gauss_session_start` reported `server_version: 0.90.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 25 search, read and validation calls through `gauss_mcp_server`'s tool functions at `v0.90.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.89.3` (`328dffa`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all eight approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory.
Prompt Text:

"Fit a logistic regression with glm where y = 0, 1, 0, 1, 1, 0, 1, 1 and x = 1 through 8, and print the coefficients."

Search `glm binomial logit matrix inputs glmOut` (#24), then `gauss_read_doc("glm.rst", ...)` (#25) for the family values and the output members.

Code (#26):
```gauss
y = { 0, 1, 0, 1, 1, 0, 1, 1 };
x = { 1, 2, 3, 4, 5, 6, 7, 8 };

// Logistic regression (binomial family, canonical logit link)
struct glmOut out;
out = glm(y, x, "binomial");

// Print coefficients (intercept first)
print out.coef.estimates;
```
Captured output (live, identical on the v0.90.0 re-run): **handoff_candidate**.
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad".
v0.89.3: identical (this three-argument call was never misaligned). The v0.89.3 dataset-file rule passes it: `y` is a literal.

Execution handoff (prepare #27, `request_id` `1c9697c8-ded7-4ded-8ace-09c8b96cb9a6`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
y = { 0, 1, 0, 1, 1, 0, 1, 1 };
x = { 1, 2, 3, 4, 5, 6, 7, 8 };

// Logistic regression (binomial family, canonical logit link)
struct glmOut out;
out = glm(y, x, "binomial");

// Print coefficients (intercept first)
print out.coef.estimates;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 106c8e2614db52f60ecb73a593af51afe1b67c17bbe7a332c2d25b644113161e

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id` (decide #28): outcome `success`; stdout:
```
Generalized Linear Model
===================================================================
Valid cases:               8           Dependent variable:        y
```
Real GAUSS (`tgauss.exe -b`, recording session): byte-identical stdout.

Expected behavior: not planned in detail ("new territory").

Observed behavior: grounded, handoff_candidate, and a full GLM table in real GAUSS (intercept −1.180, slope 0.398).

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
