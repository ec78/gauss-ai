# ADR-0004: Reasoning Framework

## Status

Accepted

## Context

Agents need a consistent process for classifying tasks, selecting expertise, retrieving knowledge, choosing tools, planning, executing, validating, and responding.

## Decision

The framework will define a shared reasoning process in `REASONING_FRAMEWORK.md`. This process will be model-agnostic and implementation-agnostic.

## Consequences

- Agents should reason through tasks using a common pipeline.
- Validation and escalation should be treated as core agent responsibilities.
- Repeated reasoning failures should lead to updates in prompts, knowledge, expert modules, tools, workflows, or evaluations.

