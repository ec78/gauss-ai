# Knowledge Registry

## 1. Purpose

This registry catalogs the knowledge sources available to the GAUSS AI framework. It records source authority, priority, version coverage, retrieval expectations, and maintenance notes so agents can ground responses transparently and consistently.

## 2. Registry Fields

- Name: Human-readable source name.
- Category: Source type, such as official documentation, reference repository, examples, blog, project convention, or evaluation record.
- Authority: Relative trust level for factual claims.
- Priority: Retrieval and conflict-resolution priority.
- Supported GAUSS Versions: GAUSS versions covered by the source.
- Coverage: Summary of topics or tasks the source supports.
- Retrieval Mode: How agents should access the source, such as local path, indexed retrieval, manual reference, or configured connector.
- Local Path: Repository or filesystem location for the source.
- Update Frequency: Expected refresh cadence.
- Notes: Additional source-specific guidance or limitations.

## 3. Initial Registered Sources

| Name | Category | Authority | Priority | Supported GAUSS Versions | Coverage | Retrieval Mode | Local Path | Update Frequency | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Official GAUSS Documentation | Official documentation | Highest | 1 | Placeholder: version-specific | GAUSS language, procedures, libraries, product behavior, and official usage guidance | Placeholder: local path or documentation index | `./knowledge/official-gauss-documentation/` | Placeholder: align with GAUSS releases | Highest authority for factual GAUSS behavior. Prefer version-matched documentation. |
| aptech/gauss-llm-reference | Reference repository | High | 2 | Placeholder: repository-defined | GAUSS language and usage reference for LLM grounding | Placeholder: local path or indexed repository | `./knowledge/aptech-gauss-llm-reference/` | Placeholder: review on repository updates | Use as a curated support source after official documentation. |
| ec78/gauss-programming-llm | Reference repository | Medium | 3 | Placeholder: repository-defined | GAUSS programming examples, patterns, and LLM-oriented reference material | Placeholder: local path or indexed repository | `./knowledge/ec78-gauss-programming-llm/` | Placeholder: review on repository updates | Use for examples and programming patterns when source scope is relevant. |
| aptech/gauss_blog | Blog examples | Medium | 4 | Placeholder: article-specific | Applied GAUSS examples, tutorials, workflows, and explanatory material | Placeholder: local path or indexed repository | `./knowledge/aptech-gauss-blog/` | Placeholder: review on content updates | Useful for applied examples; verify factual behavior against official documentation when needed. |

## Adding and Reviewing Knowledge Sources

New knowledge sources should be added intentionally and reviewed before agents rely on them.

For each new source:

1. Add a registry entry with all required fields.
2. Assign an authority level and priority relative to existing sources.
3. Record supported GAUSS versions or state that version coverage is unknown.
4. Describe source coverage and known limitations.
5. Add a placeholder or real local path.
6. Update `configs/knowledge_sources.yaml` when the source is ready for configured retrieval.
7. Add or update evaluations that depend on the new source.
8. Review source quality, version relevance, and conflict-resolution behavior before treating it as authoritative.

