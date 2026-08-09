# v0.68.0 - Real GAUSS End-to-End Alpha Validation

This milestone validates the complete installed product using **real GAUSS**, not fake substitution, exclusively through the installed `gauss-ai` command — exactly as an alpha tester would use it. No new reasoning stage, approval layer, durable session, or autonomous behavior was added; the core pipeline and the `v0.67.0` packaging layer are otherwise untouched.

## Validation Methodology

Every scenario in this milestone was driven through the real, installed `gauss-ai` console-script entry point via subprocess — real interactive stdin/stdout piping against the actual binary — never by importing product modules directly (except where the existing unit-test suite requires it, per its own long-standing convention). This proves the alpha experience as a tester will actually encounter it, not merely the underlying modules in isolation.

## Real GAUSS Scenarios

A successful execution, `G0105`, `G0036`, and `G0025` were each independently reproduced directly against `tgauss.exe -b` first, then reproduced again through the installed CLI, confirming both that this repository's own error catalog triggers are accurate and that the CLI faithfully surfaces real GAUSS behavior rather than a fake substitute. A complete real-GAUSS repair cycle — execution → interpretation → diagnosis → strategy approval → draft → draft approval → application approval → application gate → repair application → real verification execution → human review — was run end to end via `gauss-ai repair <file.gss> --runner gauss`, together with real output-file creation and explicit reading (`outputs` for metadata, `read <path>` for content). Every captured transcript explicitly shows `execution_backend: REAL_GAUSS`, `gauss_ran: true`, and a real, measured `duration_seconds`.

## Fake-Mode Scenarios

Cancelled approvals at every layer, blocked application from a stale source, completed-workspace rejection, and `reset` behavior were validated through the same installed CLI in fake mode, since these are pipeline mechanics, not GAUSS-specific — real GAUSS was used only where it was actually needed.

## Export-Session Diagnostic Bundle

A new, read-only `--export-session PATH` flag on `gauss-ai repair` (`scripts/gauss_ai_export.py`) writes a one-time JSON bundle at the end of the same process: package/Python/platform versions, configuration, runner backend, GAUSS executable and version-from-path, workspace identity, and the full session transcript — no secrets, since the configuration model has no field capable of holding one. Deliberately not a standalone command and not a durable session: there is no persisted state for a later, separate invocation to read. 11 new tests in `scripts/test_gauss_ai_export.py` prove it never changes repair outcome or terminal output, defines no execution/repair function of its own, and reads no arbitrary file.

## Defect Found and Fixed

One genuine, narrowly-scoped defect was found — the central purpose of this milestone. `examples/alpha-demo/broken.gss` had only ever been exercised in fake mode before (where `--fake-result` makes actual file content irrelevant) and had never actually been run against real GAUSS. Running it for real for the first time found it reproduced a *different*, uncataloged error (`G0008`), not the `G0105` it claimed. The pipeline itself behaved correctly and safely throughout — it disclosed the uncataloged code honestly and fabricated no cause or repair strategy; only the example file's own content was inaccurate. Fixed by correcting `broken.gss` to the catalog's own exact verified trigger (`x = ;`) and re-confirming end to end, in both fake mode and against real GAUSS, against the corrected file — with the real file on disk confirmed untouched by the guided workflow throughout.

## New Alpha Documentation

`docs/private-alpha-testing.md` (entry point: install, first run, what was validated, expected workflow, known limitations, how to report issues), `docs/reporting-bugs.md` (evidence-gathering and reporting process), `docs/known-alpha-limitations.md` (tester-facing limitations summary) — all new. `docs/alpha-feedback-template.md` extended with an "Exported Diagnostic Bundle" section and an optional "Screenshots" section. `README.md` given explicit "Private Alpha Testing," "Expected Workflow," and "How to Report Issues" sections.

## Tests Added

11 new tests in `scripts/test_gauss_ai_export.py` (detailed above). Full existing regression suite (36 test files) re-run and passing unchanged — zero diff on every core pipeline module and every prior `v0.67.0` alpha-packaging module beyond the two files touched to wire in `--export-session`.

## Full Regression Results

All 33 fake-mode-default test files pass. The three doubly-gated real-GAUSS regression harnesses (`test_gauss_execution_adapter_real.py`, `test_gauss_execution_workflow_real.py`, `test_gauss_runtime_orchestration_real.py`) correctly skip by default with no GAUSS touched; run explicitly with both required gates (`--run-real-gauss` and `GAUSS_AI_ALLOW_REAL_EXECUTION=1`) against `c:\gauss26\tgauss.exe`, the adapter-level harness completed a real, successful GAUSS invocation confirming the environment is genuinely wired end to end.

## Installation Verification

A fresh, disposable virtual environment installation (`pip install -e .`) was re-confirmed after all `v0.68.0` changes: `gauss-ai version` reports `0.68.0`; `gauss-ai doctor` correctly reports WARN (no GAUSS configured yet) on a clean environment and PASS across every check once `gauss-ai config set gauss-executable` points at the real terminal executable, including the version-parsed-from-path disclosure ("GAUSS was not launched").

## 58.x Benchmark Results

A new `58.x` Real Alpha Validation category (ten prompts) was fully evaluated against real, executed evidence — real GAUSS invocations, the installed CLI, and the genuine defect discovery and fix above. **10/10 Passed at 4.0.**

## Evaluation Tracking

`check_evaluation_tracking.py --json` reports 544 prompt IDs, 544 coverage rows, 511 run files referenced, 516 index entries, 0 errors, and the same 3 pre-existing historical warnings carried from prior milestones (two documented historical exceptions, plus one pre-existing untracked scratch file unrelated to this milestone) — `overall_pass: true`.

## Release Readiness

`check_release_readiness.py` — PASS (`validate_all_evidence.py` PASS, `check_evaluation_tracking.py` PASS).

## Supported Alpha Environment

**Windows**, verified against **GAUSS 26.1.1** for real execution. Python 3.10+. Fake-mode testing (packaging, CLI, guided workflow, doctor, init, config) has no OS-specific dependency but has only been exercised on Windows. macOS/Linux real-GAUSS execution is not claimed or supported.

## Alpha Readiness Classification

**Private Alpha.** Real GAUSS execution has now been validated end to end through the installed product itself, covering successful execution, three cataloged error codes, a complete repair-and-verification cycle, and output-file handling, with zero pipeline or safety defects found — only one narrowly-scoped example-content defect, found and fixed by this same validation process. Every safety guarantee established since `v0.62.0` (explicit confirmation before execution, independent digest-bound approval at every layer, no file read without explicit authorization, no file write except through the approved application transaction, no fabricated review) was re-proven against real GAUSS, not merely assumed to still hold. Not yet broader-alpha-ready: real-GAUSS verification remains bounded to one machine, one GAUSS version (26.1.1), and Windows only; broader alpha would need evidence from additional testers, environments, and GAUSS versions first.

## Not Implemented

Durable sessions, rollback, multi-file repair, cloud execution, new approval layers, new repair intelligence, autonomous repair, automatic retries, an LLM redesign, new workflow stages, a database, telemetry, and analytics.

## Recommendation for the Next Milestone

Broaden alpha participation to additional testers and, where possible, additional GAUSS versions/environments, using the reporting process this milestone put in place (`docs/reporting-bugs.md`, `--export-session`). This milestone deliberately does not request or imply that authorization.
