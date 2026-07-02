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

To retrieve keyword-focused evidence from the matched command page:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs" --keywords intercept formula missing ctl olsmtControl output returns
```

Keyword snippets are evidence from the matched documentation page. They are not interpretation, and the script should not infer behavior that is not present in the snippets.

Quote multi-word keyword phrases (for example `"not found"`) so the shell passes them as a single keyword. An unquoted multi-word phrase is split into separate single-word keywords, which can produce misleading individual-word hits instead of a real phrase match.

## Output Fields

- `command_name`: command requested by the user.
- `docs_root`: local documentation root searched.
- `status`: `found`, `ambiguous`, `not_found`, or `error`.
- `confidence`: confidence score for the best match.
- `matches`: candidate documentation matches.
- `best_match`: highest-confidence match when available.
- `unresolved_questions`: details that were not found or could not be resolved.
- `keyword_hits`: snippets around requested keyword matches.

Each match may include:

- `file_path`
- `source_type`
- `match_reason`
- `heading`
- `syntax_blocks`
- `inputs_section`
- `outputs_section`
- `returns_section`
- `controls_section`
- `formula_section`
- `examples`
- `notes`
- `related_links`
- `raw_section_headings`
- `keyword_hits`
- `extraction_warnings`
- `confidence`

## Limitations

- This is a lightweight prototype, not a full documentation search system.
- It searches local `.rst` files only.
- It does not execute GAUSS code.
- It does not infer syntax, arguments, defaults, return fields, or examples from category membership.
- It may miss information if the official docs use unexpected section names or formatting.

Official GAUSS documentation remains authoritative. Extracted snippets should be treated as retrieval evidence, not as a replacement for the official command page.
