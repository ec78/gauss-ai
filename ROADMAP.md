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

## v0.14.0: Software Engineering Expert Foundation (Completed)

- Operationalize a third expert, the Software Engineering Expert, which owns maintainability/design correctness (code organization, modularity, refactoring, testability, error handling, safe change management) — distinct from the GAUSS Language Expert's implementation correctness and the Econometrics Expert's methodological correctness.
- Build the Software Engineering Expert's narrative foundation (`experts/software-engineering/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/software-engineering/OPERATIONAL_PROFILE.md`), following the `v0.9.0` Econometrics Expert precedent.
- Extend `workflows/expert-routing.md` from four routing types (GAUSS-only, Econometrics-only, Both, Neither) to eight (GAUSS-only, Econometrics-only, Software-engineering-only, GAUSS + Econometrics, GAUSS + Software Engineering, Econometrics + Software Engineering, all three, Neither), each with a documented when-it-applies statement, worked example, evidence/context pattern, and response rule.
- Integrate the Software Engineering Expert into the Code Assistant's response workflow, all ten task modes, and system prompt.
- Add and evaluate Software Engineering Expert Foundation benchmarks (21.1-21.8) covering all eight routing types, including the flagship all-three-experts prompt grounded in real local `glm.evidence.json`.
- Preserve every prior guarantee: GAUSS command evidence requirements are unchanged, econometric methodology requirements are unchanged, and no expert may substitute for another — clean code is not evidence of statistical/causal validity, and valid GAUSS syntax is not evidence of good design.

## v0.15.0: Documentation Expert Foundation (Completed)

- Operationalize a fourth expert, the Documentation Expert, which owns documentation/explanation correctness (documentation clarity, reference structure, examples, comments/docstrings, usage guidance, warnings/caveats, troubleshooting notes, terminology consistency, audience awareness) — distinct from the GAUSS Language Expert's implementation correctness, the Econometrics Expert's methodological correctness, and the Software Engineering Expert's maintainability/design correctness.
- Build the Documentation Expert's narrative foundation (`experts/documentation/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/documentation/OPERATIONAL_PROFILE.md`), following the `v0.9.0`/`v0.14.0` precedent.
- Extend `workflows/expert-routing.md` from an eight-type enumeration to a compact activation matrix and common routing patterns covering four experts (Documentation-only, GAUSS + Documentation, Econometrics + Documentation, Software Engineering + Documentation, GAUSS + Software Engineering + Documentation, GAUSS + Econometrics + Documentation, GAUSS + Econometrics + Software Engineering, all four, Neither), deliberately avoiding a full 16-combination routing engine.
- Integrate the Documentation Expert into the Code Assistant's response workflow, all ten task modes, and system prompt.
- Add and evaluate Documentation Expert Foundation benchmarks (22.1-22.8) covering the documented routing patterns, including the flagship all-four-experts prompt grounded in real local `glm.evidence.json`.
- Preserve every prior guarantee: GAUSS command evidence requirements are unchanged, econometric methodology requirements are unchanged, software-engineering maintainability requirements are unchanged, and no expert may substitute for another — clear documentation is not evidence of syntax correctness, statistical validity, or maintainability, and the Documentation Expert remains distinct from the future Education Expert.

## v0.16.0: Education Expert Foundation (Completed)

- Operationalize a fifth expert, the Education Expert, which owns education/learning-design correctness (learning objectives, instructional sequencing, scaffolding, practice design, feedback design, assessment design, learner progression, misconception handling, prerequisite mapping, cognitive load management, workshop/training-plan structure, learning path design) — distinct from the GAUSS Language Expert's implementation correctness, the Econometrics Expert's methodological correctness, the Software Engineering Expert's maintainability/design correctness, and the Documentation Expert's documentation/explanation correctness.
- Build the Education Expert's narrative foundation (`experts/education/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/education/OPERATIONAL_PROFILE.md`), following the `v0.9.0`/`v0.14.0`/`v0.15.0` precedent.
- Extend `workflows/expert-routing.md` from a twelve-pattern/four-axis activation matrix to a fourteen-pattern/five-axis activation matrix and common routing patterns (Education-only, GAUSS + Education, Econometrics + Education, Documentation + Education, Software Engineering + Education, GAUSS + Documentation + Education, Econometrics + Documentation + Education, GAUSS + Econometrics + Documentation + Education, all five, Neither), deliberately avoiding a full 32-combination routing engine.
- Integrate the Education Expert into the Code Assistant's response workflow, all ten task modes, and system prompt, closing a latent gap by naming the Product Expert explicitly in the two files' remaining-narrative-only lists.
- Add and evaluate Education Expert Foundation benchmarks (23.1-23.8) covering the documented routing patterns, including dedicated boundary tests confirming the Education Expert is distinct from the Documentation Expert and from the future Product Expert.
- Preserve every prior guarantee: GAUSS command evidence requirements are unchanged, econometric methodology requirements are unchanged, software-engineering maintainability requirements are unchanged, documentation requirements are unchanged, and no expert may substitute for another — a well-designed lesson is not evidence of syntax correctness, statistical validity, maintainability, documentation quality, or product value.

