# Evaluation Result

Date: 2026-10-12
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. The session did not read the planning doc or PROJECT_STATUS.md until all fifteen tasks were done. (It did read validator source during 73.10 and 73.14, to locate the defects it had just observed.)
Agent Version: v0.83.0 (released; tag `v0.83.0`, commit `2740519`; HEAD `a6f2b80`), editable install of this checkout
Prompt ID: 73.14
Prompt Category: Verdict Explanations and Search Recall (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.83.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Sessions 98c14f4dc5634f7986b9b2c878a320b1 (task) and 95a04cf34fe745fb8e0840303f549b55 (the client's `fakeinverse` probe). The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs.
Prompt Text:

"Compute the determinant of a 3x3 matrix and print it with a label like "det = ..."."

Attempt 1 (the client's first answer, exactly as asked):
```gauss
x = { 3 2 1, 0 1 -2, 1 3 4 };
d = det(x);
print "det = " d;
```

Attempt 2 (a diagnostic by the client: only the string changed):
```gauss
x = { 3 2 1, 0 1 -2, 1 3 4 };
d = det(x);
print "determinant: " d;
```

Attempt 3 (the client's safety probe):
```gauss
x = { 3 2 1, 0 1 -2, 1 3 4 };
d = det(x);
f = fakeinverse(x);
print "fakeinverse = " f;
```

Captured output (abridged, verbatim fields):
```
search_docs("det") -> "grounded"; det.rst
attempt 1 -> "not_ready"; reason: the no-documented-calls reason; called_symbols []; user_defined_symbols ["d","det","x"]
attempt 2 -> "handoff_candidate"; called_symbols ["det"]
attempt 3 -> "review_required"; reason "validation coverage is partial (incomplete: signatures partial) ...";
             called_symbols ["det"]; user_defined_symbols ["d","f","fakeinverse","x"]; unknown_symbols [];
             coverage.symbol_check "complete"; coverage_gaps []
```

Post-run diagnosis (direct `validate_code` plus the internals):
```
_ASSIGNMENT_TARGET_RE.findall(_strip_comments_for_analysis(attempt 1)) -> ['x', 'd', 'det']
attempt 3 call_validations: det documented=True signature_known=True;
                            fakeinverse documented=False signature_known=False
```
`validate_code` (`gauss_conversation_engine.py:1909-1916`) collects user-defined names with `_ASSIGNMENT_TARGET_RE` over code with comments stripped but **strings not masked**, so the `det =` inside `"det = "` counts as an assignment to `det`. Every name in that set is then dropped from `called_symbols`, and so from the unknown-symbol check. `compute_coverage_gaps` lists signature gaps only for **documented** calls, so the undocumented `fakeinverse` produces no gap at all.

Supplementary probes (recording session, direct `validate_code`):

| Snippet | Verdict | Note |
|---|---|---|
| attempt 3 without the string label | **not_ready** | `unresolved/unsupported call symbol(s): fakeinverse` (correct) |
| `f = fakeinverse(x); print "fakeinverse = " f;` (sole call) | not_ready | for the wrong reason ("no documented call") |
| `x = {1 2, 2 1}; y = invpd(x); print "invpd = " y;` | not_ready | precondition still VIOLATED, but the first reason is the wrong "no documented call" |
| `dos dir;` next to `print "dos = " d;` | not_ready | `os_command`; the system registry is not affected |

Expected behavior: handoff_candidate: one documented call (`det`) on a traced literal matrix. The label text is irrelevant to the verdict.

Observed behavior: **Real defect found live.** Text inside a string literal changes symbol classification. (1) The requested code is a **false not_ready** with a misleading reason, because `det` is treated as a variable. (2) More seriously, the client's probe shows a **hallucinated function hidden from the unknown-symbol check**: with a `"fakeinverse = "` label, `fakeinverse` is not reported unknown, `symbol_check` claims `complete`, and the verdict softens from not_ready (correct, without the label) to review_required. Only the signature-coverage dimension, which still counts the undocumented call, stops it from going further. In no probe did it reach handoff_candidate. (3) **`coverage_gaps` was empty** while `signature_check` was `partial`, so the response named no cause. The client's statement that "a separate check came back partial" was right, but it could not see which one. Labels of the form `"name = "` are very common in GAUSS `print` statements. The client diagnosed the root cause correctly and proposed the right fix (scan with strings masked, as `_masked_statements` already does).

Pass/fail: Fail (real validator defect found live; the client's diagnosis was correct)
Defect severity: Major (wrong verdicts in both directions from string contents; defeats the unknown-symbol check, the hallucination guard, in the unsafe direction; not observed to reach handoff_candidate; `coverage_gaps` silent)
Remediation: Next milestone, first item: run the user-defined-name scan on string-masked code; list undocumented calls in `coverage_gaps`; regression tests for all four probes above; CLAUDE.md verdict diff.

Overall Score: 2.0
Decision: Fail — real defect, carried to the next milestone
