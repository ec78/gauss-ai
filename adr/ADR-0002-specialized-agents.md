# ADR-0002: Specialized Agents

## Status

Accepted

## Context

A single broad assistant is difficult to evaluate, constrain, and improve reliably for GAUSS-specific tasks.

## Decision

The framework will use specialized agents with explicit purposes, capabilities, limitations, inputs, outputs, and evaluation expectations.

## Consequences

- Every agent should follow `AGENT_SPEC.md`.
- Agents should be scoped by task area or workflow.
- Shared components should be reused rather than duplicated across agents.

