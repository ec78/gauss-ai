# GAUSS AI Agent Framework

This repository is a starter framework for building, configuring, evaluating, and iterating on GAUSS-focused AI agents.

The project is organized around a few core areas:

- `agents/` - Agent definitions, behavior notes, capabilities, and operating constraints.
- `prompts/` - Shared system, developer, and task prompt templates.
- `configs/` - Configuration files for knowledge sources, retrieval, tools, and runtime settings.
- `tools/` - Tool definitions, wrappers, adapters, and integration notes.
- `workflows/` - Repeatable agent workflows and task playbooks.
- `evaluations/` - Benchmark prompts, scoring rubrics, and evaluation runs.
- `benchmarks/` - Benchmark datasets, suites, and result artifacts.
- `examples/` - Example tasks, transcripts, and reference agent runs.

External source content has not been added yet. Knowledge sources are represented with placeholder paths in `configs/knowledge_sources.yaml`.

## Getting Started

1. Define the first agent in `agents/code-assistant/AGENT.md`.
2. Refine the shared behavior in `prompts/system_prompt.md`.
3. Add real knowledge source paths to `configs/knowledge_sources.yaml`.
4. Expand benchmark prompts and scoring criteria in `evaluations/`.
5. Add examples that demonstrate expected behavior for common GAUSS tasks.

