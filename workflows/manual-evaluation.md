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

Keep this workflow aligned with the benchmark suite, scoring rubric, agent specification, and knowledge retrieval policy.
