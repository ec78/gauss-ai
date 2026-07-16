# Execution-Aware Analysis Workflow

## Purpose

This workflow defines how the Code Assistant should interpret and respond to structured `gauss_code_execution` result objects.

- It helps transform execution-result evidence into safe user-facing analysis.
- It distinguishes execution status from interpretation.
- It routes interpretation to the correct expert dimensions.
- It preserves Advisory Mode when execution does not occur or cannot be trusted.
- It prevents overclaims from completed execution.

State clearly:

- This workflow does not execute GAUSS code.
- This workflow does not fix GAUSS invocation.
- This workflow does not implement runtime orchestration.
- This workflow does not generate polished reports.
- This workflow does not replace econometric/statistical review.

## When to Use This Workflow

**Use when:**

- The assistant receives a structured execution result object.
- The user asks what an execution result means.
- `stdout`/`stderr`/`output_files`/`warnings`/`errors` need interpretation.
- Execution completed, failed, timed out, was blocked, skipped, errored, or unknown.
- The user asks whether execution proves the code/model/result is valid.

**Do not use when:**

- The user only asks for code generation and no execution result is present.
- The user asks to execute code but no execution tool/result is available.
- The task is pure documentation, education, product, or econometrics without execution evidence.
- The user asks for a polished report from output — that belongs to a future report-generation workflow.

## Inputs

**Primary input:** a result shaped by `schemas/gauss_code_execution.schema.json`.

**Important fields:** `checked`, `executed`, `execution_status`, `operating_mode`, `executable_path`, `gauss_version`, `working_directory`, `command`, `code_source`, `script_path`, `timeout_seconds`, `elapsed_seconds`, `exit_code`, `stdout`, `stderr`, `output_files`, `warnings`, `errors`, `next_steps`, `raw_execution_details`.

**Optional context:**

- Environment detection result.
- Package inspection result.
- Original user request.
- Code or script content, if available.
- Model/econometric context, if provided.

## First Step: Separate Evidence from Interpretation

This is the first rule, applied before anything else in this workflow.

**Execution evidence includes:**

- Whether the helper reports execution occurred.
- `execution_status`.
- `exit_code`.
- `elapsed_seconds`.
- `stdout`.
- `stderr`.
- `output_files` metadata.
- `warnings`.
- `errors`.
- `next_steps`.

**Interpretation includes:**

- What estimates mean.
- Whether model assumptions are plausible.
- Whether diagnostics are adequate.
- Whether code is maintainable.
- Whether results support a decision.
- Whether output should be reported to users/customers.

**Never treat interpretation as directly proven by execution evidence.**

## Execution Status Handling

### completed

**Assistant may say:**

- The helper reports that GAUSS was invoked.
- The process completed in the reported context.
- Exit code, elapsed time, stdout/stderr, and output file metadata were captured if present.

**Assistant must not say:**

- The model is statistically valid.
- The estimates are trustworthy.
- The method is appropriate.
- Syntax is generally valid across GAUSS versions.
- Diagnostics are adequate.
- Conclusions are supported without review.

**Required next step:**

- Explain what was captured.
- State interpretation limits.
- Route estimates/diagnostics/methodology to the Econometrics Expert.
- Route implementation details to the GAUSS Language Expert if needed.

### failed

**Assistant may say:**

- GAUSS was invoked but execution failed.
- stderr/errors are evidence for debugging.
- Failure may indicate syntax, runtime, dependency, data, or path issues.

**Assistant must not say:**

- The model is methodologically invalid solely because execution failed.
- Results were produced if they were not captured.
- Code has been fixed unless it was actually rerun.

**Required next step:**

- Summarize error evidence.
- Route syntax/runtime issues to the GAUSS Language Expert.
- Route dependency context to package/environment handling.
- Preserve Advisory Mode fallback.

### timed_out

**Assistant may say:**

- GAUSS was invoked but exceeded the timeout.
- Partial stdout/stderr may exist.
- Timeout can reflect loops, large data, convergence, inefficient code, or invocation behavior.

