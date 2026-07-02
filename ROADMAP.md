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

## v0.4.0: Retrieval Prototype

- Prototype local-first command documentation lookup against official GAUSS docs.
- Retrieve command-specific documentation for syntax, defaults, options, return values, and examples.
- Extract concise source-aware command notes without mirroring full documentation pages.
- Validate curated command notes against official command-specific documentation.
- Add retrieval-focused benchmarks for command lookup behavior.

## v0.5.0: Expanded Benchmark Suite and Automated Evaluation Support

- Expand benchmark coverage across GAUSS workflows and failure modes.
- Add automated or semi-automated evaluation support.
- Track benchmark regressions across prompt, expert, and retrieval changes.
