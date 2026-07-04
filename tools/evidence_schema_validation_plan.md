# Evidence Schema Validation Plan

## Purpose

Plan a lightweight validator for command lookup evidence objects. This is an implementation plan only; the validator is not created in this task.

## Proposed Script

`scripts/validate_lookup_evidence.py`

## Inputs

- Path to a lookup JSON file.
- Path to a JSON Schema file, typically `schemas/command_lookup_evidence.schema.json`.

## Outputs

- Pass/fail result.
- JSON Schema validation errors.
- Warnings for risky evidence states.
- Optional summary of retrieval status, source authority, and unresolved questions.

## Suggested Checks

- JSON Schema validation.
- `retrieval_status` enum validity.
- Required fields are present.
- `confidence` is numeric between 0 and 1.
- No unredacted local absolute docs path appears in committed artifacts.
- No verified facts appear without source provenance.
- `extraction_warnings` are surfaced when present.
- `ambiguity` is present and populated when `retrieval_status` is `ambiguous`.
- `conflicts` is present and populated when `retrieval_status` is `conflict`.
- `stale_evidence` is present when `retrieval_status` is `stale`.
- `error_code` or `error_message` is present when `retrieval_status` is `error`.

## Risk Warnings

The validator should warn, not necessarily fail, when:

- `retrieval_status` is `found_incomplete`.
- `unresolved_questions` is non-empty.
- `extraction_warnings` is non-empty.
- `source_authority` is lower than official documentation.
- `source_authority` is `category_list` but verified syntax or output fields are populated.
- `docs_root_redacted` is absent or false in a committed artifact.

## Testing Strategy

Start with small fixtures rather than rewriting existing prototype lookup JSON:

- A minimal `found_complete` fixture.
- A `found_incomplete` fixture with warnings.
- A `not_found` fixture.
- An `ambiguous` fixture with two candidates.
- A `conflict` fixture with official and curated values.
- A `stale` fixture.
- An `error` fixture.

Each fixture should have one expected pass/fail result and expected warnings.

## Open Questions

- Which JSON Schema validator dependency should be used, if any, or should validation rely only on the Python standard library plus custom checks?
- Should validation failures block commits, or remain an advisory tool during the prototype stage?
- Should existing `examples/retrieval/*.lookup.json` files be mapped into schema-aligned fixtures before the script is built?
- How should the validator distinguish documentation snippets from copied full documentation pages?
- Should docs-root redaction be enforced for all local runs or only committed artifacts?
- How should `tool_version` be derived: package version, script hash, git commit, or manual string?
