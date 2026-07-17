# GAUSS Code Execution Tool

## Purpose

`gauss_code_execution` is a controlled execution helper for explicitly provided GAUSS code or an explicitly specified GAUSS script file.

It is intended to:

- Run GAUSS code only when execution is explicitly requested — never inferred from a code-generation or debugging request alone.
- Use the selected environment context from `gauss_environment_check` (executable path, version, platform, detection status).
- Optionally use package context from `gauss_package_inspection` (requested-package installed/missing/unknown status) as feasibility context before executing.
- Return structured execution results: whether execution actually occurred, its status, captured stdout/stderr/exit code, elapsed time, and any output files discovered inside a safe working directory.
- Distinguish actual execution output from interpretation of that output.

State clearly:

- This tool does not validate methodology.
- This tool does not prove statistical correctness.
- This tool does not prove product value.
- This tool does not install packages.
- This tool does not activate licenses.
- This tool does not perform runtime orchestration by itself — it is a single, bounded execution operation, not a workflow engine.

## Tool Status

- **Status:** specified and implemented as a controlled, safety-constrained helper.
- **Implementation:** `scripts/gauss_code_execution.py` — usable from the command line (`python scripts/gauss_code_execution.py`) and importable for tests (`execute_gauss_code(...)`).
- **Permission level:** explicit, bounded code execution — the highest-risk helper in this repository, per the Permission and Safety Model below.
- **Runtime orchestration:** not implemented.
- **Code Assistant workflow integration:** not implemented.
- **Package installation:** not implemented.
- **License activation:** not implemented.
- **Metadata/dependency commands:** never run automatically.
- **Automatic rerun/repair loops:** not implemented.
- **Real GAUSS non-interactive invocation:** verified on Windows against GAUSS 26.1.1 only — see "Command Construction Status" below. Cross-platform and cross-version behavior remain unverified, and real execution overall remains not production-ready. Self-tests use an injectable fake runner and require no real GAUSS installation.
- **Result schema:** created (`schemas/gauss_code_execution.schema.json`) — see "Planned Schema" below.
- **Example outputs:** created (`examples/tools/gauss-code-execution-*.json`) — see "Examples" below.

Execution Mode is only ever a real, momentary state — `operating_mode: execution` is set solely when the runner actually invoked a subprocess for that specific call, never as a standing mode the assistant enters. This spec does not authorize silent execution. Implementation follows the same specify-before-implement discipline already used for `gauss_environment_check` (`v0.20.0` spec / `v0.21.0` implementation) and `gauss_package_inspection` (`v0.22.0` spec / `v0.23.0` implementation) — `v0.24.0` specified this tool, `v0.25.0` implemented it.

### Command Construction Status

`scripts/gauss_code_execution.py`'s original default command builder constructed `[executable_path, script_path]`. Manual verification against this development machine's real GAUSS 26 installation during `v0.25.0` implementation confirmed this naive form does **not** run non-interactively: GAUSS launched, printed its startup banner and the script's `print` output, then dropped into an interactive `(gauss)` prompt awaiting further input rather than exiting — the process only terminated because the helper's timeout killed it.

