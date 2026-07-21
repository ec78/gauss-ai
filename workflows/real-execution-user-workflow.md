# Real Execution User Workflow

## Purpose

This workflow governs user-facing real execution scenarios for GAUSS code.

It defines:

- when execution may be offered
- when the assistant must remain in Advisory Mode
- what explicit consent is required
- what must be checked before execution
- how execution should be reported
- how output files should be handled
- how failures, timeouts, blocked runs, and reruns should be handled
- how execution-aware analysis and report generation connect to real execution

This workflow does not itself run GAUSS code or add automatic runtime orchestration.

## Scope

**In scope:**

- user requests to run, test, execute, or smoke-test GAUSS code
- execution eligibility decisions
- consent prompts
- pre-execution safety review
- working-directory and file-handling rules
- post-execution response patterns
- `output_files` metadata handling
- failure/timeout/blocking response patterns
- rerun/repair policy
- trust-boundary language

**Out of scope:**

- automatic execution
- runtime orchestration
- package installation
- license activation
- network access
- global GAUSS configuration changes
- execution of unclear/destructive code
- production-ready execution claims
- cross-platform/cross-version certification
- methodology validation
- automatic file reading
- report export

## Starting Assumptions

- Real GAUSS execution has been verified only on the observed Windows GAUSS 26.1.1 environment.
- The verified invocation form is `tgauss.exe -b <script_path>`.
- The GUI executable `gauss.exe` is blocked by default.
- `exit_code` is unreliable — GAUSS has returned `exit_code: 0` for both successful execution and every observed failure type.
- GAUSS error-output detection is heuristic (`_detect_gauss_error`), not exhaustive.
- `output_files` metadata is not content — files are listed, not read.
- Generated helper scripts (from inline `code`) should be excluded from `output_files`.
- Execution does not prove methodology validity.
- `workflows/execution-aware-analysis.md` and `workflows/report-generation.md` already exist and govern interpretation once an execution result is present.

## Workflow Principles

1. Advisory-first, execution-second.
2. Explicit consent before execution.
3. No hidden execution.
4. Execute only the confirmed code/context.
5. Keep file writes bounded.
6. Refuse unsafe or unclear execution.
7. Treat execution output as evidence, not truth.
8. Treat `output_files` metadata as metadata, not file content.
9. Preserve limitations in user-facing reports.
10. Reruns require fresh confirmation when code/context changes.

## Execution Eligibility Decision

**Execution may be eligible only when all are true:**

- user explicitly asks to run/test/execute/smoke-test
- code is provided or can be safely generated and shown
- task purpose is clear
- working directory is known and safe
- executable/environment is known and uses the terminal GAUSS executable
- code does not require package installation
- code does not require license activation
- code does not require network access
- code does not mutate global configuration
- code does not delete or overwrite unrelated files
- file writes are confined to the allowed working/output directory
- timeout can be enforced
- user confirms the specific run

**Execution is not eligible when:**

- user only asks for explanation, review, or advice
- code is missing or ambiguous
- data/files are missing
- working directory is unknown or unsafe
- executable is GUI `gauss.exe`
- environment is ambiguous or unverified
- code has unclear side effects
- code writes outside the allowed directory
- code requires package install/license/network/global config
- user asks for production-ready certainty
- execution would imply methodology validation

## Mode Selection

### Advisory Mode

No execution. Used when:

- user asks for explanation/review/debugging guidance
- execution is unsafe or not requested
- consent is missing
- environment is missing/ambiguous
- data/files are missing
- the request is better answered conceptually

### Proposed Execution Mode

Assistant proposes a specific run and asks for confirmation.

Used when:

- execution appears eligible
- enough details are known to present a safe execution plan
- consent has not yet been given

### Assisted Execution Mode

Assistant executes only after explicit confirmation.

Used when:

- eligibility criteria pass
- user confirms the exact code/context
- execution helper is available
- safety review passes

### Post-Execution Analysis Mode

Assistant interprets the execution result using:

- `workflows/execution-aware-analysis.md`
- `workflows/report-generation.md` when the user requests a report, summary, write-up, or structured interpretation

## Consent Model

Consent must be:

- explicit
- specific to the code/context
- given after the assistant shows the execution plan
- renewed when code, directory, files, packages, or write behavior changes

**Consent prompt must include:**

- purpose
- code preview or script path
- working directory
- executable/environment
- timeout
- expected file reads/writes
- output directory, if any
- package requirements
- safety assumptions
- what execution can and cannot prove

