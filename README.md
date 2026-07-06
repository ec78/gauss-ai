# GAUSS AI

**GAUSS AI** is an open architecture for building specialized AI agents that assist with GAUSS programming, econometrics, documentation, education, and product development.

Rather than creating a single, monolithic chatbot, this project defines a collection of focused agents that share a common knowledge base, evaluation framework, and development standards.

## Current Status

The project is currently working toward `v0.8.0` - Operational Expert Modules. This milestone turns expert modules from documentation/specification assets into operational components the Code Assistant explicitly routes through, starting with the GAUSS Language Expert: a reusable operational expert interface, a filled-in GAUSS Language Expert profile, a routing workflow, and Code Assistant integration, evaluated by Expert Routing benchmarks. Expert activation is internal by default and does not weaken existing retrieval/evidence requirements; only the GAUSS Language Expert is operationalized so far.

Prior milestones: `v0.2.0` established the knowledge and evaluation foundation (expert guidance, benchmark prompts, scoring rubrics, manual evaluation records, native command category discovery, and command documentation retrieval workflows); `v0.3.0` made the Code Assistant usable and evaluable for manual preview; `v0.4.0` added a local-first command documentation lookup prototype; `v0.5.0` standardized retrieval-backed response behavior across the assistant's task modes; `v0.6.0` represented command lookup evidence in a structured, versioned JSON Schema, validated that evidence mechanically, and added schema-aligned output to the retrieval prototype alongside the existing lookup format; `v0.7.0` expanded real schema-aligned command evidence coverage across varied documentation shapes and added an aggregate validator so every committed evidence example and fixture can be checked in one pass. See [ROADMAP.md](ROADMAP.md) for full milestone history.

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

See [ROADMAP.md](ROADMAP.md) for milestone-level planning. The current target is `v0.8.0`, Operational Expert Modules, which builds a routable expert layer (starting with the GAUSS Language Expert) on top of the evidence schema and validator introduced in `v0.6.0` and the broadened evidence coverage from `v0.7.0`.

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
