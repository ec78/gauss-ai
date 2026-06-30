# Knowledge Search Tool

## 1. Purpose

This document defines the specification for a future `knowledge_search` tool used by GAUSS AI agents to retrieve relevant, source-grounded GAUSS knowledge.

## 2. Tool Role

`knowledge_search` should help agents locate authoritative snippets, examples, package behavior, and expert guidance before writing, reviewing, explaining, or debugging GAUSS code. It is a retrieval aid, not a source of independent claims.

## 3. Inputs

- `query`: The search text or question to retrieve relevant knowledge for.
- `source_ids`: Optional list of source identifiers to restrict retrieval.
- `task_mode`: Optional task context, such as code generation, debugging, explanation, translation, review, documentation, testing, or design guidance.
- `max_results`: Optional limit on the number of returned matches.
- `require_official_source`: Optional flag requiring official or highest-authority sources when available.

## 4. Outputs

- Matched source.
- Title or file path.
- Snippet.
- Relevance score.
- Source authority.
- Version information if available.

## 5. Source Resolution

- Uses `configs/knowledge_sources.yaml` as the committed source registry.
- Applies local overrides from `configs/knowledge_sources.local.yaml`.
- Prefers enabled local paths.
- Falls back to canonical URLs when supported.

## 6. Retrieval Policy

- Official docs first for syntax, arguments, return values, and version behavior.
- LLM reference for AI failure modes.
- Blog examples for applied workflows.
- Package source for package-specific behavior.
- Expert modules for reasoning and best practices.

## 7. Safety and Accuracy Rules

- Do not invent sources.
- Do not treat unverified function names as confirmed.
- Preserve source identity.
- Prefer local indexed sources when available.

## 8. Failure Modes

- Requested sources are unavailable or disabled.
- Local paths are configured but missing or unreadable.
- Canonical URLs are unavailable or unsupported by the current environment.
- Search results are relevant but not authoritative enough for the requested task.
- Version information is missing, ambiguous, or inconsistent across sources.
- The query matches examples but not official syntax or API references.

## 9. Future Implementation Notes

Future implementations may index local files, resolve configured source priorities, validate local override files, fetch canonical URLs, filter by task mode, and rank results by source authority. Until implemented, this specification defines intended behavior only and should not be treated as executable tooling.
