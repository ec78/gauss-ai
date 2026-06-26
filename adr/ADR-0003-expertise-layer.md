# ADR-0003: Expertise Layer

## Status

Accepted

## Context

Multiple agents need access to the same domain reasoning, best practices, and common mistake patterns.

## Decision

The framework will include a first-class `experts/` layer for reusable expert modules. Expert modules will sit between agents and shared knowledge, helping agents interpret and apply domain guidance without replacing factual sources.

## Consequences

- Every expert module should follow `EXPERT_SPEC.md`.
- Expert modules should separate reasoning guidance from factual knowledge.
- Agents may consult one or more experts depending on task requirements.

