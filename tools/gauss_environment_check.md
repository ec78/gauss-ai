# GAUSS Environment Check Tool

## Purpose

This tool is intended to inspect whether GAUSS is installed or discoverable in a local/user-provided environment.

It should help determine:

- Whether GAUSS appears installed.
- Whether an executable path can be found.
- Whether the executable appears accessible.
- Whether the GAUSS version can be identified, if allowed.
- What detection method was used.
- Whether the assistant should remain in Advisory Mode, Verified Knowledge Mode, or mark the environment as an Execution Mode candidate.

State clearly:

- This tool does not run user GAUSS code.
- This tool does not inspect installed GAUSS packages.
- This tool does not validate GAUSS syntax.
- This tool does not prove statistical validity.
- This tool does not make Execution Mode active by itself.
- This tool is a prerequisite signal for future execution capability, not an execution engine.

## Tool Status

- **Status:** planned / specified.
- **Implementation:** not yet implemented.
- **Permission level:** read-only environment inspection.
- **Runtime orchestration:** not implemented.
- **Code execution:** not implemented.
- **Package inspection:** not implemented.
- **Result schema:** created (`schemas/gauss_environment_check.schema.json`) — see "Result Schema" below.
- **Example outputs:** created (`examples/tools/gauss-environment-*.json`) — see "Examples" below.

## Operating Mode Relationship

This tool exists to support the three operating modes defined in `planning/v0.19.0-gauss-tooling-strategy-and-execution-modes.md`.

### Advisory Mode

Recommended when:

- GAUSS is not found.
- GAUSS availability is unknown.
- The executable is inaccessible.
- Multiple candidates are ambiguous.
- Detection fails.
- The user has not requested execution.
- Execution tooling is unavailable.

### Verified Knowledge Mode

- Environment detection is not required for Verified Knowledge Mode.
- Verified command evidence can still support syntax/usage claims even if GAUSS is not detected.
- Verified evidence is not execution.

### Execution Candidate

- If GAUSS is found and accessible, the tool may recommend `execution_candidate`.
- `execution_candidate` is not the same as Execution Mode.
- Future execution tools, user permission, a scoped working directory, package checks, and safety constraints are still required before code execution.

## Permission and Safety Model

- Read-only inspection only.
- No user code execution.
- No package installation.
- No license activation or modification.
- No environment mutation.
- No file modification.
- No deletion.
- No writing generated files.
- No long-running commands.
- No network access required.
- An optional future version query must be minimal and must not run user code.
- All failures should return structured results rather than crashing the assistant.
- Advisory Mode remains available after any failure.

This tool is classified as low-risk read-only inspection per `TOOL_SPEC.md`'s Permission Model, in contrast to the future GAUSS Code Execution Tool, which `TOOL_SPEC.md`'s categories would classify as high-risk. The one exception worth flagging explicitly: any executable invocation for version detection (e.g., a `--version`-style flag) should be treated cautiously and documented as a separate implementation decision, since it is the one point where this otherwise purely-inspecting tool would invoke the GAUSS executable at all.

## Inputs

| Input | Optional | Purpose | Safety considerations | Default if omitted |
|---|---|---|---|---|
| `preferred_executable_path` | Yes | Lets the user or a prior detection point directly at a specific GAUSS executable. | Must be validated for existence/accessibility before use; must not be assumed valid. | No preferred path — the tool falls back to discovery. |
| `working_directory` | Yes | Scopes any filesystem checks to a specific directory context. | Must not be modified by the tool. | The tool's own invocation directory, used read-only. |
| `platform_hint` | Yes | Lets a caller state a known platform when it cannot be reliably auto-detected. | Should not override an actual detected platform if one is available. | Detected platform, or `unknown` if undetectable. |
| `allow_version_query` | Yes | Permits the tool to attempt a minimal version check. | Governs the one input that could invoke the executable; should be conservative by default. | `false`, or implementation-defined, until the safety of the version-query mechanism is established. |
| `detection_timeout_seconds` | Yes | Bounds how long detection (including any version query) may run. | Prevents a hung or slow check from blocking the assistant. | A short, safe default (exact value is an implementation decision, not fixed by this spec). |
| `environment_overrides` | Yes | Lets a caller simulate or adjust the environment the tool inspects (e.g., an alternate `PATH`). | Must not mutate the real environment; must not be used to fabricate a misleading `installed: true`. | No overrides — the tool inspects the real environment as-is. |
| `strict` | Yes | Requests that the tool use only the `preferred_executable_path` (if given) rather than falling back to broader discovery. | Should be honored literally — a `strict` request that finds nothing should return `not_found`, not silently broaden the search. | `false` — the tool may fall back to discovery if no preferred path is given or it fails. |