**Assistant must not say:**

- The model is wrong.
- The code is invalid.
- Results are available if not captured.
- Increasing the timeout is automatically safe.

**Required next step:**

- Inspect partial output if present.
- Recommend a smaller test case, convergence checks, loop review, data-size review, or timeout policy review.
- Route performance/code structure to the Software Engineering Expert.
- Route convergence/model issues to the Econometrics Expert.

### blocked

**Assistant may say:**

- Execution did not occur.
- Safety policy blocked the request.
- The blocking reason and a safe next step.

**Assistant must not say:**

- Code ran.
- Output exists.
- The block proves the code or method invalid.

**Required next step:**

- Identify the blocker.
- Recommend safe remediation, such as selecting an environment, providing a working directory, resolving an unsafe path, or addressing a missing package.

### skipped

**Assistant may say:**

- Execution did not run because required execution input was absent or no explicit execution request was present.

**Assistant must not say:**

- Code ran.
- Output was produced.

**Required next step:**

- Ask for explicit code or a script path and a working directory.
- Offer advisory review if the user does not want execution.

### error

**Assistant may say:**

- The helper/tool encountered an unexpected error.
- Execution state may be unreliable.

**Assistant must not say:**

- Execution succeeded.
- The model is invalid.
- Outputs are complete.

**Required next step:**

- Explain the helper/tool error.
- Recommend a safe retry or diagnostic path.
- Preserve Advisory Mode fallback.

### unknown

**Assistant may say:**

- Execution state could not be determined.

**Assistant must not say:**

- Code ran successfully.
- Code failed definitively.
- Results are reliable.

**Required next step:**

- Recommend a rerun with clearer environment/tool context.
- Continue Advisory Mode if a rerun is not available.

## Expert Routing Rules

Use the six operational experts.

### GAUSS Language Expert

Use for: GAUSS syntax/runtime errors, command usage, data structures, the package/base distinction, implementation correctness, stdout/stderr debugging.

### Econometrics Expert

Use for: model assumptions, identification, diagnostics, statistical validity, coefficient interpretation, forecast/model evaluation, whether results can be trusted statistically.

### Software Engineering Expert

Use for: performance/timeouts, long-running code, code organization, maintainability, testability, safe refactoring.

### Documentation Expert

Use for: explaining outputs clearly, documenting execution results, usage/troubleshooting notes, reference-style clarity.

### Education Expert

Use for: teaching what the output means, scaffolding beginner understanding, conceptual explanation, exercises/checks for learning.

### Product Expert

Use for: user workflow impact, time-to-value, prioritizing next steps, product/user-value implications.

**Execution status is evidence routed through the expert system, not an expert conclusion by itself.**

## Interpretation Boundaries

**Execution result can support claims about:**

- Whether the helper reports execution happened.
- Status.
- Exit code.
- Elapsed time.
- stdout/stderr.
- Output file metadata.
- Warnings/errors.
- Next steps reported by the helper.

**Execution result cannot prove:**

- Methodology validity.
- Statistical correctness.
- Estimate reliability.
- Causal identification.
- Model assumptions.
- Diagnostic adequacy.
- Code maintainability.
- Documentation quality.
- Learner understanding.
- Product value.
- Production readiness.

**`completed` with `exit_code: 0` is execution evidence only.**

## Response Pattern

**Recommended five-part response:**

1. Execution status summary.
2. What was captured.
3. What this does and does not prove.
4. Expert-routed interpretation.
5. Safe next steps.

**Template:**

```text
The execution result reports that the code [completed/failed/timed out/was blocked/was skipped].
Captured evidence: [exit code, elapsed time, stdout/stderr, warnings/errors, output files].
This shows [what execution evidence supports], but it does not by itself prove [methodology/statistical/interpretation limits].
From a [GAUSS/econometrics/software/documentation/education/product] perspective, ...
Next step: ...
```

