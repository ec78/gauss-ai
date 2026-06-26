# Agent Specification

This document defines the standard specification every AI agent in this repository should follow. It is implementation-agnostic and should be used as the template for future agent definitions.

## 1. Purpose

Describe why the agent exists, what user need it serves, and which GAUSS-focused domain or workflow it supports.

## 2. Public Interface

### Description

Provide a concise user-facing summary of the agent's role.

### Capabilities

List the tasks the agent is expected to perform reliably.

### Example Tasks

Provide representative prompts or workflows that the agent should handle.

### Limitations

State what the agent should not do, where it must defer, and which assumptions it must avoid.

## 3. Internal Interface

### Experts

List the expert modules the agent may use for domain-specific reasoning, best practices, and common mistakes.

### Knowledge Sources

List the configured knowledge sources the agent should prefer when grounding responses.

### Prompts

List the prompt assets that define or support the agent's behavior.

### Tools

List the tools the agent may use for retrieval, inspection, validation, transformation, or other controlled actions.

### Workflows

List the repeatable workflows the agent participates in or triggers.

### Evaluation Suite

List the benchmark prompts, scoring rubrics, and evaluation suites used to measure agent quality.

## 4. Inputs

Define the inputs the agent expects, such as user requests, repository files, configured knowledge, tool outputs, workflow context, or prior evaluation feedback.

## 5. Outputs

Define the outputs the agent may produce, such as explanations, code changes, review findings, documentation drafts, recommendations, test plans, or evaluation results.

## 6. Success Criteria

Describe what a successful response or action looks like. Criteria should include correctness, GAUSS fluency, grounding in available knowledge, clarity, usefulness, and respect for the agent's stated boundaries.

## 7. Failure Modes

Document known or anticipated ways the agent may fail, such as unsupported claims, hallucinated GAUSS syntax, overbroad assumptions, poor tool use, incomplete grounding, unclear explanations, or unsafe actions.

## 8. Versioning

Track meaningful changes to the agent specification, including updates to capabilities, limitations, expert modules, knowledge sources, prompts, tools, workflows, and evaluations. Version history should make it clear when behavior expectations changed and why.

