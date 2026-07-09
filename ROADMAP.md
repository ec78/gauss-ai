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

## v0.9.0: Second Operational Expert and Multi-Expert Routing (Completed)

- Operationalize a second expert, the Econometrics Expert, proving the operational expert interface generalizes beyond the GAUSS Language Expert.
- Build the Econometrics Expert's narrative foundation (`experts/econometrics/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/econometrics/OPERATIONAL_PROFILE.md`).
- Extend `workflows/expert-routing.md` from single-expert (GAUSS-only) routing to four routing types: GAUSS-only, Econometrics-only, Both, and Neither, with coordination rules keeping implementation correctness (GAUSS Language Expert) and methodological correctness (Econometrics Expert) as separate, non-substitutable claims.
- Integrate multi-expert routing into the Code Assistant's response workflow, task modes, and system prompt.
- Add and evaluate Multi-Expert Routing benchmarks (16.1-16.8) covering all four routing types, causal-interpretation separation from code translation, p-value misinterpretation correction, and multi-expert uncertainty handling.
- Preserve every `v0.8.0` guarantee: GAUSS command evidence requirements are unchanged, and neither expert may substitute for the other (command availability is not methodological validity; methodological plausibility does not invent GAUSS syntax).

## v0.10.0: Evidence Coverage and Routing Regression Guards (Completed)

- Close the local `glm` evidence gap surfaced by a `v0.9.0` benchmark evaluation (`16.7`), which had to verify `glm` against live official documentation instead of a committed local file: add real schema-aligned evidence (`examples/retrieval/schema-aligned/glm.evidence.json`) generated from the local official `glm.rst`.
- Systematically audit local and package-level GAUSS documentation for a panel-estimation command, resolving the open question left by `v0.9.0`'s `16.4` evaluation: find `tscsFit` (from the commercial TSMT package) as a verified pooled time-series-cross-section regression estimator, document it (`examples/retrieval/panel-estimation-coverage-audit.md`), and add real schema-aligned evidence (`examples/retrieval/schema-aligned/tscsfit.evidence.json`) while clearly distinguishing panel data-management utilities and panel diagnostic/test commands from actual panel estimation.
- Add a lightweight, local evaluation tracking consistency guard (`scripts/check_evaluation_tracking.py`) that checks benchmark prompts, coverage rows, run files, and the run index for consistency with each other, so tracking drift is caught mechanically rather than only by an evaluator's diligence.
- Add and evaluate Evidence Coverage and Tracking Guards benchmarks (17.1-17.6) covering `glm` evidence validation, a logistic-regression response grounded in local evidence, panel-audit non-invention, and the tracking guard's default/JSON/strict behavior including historical-warning handling.
- Add no new operational expert, no new routing type, and no runtime orchestration — this milestone hardens the evidence and tracking layers underneath the `v0.9.0` routing system rather than extending routing itself.

## v0.11.0: Repository Hygiene and Evaluation Policy Cleanup (Completed)

- Fix stale wording in the Econometrics Expert's operational profile (`experts/econometrics/OPERATIONAL_PROFILE.md`) that still described multi-expert routing as unbuilt, despite `v0.9.0` having completed and evaluated it — a documentation-only fix with no change to expert behavior, decision rules, or activation conditions.
- Document an explicit, written policy for two long-standing evaluation-tracking warnings (a historical Prompt ID mismatch, and a pre-Prompt-ID-era smoke-test run file) in `evaluations/benchmark-coverage.md`'s "Historical Tracking Exceptions" section: preserve both without rewriting historical run files, since rewriting them would misrepresent what was actually evaluated at the time.
- Add benchmark-authoring guidance (`workflows/manual-evaluation.md`) against hardcoding volatile repository counts in a benchmark's expected-behavior text, grounded in a real precedent from `v0.10.0`'s `17.5`/`17.6` evaluations.
- Clarify `experts/econometrics/knowledge.md`, a one-line placeholder superseded by `BODY_OF_KNOWLEDGE.md`, as an explicit compatibility stub rather than an unexplained gap.
- Close a command-evidence source-classification gap: `scripts/command_doc_lookup.py` now distinguishes core GAUSS documentation from separately-licensed package documentation (`official_docs`/`official_local_rst` vs. `official_package_docs`/`official_package_rst`), using a package-directory list derived from the official GAUSS Applications index — the schema already supported this distinction; only the tool's classification logic was missing it.
- Add and evaluate Repository Hygiene and Evaluation Policy Cleanup benchmarks (18.1-18.6) validating every item above.
- Add no new operational expert, no new routing type, and no runtime orchestration — this milestone is cleanup and policy clarity only.

