# GAUSS Package Inspection Tool

## Purpose

This tool is intended to inspect or infer which GAUSS packages, application modules, or package-like add-ons appear available in a detected GAUSS environment.

It should help determine:

- Whether package inspection was possible.
- Which GAUSS environment/version is being inspected.
- Whether requested packages appear installed, missing, unknown, or inaccessible.
- Whether package availability can be assumed.
- What inspection method was used.
- What assistant operating mode should be recommended.

State clearly:

- This tool does not run user GAUSS code.
- This tool does not execute statistical analysis.
- This tool does not install packages.
- This tool does not activate Execution Mode.
- This tool does not validate GAUSS syntax.
- This tool does not prove statistical validity.
- This tool does not prove package-dependent code will run.
- This tool depends on, but is separate from, environment detection.

## Tool Status

- **Status:** planned / specified.
- **Implementation:** not yet implemented.
- **Permission level:** read-only package/environment inspection.
- **Runtime orchestration:** not implemented.
- **Code execution:** not implemented.
- **Package installation:** not implemented.
- **Result schema:** created (`schemas/gauss_package_inspection.schema.json`) — see "Result Schema" below.
- **Example outputs:** planned separately (`examples/tools/gauss-package-inspection-*.json`, not yet created).

## Relationship to Environment Detection

- Package inspection should normally use `gauss_environment_check` output as primary context.
- The selected executable path, GAUSS version, platform, and detection status should guide package inspection.
- Package inspection should inspect the selected GAUSS environment only.
- If environment detection selected GAUSS 26, inspect the GAUSS 26 package context by default.
- If the user selected GAUSS 25, inspect the GAUSS 25 package context.
- Do not mix package results across GAUSS versions unless explicitly requested.
- GAUSS found does not mean packages are installed.
- GAUSS version known does not mean package availability is known.
- `execution_candidate` does not mean package inspection has occurred.

This mirrors the same environment-first design already established in `tools/gauss_environment_check.md` and `schemas/gauss_environment_check.schema.json` — package inspection is a second, dependent layer, not a replacement for environment detection.

## Operating Mode Relationship

### Advisory Mode

Recommended when:

- The GAUSS environment is not found.
- The GAUSS environment is ambiguous.
- The GAUSS executable is inaccessible.
- Package inspection fails.
- Package status is unknown.
- A required package is missing.
- Execution tooling is unavailable.

### Verified Knowledge Mode

- Package inspection is not required for Verified Knowledge Mode.
- Verified command evidence can still support syntax or usage claims.
- Package availability is not the same as command evidence.
- Command evidence is not execution.

### Execution Candidate

- Package inspection may support a future execution-candidate assessment.
- Installed package status does not activate Execution Mode.
- Future execution still requires an execution tool, user permission, a safe working directory, and safety constraints.
- A package being installed does not mean user code has run.

## Permission and Safety Model

- Read-only inspection only.
- No user GAUSS code execution.
- No statistical analysis.
- No package installation.
- No license activation or modification.
- No environment mutation.
- No file modification.
- No deletion.
- No generated output files.
- No hidden metadata query unless explicitly allowed in a future implementation.
- No long-running commands.
- No network access required.
- An optional future metadata query must be minimal, timeout-bounded, and must not run user code.
- All failures should return structured results.
- Advisory Mode remains available after any failure.

This tool is classified as read-only inspection, the same category as `gauss_environment_check`. Any future GAUSS metadata invocation is higher risk than filesystem inspection and must be treated as a separate implementation decision — the same caveat `tools/gauss_environment_check.md` already applies to its own optional version query.

## Inputs