## Handling stdout and stderr

- Summarize stdout/stderr rather than overquoting long output.
- Do not hide stderr just because `exit_code` is `0`.
- Do not invent missing output.
- Preserve materially important warnings/errors.
- Mention truncation warnings.
- Separate captured output from interpretation.
- If output is too long, summarize and recommend inspecting full artifacts if available.

## Handling Output Files

- `output_files` metadata means files were listed, not read.
- Do not claim file contents unless they are provided or read by a later explicit workflow/tool.
- Distinguish `created_by_execution` `true`/`false`/`"unknown"`.
- Avoid exposing unnecessary sensitive local paths.
- Recommend reading output files only through an explicit future file-reading/reporting workflow.

## Handling Warnings and Errors

- Surface execution warnings.
- Surface errors that affected execution.
- Do not treat warnings as fatal unless indicated.
- Do not ignore warnings about:
  - Timeout.
  - Truncation.
  - Package status.
  - Unsafe paths.
  - Missing environment.
  - Real-invocation limitation.
  - Non-interactive invocation uncertainty.

## Handling Package Context

- A missing package before execution may block execution.
- Unknown package status may warn.
- An installed package does not prove syntax validity.
- An installed package does not prove methodology validity.
- An installed package does not prove execution success.
- A missing package does not mean GAUSS is missing.
- No auto-installation.

## Handling Real Invocation Limitation

- `v0.25.0` found that the naive `[executable_path, script_path]` command form entered the interactive GAUSS 26 prompt and timed out rather than exiting non-interactively.
- Fake-runner self-tests are not proof of real GAUSS invocation success.
- Do not describe real execution as production-ready while this remains unresolved.
- If the user asks whether execution is reliable/production-ready, say it is not yet confirmed.
- If an execution result comes from a fake runner/synthetic example, label it as such.

## Failure and Fallback Patterns

- `failed` → debug using stderr/errors; do not fabricate results.
- `timed_out` → inspect partial output and investigate performance/convergence/invocation.
- `blocked` → resolve the safety/input issue.
- `skipped` → ask for explicit code/script and a working directory.
- `error` → diagnose the tool/helper issue.
- `unknown` → rerun or continue Advisory Mode.

**Advisory Mode remains available in all cases.**

## Integration Guidance

This workflow can be referenced by `workflows/code-assistant-response.md` in a later task.

**Future integration should:**

- Apply this workflow when execution result objects are present.
- Never invoke execution automatically.
- Never claim execution unless `executed: true`.
- Never treat execution output as methodology validation.
- Preserve expert routing.

## Evaluation Strategy

Document future `29.x` benchmark topics:

1. Completed execution with coefficient output — avoid methodology overclaim.
2. Completed execution with stderr warning — surface warning.
3. Failed execution with syntax/runtime error — debug without fabricating results.
4. Timed-out execution — performance/convergence fallback.
5. Blocked execution — no execution claims.
6. Skipped execution — ask for explicit code/script.
7. `output_files` present — do not claim file contents were read.
8. Fake-runner self-test passed — do not claim real GAUSS invocation is production-ready.

**Do not add benchmark prompts in this task.**

## Related Files

- `planning/v0.26.0-execution-aware-analysis-workflow.md`
- `workflows/code-assistant-response.md`
- `workflows/expert-routing.md`
- `workflows/expert-routing-cheatsheet.md`
- `experts/EXPERT_REGISTRY.md`
- `experts/EXPERT_BOUNDARY_MATRIX.md`
- `tools/gauss_code_execution.md`
- `schemas/gauss_code_execution.schema.json`
- `scripts/gauss_code_execution.py`

## Maintenance Notes

- Update this workflow if the execution schema changes.
- Rerun response-behavior benchmarks after Code Assistant integration.
- Keep interpretation boundaries aligned with `EXPERT_BOUNDARY_MATRIX.md`.
- Do not add automatic execution or rerun behavior here.
- Keep report generation separate until `v0.27.0` or later.
