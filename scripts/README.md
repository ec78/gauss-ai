# Scripts

## `command_doc_lookup.py`

Purpose:
Locate and extract limited, source-aware details from official GAUSS command-specific `.rst` documentation stored locally.

Example:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs"
```

For shareable example output, redact the local docs root:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs" --redact-docs-root
```

## Output Fields

- `command_name`: command requested by the user.
- `docs_root`: local documentation root searched.
- `status`: `found`, `ambiguous`, `not_found`, or `error`.
- `confidence`: confidence score for the best match.
- `matches`: candidate documentation matches.
- `best_match`: highest-confidence match when available.
- `unresolved_questions`: details that were not found or could not be resolved.

Each match may include:

- `file_path`
- `source_type`
- `match_reason`
- `heading`
- `syntax_blocks`
- `inputs_section`
- `outputs_section`
- `examples`
- `notes`
- `confidence`

## Limitations

- This is a lightweight prototype, not a full documentation search system.
- It searches local `.rst` files only.
- It does not execute GAUSS code.
- It does not infer syntax, arguments, defaults, return fields, or examples from category membership.
- It may miss information if the official docs use unexpected section names or formatting.

Official GAUSS documentation remains authoritative. Extracted snippets should be treated as retrieval evidence, not as a replacement for the official command page.
