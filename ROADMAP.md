# Roadmap

## v0.2.0: Knowledge and Evaluation Foundation (Completed)

- Stable benchmark prompt IDs.
- Manual evaluation workflow and scoring rubric.
- Completed manual evaluation runs, run index, and coverage tracker.
- GAUSS Language Body of Knowledge and native command category discovery.
- Native command selection and hybrid command documentation retrieval workflows.

## v0.3.0: Code Assistant Preview (Completed)

- Make the Code Assistant understandable and usable for manual preview users.
- Add quickstart, examples, limitations, and safe-use guidance.
- Strengthen retrieval guidance for official command documentation.
- Broaden benchmark coverage across high-value task modes.

## v0.4.0: Retrieval Prototype (Completed)

- Prototype local-first command documentation lookup against official GAUSS docs.
- Retrieve command-specific documentation for syntax, defaults, options, return values, and examples.
- Extract concise source-aware command notes without mirroring full documentation pages.
- Validate curated command notes against official command-specific documentation.
- Add retrieval-focused benchmarks for command lookup behavior.

## v0.5.0: Retrieval Integration and Response Quality (Completed)

- Move from a working local lookup prototype to consistent retrieval-backed Code Assistant response behavior.
- Define standard retrieval-backed response patterns, including handling for docs found, docs missing, ambiguous matches, and incomplete extraction.
- Require a validation step in retrieval-backed code translation and debugging responses.
- Add retrieval failure-mode benchmarks and manual evaluation coverage for ambiguous match, docs not found, incomplete extraction, curated-note-vs-official-docs conflict, translation validation, and debugging return behavior.
- Keep broader pilot command coverage as a follow-up after the response pattern is validated.

## v0.6.0: Tool Interface and Evidence Schema (Completed)

- Move from retrieval-backed response guidance to a structured, testable evidence layer.
- Define a command lookup evidence schema: required/optional fields, status values, confidence, and source provenance.
- Define an explicit source authority model (official docs, official package docs, official source, curated notes, examples, category lists, general knowledge).
- Define consumption rules tying schema fields back to retrieval-backed response behavior, and validation checks for evidence quality (missing fields, unredacted paths, missing provenance).
- Add a lightweight evidence validator for lookup JSON artifacts (`scripts/validate_lookup_evidence.py`), plus schema-aligned output support (`--schema-output`) in the retrieval prototype.
- Add and evaluate evidence-schema-focused benchmarks (13.1-13.7) distinct from `v0.5.0`'s response-quality benchmarks.

## v0.7.0: Broader Command Coverage and Automated Evidence Tests

- Expand real schema-aligned command evidence coverage beyond the two `v0.6.0` pilots (`olsmt`, `strindx`) to a deliberately varied set of documentation shapes: `strsplit`, `dstatmt`, `qnewtonmt`, `pdsummary`, and `minimize`.
- Add an aggregate validator (`scripts/validate_all_evidence.py`) that checks every committed schema-aligned example and schema fixture in one pass, distinguishing expected-valid from intentionally-invalid files.
- Document a strict-mode release policy: the non-strict validate-all run is the release-health check, with known reviewed warnings named explicitly rather than hidden.
- Add and evaluate Automated Evidence Validation benchmarks (14.1-14.5) covering default validate-all health, strict-mode warning policy, aggregator discovery of new evidence, and both expected-invalid and expected-valid regression scenarios.
- Keep the legacy (non-`--schema-output`) lookup format byte-for-byte unchanged.