| Input | Optional | Purpose | Safety considerations | Default if omitted |
|---|---|---|---|---|
| `environment_check_result` | Yes | Lets a caller pass a prior `gauss_environment_check` result directly as context, avoiding redundant detection. | Should be treated as primary context when provided and valid; a stale or fabricated result must not be trusted blindly. | No prior result — package inspection would need to request or assume environment context is unavailable. |
| `executable_path` | Yes | Lets a caller point directly at a specific GAUSS executable, bypassing `environment_check_result`. | Must be handled cautiously; providing a path does not by itself imply any package is installed. | No path — falls back to `environment_check_result` context if given, otherwise unavailable. |
| `gauss_version` | Yes | Lets a caller state which GAUSS version's package context to inspect. | Should match the selected environment's version where possible; must not be used to fabricate results for an unconfirmed version. | The version implied by `environment_check_result` or `executable_path`, if any. |
| `platform_hint` | Yes | Lets a caller state a known platform when it cannot be reliably auto-detected. | Should not override an actual detected platform if one is available. | Detected platform, or `unknown` if undetectable. |
| `requested_packages` | Yes | Narrows inspection to specific named packages rather than a broad scan. | Must not fabricate a status for a package that was never actually checked. | No specific packages requested — inspection may report whatever it can determine generally. |
| `package_search_paths` | Yes | Lets a caller supply known package/application directories to check. | Must be read-only; must not be assumed to exist without checking. | No caller-supplied paths — the tool uses its own conservative, documented candidate locations. |
| `allow_metadata_query` | Yes | Permits the tool to attempt a minimal GAUSS metadata query for package listing. | Governs the one input that could invoke the executable; should be conservative by default. | `false`, or implementation-defined, until the safety of the metadata-query mechanism is established. |
| `inspection_timeout_seconds` | Yes | Bounds how long inspection (including any metadata query) may run. | Prevents a hung or slow check from blocking the assistant. | A short, safe default (exact value is an implementation decision). |
| `strict` | Yes | Requests that the tool avoid guessing outside supplied paths/context. | Should be honored literally — a `strict` request that finds nothing should return `unavailable`/`unknown`, not silently broaden the search. | `false` — the tool may fall back to its own conservative discovery if no explicit context is given. |

Important input rules:

- `environment_check_result` should be primary when provided.
- A directly supplied `executable_path` should be handled cautiously and should not imply package availability.
- `requested_packages` narrows inspection to named packages when supplied.
- `package_search_paths` should be read-only.
- `allow_metadata_query` should default to `false` or implementation-defined until safety is established.
- `strict` should avoid guessing outside supplied context.
- Inputs must not mutate files or environment variables.

## Outputs

| Output | Type |
|---|---|
| `checked` | boolean |
| `environment_status` | `found` / `not_found` / `ambiguous` / `inaccessible` / `error` / `unknown` |
| `executable_path` | string or null |
| `gauss_version` | string or null |
| `package_inspection_status` | `complete` / `partial` / `unavailable` / `error` / `unknown` |
| `packages` | array |
| `requested_packages` | array |
| `missing_packages` | array |
| `unknown_packages` | array |
| `package_search_paths` | array |
| `inspection_method` | string |
| `operating_mode_recommendation` | `advisory` / `verified_knowledge` / `execution_candidate` |
| `can_assume_package_availability` | true / false / unknown |
| `warnings` | array |
| `errors` | array |
| `next_steps` | array |
| `raw_inspection_details` | optional object |

**Each package object:**

| Field | Type |
|---|---|
| `name` | string |
| `installed` | true / false / unknown |
| `version` | string or null |
| `version_known` | boolean |
| `source` | string |
| `path` | string or null |
| `package_type` | `base` / `application_module` / `package` / `unknown` |
| `notes` | array |

**Important meanings:**

- `checked: true` means package inspection was attempted, not that packages were found.
- `package_inspection_status: complete` does not mean execution is possible.
- `installed: true` for a package does not mean code was executed.
- `installed: true` does not validate command syntax.
- `installed: false` does not mean GAUSS is missing.
- `installed: "unknown"` is not the same as missing.
- `can_assume_package_availability: true` should be conservative.
- Package availability may differ by GAUSS version.
- Package availability does not prove methodology validity or product value.

## Package Inspection Status Semantics

### complete

**Use when:**

- Inspection completed for the requested scope.
- Requested packages, if any, have `installed`/`missing`/`unknown` statuses.
- Uncertainty is low enough to report the result as complete.

