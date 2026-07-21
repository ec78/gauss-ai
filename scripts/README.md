# Scripts

## `command_doc_lookup.py`

Purpose:
Locate and extract limited, source-aware details from official GAUSS command-specific `.rst` documentation stored locally.

Example:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs"
```

For shareable example output, redact the local docs root:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs" --redact-docs-root
```

To retrieve keyword-focused evidence from the matched command page:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs" --keywords intercept formula missing ctl olsmtControl output returns
```

Keyword snippets are evidence from the matched documentation page. They are not interpretation, and the script should not infer behavior that is not present in the snippets.

Quote multi-word keyword phrases (for example `"not found"`) so the shell passes them as a single keyword. An unquoted multi-word phrase is split into separate single-word keywords, which can produce misleading individual-word hits instead of a real phrase match.

## Schema-Aligned Output (`--schema-output`)

By default, the script prints the legacy output shape described below. Pass `--schema-output` to instead emit an evidence object conforming to `schemas/command_lookup_evidence.schema.json`:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs" --keywords intercept formula missing ctl olsmtControl output returns --schema-output --redact-docs-root
```

`--schema-output` only changes the output shape — it does not change what is extracted or searched. It renames and regroups the same fields the legacy output already produces: `status` becomes `retrieval_status` (`found` splits into `found_complete`/`found_incomplete` depending on whether unresolved questions or extraction warnings exist), each match gains `command_name` and `source_authority`, and string sections that were `examples`/`notes` become string arrays (`""`/`null` -> `[]`, a non-empty string -> a one-element array). It also adds `schema_version`, `generated_at`, `tool_name`, `tool_version`, and `docs_root_redacted`.

`--schema-output` does not affect the default output format; omit the flag to get the original shape.