## v0.17.0: Product Expert Foundation (Completed)

- Operationalize a sixth expert, the Product Expert, which owns product/user-value correctness (user problem framing, customer/job-to-be-done framing, workflow fit, user journey, first-use experience, activation and time-to-value, adoption barriers, value proposition, positioning, product requirements framing, prioritization tradeoffs, scope tradeoffs, product discovery questions, product assumptions, product risk identification) — distinct from the GAUSS Language Expert's implementation correctness, the Econometrics Expert's methodological correctness, the Software Engineering Expert's maintainability/design correctness, the Documentation Expert's documentation/explanation correctness, and the Education Expert's education/learning-design correctness.
- Build the Product Expert's narrative foundation (`experts/product/EXPERT.md`, `BODY_OF_KNOWLEDGE.md`, `reasoning.md`, `best_practices.md`, `common_mistakes.md`) from placeholder files, then fill in the operational interface (`experts/product/OPERATIONAL_PROFILE.md`), following the `v0.9.0`/`v0.14.0`/`v0.15.0`/`v0.16.0` precedent.
- Extend `workflows/expert-routing.md` from a fourteen-pattern/five-axis activation matrix to a sixteen-pattern/six-axis activation matrix and common routing patterns (Product-only, Product + Documentation, Product + Education, Product + GAUSS, Product + Econometrics, Product + Software Engineering, Documentation + Education + Product, GAUSS + Documentation + Education + Product, GAUSS + Econometrics + Product, all six, Neither), deliberately avoiding a full 64-combination routing engine.
- Integrate the Product Expert into the Code Assistant's response workflow, all ten task modes, and system prompt, completing six-expert integration with no remaining narrative-only expert placeholder.
- Add and evaluate Product Expert Foundation benchmarks (24.1-24.8) covering the documented routing patterns, including dedicated boundary tests confirming the Product Expert is distinct from the Documentation Expert and the Education Expert.
- Preserve every prior guarantee: GAUSS command evidence requirements are unchanged, econometric methodology requirements are unchanged, software-engineering maintainability requirements are unchanged, documentation requirements are unchanged, education requirements are unchanged, and no expert may substitute for another — product value is not evidence of syntax correctness, statistical validity, maintainability, documentation quality, or education quality, and product hypotheses must be labeled when evidence is missing.

## v0.18.0: Expert System Consolidation

