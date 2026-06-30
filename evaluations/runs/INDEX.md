# Evaluation Run Index

This index summarizes completed manual evaluation runs for GAUSS AI agents. Use it to see what has been tested, what passed, and what follow-up actions remain.

| Run File | Date | Prompt ID | Category | Benchmark Name | Overall Score | Decision | Main Finding | Follow-up Needed |
|---|---|---:|---|---|---:|---|---|---|
| [2026-06-30-code-assistant-manual-run-001.md](2026-06-30-code-assistant-manual-run-001.md) | 2026-06-30 | 2.3 | Debugging / String Search | String search `strpos` to `strindx` | 3.9 | Pass | Correctly replaced non-GAUSS `strpos` with `strindx` and handled not-found as `0`. | None. |
| [2026-06-30-code-assistant-manual-run-002.md](2026-06-30-code-assistant-manual-run-002.md) | 2026-06-30 | 2.1 | Debugging / Dimension Mismatch | Trimmed `y` row mismatch | 4.0 | Pass | Correctly identified row mismatch after trimming `y`, checked `rows(y)` and `rows(x)`, and avoided fake transpose fixes. | None. |
| [2026-06-30-code-assistant-manual-run-003.md](2026-06-30-code-assistant-manual-run-003.md) | 2026-06-30 | 4.1 | Code Translation / Python to GAUSS | Python `.find()` to GAUSS `strindx` | 3.9 | Pass | Translated Python string-search intent into concise GAUSS code using `strindx` and `idx == 0`. | None. |
| [2026-06-30-code-assistant-manual-run-004.md](2026-06-30-code-assistant-manual-run-004.md) | 2026-06-30 | 4.2 | Code Translation / R to GAUSS Regression Setup | R `lm()` workflow without native OLS mention | 3.7 | Needs Revision (minor) | Valid manual matrix OLS pattern, but missed `olsmt` as the preferred native high-level OLS workflow. | Update benchmark expectations and expert guidance so common statistical workflow translations check for native GAUSS procedures before manual implementations. |
| [2026-06-30-code-assistant-manual-run-005.md](2026-06-30-code-assistant-manual-run-005.md) | 2026-06-30 | 4.3 | Code Translation / R to GAUSS Regression Setup | R `lm()` workflow with `olsmt` mention | 3.7 | Pass with minor revision | Improved by mentioning `olsmt`, but still lacked an `olsmt`-based primary example or explicit retrieval step before manual OLS. | Update benchmark expectations and Code Assistant guidance so recommended native procedures get concrete examples when syntax is known, or explicit retrieval when not known. |
| [2026-06-30-code-assistant-manual-run-006.md](2026-06-30-code-assistant-manual-run-006.md) | 2026-06-30 | 5.1 | Code Review / Public API Design | `fitModel(y, x, ctl)` package API | 4.0 | Pass | Strong GAUSS-specific API review covering public/helper separation, `y`/`x`/`ctl` validation, control defaults, dependencies, and tests. | None. |

## Patterns Observed So Far

- Strong handling of GAUSS string search and `strindx == 0`.
- Strong handling of dimension mismatch and row alignment.
- Improved but still evolving handling of native GAUSS statistical procedures such as `olsmt`.
- Strong public API review behavior.
