# Architecture Decision Records

Architecture Decision Records (ADRs) capture significant architectural decisions made in this repository.

An ADR records the context for a decision, the decision itself, its current status, and the consequences or follow-up work. ADRs are intentionally concise so the project can preserve decision history without turning every discussion into long-form documentation.

## Why ADRs Are Used

ADRs help the GAUSS AI framework stay understandable as it evolves. They make it easier to see why the project uses specialized agents, expert modules, structured reasoning, knowledge governance, and evaluation-driven development.

ADRs should be used to:

- Preserve architectural intent.
- Explain tradeoffs behind durable choices.
- Avoid rediscovering the same decisions repeatedly.
- Give future contributors a clear record of accepted direction.

## When to Create a New ADR

Create a new ADR when a decision:

- Changes the repository architecture.
- Establishes or replaces a major framework pattern.
- Introduces a new first-class layer, specification, workflow, or governance model.
- Affects how agents, experts, tools, prompts, knowledge, or evaluations are designed.
- Supersedes an earlier ADR.

Small implementation details, temporary experiments, and routine documentation edits usually do not need ADRs.

## ADR Lifecycle

- `Proposed`: The decision is under consideration and may change.
- `Accepted`: The decision is current architectural guidance.
- `Superseded`: The decision has been replaced by a later ADR.

When an ADR is superseded, keep the original file and link to the newer ADR that replaces it.

