# GAUSS AI

**GAUSS AI** is an open architecture for building specialized AI agents that assist with GAUSS programming, econometrics, documentation, education, and product development.

Rather than creating a single, monolithic chatbot, this project defines a collection of focused agents that share a common knowledge base, evaluation framework, and development standards.

## Current Status

The project is currently working toward `v0.23.0` - GAUSS Package Inspection Implementation. This milestone implements the already-specified `gauss_package_inspection` tool from `v0.22.0` as a real, read-only helper: `scripts/gauss_package_inspection.py`, both CLI-usable (`python scripts/gauss_package_inspection.py`) and importable (`inspect_packages(...)`), returning schema-shaped output conforming to `schemas/gauss_package_inspection.schema.json`. The helper consumes GAUSS environment context — a supplied `gauss_environment_check` result, a direct executable-path/version override, or an automatic call to `v0.21.0`'s `detect_environment(...)` (skipped when `--strict` is set) — and preserves that version-specific package context without mixing results across GAUSS versions. Package discovery is conservative and read-only: caller-supplied `package_search_paths` are checked authoritatively, a small documented-non-exhaustive `pkgs`/`packages` sibling-directory heuristic supplements them, and requested-package name matching is case/separator-insensitive only with no alias inference (`tscsFit`, one command within the TSMT package, is never treated as a synonym for the `tsmt` package itself). Requested packages are classified `installed`, `missing`, or `unknown` depending on how complete the inspection scope was: `installed: true` never means code was executed or syntax is valid, `installed: false` never means GAUSS itself is missing, and `installed: "unknown"` is never treated as missing. `--allow-metadata-query` is accepted but remains a documented no-op, since no safe GAUSS package-metadata-query command is confirmed yet — the same conservative pattern `v0.21.0`'s `--allow-version-query` already established. A built-in `--self-test` suite (13 synthetic-fixture cases, no real GAUSS installation required) passes both with and without `--validate-schema`, and the helper has been manually verified against this development machine's real GAUSS 26 installation. Still not implemented: GAUSS code execution, package installation, license activation, metadata query invocation, statistical analysis execution, runtime orchestration, Code Assistant workflow integration, and report generation from actual execution output.

