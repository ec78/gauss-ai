# Evaluation Result

Date: 2026-10-28
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`a3570b26…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-81x`), as in 80.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, answered every run prompt themselves, and answered three of the client's own numbered options ("2", "1", "1"). All tasks ran on 2026-10-28, 06:01-06:19 local (11:01-11:19 UTC). The client used only gauss-ai tools: no file read, no shell command, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.90.0 (tag `v0.90.0`, commit `1ee121c`, pushed 2026-10-24; not yet on PyPI), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.90.0).
Prompt ID: 81.7
Prompt Category: MCP Call-Form Alignment of v0.90.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.90.0 over stdio, registered at user scope with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (the 2026-10-23 fetch), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session served every task; `gauss_session_start` reported `server_version: 0.90.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 25 search, read and validation calls through `gauss_mcp_server`'s tool functions at `v0.90.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.89.3` (`328dffa`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all eight approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory.
Prompt Text:

"Estimate an OLS regression on simulated data with olsmt, and print the coefficients and their standard errors."

Search `asDF rndseed rndn olsmtOut stderr` (#29), then `gauss_read_doc("olsmt.rst", ...)` (#30).

Code (#31):
```gauss
// Set seed for repeatable output
rndseed 12345;

// Simulate regressors and error term
x1 = rndn(100, 1);
x2 = rndn(100, 1);
e = rndn(100, 1);

// True model: y = 1 + 2*x1 - 0.5*x2 + e
y = 1 + 2*x1 - 0.5*x2 + e;

// Convert to a dataframe with variable names
data = y ~ x1 ~ x2;
df = asdf(data, "y", "x1", "x2");

// Estimate OLS
struct olsmtOut out;
out = olsmt(df, "y ~ x1 + x2");

// Print coefficients and standard errors (constant first)
print out.b ~ out.stderr;
```
Captured output (live, identical on the v0.90.0 re-run): **review_required**.
Reasons: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `asdf` argument 1 (parameter `x`): `data` is assigned from an expression (`y ~ x1 ~ x2`), which is never evaluated"; "parameter role unknown -- `asdf` argument 2 (parameter `varname_1`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `asdf` argument 3 (parameter `varname_2`): no documented `:type` line was matched to this parameter".
Coverage gaps: asdf arg 1 (`x`) `argument_assigned_from_expression`; asdf arg 2 (`varname_1`) `documented_type_missing`; asdf arg 3 (`varname_2`) `documented_type_missing`.
v0.89.3: identical.

Diagnosis: `olsmt(df, "y ~ x1 + x2")` itself has no gap: its formula form aligns, and the v0.89.3 dataset rule passes `df`, which is traced to `asdf`'s documented dataframe return. The gaps are all `asdf`'s: `data` is built from an expression (`y ~ x1 ~ x2`), and `asdf.rst` gives `varname_1`/`varname_2` no `:type` line. The client's account agrees.

The client offered to let the user run it, or to try a matrix version whose standard-error step would also pass expressions; the user chose to run it themselves. Nothing ran.

Expected behavior: review_required with the expression gap (plan §7).

Observed behavior: review_required, honestly explained. Compared with 80.10, the gap no longer names a wrong `olsmt` parameter; but simulated data is still unrunnable, because it is always built from expressions (finding 2).

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.6
Decision: Pass
