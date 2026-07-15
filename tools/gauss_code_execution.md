# GAUSS Code Execution Tool

## Purpose

`gauss_code_execution` is a planned helper for controlled execution of explicitly provided GAUSS code or an explicitly specified GAUSS script file.

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

- **Status:** planned / specified.
- **Implementation:** not yet implemented.
- **Planned implementation file:** `scripts/gauss_code_execution.py`.
- **Result schema:** created (`schemas/gauss_code_execution.schema.json`) — see "Planned Schema" below.
- **Planned examples:** `examples/tools/gauss-code-execution-*.json`.

Execution Mode remains inactive until implementation and explicit orchestration policies exist. This spec does not authorize silent execution — it defines the contract a future implementation must satisfy, following the same specify-before-implement discipline already used for `gauss_environment_check` (`v0.20.0` spec / `v0.21.0` implementation) and `gauss_package_inspection` (`v0.22.0` spec / `v0.23.0` implementation).

## Relationship to Environment Detection

- The tool should consume the selected environment context from `gauss_environment_check` rather than re-detecting GAUSS itself.
- If GAUSS 26 is selected by environment detection (per `v0.21.0`'s newest-version default), execution should use GAUSS 26 by default.
- If the user explicitly selected GAUSS 25, execution should use GAUSS 25.
- If the user provides an explicit executable path, that path controls.
- The tool must not silently switch GAUSS versions.
- The tool must not execute when environment detection is `not_found`, `ambiguous`, `inaccessible`, or `error`.
- If version is unknown but the executable is accessible (`detection_status: found`, `version_known: false`), execution may only proceed if prototype policy explicitly permits it — this remains an open decision, not resolved by this spec (see `planning/v0.24.0-gauss-code-execution-prototype.md`'s "Risks and Open Questions").

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

## Planned Schema

**Schema file:** `schemas/gauss_code_execution.schema.json`

The schema now exists and validates the full output contract defined above: `execution_status`, `operating_mode`, and `code_source` are controlled enums; `output_files` is an array of output-file objects (`path`, `size_bytes`, `file_type`, `created_by_execution` as a tri-state `true`/`false`/`"unknown"`, `notes`); `warnings`, `errors`, and `next_steps` are string arrays; `raw_execution_details` is optional with `additionalProperties: true`; `checked` and the other eighteen top-level fields are required. The schema also encodes cross-field consistency constraints via `allOf`/`if`/`then` blocks: `executed: false` restricts `execution_status` away from `completed` and restricts `operating_mode` to `advisory`/`verified_knowledge`; `executed: true` requires `operating_mode: execution`; `execution_status: completed` requires `executed: true`; `execution_status: timed_out` requires `executed: true` plus at least one warning or error; `execution_status: blocked` requires `executed: false` and `operating_mode: advisory`; `execution_status: error` requires at least one error; `code_source: inline` requires a null `script_path`; `code_source: script_path` requires a string `script_path`; and `code_source: none` requires `executed: false` and a null `script_path`.

Implementation of the tool itself remains not yet done — the schema validates a future tool's output shape; it does not run any execution code.

## Planned Examples

Planned examples may include:

- `completed`
- `failed`
- `timed_out`
- `blocked_missing_environment`
- `blocked_missing_working_directory`
- `skipped_no_code`
- `blocked_unsafe_path`
- `package_missing_before_execution`

**This task does not create examples.**

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

- This tool spec is not runtime orchestration.
- Code Assistant workflow integration is future work.
- Execution-aware analysis workflow is future `v0.25.0` work.
- Report generation from execution output is future `v0.26.0` work.
- The execution helper should produce structured results that later workflows can consume, the same way `gauss_environment_check` and `gauss_package_inspection` already produce structured results without themselves implementing any workflow.

## Related Files

- `planning/v0.24.0-gauss-code-execution-prototype.md`
- `tools/gauss_environment_check.md`
- `tools/gauss_package_inspection.md`
- `scripts/gauss_environment_check.py`
- `scripts/gauss_package_inspection.py`
- `schemas/gauss_environment_check.schema.json`
- `schemas/gauss_package_inspection.schema.json`
- `schemas/gauss_code_execution.schema.json`
- Future `scripts/gauss_code_execution.py`
- `TOOL_SPEC.md`
- `tools/operational_expert_interface.md`
- `workflows/code-assistant-response.md`
- `workflows/expert-routing.md`
- `experts/EXPERT_BOUNDARY_MATRIX.md`
- `KNOWN_LIMITATIONS.md`

## Maintenance Notes

- Keep execution safety boundaries stricter than advisory tools — this is the highest-risk tool this repository has specified so far, and any relaxation must be a deliberate, documented decision, not an incidental one.
- Update this spec before implementation if execution policy changes.
- Keep schema/result wording distinct from interpretation claims — an `execution_status` field must never be phrased in a way that could be read as a correctness or validity claim.
- Re-run response-behavior benchmarks after workflow integration, not just after implementation.
- Do not add automatic retries/reruns without a separate design milestone.
- Revisit platform-specific GAUSS invocation behavior (Windows/macOS/Linux differences in process invocation, termination, and timeout enforcement) before implementation.
- Do not claim execution, schema validation, examples, or benchmarks are implemented until each actually exists.
