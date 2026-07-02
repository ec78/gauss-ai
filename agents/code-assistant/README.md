# GAUSS Code Assistant

The GAUSS Code Assistant is the framework's specialized agent for helping users write, debug, translate, explain, review, refactor, optimize, document, and test GAUSS code.

## Core Files

- [AGENT.md](AGENT.md) defines the agent role, responsibilities, and operating principles.
- [task_modes.md](task_modes.md) defines supported task modes and response patterns.
- [QUICKSTART.md](QUICKSTART.md) explains how to try the assistant manually.
- [Code Assistant examples](../../examples/code-assistant/README.md) provide representative manual trials.

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
- [GAUSS Language Body of Knowledge](../../experts/gauss-language/BODY_OF_KNOWLEDGE.md) for GAUSS reasoning patterns and failure modes.
- [Command categories](../../experts/gauss-language/COMMAND_CATEGORIES.md) for native command discovery.
- [Curated command notes](../../experts/gauss-language/commands/README.md) for short verified notes when available.
- [Benchmark prompts](../../evaluations/benchmark-prompts.md) and [benchmark coverage](../../evaluations/benchmark-coverage.md) for tested behaviors.

Command categories are for discovery. Official command-specific documentation remains the source of truth for exact syntax, inputs, outputs, examples, and return behavior.

## Relationship To The GAUSS Language Expert

The Code Assistant uses the GAUSS Language Expert for syntax, data structures, procedures, packages, public APIs, debugging, optimization, documentation, and AI failure-mode guidance.

The expert module is reusable knowledge. The Code Assistant prompt is runtime behavior guidance. Benchmark runs are evidence of behavior, not source-of-truth documentation.

## Evaluation

Manual evaluations are tracked in:

- [benchmark prompts](../../evaluations/benchmark-prompts.md)
- [scoring rubric](../../evaluations/scoring.md)
- [evaluation run index](../../evaluations/runs/INDEX.md)
- [benchmark coverage tracker](../../evaluations/benchmark-coverage.md)

These files show what has been tested and where coverage is still incomplete.

## Trust And Verification

The assistant should not invent GAUSS syntax, commands, packages, or APIs. Native command categories identify candidate commands, but command-specific documentation verifies exact usage. If exact syntax is not verified, the assistant should say so and avoid presenting the code as production-ready. Generated code should be reviewed, tested, and checked against official GAUSS documentation before production use.

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
- Preview materials are still being refined for `v0.3.0`.

See [known limitations](../../KNOWN_LIMITATIONS.md) for current constraints before broader use.

## Related Workflows

- [Code Assistant response workflow](../../workflows/code-assistant-response.md)
- [Native command selection](../../workflows/native-command-selection.md)
- [Command documentation retrieval](../../workflows/command-documentation-retrieval.md)
- [Manual evaluation](../../workflows/manual-evaluation.md)
- [Knowledge loading](../../workflows/knowledge-loading.md)

## Roadmap

`v0.3.0` focuses on making the Code Assistant understandable and usable by people who were not part of the design process. Later milestones focus on retrieval prototypes, expanded benchmarks, and automated evaluation support. See the project [roadmap](../../ROADMAP.md) and the [v0.3.0 preview plan](../../planning/v0.3.0-code-assistant-preview.md).
