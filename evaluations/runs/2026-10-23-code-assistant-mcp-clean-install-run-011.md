# Evaluation Result

Date: 2026-10-23
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension 2.1.309), driven live as the MCP client in a fresh conversation (`0819d226…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-80x`), so neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's own memory directory is empty). An earlier conversation in the same folder (`ee5f3edc…`, 06:53 local) only started a session before the real-GAUSS opt-in was registered (`runner: fake`, `real_gauss_allowed: false`). The human asked each task in plain words, one at a time, and answered every run prompt themselves. All tasks ran on 2026-10-23, 06:59-07:18 local (10:59-11:18 UTC). During the tasks the client read no gauss-ai source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`, and read no GAUSS documentation file from disk; it ran `gauss-ai doctor` and two directory listings in PowerShell, and in 80.14 read the user's own `dccelib` package (`C:\gauss26\pkgs\dccelib`, an additional working directory of that Claude Code setup) from disk.
Agent Version: v0.89.1 (tag `v0.89.1`, commit `f6b9c6f`), installed as a stranger would: `pip install "gauss-ai[mcp] @ git+https://github.com/ec78/gauss-ai@v0.89.1"` into the user's Python 3.12 after `pip uninstall` of the editable install, with `~/.gauss-ai/` moved aside first (`gauss-ai version` = 0.89.1).
Prompt ID: 80.11
Prompt Category: MCP Clean-Install Walkthrough of v0.89.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.89.1 over stdio, registered at user scope (`claude mcp add --transport stdio --scope user gauss-ai -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`). Fresh config written by the quickstart: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (a new `gauss-ai docs fetch` on 2026-10-23), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss, no workspace parent. One server session (`e28987e1…`) served every task; `gauss_session_start` reported `server_version: 0.89.1` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run: the recording session (this repository's own Claude Code session) re-ran every one of the 33 search, read and validation calls (8 searches, 11 reads, 14 validations) by calling `gauss_mcp_server`'s tool functions at the `v0.89.1` tag and on a `git archive` of `v0.88.0` (each archive's modules asserted imported), against the same docs copy. **Every live response equals the v0.89.1 re-run in every field** (`validation_id`, digests and the session id aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) re-runs of every approved snippet and of the probes, each from its own new empty directory under the recording session's scratchpad.
Prompt Text:

"Make a scatter plot of 75 random points."

Search `plotScatter` (#39, grounded; Syntax `plotScatter([myPlot, ]x, y); plotScatter([myPlot, ]df, formula)`).

First code (#40):
```gauss
rndseed 345567;
x = rndn(75, 1);
y = rndn(75, 1);
plotScatter(x, y);
```
Captured output (live, identical on the v0.89.1 re-run): **review_required**.
Reasons: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `plotScatter` argument 1 (parameter `myPlot`): the argument (traced to `x = ...`, a call whose documented return type is matrix) may not fit the documented type for parameter 'myPlot' (control); a documented return type is not precise enough to call this a mismatch".
Coverage gaps: parameter_role/plotScatter arg 1 (`myPlot`) `return_type_imprecise`
The same misalignment as 80.10 (finding 2): `x` was checked against the optional leading `myPlot`. With literal `x`/`y` the call is a false **not_ready** (probe c1; GAUSS runs it).

Second code (#41), with a `plotControl` structure passed explicitly and a title:
Captured output (live, identical on the v0.89.1 re-run): **review_required**.
Reasons: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `plotSetTitle` argument 1 (parameter `&myPlot`): no documented `:type` line was matched to this parameter".
Coverage gaps: parameter_role/plotSetTitle arg 1 (`&myPlot`) `documented_type_missing`
This is the `&`-parameter gap disclosed since v0.83.0 (74.16).

Third code (#42), the title dropped:
```gauss
rndseed 345567;
x = rndn(75, 1);
y = rndn(75, 1);

struct plotControl myPlot;
myPlot = plotGetDefaults("scatter");

plotScatter(myPlot, x, y);
```
Captured output (live, identical on the v0.89.1 re-run): **handoff_candidate**.
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad".
v0.88.0: all three identical.

**The client shaped code around a known defect**, and said so: it passed `myPlot` explicitly to avoid finding 2, and dropped `plotSetTitle` to avoid the `&` gap.

Execution handoff (prepare #43, `request_id` `7c990d69-af9b-4803-854b-a56afc7808a5`). Before preparing, the client warned that `tgauss` has no window and the directory is deleted, so no plot would be visible. The user: "yes run anyways", then "yes" to the prompt itself (decide #44): outcome `success`, launched True; stdout:
```
(none)
```
Real GAUSS: exit 0, no output, as live.

Expected behavior: likely review_required (plan §7).

Observed behavior: the plain call was review_required for a false reason (finding 2); the reshaped call ran, but **no plot can be seen or kept** through the handoff (finding 4, the run environment; `plotSave` is a file write).

Pass/fail: Fail
Defect severity: Medium (finding 2, as 80.10)
Remediation: As 80.10 for finding 2; the plot-output gap belongs to the analysis-workspace milestone.

Overall Score: 3.3
Decision: Fail
