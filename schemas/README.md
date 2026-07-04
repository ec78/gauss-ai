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

The initial retrieval prototype is `scripts/command_doc_lookup.py`. Existing lookup examples may predate this schema or only partially align with it.

Future command lookup outputs should align with `command_lookup_evidence.schema.json`, but this directory does not require rewriting existing prototype outputs.

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

These schemas are design/prototype artifacts. They are not yet production enforcement, and no validator is implemented in this task.

Official GAUSS documentation remains the source of truth for exact syntax, inputs, outputs, defaults, examples, and command behavior.
