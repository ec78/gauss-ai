# Evaluation Result

Date: 2026-10-28
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`a3570b26…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-81x`), as in 80.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, answered every run prompt themselves, and answered three of the client's own numbered options ("2", "1", "1"). All tasks ran on 2026-10-28, 06:01-06:19 local (11:01-11:19 UTC). The client used only gauss-ai tools: no file read, no shell command, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.90.0 (tag `v0.90.0`, commit `1ee121c`, pushed 2026-10-24; not yet on PyPI), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.90.0).
Prompt ID: 81.5
Prompt Category: MCP Call-Form Alignment of v0.90.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.90.0 over stdio, registered at user scope with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (the 2026-10-23 fetch), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session served every task; `gauss_session_start` reported `server_version: 0.90.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 25 search, read and validation calls through `gauss_mcp_server`'s tool functions at `v0.90.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.89.3` (`328dffa`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all eight approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory.
Prompt Text:

"Run an OLS regression with olsmt where y = 2, 3, 1, 7, 5 and x has rows (1 3 2), (2 3 1), (7 1 7), (5 3 1), (3 5 5). Print the coefficients."

Search `olsmt olsmtOut olsmtControl matrix inputs` (#17), then `gauss_read_doc("olsmt.rst", ...)` (#19).

Code (#18):
```gauss
y = { 2, 3, 1, 7, 5 };

x = { 1 3 2,
      2 3 1,
      7 1 7,
      5 3 1,
      3 5 5 };

// Estimate OLS using matrices (empty string for data)
struct olsmtOut out;
out = olsmt("", y, x);

// Print coefficients (constant first)
print out.b;
```
Captured output (live, identical on the v0.90.0 re-run): **review_required**.
Reasons: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `olsmt` argument 2 (parameter `depvar`): no documented `:type` line was matched to this parameter".
Coverage gaps: olsmt arg 2 (`depvar`) `documented_type_missing`.
**v0.89.3: not_ready** ("… does not match the documented type for parameter 'formula' (string)"): the false not_ready of 80.x finding 2, now gone.

Diagnosis (`validate_code` directly): the arguments now align with `olsmt(data, depvar, indvars[, ctl])`; `data` and `indvars` match. The only gap is real: **`olsmt.rst` documents `depvar` with no `:type` line** (its prose says "Nx1 vector"). The `coverage_gaps` the client saw agree, and the client read them correctly: "the block comes from a gap in the docs."

The client offered two options (run `olsmt` yourself, or matrix least squares here); the user chose 2. `X = ones(rows(x), 1) ~ x; b = y / X;` (#20) was **review_required**: `ones` arg 1, `rows(x)` is an expression. The client then wrote `ones(5, 1)` (#21): handoff_candidate.

Execution handoff (prepare #22, `request_id` `55f5e9e4-13c5-45a2-8292-309de8d35fa3`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
y = { 2, 3, 1, 7, 5 };

x = { 1 3 2,
      2 3 1,
      7 1 7,
      5 3 1,
      3 5 5 };

// Add a constant column, matching the olsmt default
xc = ones(5, 1) ~ x;

// Least squares coefficients (constant first)
b = y / xc;
print b;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 2842996ad34536d4090c1b43cdfaae698dd77d1b92578abd29ab7e40c98ebd32

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id` (decide #23): outcome `success`; stdout:
```
-3.1488825 
       1.1045422 
       1.7278298 
     -0.75342466
```
Real GAUSS (`tgauss.exe -b`, recording session): byte-identical stdout.

Expected behavior: review_required naming `depvar`/`ctl`, not `formula` (plan §9.1, deviation 5).

Observed behavior: as expected, and the gap is named correctly. But `olsmt`'s matrix form still cannot run through gauss-ai (finding 1), and the workaround needed a literal where `rows(x)` is idiomatic (finding 2). **The client shaped code around a known limitation** (expressions are never evaluated), and said so.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.6
Decision: Pass
