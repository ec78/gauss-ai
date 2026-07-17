# Report Generation Workflow

## Purpose

This workflow defines how the Code Assistant should generate structured reports from GAUSS-related analysis artifacts.

The workflow should help produce:

- Technical analysis summaries.
- Econometric interpretation notes.
- Debugging reports.
- Teaching explanations.
- Product/user workflow summaries.

The workflow turns available evidence into a safe, structured report while preserving evidence boundaries.

State clearly:

- This workflow does not run GAUSS code.
- This workflow does not fix GAUSS invocation.
- This workflow does not implement runtime orchestration.
- This workflow does not read output files automatically.
- This workflow does not fabricate missing results.
- This workflow does not turn execution output into methodology validation.
- This workflow does not produce final publication-ready conclusions without expert review.

## When to Use This Workflow

**Use when:**

- The user asks for a report, summary, write-up, technical note, diagnostic report, or explanation based on GAUSS work.
- The user provides GAUSS code and asks for a structured interpretation.
- The user provides execution results and wants a report.
- The user provides stdout/stderr or output snippets.
- The user provides output files or tables that have been explicitly read.
- The user asks for a beginner-friendly explanation of results.
- The user asks for a debugging summary after failed/timed-out execution.

**Do not use when:**

- The user only wants code generation.
- The user only wants syntax debugging without a report.
- No evidence is available and the user has not provided a report goal.
- The user asks to execute code.
- The user asks for polished publication-ready conclusions that evidence does not support.

## Inputs

**Supported inputs may include:**

- User report goal.
- Target audience.
- GAUSS code.
- Execution result object.
- Captured stdout/stderr.
- `output_files` metadata.
- User-provided result tables.
- User-provided charts/images.
- User-provided output files, if explicitly read.
- Dataset description.
- Econometric context.
- Assumptions and limitations.
- Expert-routed interpretation.
- User preferences about length, tone, or format.

**The workflow must distinguish between evidence that was provided or read and evidence that is missing, inferred, or assumed.**

## Evidence Hierarchy

1. User-provided source documents, tables, code, output, or files that have been explicitly read.
2. Structured execution result fields from `gauss_code_execution`.
3. Captured stdout/stderr included in the execution result.
4. Output file metadata, but not file contents.
5. Expert interpretation based on available evidence.
6. General domain knowledge.
7. Assumptions clearly labeled as assumptions.

**Rules:**

- Lower tiers must not be treated as higher tiers.
- Output file metadata is not file content.
- Completed execution is not methodology validation.
- Fake-runner or synthetic output is not real GAUSS execution evidence.
- Missing tables, plots, coefficients, diagnostics, or data descriptions must not be fabricated.
- Assumptions must be labeled.
- Limitations must be included when evidence is incomplete.

## Report Type Selection

### Technical Analysis Summary

**Use for:** summarizing what was run or reviewed, explaining code and captured output, listing warnings/limitations/next steps, summarizing reproducibility context.

**Primary experts:** GAUSS Language Expert, Documentation Expert, Econometrics Expert as needed.

### Econometric Interpretation Note

**Use for:** coefficient interpretation, assumptions, diagnostics, model limitations, forecast/model evaluation, whether conclusions are warranted.

**Primary experts:** Econometrics Expert, Documentation Expert.

### Debugging Report

**Use for:** failed execution, stderr/errors, syntax/runtime issues, package/environment issues, path/working-directory problems, timeout causes, safe retry plan.

**Primary experts:** GAUSS Language Expert, Software Engineering Expert, Documentation Expert.

### Teaching Explanation

**Use for:** beginner-friendly explanation of output, conceptual interpretation, step-by-step learning summary, misconception warnings.

**Primary experts:** Education Expert, Econometrics Expert or GAUSS Language Expert as needed, Documentation Expert.

### Product/User Workflow Summary

**Use for:** user workflow impact, time-to-value, prioritizing what to do next, what should be automated later, product/user-value implications.

**Primary experts:** Product Expert, Documentation Expert, Software Engineering Expert as needed.

**The report type should determine structure, expert routing, and level of detail.**

## Default Report Structure

1. Title.
2. Purpose / user question.
3. Evidence used.
4. Execution status, if available.
5. Key findings.
6. Interpretation.
7. Limitations.
8. Recommended next steps.
9. Appendix / technical details, if useful.

**Optional sections:**

- Model specification.
- Data notes.
- Diagnostics.
- Warnings/errors.
- Reproducibility notes.
- Output files listed but not read.
- Questions to resolve.

**The report should be structured but should not become more definitive than the evidence allows.**

## Expert Routing Rules

### GAUSS Language Expert

Use for: code behavior, syntax/runtime interpretation, GAUSS command usage, implementation details, package/base distinction, debugging sections.

### Econometrics Expert

Use for: model interpretation, assumptions, diagnostics, coefficient meaning, forecast/evaluation claims, causal/statistical limitations.

### Software Engineering Expert

Use for: maintainability, performance, timeout/root-cause analysis, reproducibility, safe rerun plan.

### Documentation Expert

Use for: report structure, clarity, audience framing, caveats, reference-style explanation, final organization.

### Education Expert

Use for: learner-friendly explanation, scaffolding, conceptual sequencing, misconception handling.

### Product Expert

Use for: workflow impact, prioritization, value to user, what should be automated next.