## v0.12.0: GAUSS Language Knowledge Cleanup and CI Guard Prep (Completed)

- Clarify `experts/gauss-language/knowledge.md`, a one-line placeholder superseded by `BODY_OF_KNOWLEDGE.md`, as an explicit compatibility stub — the direct parallel to `v0.11.0`'s Econometrics fix, flagged as a deferred follow-up at the time.
- Add a local release-readiness check (`scripts/check_release_readiness.py`) that runs the existing default guard suite (`validate_all_evidence.py`, `check_evaluation_tracking.py`) in one command; `--strict` runs both scripts' strict mode as a separate, informational section that never affects the script's own exit code.
- Document strict-mode policy and future CI expectations in `scripts/README.md`: default checks are the release-health gate; strict checks are warning-free gates currently expected to fail for named, reviewed reasons; future CI should start with default checks only and never hide warnings to appear green.
- Document the `PACKAGE_DOC_DIRECTORIES` refresh process: concrete steps for updating the hardcoded, `applications.rst`-derived package-directory snapshot when the official Applications index changes.
- Add and evaluate GAUSS Language Knowledge Cleanup and CI Guard Prep benchmarks (19.1-19.5) validating every item above.
- Add no new operational expert, no new routing type, no runtime orchestration, and no CI workflow files — this milestone prepares for CI, it does not add it.

## v0.13.0: Default CI Guard Integration (Completed)

- Add a minimal GitHub Actions workflow (`.github/workflows/release-readiness.yml`, name "Release Readiness") that runs on every `push` and `pull_request`: checks out the repository, sets up Python `3.11`, installs the one required dependency (`jsonschema`), and runs `python scripts/check_release_readiness.py` — the same default-mode entrypoint already used locally, with no separate CI-only code path.
- Do not enforce strict-mode checks in CI: the workflow never passes `--strict`, so the currently-expected strict-mode warnings (reviewed `glm`/`olsmt` HDF5-URI path warnings; two documented historical tracking warnings) have no effect on whether CI passes.
- Do not suppress or filter any warning: the workflow's output is the underlying scripts' real stdout/stderr, unmodified, so every warning stays visible in CI logs exactly as it would locally.
- Document CI behavior in `scripts/README.md` (a new CI paragraph, plus updated strict-mode-policy wording reflecting that CI now exists) and `RELEASE_CHECKLIST.md` (a pointer note).
- Add and evaluate Default CI Guard Integration benchmarks (20.1-20.5) validating every item above.
- Add no new operational expert, no new routing type, no runtime orchestration, no schema changes, and no strict-mode CI enforcement — this milestone is CI integration for the existing default gate only.

## v0.14.0: Software Engineering Expert Foundation

- Operationalize a third expert, the Software Engineering Expert, which owns maintainability/design correctness (code organization, modularity, refactoring, testability, error handling, safe change management) — distinct from the GAUSS Language Expert's implementation correctness and the Econometrics Expert's methodological correctness.
- Build the Software Engineering Expert's narrative foundation (`experts/software-engineering/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/software-engineering/OPERATIONAL_PROFILE.md`), following the `v0.9.0` Econometrics Expert precedent.
- Extend `workflows/expert-routing.md` from four routing types (GAUSS-only, Econometrics-only, Both, Neither) to eight (GAUSS-only, Econometrics-only, Software-engineering-only, GAUSS + Econometrics, GAUSS + Software Engineering, Econometrics + Software Engineering, all three, Neither), each with a documented when-it-applies statement, worked example, evidence/context pattern, and response rule.
- Integrate the Software Engineering Expert into the Code Assistant's response workflow, all ten task modes, and system prompt.
- Add and evaluate Software Engineering Expert Foundation benchmarks (21.1-21.8) covering all eight routing types, including the flagship all-three-experts prompt grounded in real local `glm.evidence.json`.
- Preserve every prior guarantee: GAUSS command evidence requirements are unchanged, econometric methodology requirements are unchanged, and no expert may substitute for another — clean code is not evidence of statistical/causal validity, and valid GAUSS syntax is not evidence of good design.