Important input rules:

- The tool should work with no inputs.
- A user-provided path should take precedence over discovery.
- `allow_version_query` should default to `false` or implementation-defined until safety is established.
- `detection_timeout_seconds` should have a safe default.
- Environment overrides must not mutate the real environment.
- `working_directory` must not be modified.

## Outputs

| Output | Type |
|---|---|
| `checked` | boolean |
| `installed` | true / false / unknown |
| `accessible` | true / false / unknown |
| `executable_path` | string or null |
| `executable_candidates` | list |
| `version` | string or null |
| `version_known` | boolean |
| `platform` | string or null |
| `detection_method` | string |
| `detection_status` | `found` / `not_found` / `ambiguous` / `inaccessible` / `error` / `unknown` |
| `operating_mode_recommendation` | `advisory` / `verified_knowledge` / `execution_candidate` |
| `can_execute_gauss_code` | true / false / unknown |
| `warnings` | list |
| `errors` | list |
| `next_steps` | list |
| `raw_detection_details` | optional object |

**Important meanings:**

- `checked: true` means detection was attempted, not that GAUSS was found.
- `installed: true` does not mean code was executed.
- `accessible: true` does not mean package availability is known.
- `version_known: false` does not mean GAUSS is missing.
- `execution_candidate` does not mean Execution Mode is active.
- `can_execute_gauss_code: true` means future execution *may* be possible, not that execution occurred.
- `raw_detection_details` should avoid exposing sensitive path information beyond what is needed.

## Detection Status Semantics

### found

**Use when:**

- A plausible GAUSS executable was found.
- It appears accessible.
- Ambiguity is resolved.

**Recommendation:** `operating_mode_recommendation: execution_candidate`

**Caveat:** no user code has run; no package inspection has occurred; no syntax or methodology has been validated.

### not_found

**Use when:** no plausible GAUSS executable is found.

**Recommendation:** `operating_mode_recommendation: advisory`

### ambiguous

**Use when:**

- Multiple plausible executables are found.
- The tool cannot safely choose one.

**Recommendation:** `operating_mode_recommendation: advisory`; ask the user to provide a preferred path or choose a candidate.

### inaccessible

**Use when:**

- A path exists but cannot be accessed or queried.
- Permissions, licensing, or execution restrictions prevent confirmation.

**Recommendation:** `operating_mode_recommendation: advisory`

### error

**Use when:** detection fails unexpectedly.

**Recommendation:** `operating_mode_recommendation: advisory`; include a structured error.

### unknown

**Use when:**

- The environment cannot be checked.
- The platform is unsupported.
- Detection is inconclusive.

**Recommendation:** `operating_mode_recommendation: advisory`

## Detection Strategy

Planned strategy, described without implementation code.

### User-provided path

- Check first.
- Validate existence/accessibility if possible.
- Do not search broadly if `strict` mode requires using only the provided path.
- Return `inaccessible` if the path exists but cannot be used.
- Return `not_found` if the provided path does not exist.
- Return `found` if it is plausible and accessible.

### PATH lookup

- Search `PATH` for plausible GAUSS executable names.
- Record candidates.
- Return `ambiguous` if multiple candidates are plausible and no deterministic policy exists.
- Do not silently choose one unless an implementation policy defines precedence.

### Common installation locations

List categories, not overly specific hardcoded promises:

- **Windows:** Program Files / GAUSS install directories / `PATH` / user-provided path.
- **macOS:** Applications / command-line paths / `PATH` / user-provided path.
- **Linux:** `PATH` / `opt` or local application directories / user-provided path.
- **WSL/container environments** may require special handling.

Exact executable names and path patterns should be verified during implementation. This planning-adjacent spec does not claim these paths are exhaustive.

### Optional version query

- May be attempted only if `allow_version_query` permits it.
- Must not run user code.
- Must use a timeout.
- Failure should set `version_known: false`.
- Failure should not automatically change `installed: true` to `false`.
- Output should distinguish version unknown from executable missing.

## Assistant Response Rules

**If status is `found`:**

- Say GAUSS appears available.
- Report path/version when appropriate.
- Say no GAUSS code has been run.
- Say package availability is still unknown.
- Explain that future execution still requires an execution tool and user permission.

**If status is `not_found`:**

