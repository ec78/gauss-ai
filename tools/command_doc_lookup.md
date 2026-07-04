# Command Documentation Lookup Tool Design

## Purpose

Define a lightweight tool design for locating and extracting official GAUSS command-specific documentation from local documentation sources.

This design supports retrieval prototypes only. Official GAUSS documentation remains the source of truth, and this repository should not become a mirror of full command pages.

First prototype:
The initial local script exists at `scripts/command_doc_lookup.py`.

Future command lookup outputs should align with `schemas/command_lookup_evidence.schema.json`. The current script and existing retrieval examples predate that formal schema and are not required to emit schema-aligned evidence yet.

## Inputs

- `command_name`: GAUSS command or procedure name to look up.
- `docs_root`: local root directory for official GAUSS documentation.
- `category_hint`: optional category name or category file hint from command discovery.
- `max_results`: optional maximum number of candidate matches to return.
- `keywords`: optional terms to search within the best-matched command documentation page.

## Outputs

- Command name.
- Matched docs file path.
- Source type, such as official local `.rst` docs or curated note.
- Verified syntax if found.
- Documented inputs if found.
- Documented outputs if found.
- Examples if found.
- Keyword-focused snippets if requested.
- Control, formula, return, related-link, and raw-heading evidence if found.
- Unresolved questions.
- Confidence level.

The evidence schema design in `tools/evidence_schema.md` defines the target structure for future command lookup evidence objects, including retrieval status, source authority, ambiguity, conflicts, stale evidence, unresolved questions, and extraction warnings.

## Expected Local Docs Source

The expected source is a local checkout or installation of official GAUSS documentation containing command-specific `.rst` files. The tool may use command category files for discovery, but category files do not verify exact command syntax or behavior.

## Search Strategy

1. Normalize the requested command name for matching while preserving the original spelling.
2. Search for exact file-name matches such as `<command_name>.rst`.
3. Search command reference directories for headings or anchors matching the command name.
4. Use `category_hint` only to narrow candidate locations, not to infer syntax.
5. If multiple plausible matches exist, return ambiguity rather than selecting silently.

## Extraction Targets

- Command title or heading.
- Syntax or format blocks.
- Inputs, arguments, or parameters.
- Return values, output structures, or output fields.
- Defaults, options, control structures, and version notes.
- Formula, intercept, constant, missing-value, dataset, and DataFrame behavior when present.
- Related commands or cross references.
- Short examples or references to examples.
- Source path and any available version marker.
- Keyword snippets around requested terms.

Keyword snippets are evidence only. They should not be treated as interpreted behavior unless the response explicitly explains what the official text verifies.

## Failure Behavior

- If no docs file is found, report retrieval failure.
- If multiple docs files match, report ambiguity and include candidates.
- If syntax is absent from the matched page, report that syntax was not found.
- If inputs, outputs, defaults, or examples are absent, list them as unresolved.
- If requested keyword hits are absent, report that no hits were found.
- Never fill missing fields from memory or category membership.

## Safety Rules

- Do not infer syntax from category membership.
- Do not invent missing arguments or return fields.
- If multiple docs matches exist, report ambiguity.
- If docs are not found, say retrieval failed.
- Preserve source identity and matched file path.
- Keep extracted snippets short and source-aware.
- Treat curated notes as convenience references, not authoritative replacements.

## Example Lookup Flow

1. Input: `command_name = "olsmt"`, `docs_root = <local official docs root>`.
2. Search for a command-specific `olsmt.rst` file.
3. If found, extract documented formats, inputs, outputs, examples, and unresolved details.
4. Return the source path, verified fields, confidence level, and any missing extraction targets.
5. If not found, report that command-specific retrieval failed and avoid exact syntax claims.