Prior milestones: `v0.2.0` established the knowledge and evaluation foundation (expert guidance, benchmark prompts, scoring rubrics, manual evaluation records, native command category discovery, and command documentation retrieval workflows); `v0.3.0` made the Code Assistant usable and evaluable for manual preview; `v0.4.0` added a local-first command documentation lookup prototype; `v0.5.0` standardized retrieval-backed response behavior across the assistant's task modes; `v0.6.0` represented command lookup evidence in a structured, versioned JSON Schema, validated that evidence mechanically, and added schema-aligned output to the retrieval prototype alongside the existing lookup format; `v0.7.0` expanded real schema-aligned command evidence coverage across varied documentation shapes and added an aggregate validator so every committed evidence example and fixture can be checked in one pass; `v0.8.0` operationalized the GAUSS Language Expert as the first expert the Code Assistant explicitly routes through; `v0.9.0` operationalized a second expert, the Econometrics Expert, and extended expert routing to four routing types (GAUSS-only, Econometrics-only, Both, Neither), with the GAUSS Language Expert owning implementation correctness and the Econometrics Expert owning methodological correctness — neither may substitute for the other; `v0.10.0` closed the local `glm` evidence gap, audited and documented GAUSS panel-estimation coverage (finding a verified command, `tscsFit`, from the commercial TSMT package), and added a local evaluation tracking consistency guard (`scripts/check_evaluation_tracking.py`); `v0.11.0` fixed stale expert-profile wording, documented a historical evaluation-tracking warning policy, added benchmark-authoring guidance, clarified a superseded expert-knowledge placeholder, and closed a command-evidence source-classification gap the schema already supported but the retrieval tool hadn't implemented; `v0.12.0` clarified the GAUSS Language Expert's `knowledge.md` placeholder, added a local release-readiness check (`scripts/check_release_readiness.py`), and documented strict-mode behavior and the `PACKAGE_DOC_DIRECTORIES` refresh process ahead of eventual CI; `v0.13.0` moved the local default release-readiness gate into CI via a minimal GitHub Actions workflow (`.github/workflows/release-readiness.yml`) that runs the default (non-strict) release-readiness check on every push and pull request; `v0.14.0` operationalized a third expert, the Software Engineering Expert, and extended expert routing to eight routing types covering every combination of the three experts; `v0.15.0` operationalized a fourth expert, the Documentation Expert, and replaced the eight-type enumeration with a compact activation matrix and common routing patterns covering four experts; `v0.16.0` operationalized a fifth expert, the Education Expert, and extended the activation matrix to fourteen patterns covering five experts; `v0.17.0` operationalized a sixth expert, the Product Expert, and extended the activation matrix to sixteen patterns/six axes, completing six-expert integration with no remaining narrative-only expert placeholder; `v0.18.0` consolidated the completed six-expert system without adding a new expert (an expert registry, boundary matrix, routing cheat sheet, operational-profile audit, evaluation dashboard, and maintenance guide); `v0.19.0` planned the tool-enabled future, defining Advisory Mode/Verified Knowledge Mode/Execution Mode and a Graceful Fallback Principle without implementing any tool; `v0.20.0` specified, added a result schema for, exemplified, and evaluated expected behavior for a GAUSS environment-detection tool (tool spec, result schema, five synthetic examples, eight evaluated benchmark prompts) without implementing it; `v0.21.0` implemented the first real, read-only GAUSS tooling capability, environment detection (`scripts/gauss_environment_check.py`), with a newest-version default selection rule and user-override support, manually verified against real GAUSS 24/25/26 installations; `v0.22.0` specified, schema'd, exemplified, and evaluated the second read-only GAUSS tooling capability, package inspection (`tools/gauss_package_inspection.md`, `schemas/gauss_package_inspection.schema.json`, five synthetic examples, `27.x` benchmarks 8/8 at 4.0), deferring implementation to `v0.23.0`. See [ROADMAP.md](ROADMAP.md) for full milestone history.

## Try The GAUSS Code Assistant

Start with the Code Assistant materials:

* [Code Assistant README](agents/code-assistant/README.md)
* [Code Assistant Quickstart](agents/code-assistant/QUICKSTART.md)
* [Code Assistant examples](examples/code-assistant/README.md)

The assistant can be tried manually by providing the Code Assistant prompt, agent specification, task mode guidance, and relevant expert or workflow context files. The quickstart explains which files to include for common tasks such as debugging GAUSS code, translating from Python/R/MATLAB, reviewing package APIs, explaining matrix code, and generating tests.

## How GAUSS AI Reduces Hallucinations

GAUSS AI is designed to reduce plausible but invalid code by combining source hierarchy, expert guidance, and benchmark evaluation:

* Official GAUSS documentation is the highest authority for syntax, arguments, return values, examples, and version behavior.
* Command categories help discover candidate native GAUSS commands and procedures.
* Command-specific documentation is required before giving exact production-ready syntax.
* Curated command notes are short convenience references, not a replacement for official documentation.
* Benchmark evaluations test known AI failure modes, including cross-language syntax contamination and hallucinated functions.
* Generated code should still be reviewed, verified, and tested before production use.

## Evaluation

Evaluation materials are organized into reusable benchmark prompts and completed evaluation records:

* [Benchmark prompts](evaluations/benchmark-prompts.md) define the reusable test suite.
* [Scoring rubric](evaluations/scoring.md) defines how responses are evaluated.
* [Benchmark coverage](evaluations/benchmark-coverage.md) tracks which prompts have been evaluated.
* [Evaluation run index](evaluations/runs/INDEX.md) summarizes completed manual runs.

Benchmark prompts describe what should be tested. Evaluation runs record how a specific assistant response performed at a point in time.