**Documentation Expert may shape the final report structure, but technical/statistical/product claims must route through the relevant expert dimension.**

## Handling Execution Results

Require use of `workflows/execution-aware-analysis.md`.

**Rules:**

- Summarize execution status first.
- State what was captured.
- State what execution does and does not prove.
- Route interpretation through experts.
- Include warnings/errors.
- Include timeout/failure/blocking context.
- Preserve Advisory Mode when execution did not occur.
- Never claim execution occurred unless `executed: true`.
- Never claim blocked/skipped/error/unknown results produced output.
- Never treat `completed` or `exit_code: 0` as proof of methodology validity.

## Handling stdout and stderr

- Summarize important stdout/stderr.
- Quote only short relevant snippets.
- Avoid overquoting long output.
- Surface stderr warnings even with `exit_code 0`.
- Mention truncation.
- Do not invent omitted output.
- Separate captured output from interpretation.

## Handling Output Files

- `output_files` metadata means files were listed, not read.
- Do not describe CSV, dataset, plot, image, or table contents unless files are explicitly read or the user provides contents.
- `created_by_execution: "unknown"` should be reported as unknown if relevant.
- Avoid exposing unnecessary sensitive local paths.
- Include an "Output files listed but not reviewed" section when appropriate.
- Recommend the user provide files or use an explicit file-reading workflow if content interpretation is needed.

## Handling Missing or Partial Evidence

Define safe behavior for:

- Missing execution result.
- Partial stdout/stderr.
- Output file metadata without contents.
- User-provided coefficients without code.
- Code without results.
- Results without dataset context.
- Model output without diagnostics.
- Unclear user goal.

**Rules:**

- State what is missing.
- State what can still be summarized.
- Avoid invented details.
- Ask one focused clarification only if needed.
- Otherwise provide a scoped report with assumptions and limitations.

## Handling Real Invocation Limitation

- `v0.25.0` found the naive `[executable_path, script_path]` command entered the interactive GAUSS 26 prompt and timed out.
- `v0.27.0` report generation must not imply real GAUSS execution is production-ready.
- Fake-runner or synthetic execution results must be labeled as such.
- The report should include an execution limitation note when real invocation reliability matters.
- Do not hide this limitation in a technical appendix only if it affects user trust.

## Report Quality Rules

**Reports should be:**

- Structured.
- Concise enough to be usable.
- Explicit about evidence.
- Explicit about limitations.
- Clear about next steps.
- Appropriate to user audience.
- Free of fabricated results.
- Careful with statistical claims.
- Careful with causal claims.
- Clear when outputs were not read.
- Clear when execution was not performed.

**Reports should not:**

- Launder unsupported analysis into polished prose.
- Convert weak evidence into strong conclusions.
- Omit material warnings/errors.
- Imply production readiness where it is unconfirmed.
- Describe output files as reviewed when only metadata is available.

## Response Pattern

1. Identify report type and audience.
2. Inventory evidence.
3. Apply execution-aware analysis if execution result exists.
4. Route technical/statistical/product claims through experts.
5. Draft report with limitations.
6. Add safe next steps.
7. Avoid unsupported claims.

## Example Report Skeletons

### Technical Analysis Summary Skeleton

- Purpose
- Evidence used
- What ran / what was reviewed
- Key output
- Limitations
- Next steps

### Econometric Interpretation Note Skeleton

- Model/question
- Evidence used
- Results summary
- Interpretation
- Assumptions and diagnostics
- Limitations
- Recommended next checks

### Debugging Report Skeleton

- Execution status
- Error/warning evidence
- Likely issue categories
- What was not proven
- Safe retry plan

### Teaching Explanation Skeleton

- Plain-language summary
- Key concepts
- What the output shows
- What it does not prove
- Practice/next learning step

### Product/User Workflow Summary Skeleton

- User goal
- Current workflow evidence
- Friction or blocker
- Impact
- Recommended next step
- Automation opportunity

## Evaluation Strategy

Document future `30.x` benchmark topics:

1. Generate report from completed execution output without overclaiming.
2. Generate report from failed execution as debugging report.
3. Generate report from timed-out execution with partial output.
4. Generate report when `output_files` metadata exists but contents are unread.
5. Generate econometric interpretation note from coefficients with missing diagnostics.
6. Generate beginner-friendly teaching explanation from execution output.
7. Generate product/user workflow summary from execution result.
8. Refuse or caveat unsupported final conclusions when evidence is insufficient.

**Do not add benchmark prompts in this task.**

## Related Files

- `planning/v0.27.0-report-generation-workflow.md`
- `workflows/execution-aware-analysis.md`
- `workflows/code-assistant-response.md`
- `workflows/expert-routing.md`
- `workflows/expert-routing-cheatsheet.md`
- `experts/EXPERT_REGISTRY.md`
- `experts/EXPERT_BOUNDARY_MATRIX.md`
- `tools/gauss_code_execution.md`
- `schemas/gauss_code_execution.schema.json`
- `scripts/gauss_code_execution.py`

## Maintenance Notes

- Update this workflow if the execution-aware workflow changes.
- Update this workflow if report-generation benchmarks reveal gaps.
- Keep the evidence hierarchy aligned with execution-aware analysis.
- Keep expert routing aligned with `EXPERT_BOUNDARY_MATRIX.md`.
- Do not add automatic execution or output-file reading here.
- Keep report export/file creation separate unless explicitly scoped later.
