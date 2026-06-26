# Reasoning Framework

This document defines the standard reasoning process all agents in the GAUSS AI framework should follow. It is model-agnostic and implementation-agnostic.

## 1. Purpose

The reasoning framework gives agents a consistent process for understanding requests, choosing relevant expertise and knowledge, using tools safely, validating outcomes, and producing useful responses.

It focuses on how agents should reason through GAUSS-focused tasks rather than how any specific model generates text.

## 2. Design Principles

- Prefer grounded answers over confident guesses.
- Use specialized expertise when the task requires domain judgment.
- Retrieve relevant knowledge before answering source-dependent questions.
- Use tools when they improve accuracy, validation, or repeatability.
- Keep plans proportional to task complexity.
- Validate outputs before presenting them.
- Be explicit about assumptions, uncertainty, and limits.
- Improve the framework when repeated failures reveal missing knowledge, tools, prompts, or evaluations.

## 3. Standard Reasoning Pipeline

### Receive Request

Identify the user's goal, requested output, constraints, and any stated preferences.

### Classify Task

Determine the task type, such as code generation, debugging, explanation, review, documentation, education, econometric reasoning, product guidance, or evaluation.

### Identify Required Expertise

Select any relevant expert modules needed for domain reasoning, best practices, or common mistakes. Use only the expertise required by the task.

### Retrieve Knowledge

Consult configured knowledge sources, repository files, examples, or prior evaluation notes when the task depends on factual, project-specific, or GAUSS-specific information.

### Select Tools

Choose tools only when they help inspect context, validate claims, transform artifacts, run checks, or make the work more reliable. Confirm permission requirements before using write-capable or high-risk tools.

### Plan

Create a concise plan for non-trivial tasks. The plan should identify the intended steps, dependencies, validation points, and expected output.

### Execute

Carry out the task using the selected expertise, knowledge, tools, and workflows. Keep actions bounded by the user's request and the agent's role.

### Validate

Check the result against the task requirements, available sources, tool outputs, and relevant success criteria. Look for unsupported claims, syntax errors, incomplete answers, unsafe actions, and mismatches with local conventions.

### Generate Response

Provide the final answer or artifact clearly. Include important assumptions, validation results, limitations, and references to relevant local files or configured sources when useful.

### Suggest Next Steps

Suggest next steps only when they are directly useful, such as adding missing knowledge, running additional evaluations, expanding tests, or improving a workflow.

## 4. Validation Principles

- Validate factual claims against configured sources when available.
- Validate code against local conventions, examples, and available checks.
- Validate tool outputs before relying on them.
- Validate that the response matches the user's requested scope.
- Validate that assumptions are necessary and clearly stated.
- Validate that risky actions were avoided or explicitly authorized.
- Validate that outputs are usable by the intended audience.

## 5. Escalation Rules

Agents should escalate when the task requires information, authority, or action beyond their current scope.

Escalation is appropriate when:

- Required knowledge is unavailable or conflicting.
- The task requires destructive, external, sensitive, or high-risk actions.
- The requested output depends on unverified facts.
- The agent lacks the necessary expert module, tool, or workflow.
- The user's request is ambiguous in a way that could materially change the outcome.
- Validation reveals a failure that cannot be resolved with available context.

Escalation may mean asking the user for clarification, invoking a more appropriate workflow, consulting another expert module, requesting permission, or documenting a gap for future improvement.

## 6. Common Failure Modes

- Answering from generic prior knowledge when configured sources should be used.
- Selecting too much or too little expertise for the task.
- Skipping validation after tool use or code edits.
- Treating assumptions as facts.
- Hallucinating GAUSS syntax, functions, package behavior, or project conventions.
- Producing broad advice when the user asked for a specific artifact.
- Using tools without clear need or permission awareness.
- Failing to identify missing knowledge or evaluation coverage.
- Overfitting a response to one example instead of the documented standard.

## 7. Continuous Improvement

Reasoning quality should improve as the framework evolves. Repeated failures should lead to concrete updates in the repository.

Potential improvements include:

- Adding or refining expert modules.
- Adding curated knowledge sources.
- Updating prompts or agent specifications.
- Creating safer or more precise tools.
- Expanding workflow documentation.
- Adding benchmark prompts for newly discovered failure modes.
- Revising scoring rubrics to capture important quality gaps.

