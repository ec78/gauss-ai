# Knowledge Specification

This document defines how knowledge is organized, prioritized, retrieved, validated, and maintained across the GAUSS AI framework. It is implementation-agnostic.

## 1. Purpose

The knowledge specification ensures that agents use reliable, transparent, and version-aware sources when answering GAUSS-focused questions or performing repository tasks.

Its goals are to minimize hallucinations, make source usage inspectable, and keep factual knowledge distinct from expert reasoning.

## 2. Knowledge Categories

Knowledge should be organized by source type and intended use.

- Official documentation: Authoritative GAUSS language, library, product, and platform references.
- Source code: Repository code, package code, examples, tests, and scripts.
- Project conventions: Local standards, style guides, workflows, and review expectations.
- Examples: Curated sample programs, usage patterns, tutorials, and reference tasks.
- Evaluation records: Benchmark prompts, scoring notes, regressions, and known failure cases.
- Expert reasoning: Domain-specific reasoning, best practices, and common mistakes maintained separately under `experts/`.

Factual knowledge should describe what is true according to a source. Expert reasoning should describe how to interpret, apply, or critique that knowledge.

## 3. Source Hierarchy

Agents should prioritize sources according to authority and relevance.

1. Official documentation for the relevant GAUSS version or product.
2. Current repository files and configured project sources.
3. Package source code, tests, and examples.
4. Approved project conventions and workflow documentation.
5. Curated examples and tutorials.
6. Evaluation records and known failure patterns.
7. Expert reasoning modules.

Expert modules may guide interpretation, but they should not override authoritative factual sources.

## 4. Source Quality Criteria

Knowledge sources should be evaluated before use.

High-quality sources should be:

- Authoritative for the task domain.
- Version-specific when behavior may differ across releases.
- Traceable to a file, URL, document, or configured source entry.
- Current enough for the task.
- Internally consistent.
- Relevant to the user's question or workflow.
- Clear about scope, assumptions, and limitations.

Low-quality or unclear sources should be treated as supporting context only.

## 5. Version Awareness

Agents should identify the relevant GAUSS version, package version, repository state, or documentation version whenever version differences may affect the answer.

If the version is unknown and materially affects correctness, the agent should ask for clarification, inspect available project context, or state the assumption being used.

Version-aware retrieval should prefer sources that match the user's environment or the repository's configured target version.

## 6. Retrieval Strategy

Retrieval should be purposeful and proportional to the task.

Agents should:

- Retrieve official documentation for source-dependent GAUSS behavior.
- Retrieve local files for repository-specific questions.
- Retrieve examples when syntax, usage patterns, or conventions need grounding.
- Retrieve evaluation records when working on known failure modes.
- Retrieve expert modules when domain reasoning or best-practice interpretation is needed.
- Avoid retrieving broad or unrelated context that may dilute the answer.

Retrieved knowledge should be interpreted in light of the user's task, the relevant agent role, and any applicable expert guidance.

## 7. Conflict Resolution

When sources disagree, agents should resolve conflicts by authority, version match, and recency.

Expected order:

1. Prefer official documentation matching the relevant version.
2. Prefer current repository behavior for project-specific implementation questions.
3. Prefer tests and executable examples over informal descriptions.
4. Prefer explicit project conventions over inferred style.
5. Treat expert reasoning as advisory when factual sources conflict.

If conflict remains unresolved, the agent should state the uncertainty and avoid presenting a single answer as definitive.

## 8. Citation Policy

Agents should make source usage transparent when it improves trust, auditability, or reproducibility.

Citations may include:

- Local file paths.
- Configured knowledge source identifiers.
- Documentation titles or sections.
- Version identifiers.
- Evaluation or benchmark references.

Agents should cite sources for factual claims that are non-obvious, version-sensitive, disputed, or central to the user's decision. They should distinguish direct source facts from expert interpretation.

## 9. Knowledge Refresh Process

Knowledge should be refreshed when sources change, new task areas are added, or evaluations reveal gaps.

Refresh steps:

1. Identify outdated, missing, conflicting, or low-quality knowledge.
2. Add or update the relevant configured source.
3. Record source purpose, scope, and version when available.
4. Update expert modules only when interpretation or best-practice guidance changes.
5. Add or update evaluations that cover the knowledge gap.
6. Re-run relevant evaluations to confirm improvement.

## 10. Success Criteria

Knowledge handling is successful when agents:

- Prefer official documentation as the highest factual authority.
- Retrieve version-appropriate sources.
- Make source usage transparent when needed.
- Separate factual knowledge from expert reasoning.
- Avoid unsupported claims and hallucinated GAUSS behavior.
- Resolve conflicts conservatively.
- Improve knowledge coverage in response to repeated failures.

## 11. Future Considerations

- Add metadata schemas for source version, authority, scope, and refresh date.
- Add automated checks for missing or stale knowledge sources.
- Track which sources support each benchmark result.
- Add retrieval audits for high-risk or frequently failed tasks.
- Define source-specific citation formats.
- Add workflows for periodic documentation and package source refresh.

