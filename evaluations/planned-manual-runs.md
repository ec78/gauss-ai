# Planned Manual Runs

This file lists suggested manual evaluations after the `v0.2.0` knowledge and evaluation foundation. Completed runs are tracked in `evaluations/runs/INDEX.md` and `evaluations/benchmark-coverage.md`.

## Planned Runs

| Prompt ID | Category | Benchmark Name | Why This Should Be Tested Next | Specific Scoring Risks to Watch For | Planned Run File |
|---:|---|---|---|---|---|
| 1.1 | Code Generation | Matrix summary procedure | Adds another core code generation case beyond string parsing. | Invalid `proc ... endp` structure, hallucinated summary helpers, Python/R/MATLAB contamination, unclear output shape. | `2026-07-01-code-assistant-manual-run-016.md` |
| 1.3 | Code Generation | DataFrame cleaning script | Expands DataFrame and missing-value workflow coverage. | Pandas/R method contamination, unsupported DataFrame APIs, unclear script versus procedure boundaries. | `2026-07-01-code-assistant-manual-run-017.md` |
| 6.2 | Refactoring | Control structure defaults | Covers reusable GAUSS API design and control-structure default patterns. | Invented structure syntax, unstable public APIs, generic refactoring advice, missing default behavior. | `2026-07-01-code-assistant-manual-run-018.md` |
| 7.2 | Optimization | String processing efficiency | Extends string coverage into repeated `strlen`/`strindx` performance behavior. | Proposing unavailable regex/Python APIs, changing `strindx == 0` semantics, premature optimization, no validation. | `2026-07-01-code-assistant-manual-run-019.md` |
| 10.2 | Design Guidance | Beginner vs advanced response | Tests audience adaptation for the same GAUSS debugging issue. | Same answer for both audiences, weak dimension debugging steps, language contamination, hallucinated functions. | `2026-07-01-code-assistant-manual-run-020.md` |

## Notes

- Do not rerun Prompt 4.3 unless new `olsmt` documentation retrieval behavior changes materially.
- Use the standard template in `workflows/manual-evaluation.md`.
- Update `evaluations/runs/INDEX.md` and `evaluations/benchmark-coverage.md` after each completed run.