**Caveat:** complete inspection does not mean code has run; complete inspection does not validate syntax or methodology.

### partial

**Use when:**

- Some package locations or requested packages were inspected.
- Uncertainty remains.
- Permissions, unsupported paths, or incomplete metadata limit confidence.

### unavailable

**Use when:**

- Environment detection is `not_found`, `ambiguous`, `inaccessible`, `error`, or `unknown`.
- Package inspection cannot proceed safely.
- Package inspection context is missing.

### error

**Use when:** package inspection fails unexpectedly.

### unknown

**Use when:**

- The tool cannot determine package status.
- The inspection method is unsupported or inconclusive.

## Package Object Semantics

- `name` should be the package/module name as detected or requested.
- `installed` should be `true`, `false`, or `"unknown"`.
- `version` should be `null` when unknown.
- `version_known: false` does not mean the package is missing.
- `source` should describe where status came from, such as `filesystem_scan`, `requested_only`, `metadata_query`, `manual_path`, `unknown`.
- `path` should be included only when useful and safe.
- `package_type` should distinguish `base`, `application_module`, `package`, and `unknown` when possible.
- `notes` should capture uncertainty, warnings, or mapping caveats.

## Inspection Strategy

Planned strategy, described without implementation code.

### Environment-check context

- Use the selected executable path/version/platform from environment detection.
- If environment status is not found/usable, return `unavailable` or `unknown`.
- Preserve the selected GAUSS version context.
- Do not mix package contexts across versions.

### Requested package inspection

- If requested packages are provided, inspect or report those specifically.
- Missing requested packages should be listed in `missing_packages`.
- Unknown requested packages should be listed in `unknown_packages`.
- Do not treat unknown as missing.

### Filesystem inspection

- Read package/application directories where known.
- Do not overclaim exact paths before implementation verifies them.
- Handle system-installed and user-installed locations.
- Respect version-specific package contexts.

### Configuration/path inspection

- Consider GAUSS library paths, application paths, or configuration files if known.
- Treat startup/config inspection as read-only.
- Do not execute startup files.

### Optional metadata query

- May be considered only if `allow_metadata_query` permits it.
- Must not run user code.
- Must use a timeout.
- Must not mutate state.
- Must clearly report metadata-only invocation if implemented later.
- If no safe metadata query is confirmed, do not invoke GAUSS — the same conservative default `tools/gauss_environment_check.md`'s optional version query already uses.

## Assistant Response Rules

**If package installed:**

- State the package appears available.
- Report version/path if known and safe.
- Do not claim code execution.
- Do not claim syntax validity from package availability alone.
- Still use the GAUSS Language Expert/evidence for command syntax.

**If package missing:**

- State the package was not detected.
- Do not claim GAUSS is missing.
- Recommend advisory fallback.
- Provide alternatives or installation guidance only if supported by verified evidence.

**If package unknown:**

- State package status is unknown.
- Avoid overclaiming.
- Continue in Advisory or Verified Knowledge Mode.
- Suggest next steps such as providing package paths or running inspection later.

**If inspection is unavailable:**

- Explain why package inspection could not be performed.
- Continue helping in Advisory Mode.

**If inspection errors:**

- Report a structured error.
- Do not break the assistant.
- Do not claim package status beyond what is known.

## Expert Boundary Rules

- Package inspection supports the GAUSS Language Expert but does not replace command evidence.
- Package availability does not validate syntax.
- Package availability does not validate statistical methodology.
- Package availability does not validate maintainability.
- Package availability does not validate documentation quality.
- Package availability does not validate education/learning design.
- Package availability does not validate product value.
- Package availability does not imply execution occurred.
- A missing package should not be treated as proof that a method is invalid.
- An installed package should not be treated as proof that a method is appropriate.
- Package availability may inform implementation feasibility, not methodological correctness.

## Failure and Fallback Rules

