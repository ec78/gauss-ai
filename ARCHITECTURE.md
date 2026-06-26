# Architecture

## 1. Overview

This repository defines a framework for specialized GAUSS-focused AI agents. The architecture is organized around clear agent definitions, shared prompt assets, configurable knowledge sources, tool-assisted workflows, and repeatable evaluations.

The framework is intended to support agents that are narrow enough to be reliable, grounded enough to avoid unsupported answers, equipped enough to work with real project context, and evaluated often enough to improve over time.

## 2. Architectural Goals

- Build specialized agents for distinct GAUSS development and analysis tasks.
- Ground agent behavior in curated local knowledge sources and repository context.
- Keep prompts, tools, workflows, and evaluations versioned alongside the agents they support.
- Make agent behavior inspectable through explicit documentation and repeatable benchmarks.
- Support continuous iteration as new knowledge, tools, and evaluation cases are added.

## 3. Core Layers

### Agents

Agent definitions live under `agents/`. Each agent should describe its purpose, responsibilities, boundaries, expected inputs, and expected outputs. Agents should be specialized by task area rather than treated as one broad assistant for every use case.

### Shared Knowledge

Shared knowledge is configured through `configs/knowledge_sources.yaml`. Knowledge sources should point to curated local references, examples, project conventions, and other approved materials. Source content should be added intentionally and tracked clearly.

### Prompts

Prompt assets live under `prompts/`. These files define reusable system, developer, and task-level instructions. Prompts should be concise, testable, and aligned with the agent's documented purpose.

### Tools

Tool definitions and integration notes live under `tools/`. Tools extend agents beyond text generation by enabling retrieval, file inspection, validation, formatting, testing, or other controlled actions.

### Workflows

Workflow definitions live under `workflows/`. Workflows describe repeatable task patterns such as code review, debugging, documentation generation, benchmark execution, or knowledge refresh.

### Evaluations

Evaluation assets live under `evaluations/` and `benchmarks/`. They define representative prompts, scoring rubrics, benchmark suites, and result records. Evaluations should measure correctness, GAUSS fluency, repository awareness, clarity, and safety.

## 4. Agent Design Philosophy

Agents should be specialized, knowledge-grounded, tool-assisted, and continuously evaluated.

Specialization keeps each agent's behavior focused and easier to test. Knowledge grounding reduces unsupported claims and improves consistency with GAUSS conventions. Tool assistance lets agents inspect and validate real context instead of relying only on prior knowledge. Continuous evaluation creates a feedback loop for improving prompts, sources, tools, and workflows.

## 5. Knowledge Flow

Knowledge sources are configured first, then made available to agents through retrieval or context-loading workflows. Agents should prefer configured knowledge and repository files over generic assumptions.

Expected flow:

1. Curated knowledge is added to the repository or referenced by placeholder paths.
2. `configs/knowledge_sources.yaml` records each source and its purpose.
3. Workflows decide which sources are relevant for a task.
4. Agents use those sources to produce grounded answers or edits.
5. Evaluation results identify knowledge gaps that should be filled.

## 6. Tool Flow

Tools should be used when they improve accuracy, validation, or repeatability. Tool use should remain bounded by the agent's role and the user's request.

Expected flow:

1. A task enters an agent workflow.
2. The workflow determines whether tools are needed.
3. Tools inspect files, retrieve knowledge, run checks, or prepare artifacts.
4. The agent interprets tool results and produces a response.
5. Evaluation captures whether tool use improved the outcome.

## 7. Evaluation Flow

Evaluation should be part of normal agent development, not an afterthought. Benchmark prompts and scoring rubrics should evolve as the framework encounters new task types and failure modes.

Expected flow:

1. Add or update representative benchmark prompts.
2. Run the target agent against those prompts.
3. Score outputs using documented criteria.
4. Record gaps in correctness, grounding, clarity, safety, or GAUSS fluency.
5. Improve prompts, knowledge sources, tools, or workflows.
6. Re-run evaluations to confirm improvement.

## 8. Initial Architecture Diagram Using Plain Text

```text
User Task
   |
   v
Workflow Selection
   |
   v
Specialized Agent
   |
   +--> Prompts
   |
   +--> Shared Knowledge
   |       |
   |       v
   |   Configured Sources
   |
   +--> Tools
   |       |
   |       v
   |   Inspection / Retrieval / Validation
   |
   v
Agent Output
   |
   v
Evaluation
   |
   v
Prompt, Knowledge, Tool, and Workflow Improvements
```

## 9. Future Architecture Considerations

- Add additional specialized agents for documentation, testing, package migration, code review, and model comparison.
- Define source quality rules for knowledge ingestion and refresh.
- Add structured result records for benchmark runs.
- Track prompt versions and evaluation scores together.
- Introduce tool permission policies for higher-risk actions.
- Add workflows for regression testing agent behavior after prompt or source changes.
- Support agent composition where one workflow can delegate subtasks to several specialized agents.

