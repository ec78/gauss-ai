# GAUSS AI

**GAUSS AI** is an open architecture for building specialized AI agents that assist with GAUSS programming, econometrics, documentation, education, and product development.

Rather than creating a single, monolithic chatbot, this project defines a collection of focused agents that share a common knowledge base, evaluation framework, and development standards.

## Current Status

The project is currently working toward `v0.20.0` - GAUSS Environment Detection Tool. This milestone begins the transition toward a tool-enabled GAUSS Code Assistant (strategy defined in `planning/v0.19.0-gauss-tooling-strategy-and-execution-modes.md`), but it does not implement GAUSS detection, package inspection, or code execution yet — `v0.20.0` specifies, schemas, exemplifies, and evaluates expected assistant behavior only. The planned `gauss_environment_check` tool is fully specified (`tools/gauss_environment_check.md`), its result schema exists (`schemas/gauss_environment_check.schema.json`), and five synthetic example outputs cover the found, not-found, ambiguous, inaccessible, and version-unknown states (`examples/tools/`). Benchmark prompts `26.1`-`26.8` were added and evaluated against this documented expected behavior — 8/8 passed at 4.0 — confirming graceful fallback to Advisory Mode, correct treatment of `execution_candidate` as a prerequisite signal (not active execution), and protection against treating environment detection as syntax or methodology evidence. Advisory Mode remains fully supported regardless of detection outcome, and no GAUSS code is executed by any validation, tracking, or benchmark check in this framework.

Prior milestones: `v0.2.0` established the knowledge and evaluation foundation (expert guidance, benchmark prompts, scoring rubrics, manual evaluation records, native command category discovery, and command documentation retrieval workflows); `v0.3.0` made the Code Assistant usable and evaluable for manual preview; `v0.4.0` added a local-first command documentation lookup prototype; `v0.5.0` standardized retrieval-backed response behavior across the assistant's task modes; `v0.6.0` represented command lookup evidence in a structured, versioned JSON Schema, validated that evidence mechanically, and added schema-aligned output to the retrieval prototype alongside the existing lookup format; `v0.7.0` expanded real schema-aligned command evidence coverage across varied documentation shapes and added an aggregate validator so every committed evidence example and fixture can be checked in one pass; `v0.8.0` operationalized the GAUSS Language Expert as the first expert the Code Assistant explicitly routes through; `v0.9.0` operationalized a second expert, the Econometrics Expert, and extended expert routing to four routing types (GAUSS-only, Econometrics-only, Both, Neither), with the GAUSS Language Expert owning implementation correctness and the Econometrics Expert owning methodological correctness — neither may substitute for the other; `v0.10.0` closed the local `glm` evidence gap, audited and documented GAUSS panel-estimation coverage (finding a verified command, `tscsFit`, from the commercial TSMT package), and added a local evaluation tracking consistency guard (`scripts/check_evaluation_tracking.py`); `v0.11.0` fixed stale expert-profile wording, documented a historical evaluation-tracking warning policy, added benchmark-authoring guidance, clarified a superseded expert-knowledge placeholder, and closed a command-evidence source-classification gap the schema already supported but the retrieval tool hadn't implemented; `v0.12.0` clarified the GAUSS Language Expert's `knowledge.md` placeholder, added a local release-readiness check (`scripts/check_release_readiness.py`), and documented strict-mode behavior and the `PACKAGE_DOC_DIRECTORIES` refresh process ahead of eventual CI; `v0.13.0` moved the local default release-readiness gate into CI via a minimal GitHub Actions workflow (`.github/workflows/release-readiness.yml`) that runs the default (non-strict) release-readiness check on every push and pull request; `v0.14.0` operationalized a third expert, the Software Engineering Expert, and extended expert routing to eight routing types covering every combination of the three experts; `v0.15.0` operationalized a fourth expert, the Documentation Expert, and replaced the eight-type enumeration with a compact activation matrix and common routing patterns covering four experts; `v0.16.0` operationalized a fifth expert, the Education Expert, and extended the activation matrix to fourteen patterns covering five experts; `v0.17.0` operationalized a sixth expert, the Product Expert, and extended the activation matrix to sixteen patterns/six axes, completing six-expert integration with no remaining narrative-only expert placeholder; `v0.18.0` consolidated the completed six-expert system without adding a new expert (an expert registry, boundary matrix, routing cheat sheet, operational-profile audit, evaluation dashboard, and maintenance guide); `v0.19.0` planned the tool-enabled future, defining Advisory Mode/Verified Knowledge Mode/Execution Mode and a Graceful Fallback Principle without implementing any tool. See [ROADMAP.md](ROADMAP.md) for full milestone history.

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

`v0.19.0` and `v0.20.0` are planning the first steps toward a tool-enabled GAUSS Code Assistant. As of `v0.20.0`, the environment-detection tool is fully specified, has a result schema, has example outputs, and has been evaluated against expected behavior — but is not implemented:

* [v0.20.0 planning doc](planning/v0.20.0-gauss-environment-detection-tool.md) — operating-mode relationship, detection strategy, input/output contract, and benchmark plan.
* [GAUSS environment check tool spec](tools/gauss_environment_check.md) — the `gauss_environment_check` tool's full contract (specified, not implemented).
* [GAUSS environment check result schema](schemas/gauss_environment_check.schema.json) — validates the tool's structured output shape.
* [Example outputs](examples/tools/) — five synthetic example results (found, not-found, ambiguous, inaccessible, version-unknown).
* [Evaluation dashboard](evaluations/EVALUATION_DASHBOARD.md) — includes the `26.x` GAUSS Environment Detection Tool benchmark category (8/8 passed at 4.0).

None of this implements GAUSS detection, package inspection, or code execution. A detection result of `found`/`execution_candidate` is a prerequisite signal only — it does not mean Execution Mode is active, and no GAUSS code is executed by any check in this framework.

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

See [ROADMAP.md](ROADMAP.md) for milestone-level planning. The current target is `v0.20.0`, GAUSS Environment Detection Tool, which specifies, schemas, exemplifies, and evaluates expected assistant behavior for a future read-only environment-detection tool — the tool itself remains unimplemented, and Advisory Mode remains the assistant's fully-supported default regardless of detection outcome.

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
