# v0.67.0 - Productization and Alpha Packaging

This milestone moves the GAUSS Code Assistant from capability development to an installable alpha product. No new reasoning stage, approval layer, durable session, or autonomous behavior was added — the core pipeline (Execution through Repair Session Summary, MVP-complete as of `v0.66.0`) is untouched.

## Packaging Architecture

`pyproject.toml` declares `package-dir = {"" = "scripts"}` plus every non-test module by name — **no repository restructure**. Every existing `scripts/gauss_*.py` module remains exactly as it is, importing its own siblings exactly as before. `pip install -e .` and `pip install .` both work; `python scripts/gauss_code_assistant_cli.py` continues to work exactly as before, unaffected by anything in this milestone.

## Installation Method

```
pip install -e .
```

Installs the `gauss-ai` console-script entry point and every existing module as a directly importable top-level module — no dotted namespace, no manual `sys.path` setup required by the user.

## CLI Entry Point

`gauss-ai`, backed by a new, thin dispatcher (`scripts/gauss_ai_cli.py`) that duplicates no CLI implementation: `version`/`doctor`/`init`/`config`/`repair` each call a small, dedicated new module; the no-subcommand path calls the existing, unmodified `gauss_code_assistant_cli.main(...)`.

## Version Command

`gauss-ai version` shows package version, Python version, platform, configured runner, and configured GAUSS executable. GAUSS's own version is parsed from the executable's path string only (`gauss_environment_check.parse_gauss_version(...)`, reused) — GAUSS is never launched merely to report its version.

## Configuration Model

`scripts/gauss_ai_config.py`: exactly four settings (`gauss_executable`, `default_runner`, `workspace_parent`, `default_timeout_seconds`) plus `verbose` — no secrets, no arbitrary key/value mechanism — at `~/.gauss-ai/config.json` (`Path.home()`, never hard-coded).

## Config Precedence

Explicit CLI argument → environment variable → local config file → safe default, applied identically to every setting. A genuine defect was found and fixed during this milestone's own development: `default_runner`/`default_timeout_seconds` originally had non-`None` dataclass defaults, making an absent config file indistinguishable from one that explicitly wrote the same value, misreporting precedence source as `config_file` instead of `default` — fixed by defaulting every settable field to `None` on the dataclass itself.

## Doctor Behavior

`gauss-ai doctor` (`scripts/gauss_ai_doctor.py`): read-only PASS/WARN/FAIL diagnostics — Python version, core module imports, workspace-parent writability, GAUSS executable configuration/validity, config-file validity, package version. Never runs GAUSS, installs anything, or mutates configuration. Two genuine defects were found and fixed during testing: a malformed workspace-parent path could raise an uncaught `ValueError` instead of a clean `FAIL` (now catches `(OSError, ValueError)`), and the executable-validity message didn't explicitly disclose GAUSS was not launched (now does).

## Init / First-Run Behavior

`gauss-ai init` (`scripts/gauss_ai_init.py`): idempotent. Reuses `gauss_environment_check.detect_environment(...)` for discovery; filters GUI executables out before ever offering them as a candidate; requires explicit numbered selection when multiple terminal candidates are found — never silently chosen. Re-running it reviews and updates prior configuration, never resets it.

## GAUSS Discovery Behavior

