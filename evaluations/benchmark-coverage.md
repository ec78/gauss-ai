# Benchmark Coverage

This file tracks which benchmark prompts have been manually evaluated. Statuses use the stable Prompt IDs from `evaluations/benchmark-prompts.md`.

Some early runs predate stable Prompt ID assignment. Where a run does not match the current benchmark prompt for its recorded ID, the note explains the mismatch rather than treating it as exact coverage.

| Prompt ID | Category | Benchmark Name | Status | Latest Run | Latest Score | Notes |
|---:|---|---|---|---|---:|---|
| 1.1 | Code Generation | Matrix summary procedure | Not Run | N/A | N/A | None. |
| 1.2 | Code Generation | String parser | Not Run | N/A | N/A | None. |
| 1.3 | Code Generation | DataFrame cleaning script | Not Run | N/A | N/A | None. |
| 2.1 | Debugging | Array dimension error | Not Run | N/A | N/A | Run 002 records Prompt ID 2.1, but it evaluated a separate trimmed-`y` dimension mismatch prompt, not the current array dimension benchmark. |
| 2.2 | Debugging | String search bug | Passed | [2026-06-30-code-assistant-manual-run-001.md](runs/2026-06-30-code-assistant-manual-run-001.md) | 3.9 | Run 001 predates stable IDs and records Prompt ID 2.3, but maps by benchmark content to GAUSS string search and `strindx == 0` behavior. |
| 2.3 | Debugging | Scope and package dependency | Not Run | N/A | N/A | Run 001 records historical Prompt ID 2.3 but did not evaluate the current scope/package dependency benchmark. |
| 3.1 | Code Explanation | Beginner matrix explanation | Not Run | N/A | N/A | None. |
| 3.2 | Code Explanation | Advanced structure explanation | Not Run | N/A | N/A | None. |
| 4.1 | Code Translation | MATLAB to GAUSS | Not Run | N/A | N/A | Run 003 records Prompt ID 4.1, but it evaluated a Python string `.find()` translation, not the current MATLAB benchmark. |
| 4.2 | Code Translation | Python to GAUSS | Not Run | N/A | N/A | No completed run covers the current matrix/missing-value Python translation prompt. Run 004 records historical Prompt ID 4.2 but evaluated R regression setup. |
| 4.3 | Code Translation | R to GAUSS regression setup | Passed with Minor Revision | [2026-06-30-code-assistant-manual-run-005.md](runs/2026-06-30-code-assistant-manual-run-005.md) | 3.7 | Runs 004 and 005 evaluated this workflow; latest run 005 improved `olsmt` handling but still needed an `olsmt`-based primary example or explicit syntax retrieval. |
| 5.1 | Code Review | Review public API design | Passed | [2026-06-30-code-assistant-manual-run-006.md](runs/2026-06-30-code-assistant-manual-run-006.md) | 4.0 | Strong public/helper separation, `y`/`x`/`ctl` validation, control defaults, dependency clarity, and GAUSS-specific maintainability review. |
| 5.2 | Code Review | Review matrix and array usage | Not Run | N/A | N/A | None. |
| 6.1 | Refactoring | Procedure cleanup | Not Run | N/A | N/A | None. |
| 6.2 | Refactoring | Control structure defaults | Not Run | N/A | N/A | None. |
| 7.1 | Optimization | Loop to matrix operation | Not Run | N/A | N/A | None. |
| 7.2 | Optimization | String processing efficiency | Not Run | N/A | N/A | None. |
| 8.1 | Documentation | Procedure usage docs | Not Run | N/A | N/A | None. |
| 8.2 | Documentation | Package README section | Not Run | N/A | N/A | None. |
| 9.1 | Test Generation | Matrix procedure tests | Not Run | N/A | N/A | None. |
| 9.2 | Test Generation | String utility tests | Not Run | N/A | N/A | None. |
| 10.1 | Design Guidance | Choose data representation | Not Run | N/A | N/A | None. |
| 10.2 | Design Guidance | Beginner vs advanced response | Not Run | N/A | N/A | None. |

## Completed Runs Not Directly Covered By Current Stable Prompts

- [2026-06-30-code-assistant-manual-run-002.md](runs/2026-06-30-code-assistant-manual-run-002.md): evaluated a trimmed-`y` row-alignment dimension mismatch prompt under historical Prompt ID 2.1.
- [2026-06-30-code-assistant-manual-run-003.md](runs/2026-06-30-code-assistant-manual-run-003.md): evaluated Python `.find()` to GAUSS `strindx` translation under historical Prompt ID 4.1.
