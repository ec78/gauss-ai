# Expert Specification

This document defines the standard specification every expert module in this repository should follow. It is implementation-agnostic and should be used as the reusable template for all expert modules.

## 1. Purpose

Describe why the expert module exists, which domain it represents, and how it supports specialized GAUSS-focused agents.

## 2. Expert Role

### Domain

Define the expert's domain of knowledge and reasoning.

### Responsibilities

List the types of guidance the expert should provide, such as domain reasoning, best practices, knowledge interpretation, review criteria, or common failure patterns.

### Boundaries

State what the expert should not cover, when it should defer to another expert, and which assumptions it must avoid.

## 3. Knowledge Profile

### Primary Knowledge Sources

List the preferred sources the expert should rely on first.

### Secondary Knowledge Sources

List supporting sources that may be used when primary sources are incomplete or unavailable.

### Source Priority Rules

Define how the expert should prioritize, compare, and resolve conflicts between sources.

## 4. Reasoning Profile

### How the Expert Approaches Problems

Describe the expert's reasoning style, decision process, and domain-specific checks.

### What Assumptions It May Make

List assumptions that are acceptable within the expert's domain when evidence is sufficient.

### What It Must Verify

List claims, constraints, source facts, or task details that must be checked before the expert's guidance is used.

## 5. Best Practices

Document the domain practices the expert should promote across agents.

## 6. Common Mistakes

Document common errors, misconceptions, hallucination risks, or failure patterns the expert should help agents avoid.

## 7. Agent Usage

### Which Agents May Consult This Expert

List agents or agent categories that may use this expert module.

### When This Expert Should Be Invoked

Define the task types, workflows, or signals that make this expert relevant.

### When This Expert Should Not Be Invoked

Define situations where another expert, workflow, tool, or knowledge source is more appropriate.

## 8. Inputs

Define the inputs the expert expects, such as user task context, agent goals, configured knowledge, repository files, tool results, or evaluation feedback.

## 9. Outputs

Define the outputs the expert may provide, such as reasoning guidance, best-practice checks, source interpretation, risk flags, review criteria, or recommended next steps.

## 10. Success Criteria

Describe what successful expert guidance looks like. Criteria should include domain accuracy, appropriate source grounding, clear boundaries, useful reasoning, and applicability across relevant agents.

## 11. Failure Modes

Document known or anticipated ways the expert may fail, such as overgeneralizing beyond its domain, relying on weak sources, missing required verification, duplicating another expert's role, or introducing unsupported assumptions.

## 12. Versioning

Track meaningful changes to the expert specification, including updates to domain scope, responsibilities, source priorities, reasoning guidance, best practices, common mistakes, agent usage, and evaluation expectations.

