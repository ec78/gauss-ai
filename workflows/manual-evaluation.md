# Manual Evaluation

## 1. Purpose

This workflow documents how to manually evaluate the GAUSS Code Assistant using benchmark prompts and the scoring rubric. It is intended to make evaluation repeatable, practical, and useful for improving the agent.

## 2. When to Run a Manual Evaluation

Run a manual evaluation:

- After prompt changes.
- After expert module changes.
- After knowledge source updates.
- Before tagging a release.
- After discovering a recurring failure mode.

## 3. Required Inputs

- `prompts/system_prompt.md`
- `prompts/code_assistant_system.md`
- `agents/code-assistant/AGENT.md`
- `agents/code-assistant/task_modes.md`
- `experts/gauss-language/BODY_OF_KNOWLEDGE.md`
- `evaluations/benchmark-prompts.md`
- `evaluations/scoring.md`

## 4. Evaluation Steps

1. Choose a benchmark prompt from `evaluations/benchmark-prompts.md`.
2. Run the prompt against the current Code Assistant setup.
3. Save or copy the response.
4. Score the response using `evaluations/scoring.md`.
5. Record blocking issues.
6. Identify the most likely improvement target.

## 5. Scoring Guidance

- Use the 0-4 scale from `evaluations/scoring.md`.
- Apply automatic failure rules before averaging scores.
- Score only applicable dimensions.
- Document uncertainty instead of forcing a false precision.
- Note whether the failure belongs in prompt instructions, expert knowledge, knowledge retrieval, tool behavior, or benchmark design.

## Benchmark Traceability

Every manual evaluation run should reference:

- Stable Prompt ID from `evaluations/benchmark-prompts.md`.
- Prompt category.
- Benchmark name.
- Agent version or repository state.
- Evaluation run filename.
- Any follow-up action created from the run.

When benchmark expectations are changed because of an evaluation finding, the evaluator should:

1. Update the benchmark prompt.
2. Update expert guidance if the issue reflects reusable GAUSS knowledge.
3. Update the system prompt only if the behavior should affect runtime behavior broadly.
4. Note the change in the evaluation run file or runs index.

## 6. Result Recording Template

## Evaluation Result

Date:
Evaluator:
Agent Version:
Prompt ID:
Prompt Category:
Prompt Text:

Response Summary:

Scores:
- GAUSS Syntax Correctness:
- Function and Package Validity:
- Data Structure Reasoning:
- Dimension and Numerical Awareness:
- Task Mode Fit:
- Explanation Quality:
- Assumptions and Dependencies:
- Maintainability and Best Practices:
- Testing or Validation:
- Hallucination and Cross-Language Contamination Avoidance:

Overall Score:
Decision: Pass / Needs Revision / Fail

Blocking Issues:
Suggested Improvements:
Follow-up Actions:

## 7. Pass/Fail Guidance

- Pass: The response is correct, GAUSS-specific, useful, and free of blocking issues.
- Needs Revision: The response is partly useful but has fixable gaps, weak assumptions, missing validation, or minor GAUSS-specific issues.
- Fail: The response triggers an automatic failure condition, gives invalid GAUSS code, invents functions or packages, ignores the central task, or would mislead the user.

Automatic failures override the numeric average.

## 8. Maintenance Notes

Use evaluation results to improve the right layer:

- Prompt instructions: The agent ignored style, workflow, task mode, or response-shape requirements.
- Expert knowledge: The agent lacked GAUSS reasoning, data structure knowledge, or best-practice judgment.
- Knowledge retrieval: The agent needed official docs, LLM reference material, package source, or examples but did not retrieve or cite them.
- Tool behavior: A retrieval, validation, execution, or indexing tool produced missing, stale, or misleading results.
- Benchmark design: The prompt or expected behavior was ambiguous, unrealistic, or failed to isolate the intended capability.

## 9. Benchmark Authoring Guidance

This section is for whoever is writing a new benchmark prompt's expected behavior, not for whoever is evaluating an existing one. It exists because `v0.10.0`'s Evidence Coverage and Tracking Guards category (`17.x`) surfaced a real, repeatable way a benchmark's own expected-behavior text can go stale — see "Historical Precedent" below.