**Core vs. package source classification (added `v0.11.0`).** A matched local `.rst` file's `source_type`/`source_authority` is `official_local_rst`/`official_docs` by default, or `official_package_rst`/`official_package_docs` if the file's docs-root-relative path starts with a known GAUSS "Application" (package) directory — for example, `tsmt/tscsfit.rst` classifies as `official_package_docs`, while a core-docs file like `glm.rst` or `olsmt.rst` classifies as `official_docs`. The set of known package directories is derived from the official Applications index (`docs_root/applications.rst`'s own `:link:` targets, e.g. `tsmt/index` -> `tsmt`), not guessed from command names, and is hardcoded as `PACKAGE_DOC_DIRECTORIES` in `command_doc_lookup.py` as a snapshot of that index — it should be refreshed if the Applications index changes. A directory missing from this set is classified as core documentation by default, so a stale snapshot only under-classifies a newer package; it cannot mis-classify base GAUSS documentation as a package.

Validate schema-aligned output with:

```text
python scripts/validate_lookup_evidence.py path/to/evidence.json
```

## `validate_all_evidence.py`

Purpose:
Validate every committed schema-aligned evidence example and schema fixture in one pass, instead of running `validate_lookup_evidence.py` against each file individually. It reuses `validate_lookup_evidence.py`'s validation logic directly (imported, not reimplemented), so there is one source of truth for what "valid" means.

By default it checks every `*.json` file under `examples/retrieval/schema-aligned/` and `examples/retrieval/schema-fixtures/`:

```text
python scripts/validate_all_evidence.py
```

Pass specific files or directories to check a subset instead:

```text
python scripts/validate_all_evidence.py examples/retrieval/schema-aligned/olsmt.evidence.json
```

**Expected-valid vs. expected-invalid.** Every file is expected to pass schema validation, except files under `examples/retrieval/schema-fixtures/` whose name starts with `invalid-` (currently `invalid-missing-required-fields.json`), which are expected to *fail* schema validation on purpose. The script checks each file against its expected outcome, not just "did it pass": an expected-valid file that fails, or an expected-invalid file that unexpectedly passes, is reported as unexpected and causes a nonzero exit.

**`--strict`** is passed through to each file's validation, same as `validate_lookup_evidence.py`: it treats warnings as failures for expected-valid files. Two known examples: `olsmt.evidence.json` (two false-positive path warnings) and `glm.evidence.json` (four false-positive path warnings) both cite an official-docs HDF5-URI example (`h5://C:/gauss/examples/testdata.h5/mydata` and `h5://C:/gauss23/examples/testdata.h5/mydata`, respectively), so `--strict` reports both as unexpected failures — the script states this plainly rather than hiding it, since strict mode intentionally has a higher bar than the default.

**`--json`** emits a machine-readable summary (per-file results plus an overall `overall_pass`/`unexpected_count`) instead of the human-readable listing.

Exit code is `0` only when every file's actual outcome matches its expected outcome (under the current strictness setting); otherwise nonzero.

**Strict-mode policy (established `v0.7.0`, extended `v0.10.0`).** The default, non-strict run (`python scripts/validate_all_evidence.py`) is the release-health check and is expected to pass. `--strict` promotes warnings to failures, and the current evidence set is expected to fail under `--strict` on two files: `examples/retrieval/schema-aligned/olsmt.evidence.json` (two reviewed path-warning false positives) and `examples/retrieval/schema-aligned/glm.evidence.json` (four reviewed path-warning false positives) — both from official HDF5-URI documentation examples (`h5://C:/gauss/examples/testdata.h5/mydata` and `h5://C:/gauss23/examples/testdata.h5/mydata`), not leaked local paths. Both strict-mode failures are documented here rather than suppressed or worked around. Improving the validator's path-warning heuristic so these stop triggering is tracked as future work, not a release blocker.

This script does not require GAUSS to be installed and does not access the network. It checks evidence *structure*, not GAUSS semantic correctness — a file passing here is not proof that any GAUSS code was executed or that the command behavior described is current.

## `check_evaluation_tracking.py`

Purpose:
Check that the manual-evaluation tracking files stay consistent with each other: `evaluations/benchmark-prompts.md`, `evaluations/benchmark-coverage.md`, `evaluations/runs/INDEX.md`, and the run files under `evaluations/runs/`. It reuses these existing markdown files as its only inputs — it does not introduce a new metadata format, and it does not check response quality or scoring correctness, which remain a manual-evaluation responsibility per `workflows/manual-evaluation.md`.

```text
python scripts/check_evaluation_tracking.py
```

It checks, at minimum:

- Every benchmark prompt ID in `benchmark-prompts.md` has a row in `benchmark-coverage.md` (and flags a coverage row with no matching prompt heading as a warning).
- Every coverage row's status is a recognized value (`Not Run`, `Passed`, `Failed`, `Blocked`, `Accepted Exception`); anything else is an error.
- Every `Passed`/`Failed` coverage row references a run file, and that run file exists under `evaluations/runs/`. `Not Run` rows are not required to reference one.
- Every referenced run file contains `Prompt ID`, `Prompt Category`, `Overall Score`, and `Decision` fields.
- Every referenced run file appears in `runs/INDEX.md`, and every file `runs/INDEX.md` lists actually exists.
- `runs/INDEX.md`'s recorded Prompt ID for a run file matches that run file's own `Prompt ID:` field (a hard error — both are authored together at evaluation time, so a mismatch here is a real mistake, not a historical exception).
- Duplicate Prompt IDs across coverage rows, and the same run file referenced by more than one coverage row, are both errors.
- (Warning, not error) `benchmark-coverage.md`'s linked run file for a Prompt ID states a *different* Prompt ID internally — several early runs predate stable Prompt ID assignment and are deliberately linked this way, documented in `benchmark-coverage.md`'s own notes and its "Completed Runs Not Directly Covered By Current Stable Prompts" section; this check surfaces such a mismatch without failing the default run.
- (Warning) a run file exists under `evaluations/runs/` but is referenced by neither `benchmark-coverage.md` nor `runs/INDEX.md` (an orphaned or forgotten-to-be-indexed run).
- (Warning) a benchmark prompt in the current, highest-numbered category is still `Not Run`.

**`--json`** emits a machine-readable summary (`prompt_id_count`, `coverage_row_count`, `run_files_referenced`, `index_entry_count`, `errors`, `warnings`, `overall_pass`) instead of the human-readable listing.

**`--strict`** promotes warnings to failures, the same convention as `validate_lookup_evidence.py`/`validate_all_evidence.py`. The default, non-strict run is expected to pass; `--strict` is expected to fail on the two known findings named above (a documented historical Prompt ID mismatch, and one legacy `v0.3.0`-era smoke-test run file that predates the Prompt-ID-based tracking system entirely) — this is a policy choice, not a bug, consistent with the strict-mode policy already established for evidence validation. The full policy for these two warnings — what each one is, why it is preserved rather than fixed, and why it is not a current blocker — is documented in `evaluations/benchmark-coverage.md`'s "Historical Tracking Exceptions" section (added `v0.11.0`); this README only summarizes their existence, not the policy itself.

This script does not implement CI, does not rewrite the evaluation framework, and does not modify scoring rules, benchmark prompt text, or existing run files — it only reports what it finds under `evaluations/`.

## `check_release_readiness.py`

Purpose:
Run the default release-health guard suite — `validate_all_evidence.py` and `check_evaluation_tracking.py` — in one command, instead of running each separately and manually combining the results. This is a thin wrapper: it invokes both scripts exactly as documented above, prints their real output verbatim, and summarizes overall pass/fail. It does not add new validation logic, does not change either script's behavior, and does not suppress or reinterpret any warning.

```text
python scripts/check_release_readiness.py
```

By default it runs only the two scripts' default (non-strict) modes, since those are the release-health gates (see "Strict-mode policy and future CI expectations" below). Exit code is `0` only if both default checks pass.

**`--strict`** additionally runs both scripts in `--strict` mode and reports the result separately, labeled informational. Strict-mode failure is currently expected (see below) and never affects this script's own exit code — passing `--strict` cannot turn a real default-mode failure into a pass, and it cannot turn an expected strict-mode failure into something this script reports as blocking.

**`--json`** emits a machine-readable summary (`default_checks`, `default_pass`, and, with `--strict`, `strict_checks`/`strict_pass`/`strict_note`) instead of the human-readable listing. `overall_pass` always reflects the default checks only.

This script does not implement CI itself, but as of `v0.13.0` it is exactly what CI runs. It remains a local convenience wrapper too — the same command works identically whether you run it locally or CI runs it, so there is only one place to look for what "release-ready" currently means.

**CI (added `v0.13.0`).** `.github/workflows/release-readiness.yml` (name: "Release Readiness") runs on every `push` and `pull_request`. It checks out the repository, sets up Python 3.11, installs `jsonschema` (the one external dependency `validate_all_evidence.py` needs, via `validate_lookup_evidence.py`), and runs `python scripts/check_release_readiness.py` — default mode, no flags. Strict mode is **not** enforced by CI in `v0.13.0`: the workflow never passes `--strict`, so a currently-expected strict-mode failure never fails a CI run. The workflow does not filter, quiet, or otherwise post-process the command's output, so every warning either underlying script reports still appears in the CI log exactly as it would locally — nothing is hidden.

## Strict-mode policy and future CI expectations

- **Default checks are the release-health gates.** `python scripts/validate_all_evidence.py` and `python scripts/check_evaluation_tracking.py` (or `python scripts/check_release_readiness.py`, which runs both) passing with exit code `0` is what "release-ready" currently means. A default `PASS` does not mean zero warnings — it means zero errors/unexpected results, with any warnings present and accounted for.
- **Strict checks (`--strict`) are warning-free gates and are currently expected to fail.** This is a known, reviewed, and documented state, not an unresolved bug:
  - Evidence `--strict` fails on exactly `glm.evidence.json` and `olsmt.evidence.json`, both because of reviewed HDF5-URI path-warning false positives in official documentation examples (see `scripts/README.md`'s `validate_all_evidence.py` section above), not real path leaks.
  - Tracking `--strict` fails on exactly the two documented historical warnings in `evaluations/benchmark-coverage.md`'s "Historical Tracking Exceptions" section (a Prompt ID mismatch predating stable IDs, and a legacy smoke-test run file predating the Prompt-ID tracking system).
- **CI starts with default checks only** (`scripts/check_release_readiness.py` with no flags), not `--strict` — this is what `.github/workflows/release-readiness.yml` does as of `v0.13.0`. Running `--strict` in CI today would make every run fail on the same known, already-reviewed warnings, which trains reviewers to ignore CI failures rather than act on them.
- **Do not make CI (or this script) green by hiding warnings.** If a future warning needs to stop blocking `--strict`, the correct fix is to resolve the underlying condition (regenerate evidence so the path warning no longer fires, or actually reconcile a tracking mismatch) or to explicitly document a reviewed, permanent exception (as already done for both current cases) — never to change a validator to stop reporting something true.
- **A future CI setup could add `--strict` as a second, separate job once the current warnings are resolved or explicitly allowlisted** by name (matching the specific files/messages already documented here), so a *new* undocumented warning would still fail CI rather than being silently absorbed into an ever-growing exception list.

## `gauss_runtime_orchestration.py`

Purpose:
Mock-only, in-memory runtime orchestration controller skeleton (`v0.31.0` Phase 2 of `planning/v0.31.0-runtime-orchestration-design.md`'s Implementation Phases, extended in `v0.32.0` Phase 3 Increment 1 with an adapter-bridge). It implements the canonical execution request (`planning/v0.31.0-canonical-execution-request-contract.md`) and the 13-state runtime state machine (`planning/v0.31.0-runtime-state-machine-contract.md`) well enough for deterministic unit testing, against either an injected fake runner or the new `AdapterRunner` bridge to `gauss_execution_adapter.py` (both are fake-helper-only as of this revision). It does not redefine either contract's rules — it implements them, and where implementing them surfaced two genuine inconsistencies in the state-machine contract, those were fixed in the contract document itself, not silently worked around in code.

**This module never touches real GAUSS.** Explicitly and unconditionally:

- It never imports `scripts/gauss_code_execution.py` and never calls `execute_gauss_code(...)`, directly or indirectly. The only import this revision adds, `gauss_execution_adapter`, itself never imports the real helper at module import time either.
- It never launches a subprocess and never constructs a shell command.
- It never detects a real GAUSS environment.
- It never invokes `gauss.exe` or `tgauss.exe`, directly or indirectly.
- All "execution" happens through an injected runner satisfying the `FakeRunner` Protocol — either a fake/stub callable (every test as of this revision), or `AdapterRunner`, a thin bridge to a `gauss_execution_adapter.GaussExecutionAdapter` instance that the *caller* must construct with an explicit helper (fake in every test here; a real one only via a future, separately authorized caller invoking `gauss_execution_adapter.load_real_helper()` — never automatically, and never by this module).
- All state is in-memory only, scoped to one Python process — no cross-process coordination, no database, no queue, no file-based persistence.
- It is **not** production runtime orchestration and is **not** wired into `workflows/code-assistant-response.md` or any agent.

Supported mock behavior:

- `CanonicalExecutionRequest` — an 18-field request object, mutable pre-freeze via `RequestDraft`, immutable after `freeze()` (a custom `__setattr__` blocks further mutation of plan fields), with a deterministic SHA-256 `request_hash` (`compute_request_hash(...)`) computed over exactly the 12 hash-included fields.
- `OrchestrationState` — the 13-state enum (`advisory` through `completed`/`cancelled`/`blocked`) and `VALID_TRANSITIONS`, the 18-entry valid-transition table; any transition not listed raises `InvalidTransitionError`.
- `RunnerInput` — the narrow request projection passed to any runner; extended in `v0.32.0` with `gauss_version`, `expected_input_files`, and `required_packages` so it can drive `AdapterRunner` as well as a fake runner, without exposing `safety_review`/confirmation internals.
- `AdapterRunner` — bridges a `gauss_execution_adapter.GaussExecutionAdapter` into the `FakeRunner` boundary (`invoke(runner)`'s `runner` parameter); an adapter-level pre-invocation rejection is raised as an exception, which `invoke()` correctly classifies as `RUNNER_LAUNCH_FAILURE` (confirmation was already consumed by that point, per the atomic-consumption rule).
- `MockOrchestrationInstance` — the transition engine: `submit_for_review()`, `display_plan()`, `confirm(...)`, `reject_confirmation()`, `edit_before_confirmation(...)`, `invalidate_for_session_boundary()`, `check_environment_before_invocation(...)`, `invoke(runner)`, `cancel()`, `begin_analysis(...)`, `block(...)`, `mark_runner_unavailable()`.
- Confirmation handling — `ConfirmationEvent` binds a confirmation to an exact `request_hash`; confirmation is consumed atomically with invocation authorization inside `invoke(...)`, never merely checked-then-used — unchanged whether the runner is a fake or an `AdapterRunner`.
- Duplicate-invocation prevention — a second `invoke(...)` call for an already-invoked instance raises rather than calling the runner again (`HelperInvocationStatus` tracks at most one invocation per confirmed request).
- Fake-result validation — `validate_fake_result(...)` schema-checks the dict a runner returns (structural shape only, mirroring — not replacing — `schemas/gauss_code_execution.schema.json`) and flags a malformed result as terminal rather than passing it downstream.
- Missing-expected-output detection — `_missing_expected_outputs(...)` compares a request's declared `expected_output_files` (documented as free-form, descriptive filenames, not paths a caller predicts exactly) against the result's actual `output_files` **by basename** (`v0.35.0` fix; previously compared by exact string equality against the helper's always-absolute discovered paths, which meant a genuinely-created, correctly-discovered file was always misclassified as missing — found during `v0.35.0`'s own real-invocation testing, see `planning/v0.35.0-implementation-report.md`). A mismatch sets `FailureCategory.MISSING_EXPECTED_OUTPUT` on an otherwise-`EXECUTION_COMPLETED` result — execution success and expected-output verification remain two independently tracked outcomes.
- Analysis/report hooks — `begin_analysis(...)` accepts an injected callable standing in for `workflows/execution-aware-analysis.md`/`workflows/report-generation.md`; a hook failure never rewrites the already-recorded execution result (`analysis_status`/`report_status` are tracked independently of the execution outcome).
- Cancellation modeling — `cancel()` covers pre-execution cancellation; the module also models the "cancellation during a synchronous call" case honestly (a runner may call back into the instance to simulate this), without ever implying a real subprocess was actually interrupted.
- `OrchestrationRecord.to_safe_summary()` — a redacted view excluding raw code/secrets, mirroring the Observability record's "must never contain" rules from the design document.
- `build_production_adapter_runner(...)` (`v0.33.0`) — the one, narrow, explicit factory whose invocation, by name, can result in a real GAUSS call: it calls `gauss_execution_adapter.load_real_helper()` and constructs a real-helper-backed `AdapterRunner`. Never called by `MockOrchestrationInstance`'s own construction or `invoke(...)`'s default behavior, and never called by any test in this repository's default suite — confirmed structurally, not just by convention.
- Durable state store integration (`v0.36.0`) — `MockOrchestrationInstance` gained an optional `state_store: gauss_orchestration_state_store.OrchestrationStateStore | None = None` constructor parameter, defaulting to `None` so every pre-existing test and caller is completely unaffected. When a store IS supplied, `invoke(...)` calls the store's atomic `authorize_invocation(...)` **before** any in-memory mutation or runner call — the durable commit always happens first, never after. `confirm(...)` durably records confirmation via `record_confirmation(...)` before its in-memory mirror. `build_durable_orchestration_instance(...)` is the one, explicit, named "production construction" entry point requiring a non-`None` store (mirroring `build_production_adapter_runner(...)`'s own explicitness convention); `reload_orchestration_instance(...)` reconstructs an in-memory view from durable state after a restart, with `instance.request` always `None` post-reload (raw code was deliberately never durably persisted), which is exactly what makes `begin_analysis()`/`invoke()`'s pre-existing `self.request is None` guards correctly refuse to proceed on a reloaded instance — this reload path can never resurrect execution capability from incomplete state. See `gauss_orchestration_state_store.py` below.

Self-test:

```text
python scripts/gauss_runtime_orchestration.py --self-test
```

This runs a lightweight built-in smoke test (a handful of checks that the module's core entry points work at all), the same `--self-test` convention already used by `scripts/gauss_environment_check.py`, `scripts/gauss_package_inspection.py`, and `scripts/gauss_code_execution.py`.

The focused, comprehensive test suite is a separate file, not part of `--self-test`:

```text
python scripts/test_gauss_runtime_orchestration.py
```

This repository has no `pytest` configuration anywhere (no `pyproject.toml`, `setup.py`, `pytest.ini`, or `conftest.py`), so this test file follows the same `check(name, condition)` self-test harness convention as every other `scripts/*.py` tool rather than introducing a new test framework. It runs 95 deterministic unit tests (all currently passing): the original 40 from `v0.31.0`'s implementation task, 20 `v0.32.0` Increment-1 tests (41-60) exercising the same scenarios through `AdapterRunner`, 3 `v0.33.0` tests (61-63) verifying `build_production_adapter_runner`'s existence and structural isolation, 6 `v0.34.0` tests (64-69) using "real-shaped fake" fixtures copying the exact stdout/stderr/exit_code observed during `v0.34.0`'s two real controller-path invocations, 16 `v0.35.0` tests (71-86) covering repeated independent requests, output-created/output-missing regression fixtures, and duplicate-identity/state-isolation guarantees, and 10 new `v0.36.0` tests (88-97) covering a full durable-store-backed success flow, confirmation persisting across a simulated restart, a reloaded instance correctly refusing to resurrect analysis capability, a cross-process authorization race translating to the correct in-memory exception type, the default in-memory-only mode remaining completely untouched by a store, and durable persistence of the runtime-error/missing-output/launch-failure outcomes. Every `v0.36.0` test uses a disposable temporary SQLite database, never the default repository-relative location. The final test in file order was renumbered `test_63` → `test_70` → `test_87` → `test_98` across `v0.34.0`-`v0.36.0` (identical "never imports the real helper" logic, unchanged) to remain the file's last test — so the highest test number is 98, but the total count of distinct tests is 95.

This script does not require GAUSS to be installed, does not access the network, and does not implement production runtime orchestration — it validates that the design's state machine and consent model are internally consistent, against a fake runner or a fake-helper-backed `AdapterRunner` only.

## `gauss_orchestration_state_store.py`

Purpose:
A durable, SQLite-backed orchestration state store (`v0.36.0` Durable Execution State and Cross-Process Safety, `planning/v0.36.0-durable-execution-state-and-cross-process-safety.md`). Replaces the controller's in-memory-only safeguards with a transactional layer that survives process restarts and coordinates cooperating local processes. Storage technology is the Python standard library's `sqlite3` module only — no third-party database or ORM.

**This module never imports, invokes, or knows about real GAUSS**, and never imports `gauss_runtime_orchestration.py` (the dependency direction is one-way: the controller may depend on this module, never the reverse). Never persisted: raw inline code (only a SHA-256 digest), `stdout`/`stderr` text, output-file content, secrets/credentials, environment-variable values, raw conversation text — mirroring, not loosening, the two "safe summary" exclusion sets already established by `OrchestrationRecord.to_safe_summary()` and `gauss_execution_adapter.safe_summary(...)`.

Schema (four tables, `SCHEMA_VERSION = 1`): `schema_meta` (one row, version + creation timestamp); `orchestration_records` (one row per orchestration instance, primary key `orchestration_instance_id`); `transition_events` (ordered transition history, `UNIQUE(orchestration_instance_id, sequence_number)`); `invocation_attempts` (`UNIQUE(orchestration_instance_id)` — a second, independent enforcement layer beyond the atomic conditional `UPDATE` in `authorize_invocation(...)`).

Key operations, every write an explicit `BEGIN IMMEDIATE ... COMMIT/ROLLBACK` transaction:

- `initialize()` — idempotent; fails closed with `SchemaVersionError` on any schema-version mismatch, never attempting a silent migration.
- `create_record(...)`, `load_record(...)` — creation and read access; `RecordNotFoundError`/`DuplicateRecordError` on the obvious misuse cases.
- `transition(...)` — the generic, optimistic-concurrency-checked state transition, used for every non-authorization mutation; requires the caller's `expected_transition_sequence_number` to match the durable record's own, or raises `StaleTransitionError` (a lost-update guard, not just a duplicate-invocation guard).
- `record_confirmation(...)` — validates session/hash/scope and atomically records confirmation plus the `awaiting_confirmation → confirmed` transition; computes `confirmation_expires_at` from the store's own wall clock (`time.time()`, 30-minute default TTL), never from the caller-supplied, unparsed `confirmation_timestamp` audit label.
- `authorize_invocation(...)` — the one atomic transaction this module exists to provide: verifies state/hash/session/confirmation-validity/scope/non-consumption/non-expiry/no-prior-invocation, then, only if every condition holds, atomically consumes confirmation, records the invocation ID, and transitions to `executing` — all before any caller may launch a helper.
- `record_execution_result(...)` — records the terminal execution outcome (`execution_completed`/`execution_failed`) with `execution_status`/`exit_code`/`output_file_count`/`validation_ok`/`validation_problems`/`failure_category`.
- Read-only inspection: `list_records(...)`, `get_transition_history(...)`, `list_ambiguous_invocations()` (authorized but no result yet — surfaced for manual review, never auto-resolved), `list_expired_confirmations()`, `list_terminal()`, `list_needs_review()`, `check_integrity()` (detects malformed JSON, unrecognized states, impossible confirmation states, and transition-sequence gaps/mismatches — reports only, never repairs).

Self-test:

```text
python scripts/gauss_orchestration_state_store.py --self-test
```

Read-only CLI (explicit, safe default — running with no flags just prints help; every listing/inspection flag is confirmed never to mutate the database):

```text
python scripts/gauss_orchestration_state_store.py --db-path <path> --list [--state STATE]
python scripts/gauss_orchestration_state_store.py --db-path <path> --show INSTANCE_ID
python scripts/gauss_orchestration_state_store.py --db-path <path> --history INSTANCE_ID
python scripts/gauss_orchestration_state_store.py --db-path <path> --list-ambiguous
python scripts/gauss_orchestration_state_store.py --db-path <path> --list-expired
python scripts/gauss_orchestration_state_store.py --db-path <path> --list-terminal
python scripts/gauss_orchestration_state_store.py --db-path <path> --list-needs-review
python scripts/gauss_orchestration_state_store.py --db-path <path> --check-integrity
```

No administrative, state-changing, or repair command exists anywhere in this CLI — no automatic rerun, no automatic repair, no "mark successful" shortcut, no deletion of execution history, no raw-code or secret display.

Default storage location: `<repository_root>/.gauss_orchestration_state/orchestration.db`, created deliberately (parent directory made only when a store is actually constructed, never implicitly) and excluded from version control via `.gitignore`. Never inside a user-provided `working_directory`/`output_directory`, never mixed with `evaluations/` files. Every test in this repository passes an explicit, disposable temporary path instead.

The focused, comprehensive single-process test suite:

```text
python scripts/test_gauss_orchestration_state_store.py
```

52 deterministic unit tests: schema initialization and idempotency (1-5), record creation/retrieval and code-digest-not-raw-code (6-10), transitions and optimistic concurrency (11-16), confirmation and expiry including a simulated-restart-does-not-extend-expiry case (17-24), atomic invocation authorization covering every precondition-failure category (25-32, including the same-code-new-request-may-proceed case mirroring `v0.35.0`'s own `test_84` finding), execution-result recording (33-37), seven corruption-detection scenarios (38-44), read-only inspection/safe-summary/redaction (45-50b), and a whole-database-file byte scan confirming no raw code ever appears (51). Every test uses a disposable temporary database file.

Genuine cross-process concurrency and crash-simulation tests, using real `multiprocessing.Process` workers (not threads):

```text
python scripts/test_gauss_orchestration_state_store_concurrency.py
```

15 tests (verified stable across repeated runs): persistence across a store reopen (1-5); cross-process duplicate prevention — a five-process race with exactly one winner every time, repeated-delivery refusal, process-restart-does-not-reset-protection, and same-code-new-instance-may-proceed cross-process (6-9); concurrency — a cross-process stale-transition-sequence isolation test and a real held-write-lock contention test (10-11); and all four crash-simulation scenarios from the planning document's Crash-Recovery Model, each verified by inspecting durable state through a fresh connection after the simulated crash (12-15). See `scripts/test_gauss_orchestration_state_store.py` for the seven single-process corruption scenarios, and `scripts/test_gauss_runtime_orchestration.py`'s `v0.36.0` section for controller-level durable-store integration tests.

This module does not require GAUSS to be installed, does not access the network, does not claim distributed exactly-once execution or multi-machine coordination, and does not automatically repair, retry, or rerun anything.

## `gauss_execution_adapter.py`

Purpose:
The Helper Adapter (`v0.32.0` Phase 3, Increment 1 of `planning/v0.32.0-real-helper-adapter-scope.md`) — the single controlled boundary between runtime orchestration and the verified execution helper. Implements `planning/v0.32.0-real-helper-adapter-scope.md`'s helper interface audit (§5), request-to-helper projection (§6), script-path policy (§7), and pre-invocation validation (§9).

**This module never touches real GAUSS at import time.** Explicitly:

- It never imports `scripts/gauss_code_execution.py` at module level. `load_real_helper()` performs that import lazily, inside its own function body, and is never called automatically — only an explicit, separate caller invocation constructs the real production path.
- It never launches a subprocess itself.
- It never detects a real GAUSS environment (no call into `scripts/gauss_environment_check.py`; `_default_environment_probe(...)` is a plain `Path.exists()` continuity check, not GAUSS detection).
- It never invokes `gauss.exe` or `tgauss.exe`, directly or indirectly — `GaussExecutionAdapter.invoke(...)` only ever calls the *injected* `helper` callable supplied by its caller (a fake helper in every test as of this revision).
- Script-path mode is unconditionally rejected before the injected helper is ever called — no content-fingerprinting mechanism is implemented, and a resolved path is never treated as proof of unchanged file contents.

Supported behavior:

- `GaussExecutionAdapter` — constructed with an explicit, required `helper: HelperCallable` (no default; omitting it is a `TypeError`, not a silent fallback) and an optional `environment_probe`. `invoke(request: AdapterRequest) -> AdapterOutcome` validates, projects, and calls the helper at most once per `request_identity`.
- `HelperCallable` — a `Protocol` matching `execute_gauss_code(...)`'s actual, verified signature (confirmed by direct inspection — no invented parameters).
- `load_real_helper()` — the one, lazy, explicit factory that imports `scripts/gauss_code_execution.py` and returns its real `execute_gauss_code`; never called by `GaussExecutionAdapter`'s own construction, and never called anywhere in this repository's default test suite.
- `AdapterRequest` — a narrow, self-contained 13-field projection of the canonical execution request (no import of orchestration types, preserving the `gauss_runtime_orchestration.py → gauss_execution_adapter.py → gauss_code_execution.py` import direction).
- Pre-invocation validation, in order: duplicate invocation, script-path rejection, missing inline code, structural request validity, unsupported (GUI) executable, environment mismatch, missing package context — each with its own `AdapterFailureCategory`, none collapsed into a generic failure.
- Explicit constants always passed to the helper: `strict=True`, `allow_network=False`, `allow_file_write=False`.
- Known helper no-ops preserved and documented: `allow_file_write`, `capture_stdout`, `capture_stderr`, `validate_schema` are confirmed no-ops on `execute_gauss_code(...)` itself (never relied on for any behavior); `allow_network` is a partial no-op (adds a warning if `True`, never actually grants network access).
- `safe_summary(...)` — an audit-safe view excluding code and any credential/secret-shaped data, keeping only identifiers, statuses, and the helper's own disclosed evidence.
- `validate_against_real_schema(raw_result)` (`v0.33.0`) — a separate, explicit, lazy call validating a real result against `schemas/gauss_code_execution.schema.json`, mirroring `scripts/gauss_code_execution.py`'s own convention that schema validation is never baked into execution itself. Like `load_real_helper()`, it imports the real helper module lazily and only when called; it never calls `execute_gauss_code(...)`.

Self-test:

```text
python scripts/gauss_execution_adapter.py --self-test
```

The focused, comprehensive test suite:

```text
python scripts/test_gauss_execution_adapter.py
```

31 deterministic unit tests (all currently passing), following the same `check(name, condition)` convention: exact field projection, explicit constants, orchestration-only field exclusion, inline-code acceptance, script-path/missing-code/environment-mismatch/unsupported-executable rejection (all before invocation), all seven verified helper statuses recognized distinctly, malformed-result and unrecognized-status handling, output-metadata-is-not-content, exactly-once invocation and duplicate refusal, no automatic retry, helper-exception classification, raw-result preservation, safe-summary redaction, missing-package-context fail-closed handling, three production-boundary tests (`load_real_helper()` is explicit and returns the real callable without ever calling it; a missing helper dependency raises `ImportError` honestly; constructing an adapter without an explicit helper is a `TypeError`), and one real-schema-validation test (`v0.33.0`) confirming a hand-verified-shape result validates cleanly and a malformed one does not.

This script does not require GAUSS to be installed, does not access the network, and does not implement production execution — it validates the adapter's own projection/validation/mapping logic against fake helpers only.

## `test_gauss_execution_adapter_real.py`

Purpose:
A doubly-gated **real** GAUSS smoke-test harness for the Helper Adapter (`v0.32.0` Phase 3, Increment 1's resolved smoke-test enablement decision — `planning/v0.32.0-real-helper-adapter-scope.md` §16/§22-23). **This file can invoke real GAUSS** when both of two independent gates are supplied simultaneously; it is not part of any default test path.

**`v0.33.0` verified this harness against real GAUSS exactly once**, under explicit human authorization — see `planning/v0.33.0-controlled-real-execution-integration.md` for the full preflight and execution evidence. The harness's smoke-test code was corrected during that milestone: the prior placeholder, `"print 1+1;"`, was never itself verified as script-file content (only attempted, unconfirmed, via the `-e` inline-expression flag in `v0.28.0` Test 6). It is now `"x = 2 + 2;\nprint x;"`, byte-for-byte the script content real-verified as `v0.28.0` Test 3 ("Scalar calculation"), run via the identical `tgauss.exe -b <script_path>` form this harness itself uses.

Required gates, both simultaneously — either one missing means a clean, explicit skip with no GAUSS touched:

1. The command-line flag `--run-real-gauss`.
2. The environment variable `GAUSS_AI_ALLOW_REAL_EXECUTION=1`.

```text
python scripts/test_gauss_execution_adapter_real.py
```

Run with no arguments (or with only one of the two gates), this always prints a `SKIPPED` notice and exits `0` without touching GAUSS — confirmed by direct, live invocation with no gates, with only `--run-real-gauss`, and with only `GAUSS_AI_ALLOW_REAL_EXECUTION=1` set, each producing a clean skip.

Gating/preflight self-test (never supplies both gates):

```text
python scripts/test_gauss_execution_adapter_real.py --self-test
```

Tests only the pure gate-computation logic (`gate_status(...)`/`should_run(...)`) and the zero-gate/one-gate skip paths of `main()` — it explicitly clears `GAUSS_AI_ALLOW_REAL_EXECUTION` from the environment for the duration of those checks, so the self-test's own safety does not depend on the ambient shell never having that variable set.

When both gates are present (exercised exactly once, manually, in `v0.33.0` — never by this repository's own default test/CI/release-readiness paths), the harness prints a prominent notice, then verifies the platform matches the one combination this repository has ever verified real invocation against (Windows), then verifies an explicit `--executable-path` argument is a terminal (`tgauss`/`tgauss.exe`, never GUI) executable that actually exists — only after both preflight checks pass does it construct the real helper (via `gauss_execution_adapter.load_real_helper()`) and attempt one minimal, non-destructive, verified inline-code invocation inside a working directory (an explicit `--working-directory`, or a disposable temporary directory if omitted). On success, it now also prints `elapsed_seconds`, `stdout`, `stderr`, `warnings`, `errors`, and the result of `gauss_execution_adapter.validate_against_real_schema(...)` (added in `v0.33.0` for stronger future evidence capture).

**Release-readiness (`scripts/check_release_readiness.py`) and every default test command never set either gate and never invoke this file.**

## `test_gauss_runtime_orchestration_real.py`

Purpose:
A doubly-gated **real** GAUSS smoke-test harness for the full orchestration **controller** (`v0.34.0` Confirmed Controller Execution Path; extended in `v0.35.0` Real Execution Reliability and Output Verification with five named, individually selected reliability/output-handling scenarios). Unlike `test_gauss_execution_adapter_real.py`, which exercises only the standalone `GaussExecutionAdapter` boundary, this harness drives `gauss_runtime_orchestration.MockOrchestrationInstance` through its complete confirmation/state-machine flow — `submit_for_review() → display_plan() → confirm(ConfirmationEvent(...)) → invoke(build_production_adapter_runner(...))` and, on a non-malformed result, `begin_analysis(...)`. **This file can invoke real GAUSS** when both of two independent gates are supplied simultaneously; it is not part of any default test path.

**`v0.34.0` verified this harness against real GAUSS exactly twice; `v0.35.0` extended it and verified it five more times** — see `planning/v0.34.0-implementation-report.md` and `planning/v0.35.0-implementation-report.md` for the full preflight and execution evidence. Exactly one named scenario is selected per explicit invocation via `--scenario` (no default, and there is no "run everything" mode); each scenario's code is grounded in prior verified evidence, never invented:

- `success-basic` / `success-isolation`: `"x = 2 + 2;\nprint x;"`, byte-for-byte the script content real-verified as `v0.28.0` Test 3 ("Scalar calculation"). The two names exist to exercise the same verified code through two independent requests, demonstrating state isolation — not to test different code paths.
- `output-created`: `'output file = gauss_output.txt reset;\nprint "hello output test";\noutput off;'`, byte-for-byte the idiom real-verified in `v0.29.0` Test 3/4; declares `expected_output_files=("gauss_output.txt",)`. Requires an explicit `--output-directory` (in practice, the same directory as `--working-directory`, since `output_directory` only affects where post-execution discovery looks, not where GAUSS's own `output file = ...` statement writes — that is always relative to the subprocess `cwd`, which is always `working_directory`).
- `output-missing`: reuses `success-basic`'s verified code unmodified, declaring `expected_output_files=("does_not_exist.txt",)` — only the declaration is new, not new GAUSS syntax.
- `runtime-error`: `"x = ;"`, byte-for-byte the script content real-verified as `v0.28.0` Test 4 ("Intentional syntax error," producing `error G0105`).

Required gates, both simultaneously — either one missing means a clean, explicit skip with no GAUSS touched:

1. The command-line flag `--run-real-gauss`.
2. The environment variable `GAUSS_AI_ALLOW_REAL_EXECUTION=1`.

```text
python scripts/test_gauss_runtime_orchestration_real.py
```

Run with no arguments (or with only one of the two gates), this always prints a `SKIPPED` notice and exits `0` without touching GAUSS — confirmed by direct, live invocation with no gates, with only `--run-real-gauss`, and with only `GAUSS_AI_ALLOW_REAL_EXECUTION=1` set, each producing a clean skip. With both gates present but `--scenario` omitted (or an unrecognized value), preflight fails cleanly with no GAUSS touched — confirmed live.

Gating/preflight self-test (never supplies both gates):

```text
python scripts/test_gauss_runtime_orchestration_real.py --self-test
```

Tests only the pure gate-computation logic, the preflight helper functions (`_verify_platform()`, `_verify_executable(...)`, `_verify_scenario(...)`, `_verify_invocation_number(...)`, `_verify_output_directory_if_required(...)`), scenario-code verification against the five literal strings above, and the zero-gate/one-gate skip paths of `main()` — it explicitly clears `GAUSS_AI_ALLOW_REAL_EXECUTION` from the environment for the duration of those checks and restores it afterward, so the self-test's own safety does not depend on the ambient shell.

When both gates are present and a valid scenario is selected (exercised twice in `v0.34.0` and five more times in `v0.35.0`, all manually, individually authorized — never by this repository's own default test/CI/release-readiness paths), the harness prints a prominent notice, verifies the platform (Windows), executable identity (`tgauss`/`tgauss.exe`, terminal only), scenario recognition, a caller-declared `--invocation-number` (1-5, audit-only, printed in the evidence output, not persisted anywhere or enforced across separate process invocations), and (for `output-created` only) an existing `--output-directory` — then builds a real `EnvironmentSummary`/`SafetyReviewOutcome`/`RequestDraft`, drives the full controller sequence above, and prints scenario, invocation number, state, confirmation status/consumption, request hash, helper invocation ID, execution status, exit code, stdout, stderr, output-file count and per-file metadata (path/size/type/created_by_execution — never content), and structural-validation result at every step, followed by the final state, transition count, full transition sequence, and `instance.record.to_safe_summary()`.

**Release-readiness (`scripts/check_release_readiness.py`) and every default test command never set either gate and never invoke this file.**

## `gauss_execution_workflow.py`

Purpose:
The conversational execution-workflow layer (`v0.37.0` Conversational Execution Workflow Integration, `planning/v0.37.0-conversational-execution-workflow-integration.md`) — the single, dedicated boundary between a conversational interaction and `gauss_runtime_orchestration.py`'s durable controller. Enforces the required dependency direction end to end: conversational interaction → intent classification → plan builder → canonical request → durable orchestration controller → Helper Adapter → GAUSS execution helper.

**This module never imports `gauss_execution_adapter` or `gauss_code_execution`, never launches a subprocess, and never detects a real GAUSS environment.** It has no direct binding to either module anywhere in its own namespace (verified directly by `hasattr` inspection in `scripts/test_gauss_execution_workflow.py`). Every execution it can drive still passes through `MockOrchestrationInstance.invoke(runner)` — the `runner` is supplied by this module's own caller, never constructed by this module itself.

Supported behavior:

- `classify_interaction_mode(signal: IntentSignal) -> InteractionMode` — a pure function over explicit, pre-classified booleans/enums, never natural-language parsing. Fails closed to `ADVISORY` for any ambiguous combination; only `execution_explicitly_requested=True` together with `code_present=True` reaches `PREPARE_EXECUTION_PLAN`.
- `InteractionMode` — `ADVISORY`, `EXPLAIN_CODE`, `REVIEW_CODE`, `REVISE_CODE`, `PREPARE_EXECUTION_PLAN`, `EXECUTE_AFTER_CONFIRMATION`, `CANCEL_PENDING_EXECUTION`, `INSPECT_PRIOR_RESULT`, `REQUEST_RERUN`.
- `evaluate_eligibility(...)` / `evaluate_safety_review(...)` — structural, non-inventive encodings of `workflows/real-execution-user-workflow.md`'s Execution Eligibility Decision and (13 of 14 items of) the Pre-Execution Safety Review checklists; the 14th safety-review item (user confirmation) is deliberately excluded from the hashed outcome, since confirmation is enforced as its own later, independently validated gate.
- `ExecutionWorkflow` — the workflow class itself:
  - `propose_execution(...)` — builds a durable orchestration instance (via `gauss_runtime_orchestration.build_durable_orchestration_instance(...)`, never the bare in-memory constructor), runs eligibility then the controller's own `submit_for_review()`/`display_plan()`, and returns an `ExecutionProposal` bound to a `request_hash`/`plan_digest`.
  - `confirm_execution(event: WorkflowConfirmationEvent) -> ConfirmationOutcome` — independently validates `plan_digest == request_hash`, decision literal, and `request_id` match before ever consulting the controller; `confirmed=True` alone is never accepted.
  - `execute(...)` — checks the confirmed environment immediately before invocation, then calls `MockOrchestrationInstance.invoke(runner)`.
  - `cancel(...)`, `inspect(...)`, `invalidate_for_session_boundary(...)` — pass-through to the underlying controller/durable-record view.
  - `request_rerun(...)` — always raises `RerunRequiresNewRequestError`; there is no in-place rerun path anywhere in this module.
  - Falls back transparently to `gauss_runtime_orchestration.reload_orchestration_instance(...)` when an instance is not in its process-local cache — inheriting, not reimplementing, `v0.36.0`'s cross-process/restart behavior.
- `ResponseReadyResult` — the safe, response-ready projection of an execution outcome: `executed`, final orchestration state, execution status, `exit_code` (always paired with `exit_code_is_authoritative=False`), `runtime_error_detected`, `timed_out`, `missing_expected_output`, `output_files` (path/size/type/created-by only — `OutputFileSummary` has no `content` field), `analysis_status`, `report_status`, `limitations` (`KNOWN_LIMITATIONS`, always non-empty), `methodology_caveat`, and `rerun_requires_new_request=True` (constant).

A discovered architectural finding, not a bug: `reload_orchestration_instance(...)` always leaves `request=None` (raw code is never durably persisted). This means `execute()` against a reloaded instance — i.e., in any process other than the one that built the proposal — always fails closed with `GuardFailedError`, verified directly with three real, separate racing OS processes (all refused, none corrupting the durable record, the original process still able to complete the invocation afterward). See `scripts/test_gauss_execution_workflow.py`'s `test_32`/`test_49` for the full evidence and reasoning.

Self-test:

```text
python scripts/gauss_execution_workflow.py --self-test
```

The focused, comprehensive test suite:

```text
python scripts/test_gauss_execution_workflow.py
```

60 deterministic unit tests, grouped to match this milestone's own coverage plan: intent and mode (1-8), inputs and proposal (9-21), confirmation (22-33), execution (34-49, including the cross-process finding above and a genuine `multiprocessing.Process`-based race), and response composition (50-59), plus one closing import-boundary check (60). Every test uses a fake runner and a disposable temporary SQLite database.

This script does not require GAUSS to be installed, does not access the network, and does not run GAUSS — it validates the workflow layer's own classification/proposal/confirmation/response-composition logic against fake runners only.

## `test_gauss_execution_workflow_real.py`

Purpose:
A doubly-gated **real** GAUSS smoke-test harness for the complete conversational workflow layer (`v0.37.0`). Unlike `test_gauss_runtime_orchestration_real.py`, which drives `MockOrchestrationInstance` directly, this harness drives `gauss_execution_workflow.ExecutionWorkflow` end to end: `propose_execution(...) → confirm_execution(...) → execute(..., runner=build_production_adapter_runner(...)) → inspect(...)`, backed by a disposable, temporary `OrchestrationStateStore` (never the default repository-relative location). **This file can invoke real GAUSS** when both of two independent gates are supplied simultaneously; it is not part of any default test path.

**`v0.37.0` verified this harness against real GAUSS exactly three times** — see `planning/v0.37.0-implementation-report.md` for the full preflight and execution evidence. Exactly one named scenario is selected per explicit invocation via `--scenario` (no default, no "run everything" mode); this milestone's own authorized budget is 1-3 (`--invocation-number`). Each scenario's code is reused, byte-for-byte, from the same verified evidence `test_gauss_runtime_orchestration_real.py` already uses — this harness verifies the new conversational-workflow layer relays already-trusted real GAUSS behavior correctly end to end, not new GAUSS syntax:

- `success`: `"x = 2 + 2;\nprint x;"`.
- `runtime-error`: `"x = ;"` (`error G0105`).
- `output-created`: `'output file = gauss_output.txt reset;\nprint "hello output test";\noutput off;'`; requires an explicit `--output-directory` (in practice, the same directory as `--working-directory`).

Required gates, both simultaneously — either one missing means a clean, explicit skip with no GAUSS touched:

1. The command-line flag `--run-real-gauss`.
2. The environment variable `GAUSS_AI_ALLOW_REAL_EXECUTION=1`.

```text
python scripts/test_gauss_execution_workflow_real.py
```

Run with no arguments (or with only one of the two gates), this always prints a `SKIPPED` notice and exits `0` without touching GAUSS — confirmed by direct, live invocation.

Gating/preflight self-test (never supplies both gates):

```text
python scripts/test_gauss_execution_workflow_real.py --self-test
```

When both gates are present and a valid scenario is selected (exercised exactly three times in `v0.37.0`, all manually, individually authorized — never by this repository's own default test/CI/release-readiness paths), the harness prints the full proposal (request hash, plan digest, code digest — never raw code), confirmation outcome, and every `ResponseReadyResult` field, followed by an `inspect()` readback confirming consistency and the durable record's own safe summary.

**Release-readiness (`scripts/check_release_readiness.py`) and every default test command never set either gate and never invoke this file.**

## PACKAGE_DOC_DIRECTORIES refresh process

`scripts/command_doc_lookup.py`'s `PACKAGE_DOC_DIRECTORIES` constant (added `v0.11.0`) is a hardcoded snapshot of the official GAUSS Applications index (`docs_root/applications.rst`), not a live parse of that file at lookup time. It is source classification only — it tells the evidence schema's `source_type`/`source_authority` fields whether a matched file lives in a separately-distributed package directory versus the core documentation tree. It is **not** licensing verification; the Code Assistant must still state a package's licensing/version dependency explicitly whenever it recommends a package-sourced command, regardless of this classification.

To refresh it when the official Applications index changes:

1. Inspect the current `docs_root/applications.rst` and list its `.. card::` entries' `:link:` targets (each target's first path segment is a package directory, e.g. `tsmt/index` -> `tsmt`).
2. Compare that list against the current `PACKAGE_DOC_DIRECTORIES` set in `scripts/command_doc_lookup.py`.
3. Update `PACKAGE_DOC_DIRECTORIES` to add any new package directory found, or remove one that the index no longer lists — do not add a directory name that isn't actually present in the Applications index, even if it looks package-like by name.
4. Regenerate and validate affected evidence only if needed — that is, only for existing committed evidence files whose classification would actually change (a file under a newly-added or newly-removed package directory). Do not regenerate unrelated evidence as part of this refresh.
5. Run `python scripts/validate_all_evidence.py` (and `--strict`) afterward to confirm the refresh introduced no new unexpected result or warning beyond the already-documented ones.

A directory missing from the snapshot is classified as core documentation by default, so a stale snapshot can only under-classify a newer package as core — it cannot mis-classify real base-GAUSS documentation as a package. This bounds the risk of the snapshot going stale between refreshes.

## Output Fields

- `command_name`: command requested by the user.
- `docs_root`: local documentation root searched.
- `status`: `found`, `ambiguous`, `not_found`, or `error`.
- `confidence`: confidence score for the best match.
- `matches`: candidate documentation matches.
- `best_match`: highest-confidence match when available.
- `unresolved_questions`: details that were not found or could not be resolved.
- `keyword_hits`: snippets around requested keyword matches.

Each match may include:

- `file_path`
- `source_type`
- `match_reason`
- `heading`
- `syntax_blocks`
- `inputs_section`
- `outputs_section`
- `returns_section`
- `controls_section`
- `formula_section`
- `examples`
- `notes`
- `related_links`
- `raw_section_headings`
- `keyword_hits`
- `extraction_warnings`
- `confidence`

## Limitations

- This is a lightweight prototype, not a full documentation search system.
- It searches local `.rst` files only.
- It does not execute GAUSS code.
- It does not infer syntax, arguments, defaults, return fields, or examples from category membership.
- It may miss information if the official docs use unexpected section names or formatting.

Official GAUSS documentation remains authoritative. Extracted snippets should be treated as retrieval evidence, not as a replacement for the official command page.

`--schema-output` is subject to the same limitations: it only changes the output shape, not the underlying extraction quality.
