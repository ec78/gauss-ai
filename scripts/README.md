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

## Schema-Aligned Output (`--schema-output`)

By default, the script prints the legacy output shape described below. Pass `--schema-output` to instead emit an evidence object conforming to `schemas/command_lookup_evidence.schema.json`:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "C:/Users/eclow/Documents/GitHub/docs/docs" --keywords intercept formula missing ctl olsmtControl output returns --schema-output --redact-docs-root
```

`--schema-output` only changes the output shape — it does not change what is extracted or searched. It renames and regroups the same fields the legacy output already produces: `status` becomes `retrieval_status` (`found` splits into `found_complete`/`found_incomplete` depending on whether unresolved questions or extraction warnings exist), each match gains `command_name` and `source_authority`, and string sections that were `examples`/`notes` become string arrays (`""`/`null` -> `[]`, a non-empty string -> a one-element array). It also adds `schema_version`, `generated_at`, `tool_name`, `tool_version`, and `docs_root_redacted`.

`--schema-output` does not affect the default output format; omit the flag to get the original shape.

Validate schema-aligned output with:

```text
python scripts/validate_lookup_evidence.py path/to/evidence.json
```

## `validate_all_evidence.py`

Purpose:
Validate every committed schema-aligned evidence example and schema fixture in one pass, instead of running `validate_lookup_evidence.py` against each file individually. It reuses `validate_lookup_evidence.py`'s validation logic directly (imported, not reimplemented), so there is one source of truth for what "valid" means.

By default it checks every `*.json` file under `examples/retrieval/schema-aligned/` and `examples/retrieval/schema-fixtures/`:

```text
python scripts/validate_all_evidence.py
```

Pass specific files or directories to check a subset instead:

```text
python scripts/validate_all_evidence.py examples/retrieval/schema-aligned/olsmt.evidence.json
```

**Expected-valid vs. expected-invalid.** Every file is expected to pass schema validation, except files under `examples/retrieval/schema-fixtures/` whose name starts with `invalid-` (currently `invalid-missing-required-fields.json`), which are expected to *fail* schema validation on purpose. The script checks each file against its expected outcome, not just "did it pass": an expected-valid file that fails, or an expected-invalid file that unexpectedly passes, is reported as unexpected and causes a nonzero exit.

**`--strict`** is passed through to each file's validation, same as `validate_lookup_evidence.py`: it treats warnings as failures for expected-valid files. Two known examples: `olsmt.evidence.json` (two false-positive path warnings) and `glm.evidence.json` (four false-positive path warnings) both cite an official-docs HDF5-URI example (`h5://C:/gauss/examples/testdata.h5/mydata` and `h5://C:/gauss23/examples/testdata.h5/mydata`, respectively), so `--strict` reports both as unexpected failures — the script states this plainly rather than hiding it, since strict mode intentionally has a higher bar than the default.

**`--json`** emits a machine-readable summary (per-file results plus an overall `overall_pass`/`unexpected_count`) instead of the human-readable listing.

Exit code is `0` only when every file's actual outcome matches its expected outcome (under the current strictness setting); otherwise nonzero.

**Strict-mode policy (established `v0.7.0`, extended `v0.10.0`).** The default, non-strict run (`python scripts/validate_all_evidence.py`) is the release-health check and is expected to pass. `--strict` promotes warnings to failures, and the current evidence set is expected to fail under `--strict` on two files: `examples/retrieval/schema-aligned/olsmt.evidence.json` (two reviewed path-warning false positives) and `examples/retrieval/schema-aligned/glm.evidence.json` (four reviewed path-warning false positives) — both from official HDF5-URI documentation examples (`h5://C:/gauss/examples/testdata.h5/mydata` and `h5://C:/gauss23/examples/testdata.h5/mydata`), not leaked local paths. Both strict-mode failures are documented here rather than suppressed or worked around. Improving the validator's path-warning heuristic so these stop triggering is tracked as future work, not a release blocker.

This script does not require GAUSS to be installed and does not access the network. It checks evidence *structure*, not GAUSS semantic correctness — a file passing here is not proof that any GAUSS code was executed or that the command behavior described is current.

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

`--schema-output` is subject to the same limitations: it only changes the output shape, not the underlying extraction quality.