Do not run based on implied consent such as "sounds good" unless it clearly refers to the displayed execution plan.

## Execution Request Structure

A structured pre-run checklist the assistant should prepare (workflow-level, not a schema):

- task purpose
- requested mode
- code source: inline code or script path
- code preview
- working directory
- output directory, if any
- executable path or environment result
- required packages
- timeout seconds
- allow file write
- allow output files
- expected outputs
- expected output files
- safety review result
- user confirmation status
- known limitations

## Pre-Execution Safety Review

Checklist:

- code has been shown or summarized clearly
- code purpose is understood
- code does not delete files
- code does not overwrite unrelated files
- code does not install packages
- code does not activate licenses
- code does not access the network
- code does not mutate global configuration
- file writes are relative or inside the allowed directory
- working directory exists and is safe
- output directory, if used, is inside allowed scope
- executable is `tgauss` / `tgauss.exe`
- timeout is set
- user confirmed this exact run

If any item fails:

- do not execute
- explain why
- offer an advisory alternative or a safe modification

## Working Directory and File Rules

- prefer disposable or user-approved working directories
- do not run in broad directories like home, Desktop, Documents root, repo root, or system directories unless the user explicitly approves and understands the risk
- avoid overwriting existing files
- file writes must be relative or within the allowed directory
- `output_files` metadata lists files; it does not read them
- generated helper scripts remain excluded from `output_files`
- output files should not be interpreted unless explicitly read or provided
- explicit `output_directory` behavior remains separately scoped unless verified
- use minimal file permissions and bounded filenames where possible

## Tool Invocation Boundary

This workflow may prepare a call to `gauss_code_execution`, but it does not itself implement runtime orchestration.

**Before tool invocation:**

- eligibility must pass
- safety review must pass
- consent must be explicit

**After tool invocation:**

- apply execution-aware analysis
- preserve result evidence
- do not overstate conclusions
- do not automatically rerun

## Conversational Execution Workflow Integration (v0.37.0)

As of `v0.37.0`, a real, confirmed run described by this workflow is carried out through one dedicated module -- `scripts/gauss_execution_workflow.py` -- rather than through any direct call from a conversational surface. The required dependency direction is:

```text
user-facing execution interaction
-> execution-intent and mode decision (gauss_execution_workflow.classify_interaction_mode)
-> execution-plan builder (gauss_execution_workflow.ExecutionWorkflow.propose_execution)
-> canonical request (scripts/gauss_runtime_orchestration.py)
-> durable orchestration controller (scripts/gauss_runtime_orchestration.py,
   backed by scripts/gauss_orchestration_state_store.py)
-> Helper Adapter (scripts/gauss_execution_adapter.py)
-> GAUSS execution helper (scripts/gauss_code_execution.py)
```

This does not change any rule stated above -- eligibility, the consent model, the pre-execution safety review, and the response patterns (A-J) still govern what may be proposed, shown, and reported. It adds one enforced boundary: **no conversational surface, agent, or workflow document may call `gauss_code_execution`, the Helper Adapter, or the runtime orchestration controller directly.** Every real run this workflow describes must pass through `gauss_execution_workflow.ExecutionWorkflow`'s own sequence -- `propose_execution` (eligibility + safety + exact-plan display), `confirm_execution` (an explicit confirmation event bound to the displayed plan's `request_hash`, independently re-validated), and `execute` (durable authorization, then invocation) -- never a shortcut around any of those steps, and never a fallback to an in-memory-only production path. A rerun always requires a brand-new proposal and a brand-new confirmation; no code path reuses a prior confirmation for a second invocation.

`gauss_execution_workflow.py` never invokes the Helper Adapter or `gauss_code_execution` directly, never performs shell execution, and never infers confirmation from conversational enthusiasm ("sounds good," "try this," "see if this works") -- only a fully validated, request-hash-bound confirmation event authorizes a real run. See `planning/v0.37.0-conversational-execution-workflow-integration.md` for the full interaction contract.

## Response Patterns

### Pattern A — Advisory Instead of Execution

Use when execution is not requested or not eligible.

Should include: answer/review/explanation; a note that no code was run; an optional safe next step.

### Pattern B — Offer Execution

Use when execution appears eligible but consent is missing.

Should include: "I can run this if you want me to"; code/script to run; working directory; expected outputs/files; timeout; safety checks; a confirmation question.

### Pattern C — Request Missing Inputs

