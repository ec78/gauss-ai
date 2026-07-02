# Command Documentation Lookup Implementation Plan

## Purpose

Plan a future lightweight script that can search local `.rst` documentation for a GAUSS command page and extract limited source-aware command details.

Planning only: this document does not implement the script.

## Proposed Script Name

`scripts/command_doc_lookup.py`

## Expected Inputs

- `--command-name`: required GAUSS command or procedure name.
- `--docs-root`: required local official documentation root.
- `--category-hint`: optional category or relative category file.
- `--max-results`: optional maximum candidate count.
- `--keywords`: optional list of terms to search within the best-matched command page.
- `--format`: optional output format such as text or JSON.

## Expected Outputs

- Command name.
- Matched file path or candidate paths.
- Match confidence.
- Source type.
- Extracted syntax blocks if found.
- Extracted input, output, option, and example sections if found.
- Keyword-focused snippets around requested terms.
- Raw section headings, related links, and extraction warnings.
- Unresolved questions.
- Retrieval failure or ambiguity messages.

## File Discovery Strategy

- Prefer exact file-name matches for `<command-name>.rst`.
- Search likely command-reference and command-category directories under `docs_root`.
- Follow category hints only as a narrowing signal.
- Avoid recursively indexing every file in early prototypes unless needed for a small local test set.

## Matching Strategy

- Match exact command names case-insensitively where filesystem behavior requires it.
- Prefer exact file basename matches over heading matches.
- Treat anchor or heading matches as lower-confidence candidates.
- If multiple candidates remain, return ambiguity.

## Handling `.rst` Headings, Anchors, and Toctrees

- Parse simple `.rst` headings using underline patterns.
- Detect anchors and labels that include the command name.
- Read `toctree` entries as navigation hints only.
- Do not infer command existence from a `toctree` target unless the command-specific page is found.

## Extracting Syntax Blocks and Examples

- Look for sections named with terms such as syntax, format, parameters, inputs, outputs, returns, examples, remarks, notes, controls, formula, and related commands.
- Extract short literal blocks or directive blocks near those sections.
- When keywords are supplied, extract short surrounding snippets without inferring meaning beyond the snippet.
- Preserve source order and section names.
- Keep examples short and avoid copying large documentation sections.

## Avoiding Over-Extraction

- Return concise snippets and section summaries.
- Do not copy complete command pages.
- Include source path and section names so users can inspect official docs directly.
- Prefer unresolved questions over guessed details.

## Testing The Script

- Test successful lookup for a command with a known command-specific `.rst` file.
- Test lookup for `strindx` not-found behavior if official docs are available locally.
- Test lookup for `olsmt` syntax and behavior fields.
- Test a command name that appears only in categories but lacks a command-specific match.
- Test ambiguous matches and verify that the script reports ambiguity.
- Test a missing docs root and verify that retrieval fails clearly.

## Open Questions Before Implementation

- What exact local official docs layout should be supported first?
- Should the script read YAML config directly or accept explicit `docs_root` only?
- How should source version information be detected?
- Should curated notes be searched by this script or by a separate fallback layer?
- What output schema should downstream Code Assistant tooling expect?
