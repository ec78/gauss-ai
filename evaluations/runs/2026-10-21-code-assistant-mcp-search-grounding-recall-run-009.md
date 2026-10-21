# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.9
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"Generate 2 columns of random data with 75 observations each and plot the data as a scatter plot"

Search `plotScatter` (live, identical on the v0.88.0 re-run): **grounded**
- sources: `plotscatter` (plotscatter.rst)
- unmatched: none; ambiguous: none
- v0.87.0, same query: identical

Code (call #23):
```gauss
// 75 observations, 2 columns of standard normal random data
rndseed 2026;
data = rndn(75, 2);

x = data[., 1];
y = data[., 2];

// Plot control structure for titles and axis labels
struct plotControl myPlot;
myPlot = plotGetDefaults("scatter");
plotSetTitle(&myPlot, "75 random observations");
plotSetXLabel(&myPlot, "Column 1");
plotSetYLabel(&myPlot, "Column 2");

plotScatter(myPlot, x, y);
```

Captured output (live, reproduced exactly on v0.88.0): **review_required**; preconditions: none.
Reasons: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `plotSetTitle` argument 1 (parameter `&myPlot`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `plotSetXLabel` argument 1 (parameter `&myPlot`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `plotSetYLabel` argument 1 (parameter `&myPlot`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `plotScatter` argument 2 (parameter `x`): `x` is assigned from an expression (`data[., 1]`), which is never evaluated"; "parameter role unknown -- `plotScatter` argument 3 (parameter `y`): `y` is assigned from an expression (`data[., 2]`), which is never evaluated"
Coverage gaps: parameter_role/plotSetTitle arg 1 `documented_type_missing`; parameter_role/plotSetXLabel arg 1 `documented_type_missing`; parameter_role/plotSetYLabel arg 1 `documented_type_missing`; parameter_role/plotScatter arg 2 `argument_assigned_from_expression`; parameter_role/plotScatter arg 3 `argument_assigned_from_expression`
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no output and no error. Batch mode opens no graphics window, so nothing is displayed, as the client said.

Expected behavior: `plotScatter` grounds; review_required (expression arguments; `&myPlot` has no documented `:type`).

Observed behavior: Grounded; identical on v0.87.0. review_required: three `documented_type_missing` gaps (`&myPlot` for `plotSetTitle`/`plotSetXLabel`/`plotSetYLabel`) and two `argument_assigned_from_expression` gaps (`data[., 1]`, `data[., 2]`). The diagnosis agrees, and the client named both causes. It also said, correctly, that the batch runner could not show a plot anyway.

Search: **steered by prior knowledge**: the client searched `plotScatter`, not the user's words.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.8
Decision: Pass
