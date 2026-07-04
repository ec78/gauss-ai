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

## v0.6.0: Tool Interface and Evidence Schema

- Move from retrieval-backed response guidance to a structured, testable evidence layer.
- Define a command lookup evidence schema: required/optional fields, status values, confidence, and source provenance.
- Define an explicit source authority model (official docs, official package docs, official source, curated notes, examples, category lists, general knowledge).
- Define consumption rules tying schema fields back to retrieval-backed response behavior, and validation checks for evidence quality (missing fields, unredacted paths, missing provenance).
- Plan a lightweight evidence validator for lookup JSON artifacts.
- Add evidence-schema-focused benchmarks distinct from `v0.5.0`'s response-quality benchmarks.

## v0.7.0: Expanded Benchmark Suite and Automated Evaluation Support

- Expand benchmark coverage across GAUSS workflows and failure modes.
- Add automated or semi-automated evaluation support.
- Track benchmark regressions across prompt, expert, and retrieval changes.