Reuses the existing `gauss_environment_check.py` PATH-lookup and common-installation-location scanning, layering the existing terminal-executable-only restriction (`gauss_code_execution.py`'s own canonical `tgauss`/`tgauss.exe` basename set) on top for `init`/`doctor`/`config set gauss-executable` — no new, inconsistent discovery implementation.

## Guided Repair Workflow

`gauss-ai repair <file.gss>` (`scripts/gauss_ai_guided_repair.py`): orchestration/UI only, driving the exact same `InteractiveMvpAdapter.handle_line(...)` sequence the lower-level REPL uses. Copies the named file into a fresh, approved workspace — the original file is never written to, anywhere in this module. Walks execution confirmation, diagnosis-driven strategy approval, a human-described draft, draft approval, application approval, a freshly-re-hashed application-gate check, application, an optional verification-and-review pass, and a closing session summary — every approval point requires a real, explicit answer. Two genuine defects were found and fixed during testing: the workspace copy was written via `write_text(...)`, which silently translates `\n` to `\r\n` on Windows and corrupted the content hash (now `write_bytes(...)`); and the application-gate check resupplied the original content hash instead of freshly re-reading the workspace file, so it could never detect real staleness (now re-reads and re-hashes immediately before the gate check).

## Safety-Boundary Preservation

`scripts/test_gauss_ai_guided_repair.py` (18 tests) proves the guided command cannot execute before confirmation, cannot auto-approve any of the three approval layers, cannot bypass the application gate, cannot read any file other than the one named, cannot rerun without an ordinary execution confirmation, cannot fabricate a review, and never writes outside the workspace it creates. Every core pipeline module (`gauss_code_assistant_cli.py` through `gauss_repair_session_summary.py`) has zero diff.

## CLI UX Changes

Plain-language guidance and per-step disclosure at every approval point in the guided workflow; `doctor`'s consistent PASS/WARN/FAIL formatting with actionable next steps; the lower-level command-by-command REPL is entirely unchanged and remains available for advanced/debugging use.

## Sample Project

`examples/alpha-demo/`: `working.gss` (valid) and `broken.gss` (a `G0105`-triggering missing semicolon — the exact verified fault class in `scripts/gauss_error_catalog.py`), with a README describing the expected workflow. Verified end to end against the real files, in both the "repair needed" and "nothing to repair" paths.

## Alpha Documentation

`docs/alpha-installation.md`, `docs/alpha-quickstart.md`, `docs/alpha-troubleshooting.md`, `docs/alpha-tester-guide.md` — new. `docs/alpha-feedback-template.md` extended with repair-pipeline-specific fields.

## Packaging Tests

`scripts/test_gauss_ai_packaging.py`: a real, disposable-venv `pip install -e .`, the installed entry point, `gauss-ai version`/`gauss-ai doctor` working without GAUSS installed, and cwd-independence (both the entry point and a direct module import work from a directory outside the repository entirely).

## Guided-Workflow Tests

`scripts/test_gauss_ai_guided_repair.py` (18 tests, detailed above) plus supporting coverage across `scripts/test_gauss_ai_config.py` (24), `scripts/test_gauss_ai_doctor.py` (21), `scripts/test_gauss_ai_init.py` (14), and `scripts/test_gauss_ai_cli.py` (17) — 94 new unit-style tests in total.

## Full Regression Results

Every existing test file (36 files, hundreds of tests) re-run and passing unchanged — zero diff on every core pipeline module.

## 57.x Benchmark Results

A new `57.x` Productization and Alpha Packaging category (ten prompts) was fully evaluated against a real, disposable virtual environment, the real `examples/alpha-demo/` files, and real `InteractiveMvpAdapter` sessions. **10/10 Passed at 4.0.** (Three genuine defects were found and fixed *during development*, all documented above and in each affected module's own docstring — the final evaluation itself found zero remaining defects.)

## Evaluation Tracking

`check_evaluation_tracking.py --json` reports 534 prompt IDs, 534 coverage rows, 501 run files referenced, 506 index entries, 0 errors, and the same 3 pre-existing historical warnings carried since `v0.52.0` — `overall_pass: true`.

## Release Readiness

`check_release_readiness.py` — PASS.

## Real GAUSS Execution

Not run for this milestone — every test uses the fake runner or zero-byte executable stubs (proving doctor/config/init never launch a configured executable). This is packaging/CLI validation, not a real-GAUSS smoke test; the core execution pipeline's own real-GAUSS verification (`v0.33.0`-`v0.35.0`) is unaffected and untouched.

## Supported Alpha Environment

**Windows**, verified against **GAUSS 26.1.1** for real execution (unchanged from prior milestones). Python 3.10+. Fake-mode packaging/CLI testing has no OS-specific dependency but has only been exercised on Windows in this milestone. macOS/Linux real-GAUSS execution is not claimed.

## Alpha Readiness Classification

**Ready for controlled private alpha.** Installation is a single `pip install -e .`; first-run setup, environment diagnostics, and a guided end-to-end workflow all work against real evidence with zero remaining defects; every existing safety boundary is provably preserved. Not yet broader-alpha-ready: no real-GAUSS smoke coverage was added this milestone, and only one environment (this development machine, Windows/GAUSS 26.1.1) has exercised the packaging path end to end.

## Not Implemented

Durable sessions, a database, telemetry, a cloud backend, a web app, an IDE plugin, automatic updates, multi-user accounts, authentication, multi-file repair, autonomous repair, automatic retry, rollback beyond the one mandatory backup, analytics, in-GAUSS package installation, license activation, and any new reasoning or approval layer.

## Recommendation for the Next Milestone

A bounded, explicitly-gated real-GAUSS end-to-end alpha smoke test (mentioned but deliberately not added by this milestone) — run the guided workflow once against a real terminal GAUSS executable, on this same verified Windows/GAUSS 26.1.1 environment, to extend confidence beyond fake-mode-only packaging validation. This milestone deliberately does not request or imply that authorization.