## Expert System References

The six-expert system is documented and cross-referenced across several consolidation documents, added in `v0.18.0`:

* [Expert registry](experts/EXPERT_REGISTRY.md) — each expert's identity, ownership, activation triggers, escalation targets, and operational status in one place.
* [Expert boundary matrix](experts/EXPERT_BOUNDARY_MATRIX.md) — what each expert owns, does not own, and the recurring false-equivalence traps between experts.
* [Expert routing workflow](workflows/expert-routing.md) — the authoritative, detailed routing workflow: activation matrix, decision rules, output contract, and worked examples.
* [Expert routing cheat sheet](workflows/expert-routing-cheatsheet.md) — a compact summary of the routing workflow for quick orientation.
* [Expert system maintenance guide](workflows/expert-system-maintenance.md) — how to add, retire, or rename an expert, update routing, and keep documentation consistent.
* [Evaluation dashboard](evaluations/EVALUATION_DASHBOARD.md) — a snapshot of benchmark category status, guard results, and known warnings across the expert system.

These documents summarize and cross-reference existing expert behavior; none of them implement runtime routing or orchestration. Routing remains documented and manually evaluated.

## GAUSS Tooling References

`v0.19.0`-`v0.23.0` moved the GAUSS Code Assistant from strategy toward tool-enabled capabilities, one at a time. Environment detection and package inspection are both implemented:

**Environment detection (`v0.21.0`) — implemented:**

* [v0.21.0 planning doc](planning/v0.21.0-gauss-environment-detection-implementation.md) — implementation scope, the newest-version default selection rule, detection strategy, and testing approach.
* [GAUSS environment check tool spec](tools/gauss_environment_check.md) — the `gauss_environment_check` tool's full contract, marked implemented.
* [GAUSS environment check helper](scripts/gauss_environment_check.py) — the read-only implementation: a CLI (`--preferred-executable-path`, `--preferred-version`, `--strict`, `--json`, `--validate-schema`, `--self-test`, and more) and an importable `detect_environment(...)` function.
* [GAUSS environment check result schema](schemas/gauss_environment_check.schema.json) — validates the tool's structured output shape; the helper's output conforms to it.
* `26.x` GAUSS Environment Detection Tool benchmark category (8/8 passed at 4.0).

**Package inspection (`v0.23.0`) — implemented:**

* [v0.23.0 planning doc](planning/v0.23.0-gauss-package-inspection-implementation.md) — implementation scope, the version-specific package context rule, package discovery strategy, and testing approach.
* [v0.22.0 planning doc](planning/v0.22.0-gauss-package-inspection-tool.md) — the original package-inspection scope, statuses, and input/output contract this implementation builds on.
* [GAUSS package inspection tool spec](tools/gauss_package_inspection.md) — the `gauss_package_inspection` tool's full contract, marked implemented.
* [GAUSS package inspection helper](scripts/gauss_package_inspection.py) — the read-only implementation: a CLI (`--environment-result`, `--executable-path`, `--gauss-version`, `--requested-package`, `--package-search-path`, `--allow-metadata-query`, `--strict`, `--json`, `--validate-schema`, `--self-test`, and more) and an importable `inspect_packages(...)` function.
* [GAUSS package inspection result schema](schemas/gauss_package_inspection.schema.json) — validates the tool's structured output shape; the helper's output conforms to it.
* [Example outputs](examples/tools/) — five synthetic package-inspection results (complete, missing, partial, unavailable, unknown), alongside the five environment-detection examples in the same directory.
* `27.x` GAUSS Package Inspection Tool benchmark category (8/8 passed at 4.0).

[Evaluation dashboard](evaluations/EVALUATION_DASHBOARD.md) — includes both the `26.x` and `27.x` benchmark categories.

