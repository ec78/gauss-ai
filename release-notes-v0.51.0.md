# v0.51.0 - Execution Result Interpretation

This release adds deterministic post-execution interpretation to the GAUSS Code Assistant interactive adapter.

## Added

- New `scripts/gauss_execution_interpreter.py` component for evidence-only execution interpretation.
- New `scripts/gauss_error_catalog.py` central catalog for deterministic GAUSS error-code classification.
- New CLI command: `interpret`.
- New tests in `scripts/test_gauss_execution_interpreter.py`.
- CLI regression coverage for `interpret` before and after execution.
- `43.x` Execution Interpretation benchmark prompts and matching coverage rows.
- Planning record: `planning/v0.51.0-execution-result-interpretation.md`.

## Supported Interpretation Cases

- Successful execution.
- Blocked-before-launch execution.
- Syntax/parse errors, including `G0105`.
- Runtime matrix-dimension errors, including `G0036`.
- Runtime computation errors, including `G0025`.
- Timeout.
- Fake-runner results.
- Missing stdout/stderr evidence.
- Unknown GAUSS error codes.
- Unknown failures.

## Safety Boundaries

Interpretation:

- never launches GAUSS;
- never edits code;
- never retries execution;
- never reads output files automatically;
- never treats execution success as statistical or methodological validation;
- never invents explanations for uncataloged GAUSS errors.

## Notes

The `43.x` benchmarks were added but not formally evaluated in this release. They are marked `Not Run` pending a dedicated evaluation milestone.

Recommended next milestone: evaluate `43.x` Execution Interpretation against the real CLI/interpreter path.
