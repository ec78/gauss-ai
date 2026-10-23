# Evaluation Result

Date: 2026-10-23
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension 2.1.309), driven live as the MCP client in a fresh conversation (`0819d226…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-80x`), so neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's own memory directory is empty). An earlier conversation in the same folder (`ee5f3edc…`, 06:53 local) only started a session before the real-GAUSS opt-in was registered (`runner: fake`, `real_gauss_allowed: false`). The human asked each task in plain words, one at a time, and answered every run prompt themselves. All tasks ran on 2026-10-23, 06:59-07:18 local (10:59-11:18 UTC). During the tasks the client read no gauss-ai source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`, and read no GAUSS documentation file from disk; it ran `gauss-ai doctor` and two directory listings in PowerShell, and in 80.14 read the user's own `dccelib` package (`C:\gauss26\pkgs\dccelib`, an additional working directory of that Claude Code setup) from disk.
Agent Version: v0.89.1 (tag `v0.89.1`, commit `f6b9c6f`), installed as a stranger would: `pip install "gauss-ai[mcp] @ git+https://github.com/ec78/gauss-ai@v0.89.1"` into the user's Python 3.12 after `pip uninstall` of the editable install, with `~/.gauss-ai/` moved aside first (`gauss-ai version` = 0.89.1).
Prompt ID: 80.10
Prompt Category: MCP Clean-Install Walkthrough of v0.89.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.89.1 over stdio, registered at user scope (`claude mcp add --transport stdio --scope user gauss-ai -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`). Fresh config written by the quickstart: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (a new `gauss-ai docs fetch` on 2026-10-23), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss, no workspace parent. One server session (`e28987e1…`) served every task; `gauss_session_start` reported `server_version: 0.89.1` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run: the recording session (this repository's own Claude Code session) re-ran every one of the 33 search, read and validation calls (8 searches, 11 reads, 14 validations) by calling `gauss_mcp_server`'s tool functions at the `v0.89.1` tag and on a `git archive` of `v0.88.0` (each archive's modules asserted imported), against the same docs copy. **Every live response equals the v0.89.1 re-run in every field** (`validation_id`, digests and the session id aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) re-runs of every approved snippet and of the probes, each from its own new empty directory under the recording session's scratchpad.
Prompt Text:

"Estimate an OLS regression on simulated data with olsmt, and print the coefficients and their standard errors."

Search `olsmt` (#32, grounded) and five `gauss_read_doc` reads of `olsmt.rst` (#33-#37: the outline, "Basic usage with matrices", Format in two pages of 8,000 + 2,054 characters, and a dataset example).

Code (#38):
```gauss
new;
rndseed 345567;

// Simulate y = 1 + 2*x1 - 0.5*x2 + e
n = 500;
x = rndn(n, 2);
e = rndn(n, 1);
b_true = { 2, -0.5 };
y = 1 + x * b_true + e;

// Control structure: suppress the printed report
struct olsmtControl ctl;
ctl = olsmtControlCreate();
ctl.output = 0;

struct olsmtOut out;
out = olsmt("", y, x, ctl);

print "Estimate  Std. error";
print out.b ~ out.stderr;
```
Captured output (live, identical on the v0.89.1 re-run): **review_required**.
Reasons: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `olsmt` argument 2 (parameter `formula`): `y` is assigned from an expression (`1 + x * b_true + e`), which is never evaluated"; "parameter role unknown -- `olsmt` argument 3 (parameter `ctl`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `olsmt` argument 4 (parameter `depvar`): no documented `:type` line was matched to this parameter".
Coverage gaps: parameter_role/olsmt arg 2 (`formula`) `argument_assigned_from_expression`; parameter_role/olsmt arg 3 (`ctl`) `documented_type_missing`; parameter_role/olsmt arg 4 (`depvar`) `documented_type_missing`
v0.88.0: identical.

Diagnosis (`validate_code` directly; `parameter_role_checks`): the role check compares argument *i* with parameter *i* of `olsmt`'s **merged** parameter list (`data, formula, ctl, depvar, indvars, …`), built from both documented call forms (`olsmt(data, formula[, ctl])` and `olsmt(data, depvar, indvars[, ctl])`). The four-argument call can only be the second form, but arguments 2, 3 and 4 were checked against `formula`, `ctl` and `depvar`. **The `coverage_gaps` the client saw agree with this diagnosis**, and the client named the cause correctly ("matched the wrong form"). Only the first gap (`y` built from an expression) is a true reason.

Recording-session probes (v0.89.1 and v0.88.0, identical):
- the docs' own matrix example, `out = olsmt("", y, x, ctl);` with literal `y` and `x` → **not_ready**: "olsmt (argument 2): the argument's literal category (vector) … does not match the documented type for parameter 'formula' (string)". **Real GAUSS runs it** (c2: prints the four coefficients);
- `plotScatter(x, y)` with literal vectors → **not_ready** for the same reason (80.11).

So the misalignment is a real, pre-existing validator defect (finding 2): with traced arguments it yields false `review_required` gaps; with literal arguments, a false **not_ready** whose stated reason is untrue. It is in the safe direction (it never lets code run), but it blocks the docs' own examples. Not in `KNOWN_LIMITATIONS.md`.

Expected behavior: likely review_required with no run offered; output members taken from the docs (plan §7).

Observed behavior: review_required as expected, and `out.b`/`out.stderr`, `ctl.output`, `ctl.con` and `ctl.cov = "robust"` were all taken from the page. The client did not shape this code around the defect.

Pass/fail: Fail
Defect severity: Medium (validator: arguments matched to the wrong call form; false reasons, and false not_ready for valid literal calls)
Remediation: Align arguments with the call form the call can match (arity, and an optional leading `[p, ]`) before checking roles; a later milestone under decision 10 = B, with an all-pages signature diff and a verdict diff.

Overall Score: 3.2
Decision: Fail