Package inspection depends on environment detection (it uses the selected GAUSS executable/version as context and never re-detects GAUSS itself) but is a separate capability. Package availability may differ by GAUSS version, and the implementation never mixes package results across GAUSS versions. Neither capability runs user GAUSS code, installs packages, activates Execution Mode, or implements runtime orchestration. A `found`/`execution_candidate` result, and any package `installed: true` status, is a prerequisite signal only — never proof that code executed, that syntax is valid, or that a method is appropriate.

## Limitations

See [known limitations](KNOWN_LIMITATIONS.md) for the current constraint list.

At this stage:

* The framework does not yet execute GAUSS code.
* A local-first retrieval prototype and evidence schema exist (`scripts/command_doc_lookup.py`, `schemas/command_lookup_evidence.schema.json`), but they remain a small, heuristic, local-only prototype, not a production retrieval system.
* Benchmark coverage is growing but not exhaustive.
* Exact command syntax should be verified against official GAUSS documentation when it has not already been verified.
* The Code Assistant Preview is not a claim of production readiness.

## Vision

Large language models have become remarkably capable programming assistants, but they often struggle with domain-specific languages like GAUSS. Generic coding assistants frequently hallucinate syntax, recommend nonexistent functions, or ignore established programming conventions.

The goal of GAUSS AI is to build a framework that combines authoritative GAUSS knowledge with structured reasoning and evaluation to produce reliable, explainable, and maintainable AI assistants for the GAUSS ecosystem.

## Guiding Principles

* **Accuracy over confidence.** When uncertain, retrieve authoritative information instead of guessing.
* **Official sources first.** Prefer the official GAUSS documentation and vetted reference repositories.
* **Specialization beats generalization.** Small, focused agents are easier to improve than one large, general-purpose assistant.
* **Reusable architecture.** Expertise, knowledge, prompts, tools, and evaluations should be shared across agents whenever possible.
* **Continuous evaluation.** Every improvement should be measurable using benchmark tasks and scoring criteria.

## Planned Agents

* GAUSS Code Assistant
* GAUSS Code Reviewer
* GAUSS Documentation Writer
* GAUSS Blog Writer
* GAUSS Package Developer
* GAUSS Econometrics Advisor
* GAUSS Customer Support Assistant

## Shared Knowledge Sources

The framework is designed to use multiple authoritative sources, including:

* Official GAUSS documentation
* GAUSS LLM reference repositories
* GAUSS programming examples
* GAUSS blog examples
* Internal coding standards
* Common AI failure patterns
* Package source code

## Repository Organization

* `agents/` — Agent definitions, behavior, capabilities, and constraints.
* `experts/` — Domain-specific reasoning, best practices, knowledge notes, and common mistakes shared across agents.
* `adr/` — Architecture Decision Records for significant framework decisions.
* `prompts/` — Shared system, developer, and task prompts.
* `configs/` — Knowledge source configuration and runtime settings.
* `tools/` — Tool definitions and integrations.
* `workflows/` — Repeatable workflows and playbooks.
* `evaluations/` — Benchmarks and scoring rubrics.
* `benchmarks/` — Benchmark datasets and evaluation results.
* `examples/` — Representative tasks and reference interactions.

Expert modules encapsulate reusable domain expertise so multiple specialized agents can draw on consistent reasoning patterns and best practices without duplicating guidance.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for milestone-level planning. The current target is `v0.23.0`, GAUSS Package Inspection Implementation, which implements the already-specified `gauss_package_inspection` tool as a real, read-only helper (`scripts/gauss_package_inspection.py`) — GAUSS code execution, package installation, and runtime orchestration remain unimplemented, and Advisory Mode remains the assistant's fully-supported default regardless of package status.

### Phase 1

* Build the GAUSS Code Assistant.
* Connect authoritative knowledge sources.
* Develop benchmark evaluations.
* Improve prompt engineering.

### Phase 2

* Add retrieval and tool integrations.
* Support package-aware development.
* Add automated code review.
* Improve testing and validation.

### Phase 3

* Introduce specialized agents.
* Support collaborative multi-agent workflows.
* Integrate with GAUSS development tooling.
* Expand automated documentation generation.