- Always return a structured result.
- On failure, recommend Advisory Mode.
- Do not break the assistant if inspection fails.
- Do not block code writing, explanation, review, documentation, education, or product reasoning.
- Do not overstate missing packages when inspection is inconclusive.
- Prefer `unknown` over false certainty.
- Include next steps when possible.
- Do not ask for unnecessary clarification if Advisory Mode can answer the user's underlying request.

## Result Schema

**Schema file:** `schemas/gauss_package_inspection.schema.json`

The schema now exists and validates the full output contract defined above: `environment_status` matches `gauss_environment_check.schema.json`'s `detection_status` enum; `package_inspection_status` and `operating_mode_recommendation` are controlled enums; `installed` and `can_assume_package_availability` use a shared `tri_state` definition (`true`/`false`/`"unknown"`); `packages`, `requested_packages`, `missing_packages`, `unknown_packages`, `package_search_paths`, `warnings`, `errors`, and `next_steps` are arrays; each `packages` item is a fully-specified package object (`name`, `installed`, `version`, `version_known`, `source`, `path`, `package_type`, `notes`); `raw_inspection_details` is optional with `additionalProperties: true`; `checked` and the other fifteen top-level fields are required. The schema also encodes cross-field consistency constraints — for example, `package_inspection_status: complete` requires `checked: true` and zero `errors`; a non-`found` `environment_status` forbids `package_inspection_status: complete` and forbids `operating_mode_recommendation: execution_candidate`; and any non-empty `missing_packages` forbids `can_assume_package_availability: true`.

Implementation of the tool itself remains not yet done — the schema validates a future tool's output shape; it does not run any inspection code.

## Planned Examples

**Future examples:**

- `examples/tools/gauss-package-inspection-complete.json`
- `examples/tools/gauss-package-inspection-missing.json`
- `examples/tools/gauss-package-inspection-partial.json`
- `examples/tools/gauss-package-inspection-unavailable.json`
- `examples/tools/gauss-package-inspection-unknown.json`

Do not create examples in this task.

## Evaluation Plan

Future `27.x` benchmarks:

- `27.1` — Package installed but no execution.
- `27.2` — Package missing with advisory fallback.
- `27.3` — Package unknown without overclaiming.
- `27.4` — Package inspection unavailable because GAUSS not found.
- `27.5` — Base command vs. package command distinction.
- `27.6` — Package installed is not syntax evidence.
- `27.7` — Package installed is not methodology evidence.
- `27.8` — User requests execution but only package inspection exists.

Do not add these benchmarks yet. They should be added after the schema and examples exist.

## Relationship to Future Execution

Package inspection is prerequisite context for future execution, but not execution itself.

Package inspection can help answer:

- Is a required package likely available?
- Should the assistant warn that a package may be missing?
- Should future execution be blocked or flagged?

But it cannot answer:

- Will this code run successfully?
- Is the syntax valid?
- Are the results statistically valid?
- Is the analysis method appropriate?
- Is the report correct?

## Related Files

- `planning/v0.22.0-gauss-package-inspection-tool.md`
- `planning/v0.21.0-gauss-environment-detection-implementation.md`
- `scripts/gauss_environment_check.py`
- `tools/gauss_environment_check.md`
- `schemas/gauss_environment_check.schema.json`
- `TOOL_SPEC.md`
- `tools/operational_expert_interface.md`
- `workflows/code-assistant-response.md`
- `workflows/expert-routing.md`
- `experts/gauss-language/OPERATIONAL_PROFILE.md`
- `experts/EXPERT_REGISTRY.md`
- `experts/EXPERT_BOUNDARY_MATRIX.md`
- `KNOWN_LIMITATIONS.md`

## Maintenance Notes

- Update this tool spec when the schema is created.
- Update this tool spec when examples are created.
- Update this tool spec when implementation exists.
- Update `KNOWN_LIMITATIONS.md` when implementation status changes.
- Update `workflows/code-assistant-response.md` only after behavior is integrated.
- Add benchmarks only after behavior is testable.
- Do not claim package inspection is implemented until implementation exists.
- Do not weaken environment detection fallback rules when package inspection is added.
