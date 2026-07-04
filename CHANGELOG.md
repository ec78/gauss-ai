# Changelog

This file records notable changes to the GAUSS AI framework.

## [Unreleased]

- GAUSS Language Expert Body of Knowledge.
- Initial Code Assistant agent.
- Knowledge source integration.
- Evaluation benchmarks.
- Added stable benchmark prompt IDs.
- Added manual evaluation workflow and scoring rubric updates, including `N/A` scoring dimension handling.
- Added completed Code Assistant manual evaluation runs.
- Added evaluation run index and benchmark coverage tracking.
- Added benchmark traceability guidance.
- Added native GAUSS command category knowledge.
- Added native command selection workflow.
- Added hybrid command documentation retrieval workflow.
- Improved benchmark expectations for native GAUSS statistical procedures.
- Refined R-to-GAUSS regression translation expectations around `olsmt`.
- Added public API design review evaluation coverage.
- Expanded manual benchmark coverage across Code Generation, Code Explanation, Refactoring, Optimization, Documentation, Test Generation, and Design Guidance.
- Added Test Generation and Design Guidance manual evaluation coverage.
- Added release readiness checklist, known limitations, and roadmap notes for `v0.2.0`.
- Added Code Assistant quickstart documentation.
- Added Code Assistant example use cases.
- Added `v0.3.0` Code Assistant Preview planning document.
- Improved Code Assistant README documentation.
- Refined `v0.3.0` Code Assistant preview documentation links, manual trial workflow, and trust guidance.
- Added `v0.3.0` Code Assistant Preview readiness checklist and audit notes.
- Removed tracked local knowledge source configuration and added a safe local override example.
- Started `v0.4.0` retrieval prototype planning.
- Added command documentation lookup tool design and implementation plan.
- Added retrieval-focused benchmark prompts.
- Added initial local command documentation lookup prototype.
- Added retrieval examples directory.
- Improved command documentation lookup extraction.
- Added keyword-focused retrieval support.
- Fixed `strindx` retrieval example: the `"not found"` keyword phrase had been split into separate single-word keywords by an unquoted shell invocation; regenerated with the phrase quoted so the example reports honest (empty) keyword hits for the literal phrase.
- Passed the first retrieval-focused manual evaluation (Prompt 11.1): the Code Assistant verified `olsmt` syntax and intercept behavior from local `olsmt` lookup evidence instead of deferring to the user.
- Passed the `strindx` retrieval evaluation (Prompt 11.2): the Code Assistant verified `strindx` returns `0` when not found using official lookup evidence, distinct from Python `.find()`'s `-1`.
- Passed the category-only command candidate evaluation (Prompt 11.3), completing initial Retrieval category coverage: the Code Assistant refused to invent syntax from category membership alone and recommended `scripts/command_doc_lookup.py` retrieval before giving exact usage.
- Started `v0.5.0` retrieval integration and response quality planning.
- Added retrieval-backed response pattern guidance for `v0.5.0`.
- Integrated retrieval-backed guidance across Code Assistant workflows, task modes, and system prompt instructions.
- Added `v0.5.0` retrieval integration benchmark prompts.
- Evaluated `v0.5.0` retrieval integration benchmarks 12.1-12.6.
- Verified retrieval-backed response behavior across translation, debugging, incomplete extraction, docs-not-found, ambiguous-match, and curated-note-vs-official-docs cases.
- Added manual evaluation coverage for key retrieval-backed response states.
- Started `v0.6.0` tool interface and evidence schema planning.
- Started `v0.6.0` evidence schema implementation.
- Added initial command lookup evidence JSON Schema.
- Added evidence schema design and validation planning docs.
- Added initial command lookup evidence validator.
- Added validation warnings for risky evidence states.
- Added schema-aligned command lookup output mode.
- Added schema-aligned retrieval examples for pilot commands.
- Preserved legacy lookup output format for backward compatibility.

## [0.1.0] - 2026-06-26

- Added project vision in `README.md`.
- Added high-level architecture in `ARCHITECTURE.md`.
- Added reasoning framework in `REASONING_FRAMEWORK.md`.
- Added standard specifications for agents, experts, tools, and knowledge.
- Added knowledge registry.
- Added experts layer and initial expert module structure.
- Added ADR structure for architectural decisions.
- Tagged first framework baseline release.
