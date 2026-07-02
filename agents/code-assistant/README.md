# GAUSS Code Assistant

The GAUSS Code Assistant is the framework's specialized agent for helping users write, debug, translate, explain, review, refactor, optimize, document, and test GAUSS code.

## Core Files

- [AGENT.md](AGENT.md) defines the agent role, responsibilities, and operating principles.
- [task_modes.md](task_modes.md) defines supported task modes and response patterns.
- [QUICKSTART.md](QUICKSTART.md) explains how to try the assistant manually.

## Supported Task Modes

- Code Generation
- Debugging
- Code Explanation
- Code Translation
- Code Review
- Refactoring
- Optimization
- Documentation
- Test Generation
- Design Guidance

## Knowledge Sources

The assistant should use:

- Official GAUSS documentation for exact syntax and behavior.
- `experts/gauss-language/BODY_OF_KNOWLEDGE.md` for GAUSS reasoning patterns and failure modes.
- `experts/gauss-language/COMMAND_CATEGORIES.md` for native command discovery.
- `experts/gauss-language/commands/` for short curated notes when available.
- `evaluations/benchmark-prompts.md` and `evaluations/benchmark-coverage.md` for tested behaviors.

Command categories are for discovery. Official command-specific documentation remains the source of truth.

## Relationship To The GAUSS Language Expert

The Code Assistant uses the GAUSS Language Expert for syntax, data structures, procedures, packages, public APIs, debugging, optimization, documentation, and AI failure-mode guidance.

The expert module is reusable knowledge. The Code Assistant prompt is runtime behavior guidance. Benchmark runs are evidence of behavior, not source-of-truth documentation.

## Evaluation

Manual evaluations are tracked in:

- `evaluations/benchmark-prompts.md`
- `evaluations/scoring.md`
- `evaluations/runs/INDEX.md`
- `evaluations/benchmark-coverage.md`

These files show what has been tested and where coverage is still incomplete.

## Safety And Accuracy Principles

- Do not invent GAUSS syntax, commands, packages, or APIs.
- Verify exact command syntax against official docs when needed.
- Treat curated command notes as convenience summaries, not authoritative documentation.
- Avoid Python, R, MATLAB, JavaScript, and pseudocode contamination.
- Distinguish matrices, DataFrames, arrays, structures, strings, scripts, procedures, packages, and public APIs.
- Use manual implementations mainly for teaching, customization, diagnostics, or when no suitable native command exists.

## Current Limitations

- The framework does not yet execute GAUSS code.
- Retrieval workflows are documented but not fully automated.
- Benchmark coverage is meaningful but not exhaustive.
- Public quickstart and preview materials are still being expanded for `v0.3.0`.

## Related Workflows

- `workflows/code-assistant-response.md`
- `workflows/native-command-selection.md`
- `workflows/command-documentation-retrieval.md`
- `workflows/manual-evaluation.md`
- `workflows/knowledge-loading.md`

## Roadmap

`v0.3.0` focuses on making the Code Assistant understandable and usable by people who were not part of the design process. Later milestones focus on retrieval prototypes, expanded benchmarks, and automated evaluation support.
