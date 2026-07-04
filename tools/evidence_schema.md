# Evidence Schema

## Purpose

This document explains the initial evidence schema design for GAUSS command lookup results.

The schema is intended to make retrieval evidence structured enough for validation, review, and safe Code Assistant consumption. It does not replace official GAUSS documentation and does not claim that retrieved evidence is complete.

The first schema file is:

- `schemas/command_lookup_evidence.schema.json`

## Evidence Object Lifecycle

1. A retrieval tool searches official GAUSS documentation, package docs, source files, curated notes, category lists, or other configured sources.
2. The tool emits an evidence object with a retrieval status, source authority, confidence score, matches, unresolved questions, and extraction warnings.
3. A validator can check the object shape and flag risky states.
4. The Code Assistant consumes the evidence object when writing a response.
5. The final response states verified facts, unresolved items, ambiguity, conflicts, or retrieval failure according to the evidence.

Existing `examples/retrieval/*.lookup.json` files predate this schema and should be treated as prototype outputs until regenerated or mapped.

## Source Authority Model

Authority levels are represented with `source_authority`:

- `official_docs`
- `official_package_docs`
- `official_source_code`
- `curated_command_note`
- `example_or_blog`
- `category_list`
- `model_knowledge`
- `unknown`

Official command-specific docs are authoritative for syntax, inputs, outputs, defaults, examples, and command behavior. Official package docs are authoritative for package-scoped commands. Official source code can help when docs are unavailable, but source interpretation should be treated carefully.

Curated command notes are convenience references. Category lists are discovery only. Model knowledge cannot verify command-specific GAUSS syntax or behavior.

## Retrieval Status Meanings

- `found_complete`: A confident command-specific match was found and no relevant unresolved questions remain.
- `found_incomplete`: A confident match was found, but extraction is partial, truncated, or missing relevant sections.
- `not_found`: Lookup completed but found no matching command-specific documentation.
- `ambiguous`: Multiple plausible matches were found and none should be silently selected.
- `conflict`: Two sources disagree, such as official docs and a curated command note.
- `stale`: Evidence exists but has not been freshly verified against the current authoritative source.
- `error`: The lookup process failed, such as a missing docs root or unreadable file.

## Required vs Optional Fields

The schema requires:

- `schema_version`
- `command_name`
- `retrieval_status`
- `source_authority`
- `source_type`
- `confidence`
- `matches`
- `unresolved_questions`
- `extraction_warnings`

Optional fields include generation metadata, tool identity, `best_match`, `ambiguity`, `conflicts`, `stale_evidence`, notes, and error details.

Optional fields should not be used to imply verified facts. A missing optional field is not evidence that the corresponding behavior does not exist.

## Incomplete Extraction

Incomplete extraction should be represented with:

- `retrieval_status: "found_incomplete"`
- Non-empty `unresolved_questions` when user-relevant facts remain unverified.
- Non-empty `extraction_warnings` when the tool detected truncation, missing sections, parser limits, or keyword misses.
- Matches that contain only the extracted sections actually found.

The Code Assistant should present only verified fields and should not invent missing output fields, defaults, or examples.

## Ambiguity

Ambiguity should be represented with:

- `retrieval_status: "ambiguous"`
- An `ambiguity` object containing `is_ambiguous`, `candidate_count`, `reason`, and `candidates`.

The Code Assistant should list or summarize the candidates and ask for disambiguating context. It should not silently choose the highest-confidence candidate.

## Official Docs vs Curated Notes

Conflicts should be represented with:

- `retrieval_status: "conflict"`
- A non-empty `conflicts` array.
- Each conflict naming the `field`, `official_value`, `curated_value`, `resolution`, and `source_precedence`.

Official docs win in all conflicts. Curated notes should be corrected or removed when they disagree with official documentation.

## Stale Evidence

Staleness should be represented with:

- `retrieval_status: "stale"`
- A `stale_evidence` object containing `is_stale`, `reason`, optional `generated_at`, optional `checked_against`, and `recommended_action`.

The Code Assistant may use stale evidence as a starting point but should recommend re-running lookup before production use.

## Code Assistant Consumption Rules

The Code Assistant should:

- State `retrieval_status` before relying on command-specific facts.
- Use `source_authority` and `source_type` to decide how much confidence to place in evidence.
- Treat `unresolved_questions` and `extraction_warnings` as required reading.
- Use only verified syntax, inputs, outputs, defaults, and examples from official or properly caveated curated sources.
- Refuse exact syntax when status is `not_found`, `ambiguous`, `error`, or category-only discovery.
- Surface conflicts and staleness instead of hiding them.
- Avoid claiming GAUSS code was executed unless a runtime tool actually ran it.

## Validation Rules

A lightweight validator should eventually check:

- Required fields are present.
- Enum values are valid.
- Confidence values are between 0 and 1.
- Committed artifacts do not contain unredacted local absolute paths.
- Verified facts have source provenance.
- `ambiguity` exists when status is `ambiguous`.
- `conflicts` exists when status is `conflict`.
- `stale_evidence` exists when status is `stale`.
- Extraction warnings are not silently ignored.

JSON Schema can validate shape. It cannot prove that extracted facts are semantically correct or current relative to official docs.

## Known Limitations

- The schema is a design/prototype artifact.
- Existing lookup JSON files are not yet schema-aligned; both `examples/retrieval/olsmt.lookup.json` and `examples/retrieval/strindx.lookup.json` fail schema validation today because they predate this schema's field names and shapes.
- The validator (`scripts/validate_lookup_evidence.py`) checks shape and a set of practical warnings; it cannot verify official documentation semantics.
- Staleness can be represented before it can be automatically detected.
- Official GAUSS documentation remains authoritative.

## Future Improvements

- Add schema-aligned lookup output from `scripts/command_doc_lookup.py`.
- Regenerate or map existing lookup examples.
- Add schema-focused benchmark prompts.
- Add evidence fixtures for incomplete, ambiguous, stale, conflict, and error states.
