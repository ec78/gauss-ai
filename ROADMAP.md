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

## v0.7.0: Broader Command Coverage and Automated Evidence Tests (Completed)

- Expand real schema-aligned command evidence coverage beyond the two `v0.6.0` pilots (`olsmt`, `strindx`) to a deliberately varied set of documentation shapes: `strsplit`, `dstatmt`, `qnewtonmt`, `pdsummary`, and `minimize`.
- Add an aggregate validator (`scripts/validate_all_evidence.py`) that checks every committed schema-aligned example and schema fixture in one pass, distinguishing expected-valid from intentionally-invalid files.
- Document a strict-mode release policy: the non-strict validate-all run is the release-health check, with known reviewed warnings named explicitly rather than hidden.
- Add and evaluate Automated Evidence Validation benchmarks (14.1-14.5) covering default validate-all health, strict-mode warning policy, aggregator discovery of new evidence, and both expected-invalid and expected-valid regression scenarios.
- Keep the legacy (non-`--schema-output`) lookup format byte-for-byte unchanged.

## v0.8.0: Operational Expert Modules (Completed)

- Move expert modules from documentation/specification assets to operational components the Code Assistant explicitly routes through, starting with the GAUSS Language Expert.
- Define a reusable operational expert interface (`tools/operational_expert_interface.md`): activation triggers, non-activation cases, required evidence by task type, decision rules, refusal/escalation conditions, an output contract, and evaluation criteria.
- Fill in that interface for the GAUSS Language Expert (`experts/gauss-language/OPERATIONAL_PROFILE.md`), consuming the existing evidence schema and retrieval-backed response pattern rather than inventing a competing evidence vocabulary.
- Add an expert routing workflow (`workflows/expert-routing.md`) and integrate it into the Code Assistant's response workflow, task modes, and system prompt, replacing the prior one-line "identify relevant experts" step.
- Add and evaluate Expert Routing benchmarks (15.1-15.7) covering positive activation, correct non-activation, native command preference, translation, cross-language-contamination debugging, data-structure routing, ambiguity escalation, and version-sensitive command selection.
- Keep expert activation internal by default: routing is checkable from response behavior, not a required "expert activated" label. Only the GAUSS Language Expert is operationalized in this milestone; the Econometrics, Software Engineering, Documentation, and Education experts remain narrative-only.

## v0.9.0: Second Operational Expert and Multi-Expert Routing

- Operationalize a second expert, the Econometrics Expert, proving the operational expert interface generalizes beyond the GAUSS Language Expert.
- Build the Econometrics Expert's narrative foundation (`experts/econometrics/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/econometrics/OPERATIONAL_PROFILE.md`).
- Extend `workflows/expert-routing.md` from single-expert (GAUSS-only) routing to four routing types: GAUSS-only, Econometrics-only, Both, and Neither, with coordination rules keeping implementation correctness (GAUSS Language Expert) and methodological correctness (Econometrics Expert) as separate, non-substitutable claims.
- Integrate multi-expert routing into the Code Assistant's response workflow, task modes, and system prompt.
- Add and evaluate Multi-Expert Routing benchmarks (16.1-16.8) covering all four routing types, causal-interpretation separation from code translation, p-value misinterpretation correction, and multi-expert uncertainty handling.
- Preserve every `v0.8.0` guarantee: GAUSS command evidence requirements are unchanged, and neither expert may substitute for the other (command availability is not methodological validity; methodological plausibility does not invent GAUSS syntax).
