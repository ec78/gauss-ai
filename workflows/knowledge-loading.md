# Knowledge Loading

## 1. Purpose

This workflow documents how the GAUSS AI framework should resolve and use knowledge sources. It defines the intended relationship between committed source metadata, private local paths, canonical URLs, and future retrieval tooling.

## 2. Configuration Files

### `configs/knowledge_sources.yaml`

This is the committed registry of known knowledge sources. It should contain stable source metadata such as `id`, name, purpose, canonical location, priority, and whether the source is enabled.

### `configs/knowledge_sources.local.yaml`

This optional local file is for private machine-specific paths and overrides. It must not be committed. Local overrides should match committed sources by source `id`.

## 3. Resolution Rules

- Use `configs/knowledge_sources.yaml` as the committed registry.
- Use `configs/knowledge_sources.local.yaml` for private local paths.
- Match local overrides by source `id`.
- Prefer enabled local paths for retrieval.
- Fall back to canonical URLs when local paths are unavailable.
- Do not commit machine-specific paths.

YAML placeholders such as `${GAUSS_LLM_REFERENCE_PATH}` are not automatically resolved unless future tooling explicitly implements that behavior.

## 4. Local-First Retrieval Policy

When a source has an enabled local override, retrieval should use the local path first. This supports private documentation mirrors, licensed references, local notes, and offline development. If the local path is missing, disabled, or inaccessible, retrieval may fall back to the canonical URL defined in the committed registry.

## 5. Source Priority

Source priority should guide retrieval order when multiple sources are relevant. Higher-priority sources should be consulted before lower-priority sources, especially for syntax, package behavior, public APIs, and known failure modes.

## 6. Validation Checklist

- The committed registry contains stable source `id` values.
- Local overrides use matching source `id` values.
- Local paths are machine-specific and excluded from version control.
- Enabled local paths exist and are readable before use.
- Canonical URLs are present for sources that can be retrieved remotely.
- Placeholder values are treated as literal strings unless tooling resolves them.

## 7. Future Tooling

Future tooling may validate source files, resolve environment placeholders, check local path availability, rank sources by priority, and choose between local and remote retrieval. Until that tooling exists, this document defines policy only and should not be interpreted as executable behavior.

Command category files from the official GAUSS documentation may be used to build a native command inventory for retrieval. These categories should help identify candidate GAUSS commands, but exact syntax, arguments, return values, and version behavior should still be retrieved from command-specific documentation.