- Say GAUSS was not detected.
- Remain in Advisory Mode.
- Do not claim execution.
- Continue helping with code, explanation, docs, or analysis design.
- Optionally ask for a preferred executable path.

**If status is `ambiguous`:**

- List candidate paths if safe.
- Ask the user to choose.
- Do not execute.
- Remain in Advisory Mode.

**If status is `inaccessible`:**

- Explain the access issue.
- Remain in Advisory Mode.
- Suggest checking permissions/path/license if appropriate.
- Do not claim `installed: false` too strongly if a path exists.

**If status is `error` or `unknown`:**

- State detection could not be completed.
- Preserve usefulness in Advisory or Verified Knowledge Mode.
- Do not claim execution.

## Expert Boundary Rules

- The GAUSS Environment Check supports the GAUSS Language Expert but does not replace command evidence.
- Detecting GAUSS does not validate syntax.
- Detecting GAUSS does not validate statistical methodology.
- Detecting GAUSS does not validate maintainability.
- Detecting GAUSS does not validate documentation quality.
- Detecting GAUSS does not validate learning design.
- Detecting GAUSS does not validate product value.
- Successful future execution would still not prove statistical validity or product value.
- Package availability remains unknown until a package inspection tool exists.

## Failure and Fallback Rules

- Always return a structured result.
- On failure, recommend Advisory Mode.
- Do not break the assistant if detection fails.
- Do not block code writing, explanation, review, documentation, education, or product reasoning.
- Do not overstate missing GAUSS when detection is inconclusive.
- Prefer `unknown` or `inaccessible` over false certainty.
- Include next steps when possible.
- Do not ask for unnecessary clarification if Advisory Mode can answer the user's underlying request.

## Result Schema

**Schema file:** `schemas/gauss_environment_check.schema.json`

The schema now exists and validates the full output contract defined above: `installed`, `accessible`, and `can_execute_gauss_code` use a shared `tri_state` definition (`true`/`false`/`"unknown"`); `detection_status` and `operating_mode_recommendation` are controlled enums; `warnings`, `errors`, and `next_steps` are string arrays; `executable_candidates` is an array of candidate objects (`path`, `source`, `accessible`, `notes`); `raw_detection_details` is optional with `additionalProperties: true`; `checked` and the other fifteen top-level fields are required. The schema also encodes the consistency constraints between `detection_status` and the recommended fields (for example, `detection_status: found` requires `installed: true`, `accessible: true`, `operating_mode_recommendation: execution_candidate`, and a non-null `executable_path`).

Implementation of the tool itself remains not yet done — the schema validates a future tool's output shape; it does not run any detection code.

## Examples

**Example outputs now exist**, validated against `schemas/gauss_environment_check.schema.json`:

- `examples/tools/gauss-environment-found.json` — accessible executable found, version known.
- `examples/tools/gauss-environment-not-found.json` — no plausible executable found; Advisory Mode.
- `examples/tools/gauss-environment-ambiguous.json` — two candidates found; Advisory Mode, user clarification needed.
- `examples/tools/gauss-environment-inaccessible.json` — a path exists but cannot be confirmed accessible; Advisory Mode.
- `examples/tools/gauss-environment-version-unknown.json` — executable found and accessible, but version not queried; demonstrates that `found` does not require `version_known: true`.

All five are clearly synthetic (example-style paths such as `C:/example/gauss26/tgauss.exe`, explicit "Synthetic example output" warnings) and do not represent any real detected installation. Implementation of the tool itself remains not yet done.

## Evaluation Plan

Future `26.x` benchmarks, from `planning/v0.20.0-gauss-environment-detection-tool.md`:

- `26.1` — GAUSS detected, version known.
- `26.2` — GAUSS not detected.
- `26.3` — Detection ambiguous.
- `26.4` — Executable inaccessible.
- `26.5` — Version unknown but executable found.
- `26.6` — User asks to run code but GAUSS not detected.
- `26.7` — User asks whether command syntax is valid after GAUSS detected.
- `26.8` — User asks whether results are statistically valid because GAUSS is installed.

Do not add these benchmarks yet. They should be added after the schema and examples exist.

## Related Files

- `planning/v0.20.0-gauss-environment-detection-tool.md`
- `planning/v0.19.0-gauss-tooling-strategy-and-execution-modes.md`
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
- Update this tool spec if the actual detection strategy differs from the plan.
- Update `KNOWN_LIMITATIONS.md` when implementation status changes.
- Update `workflows/code-assistant-response.md` only after behavior is integrated.
- Add benchmarks only after behavior is testable.
- Do not claim the tool is implemented until implementation exists.