`v0.28.0` researched and verified a replacement. Read-only inspection of the local GAUSS 26 installation directory (`C:\gauss26\README.txt`) found a documented `-b` ("execute in batch mode and exit") flag for the terminal executable. Six controlled smoke tests (see `planning/v0.28.0-real-gauss-invocation-research.md`'s "Smoke-Test Log" and "Verification Matrix") confirmed `[executable_path, "-b", script_path]` reliably exits non-interactively — including for a deliberate syntax-error script, the highest-risk case for an unexpected interactive fallback. This is now the default command builder's behavior for terminal executables (`tgauss`/`tgauss.exe`).

**Scope of this verification:** Windows and GAUSS 26.1.1 only. Cross-platform (macOS/Linux) and cross-version (GAUSS 24/25) behavior remain unverified. Real execution through this helper should still be treated as **not production-ready** outside that one tested combination.

**GUI executables are refused by default.** `gauss.exe` (or any executable basename other than `tgauss`/`tgauss.exe`) causes the default command builder to return an empty command, which the helper treats as a `blocked` result with a clear error — only the terminal executable's batch-mode flag is documented and verified.

**Critical caveat — exit code is not a reliable failure signal.** The syntax-error smoke test returned `exit_code: 0`, identical to the successful runs. The helper therefore does not rely on `exit_code` alone to classify failure: a `_detect_gauss_error(stdout, stderr)` heuristic additionally scans for the two failure signals actually observed during smoke testing — `"Program execute failed"` in stdout, and an `error G####` pattern in stderr — and classifies the result as `failed` (with an explanatory warning) whenever either is detected, even if `exit_code == 0`. This heuristic is intentionally narrow and documented as such in the function's docstring; it is not a general-purpose GAUSS error parser and may miss failure modes not yet observed (for example, runtime errors were not separately smoke-tested).

Command construction remains isolated behind an injectable `command_builder`, and result classification remains testable via the injectable `runner`, so both can continue to be revised (broader platform/version support, a more complete error-detection heuristic) without touching the rest of the helper. Fake-runner self-tests cover the new `-b` default, GUI-executable blocking, the exit-code-0-with-detected-error case, the exit-code-0-with-banner-only-stderr case, inline code routing through `-b`, and continued `command_builder` injection override — all without requiring a real GAUSS installation.

## Relationship to Environment Detection

- The tool should consume the selected environment context from `gauss_environment_check` rather than re-detecting GAUSS itself.
- If GAUSS 26 is selected by environment detection (per `v0.21.0`'s newest-version default), execution should use GAUSS 26 by default.
- If the user explicitly selected GAUSS 25, execution should use GAUSS 25.
- If the user provides an explicit executable path, that path controls.
- The tool must not silently switch GAUSS versions.
- The tool must not execute when environment detection is `not_found`, `ambiguous`, `inaccessible`, or `error`.
- If version is unknown but the executable is accessible (`detection_status: found`, `version_known: false`), the implementation proceeds conservatively: it does not block, but it adds an explicit warning that command construction cannot verify version-specific invocation behavior. This was the policy `v0.25.0` chose among the options `planning/v0.24.0-gauss-code-execution-prototype.md`'s "Risks and Open Questions" left open.

## Relationship to Package Inspection

- Package inspection may provide feasibility context before execution, using `gauss_package_inspection`.
- Package inspection is not required for every execution.
- Missing package context may warn or block depending on policy.
- Unknown package status should not be treated as either installed or missing.
- Installed package status does not prove syntax validity.
- Installed package status does not prove methodology validity.
- Installed package status does not prove execution success.
- Execution failure may reveal missing dependencies, but the tool must not automatically install them.

## Operating Mode Relationship

This tool exists to support the operating modes defined in `planning/v0.19.0-gauss-tooling-strategy-and-execution-modes.md`.

- **Advisory Mode:** no execution.
- **Verified Knowledge Mode:** evidence-backed guidance, no execution.
- **Execution Candidate:** environment/package context suggests execution may be possible, but no execution has occurred yet.
- **Execution Mode:** only when GAUSS is actually invoked by the execution helper under explicit safety rules.

Important:

- Environment detection does not activate Execution Mode — a `found`/`execution_candidate` result from `gauss_environment_check` remains a prerequisite signal only.
- Package inspection does not activate Execution Mode — an `installed: true` result from `gauss_package_inspection` remains a prerequisite signal only.
- Execution Candidate is not Execution Mode. The two are always distinct: candidacy describes context that *could* support execution; Execution Mode describes that execution *is actually happening*.
- Execution output is not methodology validation, regardless of operating mode.

## Permission and Safety Model

This is the tool's most consequential section — code execution is the highest-risk capability planned in this framework so far, and every other section below is subordinate to these rules.

**Rules:**

- No silent execution.
- No execution from ambiguous prompts.
- No execution without explicit code or an explicit script path.
- No execution without selected executable context.
- No execution without a safe working directory.
- No execution without a timeout.
- No package installation.
- No license activation.
- No network access.
- No hidden metadata/dependency commands.
- No writes outside the safe working directory.
- No deletion of user files.
- No mutation of global GAUSS configuration.
- No permanent environment-variable mutation.
- No automatic debugging/rerun loop.
- No report generation from output unless a later workflow explicitly supports it.

The helper treats execution as a tool operation, not a reasoning shortcut: a request to write or debug GAUSS code does not by itself authorize running it, and the assistant does not execute code merely to "check its own work" implicitly.

## Inputs

| Input | Purpose |
|---|---|
| `environment_check_result` | Lets a caller pass a prior `gauss_environment_check` result directly as environment context. |
| `package_inspection_result` | Lets a caller pass a prior `gauss_package_inspection` result as feasibility context. |
| `executable_path` | Directly selects the GAUSS executable, bypassing `environment_check_result`. |
| `gauss_version` | States which GAUSS version's context execution should use. |
| `code` | An explicit GAUSS code string to execute. |
| `script_path` | An explicit path to a `.gss` or GAUSS script file to execute. |
| `working_directory` | The safe, explicit directory execution is scoped to. |
| `input_files` | Explicit files execution is permitted to read. |
| `output_directory` | Where generated output may be written and later listed; must resolve inside `working_directory`. |
| `timeout_seconds` | Bounds how long execution may run before forced termination. |
| `allow_file_write` | Permits execution to write files, strictly limited to `working_directory`. |
| `allow_output_files` | Permits listing generated output files after execution. |
| `allow_network` | Requests network access for the executed code. |
| `strict` | Requests that the tool avoid falling back to automatic environment detection or broader discovery. |
| `capture_stdout` | Whether to capture standard output. |
| `capture_stderr` | Whether to capture standard error. |
| `validate_schema` | Requests schema validation of the result. |

**Important input rules:**

- Exactly one of `code` or `script_path` should be required — supplying both, or neither, is treated as an invalid/blocked request.
- `working_directory` should be required — there is no default "current directory" fallback.
- `timeout_seconds` should be required or defaulted to a safe value, with a hard maximum the caller cannot override upward.
- `allow_network` should default to `false` and should be unsupported or blocked in the first prototype.
- `allow_file_write` should default to `false`, or when `true`, be strictly limited to `working_directory`.
- `input_files` must be explicit — no implicit discovery of "nearby" files.
- `output_directory` must resolve inside the safe working directory; a value that resolves outside it should be rejected.

## Outputs

| Output | Type |
|---|---|
| `checked` | boolean |
| `executed` | boolean |
| `execution_status` | `completed` / `failed` / `timed_out` / `skipped` / `blocked` / `error` / `unknown` |
| `operating_mode` | `advisory` / `verified_knowledge` / `execution` |
| `executable_path` | string or null |
| `gauss_version` | string or null |
| `working_directory` | string or null |
| `command` | string or null |
| `code_source` | string (for example `inline_code`, `script_path`, `not_checked`) |
| `script_path` | string or null |
| `timeout_seconds` | number or null |
| `elapsed_seconds` | number or null |
| `exit_code` | number or null |
| `stdout` | string or null |
| `stderr` | string or null |
| `output_files` | array |
| `warnings` | array |
| `errors` | array |
| `next_steps` | array |
| `raw_execution_details` | optional object |

**Important output rules:**

- `executed: true` only when GAUSS was actually invoked as a subprocess.
- `executed: false` must not coexist with `execution_status: completed`.
- `completed` means the process completed, not that results are statistically valid.
- `exit_code: 0` does not prove statistical validity.
- `stdout`/`stderr` may be truncated; truncation must be recorded in `warnings`.
- `output_files` must be limited to the safe working directory.
- `raw_execution_details` is optional implementation-specific diagnostics, not a substitute for the structured fields above.

## Execution Status Semantics

### completed

The GAUSS process completed without timing out. This does not imply correctness. The assistant must not claim results are statistically valid, syntactically valid beyond this run, or methodologically appropriate based on `completed` alone. Likely `operating_mode`: `execution` (this run) plus `verified_knowledge`/advisory guidance for interpreting the output.

### failed

The GAUSS process ran but returned a nonzero exit status or failed at runtime. The assistant must report the real exit code and captured stderr, not guess at the cause without evidence. `operating_mode`: `advisory` for next steps.

### timed_out

The GAUSS process was invoked but exceeded the timeout and was terminated. The assistant must report this as a timeout, not a silent failure, and must not claim the code is broken without further evidence — a legitimate long-running computation and a hung process look identical from the caller's side. `operating_mode`: `advisory`.

### skipped

Execution did not run because required inputs were absent (no `code`/`script_path`, no `working_directory`) or execution was not explicitly requested. The assistant must not imply an attempt occurred. `operating_mode`: `advisory`.

### blocked

Execution was refused by safety policy (missing/ambiguous environment, unsafe path, disallowed input combination, etc.). The assistant must state the specific blocking reason and a safe next step, never a generic refusal. `operating_mode`: `advisory`.

### error

An unexpected tool/helper error occurred (not a GAUSS-side failure). The assistant must report a structured error and must not fabricate any execution outcome. `operating_mode`: `advisory`.

### unknown

Execution state could not be determined (for example, the process was interrupted in a way the helper cannot classify). The assistant must not guess at `completed`/`failed` and must prefer `unknown` over false certainty. `operating_mode`: `advisory`.

## Working Directory Policy

- Execution requires an explicit safe working directory.
- Relative paths (for `script_path`, `input_files`, `output_directory`) resolve under `working_directory`, not the process's current directory.
- Path traversal (e.g., `../` segments resolving outside `working_directory`) should be rejected.
- Output file discovery is limited to `working_directory`.
- Symlinks should be handled conservatively — a symlink inside `working_directory` that resolves outside it is not treated as a legitimate path.
- No writes outside `working_directory`.
- No deletion of user files.
- No implicit use of the process's own current working directory as the safe directory.

## Timeout and Resource Policy

- A timeout is required, or defaulted to a safe value if not supplied.
- A hard maximum timeout should exist that the caller cannot override upward.
- The process is forcibly terminated on timeout, not merely flagged.
- No detached or background processes — the helper owns the full process lifecycle.
- stdout/stderr capture should be size-limited.
- Truncation must be recorded in `warnings`, never silently dropped.
- Large output should not crash the helper.

## File and Output Policy

- Input files must be explicit (`input_files`) — no implicit discovery.
- Generated output files may be listed only inside the safe working directory.
- Output file entries should include metadata such as path, size, and — when safely available — a MIME/type hint.
- Do not expose unnecessary sensitive local paths beyond what is needed to explain the result.
- Do not read arbitrary output file contents unless explicitly supported by a later design.
- Do not delete or clean up user files outside temporary helper-created locations.

## Result Interpretation Policy

Execution proves only that a specific code/script was run in a specific environment/context.

It does not prove:

- Syntax is generally valid in all GAUSS versions.
- Methodology is appropriate.
- Estimates are meaningful.
- Diagnostics are adequate.
- Code is maintainable.
- Documentation is clear.
- Education design is effective.
- Product/user value is proven.

Route interpretation to the relevant operational expert(s):

- **GAUSS Language Expert** — implementation/syntax context.
- **Econometrics Expert** — methodology, diagnostics, interpretation.
- **Software Engineering Expert** — maintainability/design.
- **Documentation Expert** — explanation/reference clarity.
- **Education Expert** — scaffolding/learning.
- **Product Expert** — user-value implications.

This extends the same independence principles `experts/EXPERT_BOUNDARY_MATRIX.md` already establishes to the specific, narrower case of code execution output — a successful run is never treated as self-certifying any of these dimensions.

## Assistant Response Rules

- If execution did not occur, say it did not occur.
- If execution was blocked, explain the blocking reason and a safe next step.
- If execution completed, report what was actually captured.
- Do not fabricate stdout, stderr, exit code, output files, model estimates, or diagnostics.
- Do not infer methodology validity from success.
- Do not infer syntax validity beyond the specific run/context.
- Do not hide warnings, timeouts, or stderr.
- Label expected output vs. actual output clearly — never blend a hypothetical/illustrative result with a real captured one.
- Provide advisory fallback when execution cannot proceed.

## Failure and Fallback Rules

- Missing executable → `blocked`/`skipped`, Advisory Mode.
- Ambiguous environment → `blocked`, Advisory Mode.
- Missing working directory → `blocked`.
- Missing code/script → `skipped` or `blocked`.
- Both code and script supplied → `blocked`, unless a later design explicitly allows both.
- Timeout → `timed_out`, with partial stdout/stderr if available.
- Nonzero exit → `failed`, with captured error details.
- Missing package → warn or block depending on policy; never auto-install.
- No output captured → `completed`, but state clearly that no output was captured.
- Uninterpretable output → provide next steps rather than guessing.

## Security and Risk Considerations

**Risks:**

- Arbitrary code execution.
- File modification/deletion.
- Path traversal.
- Environment leakage.
- Large output capture.
- Long-running processes.
- Hidden install commands.
- License prompts.
- GUI popups.
- Network access.
- Sensitive local paths in output.
- Private data in logs/output.

**Mitigations:**

- Explicit execution request.
- Safe working directory.
- No network.
- No package installation.
- No global config mutation.
- Timeout.
- Output truncation.
- Path validation.
- Structured errors.
- No automatic rerun loops.

## Command-Line Interface and Testing

`scripts/gauss_code_execution.py` exposes:

- `--environment-result`, `--package-inspection-result`, `--executable-path`, `--gauss-version`, `--code`, `--script-path`, `--working-directory`, `--input-file` (repeatable), `--output-directory`, `--timeout-seconds`, `--allow-file-write`, `--allow-output-files`, `--allow-network`, `--strict` — map directly to the Inputs above. `--environment-result`/`--package-inspection-result` accept JSON file paths containing prior `gauss_environment_check`/`gauss_package_inspection` results.
- `--json` — print the full structured JSON result (default output is a short human-readable summary).
- `--validate-schema` — validate the result against `schemas/gauss_code_execution.schema.json` when `jsonschema` is available; fails with a nonzero exit code only on a genuine schema mismatch, not when the optional dependency is simply unavailable (a warning is added to the result instead).
- `--self-test` — runs a built-in test suite (`_run_self_tests`) covering environment-missing/ambiguous blocking, code/script exclusivity, missing-working-directory blocking, successful/failed/timed-out execution via an injected fake runner, stdout/stderr capture and truncation, output-file discovery scoped to the working directory, path-traversal rejection, `--allow-network` rejection, package-missing blocking without auto-install, and schema validation of representative outputs. As of `v0.28.0`, it also covers: the default command builder using `-b` for terminal executables (`tgauss`/`tgauss.exe`), a GUI executable (`gauss.exe`) being blocked rather than attempted, `exit_code: 0` with detected GAUSS error text (`"Program execute failed"` / `error G####`) mapping to `failed`, `exit_code: 0` with only banner/job-header stderr still mapping to `completed`, nonzero exit still mapping to `failed` without detected error text, inline code's generated `.gss` script being invoked with `-b`, and `command_builder` injection still overriding the default entirely. Every case uses an injected fake runner (and, where filesystem behavior matters, a real disposable `tempfile.TemporaryDirectory()`); none depend on a real GAUSS installation or spawn a real subprocess.

`execute_gauss_code(...)` is also directly importable, and accepts `runner`/`command_builder`/`env_detect_fn`/`path_exists_fn`/`is_dir_fn`/`accessibility_fn`/`list_files_fn`/`monotonic_fn` injection points for testing without touching a real filesystem, calling real environment detection, or invoking a real subprocess. The default runner (used whenever `runner` is not supplied) is a real `subprocess.run`-based runner with `cwd=working_directory`, a timeout, no `shell=True`, and no detached/background process — calling the CLI or `execute_gauss_code(...)` without an injected `runner` and with a `found` environment context **will** attempt real GAUSS invocation.

## Planned Schema

**Schema file:** `schemas/gauss_code_execution.schema.json`

The schema now exists and validates the full output contract defined above: `execution_status`, `operating_mode`, and `code_source` are controlled enums; `output_files` is an array of output-file objects (`path`, `size_bytes`, `file_type`, `created_by_execution` as a tri-state `true`/`false`/`"unknown"`, `notes`); `warnings`, `errors`, and `next_steps` are string arrays; `raw_execution_details` is optional with `additionalProperties: true`; `checked` and the other eighteen top-level fields are required. The schema also encodes cross-field consistency constraints via `allOf`/`if`/`then` blocks: `executed: false` restricts `execution_status` away from `completed` and restricts `operating_mode` to `advisory`/`verified_knowledge`; `executed: true` requires `operating_mode: execution`; `execution_status: completed` requires `executed: true`; `execution_status: timed_out` requires `executed: true` plus at least one warning or error; `execution_status: blocked` requires `executed: false` and `operating_mode: advisory`; `execution_status: error` requires at least one error; `code_source: inline` requires a null `script_path`; `code_source: script_path` requires a string `script_path`; and `code_source: none` requires `executed: false` and a null `script_path`.

The implementation, `scripts/gauss_code_execution.py`, populates this output shape directly; every branch of `execute_gauss_code(...)` is exercised against the schema by `--self-test`'s representative-output checks.

## Examples

**Example outputs now exist**, validated against `schemas/gauss_code_execution.schema.json`:

- `examples/tools/gauss-code-execution-completed.json` — successful execution; `execution_candidate`-style signal via `operating_mode: execution`.
- `examples/tools/gauss-code-execution-failed.json` — GAUSS invoked but returned a nonzero exit status.
- `examples/tools/gauss-code-execution-timed-out.json` — GAUSS invoked but exceeded the timeout and was terminated.
- `examples/tools/gauss-code-execution-blocked-missing-environment.json` — no usable GAUSS environment context; execution never proceeded.
- `examples/tools/gauss-code-execution-blocked-missing-working-directory.json` — execution refused for lacking an explicit safe working directory.
- `examples/tools/gauss-code-execution-skipped-no-code.json` — neither `code` nor `script_path` was supplied; execution was not requested.
- `examples/tools/gauss-code-execution-blocked-unsafe-path.json` — `script_path` resolves outside the safe working directory via path traversal; refused.
- `examples/tools/gauss-code-execution-package-missing-before-execution.json` — a package the script depends on was confirmed missing before execution; blocked by dependency policy rather than auto-installed.

All eight are clearly synthetic (example-style paths such as `C:/example/gauss26/tgauss.exe` and `C:/example/work/project1`, explicit "Synthetic example output; no real GAUSS code was executed" warnings) and do not represent any real execution. The implementation now exists (`scripts/gauss_code_execution.py`), but these examples remain hand-authored illustrations, not implementation output — some fields (for example, the exact command form) may differ from what the real implementation currently produces, since real non-interactive GAUSS invocation remains unconfirmed (see "Command Construction Status" above).

## Evaluation Plan

Future `28.x` benchmarks should validate response behavior before implementation or before workflow integration.

**Suggested `28.x` benchmark topics:**

- Execution requested but environment missing.
- Execution requested with ambiguous environment.
- Successful execution does not prove methodology.
- Failed execution fallback.
- Timeout fallback.
- Package missing before execution.
- Execution output requires interpretation by the relevant expert.
- User asks to install a package and the assistant refuses.

**Do not add benchmark prompts in this task.**

## Relationship to Future Execution Workflow

- This tool spec is not runtime orchestration, and the implementation does not add any.
- Code Assistant workflow integration is future work.
- Execution-aware analysis workflow is future `v0.26.0` work (renumbered after `v0.25.0` became the code-execution implementation milestone).
- Report generation from execution output is future `v0.27.0` work.
- The execution helper produces structured results that later workflows can consume, the same way `gauss_environment_check` and `gauss_package_inspection` already produce structured results without themselves implementing any workflow.

## Related Files

- `scripts/gauss_code_execution.py`
- `planning/v0.28.0-real-gauss-invocation-research.md`
- `planning/v0.25.0-gauss-code-execution-implementation.md`
- `planning/v0.24.0-gauss-code-execution-prototype.md`
- `tools/gauss_environment_check.md`
- `tools/gauss_package_inspection.md`
- `scripts/gauss_environment_check.py`
- `scripts/gauss_package_inspection.py`
- `schemas/gauss_environment_check.schema.json`
- `schemas/gauss_package_inspection.schema.json`
- `schemas/gauss_code_execution.schema.json`
- `TOOL_SPEC.md`
- `tools/operational_expert_interface.md`
- `workflows/code-assistant-response.md`
- `workflows/expert-routing.md`
- `experts/EXPERT_BOUNDARY_MATRIX.md`
- `KNOWN_LIMITATIONS.md`

## Maintenance Notes

- Keep execution safety boundaries stricter than advisory tools — this is the highest-risk tool this repository has implemented so far, and any relaxation must be a deliberate, documented decision, not an incidental one.
- Update this spec if execution policy changes.
- Keep schema/result wording distinct from interpretation claims — an `execution_status` field must never be phrased in a way that could be read as a correctness or validity claim.
- Re-run response-behavior benchmarks after workflow integration.
- Do not add automatic retries/reruns without a separate design milestone.
- Real non-interactive GAUSS invocation is now verified on Windows/GAUSS 26.1.1 only (see "Command Construction Status" above) — cross-platform and cross-version support remain future work; revisit `_default_command_builder` and `_detect_gauss_error` together as new platforms/versions/error shapes are verified, and update this note and `planning/v0.28.0-real-gauss-invocation-research.md` together when that happens.
- Do not claim runtime orchestration, Code Assistant workflow integration, package installation, license activation, or cross-platform/cross-version confirmed real non-interactive invocation exist until each actually does.