### Avoid volatile hardcoded counts

Benchmarks should avoid hardcoding repository counts such as:

- number of prompt IDs
- number of coverage rows
- number of run files
- number of index entries
- number of warnings

unless the benchmark is explicitly and permanently tied to a fixed repository state. Counts like these change every time a later milestone adds prompts, runs, or coverage rows — including, in the `17.x` case, the very act of adding the benchmark's own prompts.

### Prefer live tool output

When a benchmark evaluates a script or guard (for example, `scripts/check_evaluation_tracking.py` or `scripts/validate_all_evidence.py`), expected behavior should usually say:

- run the tool,
- report the live output accurately,
- distinguish errors from warnings,
- explain any discrepancy from earlier documented examples or previously-written counts,

rather than requiring the response to reproduce a specific stale numeric count written into the benchmark at authoring time.

### If exact counts are required

If exact counts are genuinely necessary (for example, to test that a response can read a specific fixture precisely):

- State the repository state and timing the count applies to, so a future reader can tell at a glance whether it's still current.
- Identify whether the count is a baseline, mid-batch, or post-tracking-update figure (see "Batch evaluation states" below).
- Say explicitly whether transient warnings are expected at that point, so an evaluator doesn't mistake an expected transient warning for a defect.
- Update the benchmark if the repository state changes before the benchmark is actually evaluated, rather than leaving stale numbers in place.

### Batch evaluation states

For a batch of related evaluations (several benchmark prompts run and tracked together), explicitly distinguish three states whenever expected behavior depends on tool output:

- **Baseline** — the state before any of the batch's own run files exist.
- **Mid-batch** — the state after some of the batch's run files have been created but tracking (`evaluations/benchmark-coverage.md`, `evaluations/runs/INDEX.md`) has not yet been updated to reference them. This state can introduce its own transient warnings (for example, newly-created but not-yet-indexed run files being flagged as orphaned) that are expected and not a defect.
- **Post-update** — the state after coverage rows and index entries have been updated to reflect the batch's results.

A benchmark whose expected behavior references live tool output should say which of these three states it means, if it isn't simply "whatever is true when this prompt happens to run."

### Historical precedent

`v0.10.0` Prompts `17.5` ("Tracking guard handles historical warnings") and `17.6` ("Tracking guard passes current evaluated categories") both hardcoded specific counts in their expected-behavior text (`evaluations/benchmark-prompts.md`) — `17.6` stated "0 errors / 2 warnings" and specific prompt-ID/coverage-row/run-file/index counts, and `17.5` stated "0 errors and 2 warnings." Both counts were accurate only before the `17.x` category itself existed and was tracked. By the time these two prompts were actually evaluated (`evaluations/runs/2026-07-05-code-assistant-evidence-coverage-tracking-run-001.md` for `17.6`, `-005.md` for `17.5`), adding the six `17.x` prompts had already raised the real warning count — to 8 at the `17.6` evaluation point, and to 12 by the `17.5` evaluation point, once several of the batch's own run files existed but were not yet tracked.

Both evaluations passed at 4.0 anyway, because the generated responses correctly ran the tracking guard for real and reported the true live output — including explaining exactly why it differed from the benchmark's own originally-written figures — rather than reciting the stale numbers as if they were still accurate. **This is the preferred behavior.** Benchmarks, and the evaluators scoring responses against them, should reward accurate live-state reporting over rote reproduction of a benchmark's stale expected numbers.

### Do not weaken expectations

This guidance does not mean benchmark expectations should become vague. Stable facts, exact file paths, expected pass/fail behavior, and required distinctions (for example, errors vs. warnings, or documented historical exceptions vs. new defects) should still be stated explicitly in a benchmark's expected behavior — those don't drift the way a repository-wide count does. The issue this section addresses is narrowly about volatile repository-state counts, not about precision in general.

Keep this workflow aligned with the benchmark suite, scoring rubric, agent specification, and knowledge retrieval policy.