Use when execution might be possible but details are missing.

Ask for one focused missing input when possible — for example: working directory, data file, script path, permission to write an output file, or confirmation of package availability.

### Pattern D — Decline Unsafe Execution

Use when code/context is unsafe.

Should include: why unsafe; what would make it safe; an advisory alternative.

### Pattern E — Completed Execution

Should include: execution_status; what ran; stdout summary; stderr summary; `output_files` metadata; limitations; what execution does and does not prove; next step.

### Pattern F — Failed Execution

Should include: execution_status failed; error evidence from stdout/stderr; the likely issue, routed through the GAUSS Language Expert if syntax/runtime; no methodology overclaim; a proposed fix; ask before rerun.

### Pattern G — Timed Out Execution

Should include: timeout status; elapsed time/timeout; partial output if available; cleanup/lingering-process status if known; possible causes; a safer next step.

### Pattern H — Blocked Execution

Should include: why blocked; what would make it eligible; an advisory alternative.

### Pattern I — Output Files Present

Should include: files listed as metadata; a statement that contents were not read unless explicitly read; an offer of a safe file-review path; no inferred contents.

### Pattern J — User Asks Whether Results Are Valid

Should include: execution confirms code ran or failed, not methodology validity; identify missing diagnostics/data/context; route methodological claims through the Econometrics Expert; recommend validation steps.

## Post-Execution Interpretation

After execution, apply:

1. `workflows/execution-aware-analysis.md`
2. `workflows/report-generation.md` if a structured report is requested
3. Expert routing:
   - GAUSS Language Expert for syntax/runtime
   - Econometrics Expert for modeling/statistical validity
   - Software Engineering Expert for maintainability/performance
   - Documentation Expert for clarity
   - Education Expert for teaching explanations
   - Product Expert for workflow/user value

## Evidence and Trust Boundaries

- execution result fields are evidence
- stdout/stderr are captured outputs
- `output_files` metadata is not content
- `exit_code` is unreliable
- completed execution does not prove code correctness
- completed execution does not prove methodology validity
- failed execution does not prove method invalidity
- warnings/errors/truncation must be surfaced
- assumptions must be labeled
- cross-platform/cross-version limitations remain

## Rerun and Repair Policy

- no automatic rerun loop
- the assistant may propose a fix after failure
- the user must approve rerun
- if code changes, show the changed code
- if file writes change, repeat the safety review
- if timeout changes, repeat confirmation
- record what changed between runs
- do not silently broaden scope

## Examples

1. **User asks for review only.** Stay in Advisory Mode — explain/review the code, note that nothing was run.
2. **User asks to run safe code but gives no working directory.** Request the missing input (working directory) before offering a run.
3. **User provides safe code and confirms.** Enter Assisted Execution Mode, run only the confirmed code, report the result via the appropriate Completed/Failed pattern.
4. **User asks to run code that writes outside the allowed directory.** Decline via Pattern D, explain why, propose a safe modification (e.g., a relative path inside the working directory).
5. **Execution succeeds with an output file.** Report `output_files` metadata (Pattern I); do not infer file contents.
6. **Execution fails with a GAUSS error.** Summarize the error evidence (Pattern F); ask for confirmation before any rerun.
7. **User asks if successful execution proves the model is valid.** Explain the evidence/interpretation boundary (Pattern J); route to the Econometrics Expert.

## Maintenance Notes

- Update this workflow when execution helper behavior changes.
- Update when cross-platform/cross-version support changes.
- Update when explicit `output_directory` behavior is verified.
- Update if schemas change.
- Update if runtime orchestration is introduced.
- Keep examples aligned with real observed GAUSS behavior.
- Do not weaken consent or safety rules without explicit milestone scope.
- Update the Conversational Execution Workflow Integration section above if `scripts/gauss_execution_workflow.py`'s own interaction contract changes.

## Related Files

- `planning/v0.30.0-real-execution-user-workflow-design.md`
- `planning/v0.37.0-conversational-execution-workflow-integration.md`
- `workflows/execution-aware-analysis.md`
- `workflows/report-generation.md`
- `workflows/code-assistant-response.md`
- `tools/gauss_code_execution.md`
- `schemas/gauss_code_execution.schema.json`
- `scripts/gauss_code_execution.py`
- `scripts/gauss_execution_workflow.py`
- `scripts/gauss_runtime_orchestration.py`
- `scripts/gauss_orchestration_state_store.py`
- `scripts/gauss_execution_adapter.py`