- Pause new expert creation and consolidate the six-expert system (GAUSS Language, Econometrics, Software Engineering, Documentation, Education, Product) so it is easier to maintain, audit, route, evaluate, and extend — not a new-capability milestone.
- Add a central expert registry (`experts/EXPERT_REGISTRY.md`) summarizing each expert's identity, ownership, activation triggers, escalation targets, and operational status in one place.
- Add an expert boundary matrix (`experts/EXPERT_BOUNDARY_MATRIX.md`) consolidating what each expert owns, does not own, and the recurring false-equivalence traps between experts (e.g., command availability is not methodological validity, product value is not correctness evidence for any other dimension).
- Add a compact routing cheat sheet (`workflows/expert-routing-cheatsheet.md`) summarizing `workflows/expert-routing.md`'s six-axis classification, activation/non-activation cases, escalation rules, and multi-expert separation rules without replacing the authoritative workflow.
- Audit all six `OPERATIONAL_PROFILE.md` files for structural consistency and stale routing-count/"future Expert" wording (`planning/v0.18.0-operational-profile-audit.md`), fixing any concrete inconsistency found.
- Add an evaluation dashboard (`evaluations/EVALUATION_DASHBOARD.md`) summarizing benchmark category status, pass/fail counts, and known warnings as a labeled snapshot pointing back to `evaluations/benchmark-coverage.md` and `evaluations/runs/INDEX.md`.
- Add an expert-system maintenance guide (`workflows/expert-system-maintenance.md`) documenting how to add a future expert, which files must be checked when routing changes, and a stale-wording checklist grounded in the real drift found during the `v0.16.0` and `v0.17.0` readiness audits.
- Add no new operational expert, no new routing type, no runtime orchestration, and no schema changes — this milestone consolidates and documents the existing six-expert system rather than extending it.
- Status: the expert registry, boundary matrix, routing cheat sheet, operational profile audit, evaluation dashboard, and maintenance guide are complete; `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md` have been audited and updated to reference them. Remaining before this milestone is ready to tag: a decision on whether to add optional `25.x` consolidation benchmarks, and the `v0.18.0` readiness checklist.
- Optional: add `25.x` consolidation benchmarks testing whether the Code Assistant can correctly use the consolidated registry/boundary matrix/cheat sheet to answer routing and boundary questions, only after the consolidation documents above exist (see `planning/v0.18.0-expert-system-consolidation.md`'s "Benchmark Plan") — not yet decided.
- Create the `v0.18.0` readiness checklist once the deliverables above are complete and the benchmark decision is made.

## v0.19.0: GAUSS Tooling Strategy and Execution Modes (Planned)

Planning-only milestone. See `planning/v0.19.0-gauss-tooling-strategy-and-execution-modes.md`.

- Begins the transition from a documentation/evaluation-driven Code Assistant toward a tool-enabled GAUSS assistant that can optionally inspect the local GAUSS environment, identify installed GAUSS packages, run GAUSS code, capture results, and help users generate reports. Execution is designed as an optional capability from the outset — advisory mode (the assistant's entire current behavior) remains fully supported whether or not GAUSS is available.
- Define three operating modes: Advisory Mode (current behavior, no execution), Verified Knowledge Mode (evidence-backed claims, no execution), and Execution Mode (GAUSS installed and detected, tools available, user permits execution).
- Document the Graceful Fallback Principle: the assistant must not break, must not claim execution, and must remain useful in Advisory or Verified Knowledge Mode whenever GAUSS or an execution tool is unavailable.
- Scope (but do not implement) three future tools — a GAUSS environment detection tool, a GAUSS package inspection tool, and a GAUSS code execution tool — plus a result-reporting workflow, following `TOOL_SPEC.md`'s structure.
- Document how future tool availability interacts with the six-expert system: execution changes what evidence is available to an expert, but does not change which expert owns which correctness dimension, and successful execution never substitutes for statistical, maintainability, documentation, education, or product correctness.
- Propose a five-milestone follow-up breakdown (`v0.20.0` environment detection, `v0.21.0` package inspection, `v0.22.0` execution prototype, `v0.23.0` execution-aware analysis, `v0.24.0` report generation) and a benchmark strategy for each, none of which are implemented or committed by this milestone.
- Add no execution implementation, no new schemas, no new tools, no CI changes, and no runtime orchestration — this milestone is strategy and boundary-setting only.

## v0.20.0: GAUSS Environment Detection Tool (Planned)

See `planning/v0.20.0-gauss-environment-detection-tool.md`.

- Plans the first read-only tool capability from `v0.19.0`'s strategy: a `gauss_environment_check` tool that checks whether GAUSS is installed or discoverable, identifies the executable path and version when possible, and returns a structured result the Code Assistant can use to choose Advisory Mode, Verified Knowledge Mode, or (once it exists) Execution Mode safely.
- Defines detection states: `found`, `not_found`, `ambiguous`, `inaccessible`, `error`, and `unknown`, plus a separate `operating_mode_recommendation` field (`advisory`/`verified_knowledge`/`execution_candidate`) — detection never activates Execution Mode by itself.
- Defines a read-only permission level: no code execution beyond an optional minimal version query, no file mutation, no package installation.
- Documents advisory-mode fallback for every non-`found` state, and for `found`-but-inaccessible or `found`-but-ambiguous states, so the assistant never breaks or claims execution based on a partial detection result.
- Created the tool spec (`tools/gauss_environment_check.md`), result schema (`schemas/gauss_environment_check.schema.json`), and five synthetic example outputs (`examples/tools/gauss-environment-found.json`, `-not-found.json`, `-ambiguous.json`, `-inaccessible.json`, `-version-unknown.json`).
- Added and evaluated `26.x` benchmark prompts (`26.1`-`26.8`): 8/8 passed at 4.0, validating graceful fallback to Advisory Mode, `execution_candidate` treated as a prerequisite signal rather than active execution, and protection against treating detection as syntax or methodology evidence — against documented expected behavior, since no tool implementation exists to test for real.
- Status: the planning doc, tool spec, result schema, example outputs, `26.x` benchmark prompts, and `26.x` evaluations are complete; `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md` have been audited and updated to reference them. Remaining before this milestone is ready to tag: the `v0.20.0` readiness checklist.
- Add no implementation and no runtime orchestration — this milestone specifies, schemas, exemplifies, and evaluates expected behavior only; the tool itself remains unimplemented.

## v0.21.0: GAUSS Environment Detection Implementation (Planned)

See `planning/v0.21.0-gauss-environment-detection-implementation.md`.

- Implements the already-specified `gauss_environment_check` tool from `v0.20.0` (`tools/gauss_environment_check.md`, `schemas/gauss_environment_check.schema.json`) — moves from specification to real detection code for the first time, at `scripts/gauss_environment_check.py`.
- Adds a newest-version default selection rule: when multiple GAUSS installations are detected (for example, GAUSS 24, 25, and 26), the tool defaults to the highest version unless the user provides a preferred executable path, a preferred GAUSS version, or requests strict mode. A user-specified version or path always overrides the default; the newest version is never silently substituted, and a newest-but-inaccessible candidate is never silently downgraded to an older one without a warning.
- Implements the detection strategy already scoped in `v0.20.0` (user-provided path, user-specified version, `PATH` lookup, common-location scan, version parsing) and validates every returned result against `schemas/gauss_environment_check.schema.json`.
- Preserves every `v0.20.0` guarantee: read-only inspection, no user GAUSS code execution, no package inspection, no Execution Mode activation, and Advisory Mode as the fallback for every non-`found` (and partial `found`-but-inaccessible/ambiguous) case.
- Ships a CLI and importable module (`detect_environment(...)`) with `--json`, `--validate-schema`, and a built-in `--self-test` suite (no formal `tests/` directory exists yet) rather than a new benchmark category — `26.x` remains the response-behavior benchmark suite; a future `27.x` is only proposed if the Code Assistant workflow later integrates with real tool output.
- Status: the planning doc, helper implementation, CLI/importable module, schema-validation support, and self-test suite are complete. The newest-version default and both preferred-path/preferred-version overrides are implemented and verified — including manual verification against this development machine's real GAUSS 24/25/26 installations (default selects GAUSS 26; `--preferred-version 25` selects GAUSS 25; a nonexistent preferred path returns `not_found` without fallback; `--strict` behaves as documented). `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md` have been audited and updated to reference the implementation. Remaining before this milestone is ready to tag: the `v0.21.0` readiness checklist.
- Add no package inspection, no code execution, no runtime orchestration, and no CI changes — this milestone implements environment detection only.

## v0.22.0: GAUSS Package Inspection Tool (Planned)

See `planning/v0.22.0-gauss-package-inspection-tool.md`.

- Plans the second read-only GAUSS tooling capability, following `v0.21.0`'s environment detection: a `gauss_package_inspection` tool that identifies which GAUSS packages/application modules appear available in a detected GAUSS environment, distinguishing base GAUSS availability from package-dependent functionality where possible.
- Package inspection uses the selected GAUSS environment from `v0.21.0`'s `gauss_environment_check` (executable path, version, platform, detection status) as primary context — it does not re-detect GAUSS itself, and gracefully returns `unavailable`/`unknown` with Advisory Mode fallback whenever environment detection was not `found`.
- Respects `v0.21.0`'s newest-version default rule: if GAUSS 24/25/26 are all installed and environment detection selected GAUSS 26, package inspection inspects the GAUSS 26 package context by default; an explicit user version selection carries through to package inspection as well. Package availability may differ by GAUSS version.
- Defines five package-inspection statuses (`complete`/`partial`/`unavailable`/`error`/`unknown`) and per-package fields (`name`, `installed`, `version`, `source`, `path`, `package_type`, `notes`), plus explicit independence rules (package availability does not validate syntax, methodology, maintainability, documentation, education, or product value, and does not imply execution occurred).
- Created the tool spec (`tools/gauss_package_inspection.md`), result schema (`schemas/gauss_package_inspection.schema.json`), and five synthetic example outputs (`examples/tools/gauss-package-inspection-complete.json`, `-missing.json`, `-partial.json`, `-unavailable.json`, `-unknown.json`).
- Added and evaluated `27.x` benchmark prompts (`27.1`-`27.8`): 8/8 passed at 4.0, validating package-status uncertainty handling, base-vs-package/application-module separation, graceful fallback, and protection against treating package availability as syntax or methodology evidence — against documented expected behavior, since no tool implementation exists to test for real.
- **Scope decision:** `v0.22.0` is the package-inspection specification/evaluation milestone, not the implementation milestone. The package-inspection implementation has unresolved risks around real GAUSS package/application-module locations, version-specific package contexts, licensing, and whether metadata-only inspection can be done safely — following `v0.20.0`+`v0.21.0`'s precedent of splitting environment detection into a spec milestone and a separate implementation milestone, package-inspection implementation is deferred to `v0.23.0` (see below).
- Status: the planning doc, tool spec, result schema, example outputs, `27.x` benchmark prompts, and `27.x` evaluations are complete; `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md` have been audited and updated to reference them. Remaining before this milestone is ready to tag: the `v0.22.0` readiness checklist.
- Add no implementation, no GAUSS code execution, no CI changes, and no runtime orchestration — this milestone specifies, schemas, exemplifies, and evaluates expected behavior only; the tool itself remains unimplemented.

## Future (TBD / Possible)

Not yet planned or committed. Candidate directions after `v0.18.0`/`v0.19.0`/`v0.20.0`/`v0.21.0`/`v0.22.0`:

- `v0.23.0` - GAUSS Package Inspection Implementation, `v0.24.0` - GAUSS Code Execution Prototype, `v0.25.0` - Execution-Aware Analysis Workflow, `v0.26.0` - Report Generation Workflow. Each shifted one milestone later than `planning/v0.19.0-gauss-tooling-strategy-and-execution-modes.md`'s original numbering, now that `v0.22.0` (specification) and its implementation were split into two milestones for package inspection, mirroring the same split already used for environment detection (`v0.20.0` spec / `v0.21.0` implementation). `v0.23.0` is the most immediate: implement the `gauss_package_inspection` tool already specified, schemad, exemplified, and evaluated in `v0.22.0`, resolving the open risks around real package/application-module locations, version-specific package contexts, licensing, and safe metadata-only inspection. Each of these four still requires its own planning task before implementation, the same way `v0.19.0`-`v0.22.0` were planned before any of them.
- Expert-system automation/hygiene tooling — for example, a scripted stale-wording check in the spirit of `scripts/check_evaluation_tracking.py`, building on `workflows/expert-system-maintenance.md`'s manual Stale Wording Search Checklist.
- Retrieval/evidence expansion — broader real command evidence coverage beyond the current seven-command pilot set (`olsmt`, `strindx`, `strsplit`, `dstatmt`, `qnewtonmt`, `pdsummary`, `minimize`).
- Benchmark dashboard automation — regenerating `evaluations/EVALUATION_DASHBOARD.md` from live guard output instead of a manually maintained snapshot.
- Strict-mode warning reduction — improving the evidence validator's path-warning heuristic so it stops flagging the reviewed `glm`/`olsmt` HDF5-URI false positives.
- Runtime orchestration exploration — only if intentionally planned later; no runtime expert-routing engine or execution orchestration is currently planned or implied by any `v0.18.0`-`v0.22.0` work.

None of these are committed milestones; this list exists so `v0.18.0`-`v0.22.0`'s planning work doesn't strand good follow-up ideas without a place to record them.
