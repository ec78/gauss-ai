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
Mock-only, in-memory runtime orchestration controller skeleton (`v0.31.0` Phase 2 of `planning/v0.31.0-runtime-orchestration-design.md`'s Implementation Phases). It implements the canonical execution request (`planning/v0.31.0-canonical-execution-request-contract.md`) and the 13-state runtime state machine (`planning/v0.31.0-runtime-state-machine-contract.md`) well enough for deterministic unit testing, entirely against an injected fake runner. It does not redefine either contract's rules — it implements them, and where implementing them surfaced two genuine inconsistencies in the state-machine contract, those were fixed in the contract document itself, not silently worked around in code.

**This module never touches real GAUSS.** Explicitly and unconditionally:

- It never imports `scripts/gauss_code_execution.py` and never calls `execute_gauss_code(...)`.
- It never launches a subprocess and never constructs a shell command.
- It never detects a real GAUSS environment.
- It never invokes `gauss.exe` or `tgauss.exe`, directly or indirectly.
- All "execution" happens through an injected `FakeRunner` callable supplied entirely by the caller (in practice, a test).
- All state is in-memory only, scoped to one Python process — no cross-process coordination, no database, no queue, no file-based persistence.
- It is **not** production runtime orchestration and is **not** wired into `workflows/code-assistant-response.md` or any agent.

Supported mock behavior:

- `CanonicalExecutionRequest` — an 18-field request object, mutable pre-freeze via `RequestDraft`, immutable after `freeze()` (a custom `__setattr__` blocks further mutation of plan fields), with a deterministic SHA-256 `request_hash` (`compute_request_hash(...)`) computed over exactly the 12 hash-included fields.
- `OrchestrationState` — the 13-state enum (`advisory` through `completed`/`cancelled`/`blocked`) and `VALID_TRANSITIONS`, the 18-entry valid-transition table; any transition not listed raises `InvalidTransitionError`.
- `MockOrchestrationInstance` — the transition engine: `submit_for_review()`, `display_plan()`, `confirm(...)`, `reject_confirmation()`, `edit_before_confirmation(...)`, `invalidate_for_session_boundary()`, `check_environment_before_invocation(...)`, `invoke(runner)`, `cancel()`, `begin_analysis(...)`, `block(...)`, `mark_runner_unavailable()`.
- Confirmation handling — `ConfirmationEvent` binds a confirmation to an exact `request_hash`; confirmation is consumed atomically with invocation authorization inside `invoke(...)`, never merely checked-then-used.
- Duplicate-invocation prevention — a second `invoke(...)` call for an already-invoked instance raises rather than calling the runner again (`HelperInvocationStatus` tracks at most one invocation per confirmed request).
- Fake-result validation — `validate_fake_result(...)` schema-checks the dict a `FakeRunner` returns (structural shape only, mirroring — not replacing — `schemas/gauss_code_execution.schema.json`) and flags a malformed result as terminal rather than passing it downstream.
- Analysis/report hooks — `begin_analysis(...)` accepts an injected callable standing in for `workflows/execution-aware-analysis.md`/`workflows/report-generation.md`; a hook failure never rewrites the already-recorded execution result (`analysis_status`/`report_status` are tracked independently of the execution outcome).
- Cancellation modeling — `cancel()` covers pre-execution cancellation; the module also models the "cancellation during a synchronous call" case honestly (a `FakeRunner` may call back into the instance to simulate this), without ever implying a real subprocess was actually interrupted.
- `OrchestrationRecord.to_safe_summary()` — a redacted view excluding raw code/secrets, mirroring the Observability record's "must never contain" rules from the design document.

Self-test:

```text
python scripts/gauss_runtime_orchestration.py --self-test
```

This runs a lightweight built-in smoke test (a handful of checks that the module's core entry points work at all), the same `--self-test` convention already used by `scripts/gauss_environment_check.py`, `scripts/gauss_package_inspection.py`, and `scripts/gauss_code_execution.py`.

The focused, comprehensive test suite is a separate file, not part of `--self-test`:

```text
python scripts/test_gauss_runtime_orchestration.py
```

This repository has no `pytest` configuration anywhere (no `pyproject.toml`, `setup.py`, `pytest.ini`, or `conftest.py`), so this test file follows the same `check(name, condition)` self-test harness convention as every other `scripts/*.py` tool rather than introducing a new test framework. It runs 40 deterministic unit tests (all currently passing): the 32 scenarios required by `v0.31.0`'s implementation task (every state/transition pair, every consent-invalidation rule, duplicate-invocation prevention, malformed-result handling, cancellation, and analysis/report-hook isolation) plus 8 additional invariant-coverage tests (confirmation not reusable across requests, environment mismatch blocking execution, all failure categories distinct, no methodology-validity claim in the data model, conservative script-identity guard, unsafe-request blocking, execution-record secret exclusion, and monotonic confirmation consumption).

This script does not require GAUSS to be installed, does not access the network, and does not implement production runtime orchestration — it validates that the design's state machine and consent model are internally consistent, against a fake runner only.

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
