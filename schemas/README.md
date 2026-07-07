# Schemas

## Purpose

This directory contains schema design artifacts for GAUSS AI evidence objects.

Evidence schemas define how retrieval results should be represented before they are used by the GAUSS Code Assistant. The goal is to make command lookup evidence inspectable, comparable, and eventually mechanically validatable.

## Why Evidence Schemas Matter

The Code Assistant should distinguish:

- Verified facts from unresolved questions.
- Official documentation from lower-authority sources.
- Complete extraction from incomplete or truncated extraction.
- Ambiguous matches from a single verified command page.
- Fresh evidence from stale or unverified cached evidence.
- Source conflicts from ordinary retrieval success.

A schema gives those distinctions stable field names instead of relying on prose or one-off JSON shapes.

## Relationship to Retrieval Tools

The initial retrieval prototype is `scripts/command_doc_lookup.py`. Existing lookup examples (`examples/retrieval/olsmt.lookup.json`, `examples/retrieval/strindx.lookup.json`) predate this schema and only partially align with it; they are not required to be rewritten.

`scripts/command_doc_lookup.py` can now emit schema-aligned output directly via `--schema-output`. The default output format is unchanged when the flag is omitted. Schema-aligned examples generated with this flag live under `examples/retrieval/schema-aligned/` and are expected to validate against `command_lookup_evidence.schema.json`.

To generate and validate a schema-aligned example:

```text
python scripts/command_doc_lookup.py olsmt --docs-root "<local docs root>" --schema-output --redact-docs-root > examples/retrieval/schema-aligned/olsmt.evidence.json
python scripts/validate_lookup_evidence.py examples/retrieval/schema-aligned/olsmt.evidence.json
```

## Relationship to Code Assistant Responses

The Code Assistant should consume evidence fields to decide what can be stated as verified, what must be marked unresolved, and when exact GAUSS syntax must not be given.

The schema complements:

- `workflows/retrieval-backed-response-pattern.md`
- `workflows/command-documentation-retrieval.md`
- `workflows/native-command-selection.md`

## Source Authority Rules

Official GAUSS command-specific documentation remains authoritative. Command categories are discovery only. Curated command notes are convenience references and do not override official docs.

If evidence conflicts with official documentation, official documentation wins.

## Current Status

These schemas are design/prototype artifacts. They are not yet production enforcement. A first lightweight validator exists at `scripts/validate_lookup_evidence.py`.

Official GAUSS documentation remains the source of truth for exact syntax, inputs, outputs, defaults, examples, and command behavior.

## Running the Validator

Use the validator to check a lookup/evidence JSON file against the schema:

```text
python scripts/validate_lookup_evidence.py examples/retrieval/schema-fixtures/minimal-found-complete.json
```

Use `--json` for machine-readable output:

```text
python scripts/validate_lookup_evidence.py examples/retrieval/schema-fixtures/minimal-found-complete.json --json
```

Use `--strict` to treat warnings as failures:

```text
python scripts/validate_lookup_evidence.py examples/retrieval/schema-fixtures/minimal-found-complete.json --strict
```

The validator requires the Python `jsonschema` package. If it is not installed, the script fails clearly with an installation hint rather than silently skipping schema validation.

`examples/retrieval/schema-fixtures/invalid-missing-required-fields.json` is a companion fixture that intentionally omits required fields (`schema_version`, `retrieval_status`, `source_authority`) to demonstrate validation failure. It is clearly labeled as an intentional test fixture and uses a placeholder command name; it does not represent any real command.

`examples/retrieval/schema-fixtures/ambiguous-command-match.json` is a schema-valid fixture with `retrieval_status: "ambiguous"` and two synthetic candidates, for testing ambiguous-evidence handling. It uses placeholder command names and file paths only.

`examples/retrieval/schema-fixtures/official-vs-curated-conflict.json` is a schema-valid fixture with `retrieval_status: "conflict"` and placeholder official/curated values, for testing official-docs-vs-curated-note conflict behavior.

`examples/retrieval/schema-fixtures/stale-evidence.json` is a schema-valid fixture with `retrieval_status: "stale"` and a populated `stale_evidence` block, for testing stale-evidence handling. It uses a placeholder command name and syntax string only.

## Pass, Fail, And Warnings

A pass means the evidence object conforms to the JSON Schema and, in strict mode, has no practical warnings.

A fail means the evidence object did not validate against the schema, the validator could not perform schema validation, or `--strict` was used with warnings present.

Warnings identify risky evidence states, such as incomplete extraction, ambiguity without candidate details, conflicts without conflict records, stale evidence without staleness metadata, category-list evidence with verified-looking facts, or unredacted local paths.

Existing v0.4.0 prototype lookup JSON files may not fully conform until regenerated or mapped into the schema. They remain useful evidence, but schema validation should not be treated as retroactively required for those files.

Schema validation checks evidence *structure* — required fields, enum values, types — not GAUSS execution or semantic correctness. A schema-valid object is not proof that any GAUSS code was run, and it does not replace official GAUSS documentation as the authoritative source.

## Validating Everything At Once

`scripts/validate_all_evidence.py` checks every schema-aligned example and schema fixture in one command, instead of running the single-file validator against each one by hand:

```text
python scripts/validate_all_evidence.py
```

It treats every file as expected to pass, except `examples/retrieval/schema-fixtures/invalid-*.json` files, which are expected to fail — and reports an unexpected result (an expected-valid file failing, or an expected-invalid file passing) as an overall failure. It supports `--strict` and `--json` with the same meaning as the single-file validator, and accepts optional file/directory arguments to check a subset. See `scripts/README.md` for full usage.

The default non-strict run is the release-health check and currently passes. `--strict` is expected to fail on the known, reviewed `olsmt.evidence.json` and `glm.evidence.json` path warnings (both official HDF5-URI documentation examples, not leaked local paths); see the strict-mode policy note in `scripts/README.md` rather than treating that failure as hidden or unexplained.
