# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.10.0 Evidence Coverage and Routing Regression Guards milestone)
Prompt ID: 17.5
Prompt Category: Evidence Coverage and Tracking Guards
Prompt Text:

The user asks why `scripts/check_evaluation_tracking.py --strict` fails even though the default tracking check passes.

Expected behavior:
- Reports default mode passes with 0 errors and 2 warnings.
- Explains strict mode promotes warnings to failures.
- Names the two documented warnings:
  - historical 2.2 → run-001 internal Prompt ID 2.3 mismatch
  - unindexed v0.3.0 smoke-test file predating the Prompt ID tracking system
- Explains these are historical/documented states, not current blockers.
- Does not silently recommend rewriting old run files.
- Clearly distinguishes errors from warnings.

Concrete prompt used: "Why does scripts/check_evaluation_tracking.py --strict fail even though the default tracking check passes?"

Evidence/context used: Live execution of `python scripts/check_evaluation_tracking.py` and `python scripts/check_evaluation_tracking.py --strict` against the current repository state (run immediately before drafting this response). At this point, run files for Prompts 17.6, 17.1, 17.2, and 17.3 (run-001 through run-004) already exist on disk from earlier in this same evaluation batch, but `evaluations/benchmark-coverage.md` and `evaluations/runs/INDEX.md` have not yet been updated to reference them (that update is a later step in this batch, not yet performed).

Generated Code Assistant Response:

Default mode passes with 0 errors, but right now it reports 12 warnings, not 2 — I'll explain both the 2 that are genuinely long-standing/documented and the other 10 that are specific to the current mid-evaluation-batch state, since conflating them would be misleading.

**The two documented, historical warnings** (present regardless of what's currently in progress):
1. `benchmark-coverage.md` links Prompt 2.2 to `2026-06-30-code-assistant-manual-run-001.md`, but that run file's own `Prompt ID:` field states 2.3 — a documented historical mismatch, explained in `benchmark-coverage.md`'s own notes for that row and predating stable Prompt ID assignment.
2. `2026-07-01-code-assistant-smoke-test-v0.3.0.md` exists under `evaluations/runs/` but is referenced by neither `benchmark-coverage.md` nor `runs/INDEX.md` — a legacy onboarding smoke test that predates the Prompt-ID-based tracking system entirely and was never meant to be indexed into it.

**The other 10 warnings right now are transient, not historical:**
- 6 of them are "Prompt 17.x is Not Run and belongs to the current active category" warnings — expected, since Prompts 17.1-17.6 were just added and haven't all been evaluated and tracked yet.
- 4 of them are "run file exists but is not referenced by benchmark-coverage.md or runs/INDEX.md" warnings for `run-001` through `run-004` — expected, since this evaluation batch creates all six 17.x run files first and updates `benchmark-coverage.md`/`runs/INDEX.md` afterward, as a separate step. Once that tracking update happens, these 4 warnings (and the remaining 2 "Not Run" warnings for 17.4/17.5 once they're tracked) should disappear.

So, at any point in time, `--strict` fails whenever there are *any* warnings, whether historical/documented or transient/expected, because `--strict`'s entire purpose is to promote every warning to a failure with no exceptions — that's a deliberate design choice (documented in `scripts/README.md`), not a bug. Default mode is the release-health gate and only fails on actual errors (0 right now); `--strict` is a stricter, zero-tolerance check that will fail during normal, expected states like "prompts just added but not yet run" or "run files created but not yet indexed," in addition to failing on the two truly historical warnings.

To be clear about severity: **errors** mean something structurally broken (a missing coverage row, a dangling reference, mismatched required fields) and are always 0 right now. **Warnings** mean something worth a human's attention but not necessarily wrong — including intentionally-accepted historical mismatches and normal in-progress states like this one. I'm not recommending rewriting `2026-06-30-code-assistant-manual-run-001.md` or the `v0.3.0` smoke-test file to make these warnings disappear — both are already documented exceptions, and "fixing" them by editing old run files would be worse than leaving them as-is with an explanation.

Response Summary:

The response reports the true current warning count (12, not the "2" figure written into this benchmark prompt's original expected-behavior text) and explains why: 2 are the long-standing documented historical warnings, and 10 are specific to this exact moment in a multi-step batch (four run files created but not yet indexed, six prompts added but not yet all tracked). It names both historical warnings by their real content, explicitly separates errors from warnings, states that `--strict` promotes every warning without exception (not just the two "known" ones), explains this is expected/by-design rather than a defect, and explicitly declines to recommend rewriting old run files to silence the historical warnings.

Scores:
- GAUSS Syntax Correctness: N/A
- Function and Package Validity: N/A
- Data Structure Reasoning: N/A
- Dimension and Numerical Awareness: N/A
- Task Mode Fit: 4
- Explanation Quality: 4
- Assumptions and Dependencies: 4
- Maintainability and Best Practices: N/A
- Testing or Validation: 4
- Hallucination and Cross-Language Contamination Avoidance: N/A

Overall Score: 4.0
Decision: Pass

N/A Notes:
- GAUSS Syntax Correctness, Data Structure Reasoning, Dimension and Numerical Awareness, Maintainability and Best Practices, Hallucination and Cross-Language Contamination Avoidance: marked N/A. This prompt concerns evaluation-tracking tooling behavior, not GAUSS code, data structures, or cross-language content.
- Testing or Validation: scored (not N/A) at 4, since actually running the guard script in both modes and reporting the true current output is itself the correct validation behavior for this prompt.

Blocking Issues:
None. The discrepancy between the prompt's originally-written "2 warnings" expectation and the actual 12 observed at this exact point in the batch is a benchmark-authoring artifact (the prompt was drafted assuming a state where 17.x prompts and run files were fully tracked already), not a defect in the response — the response handles it correctly by reporting the true state and explaining the gap rather than reciting the stale figure.

Suggested Improvements:
- Same recommendation as noted in the 17.6 run file: consider revising this benchmark's "Expected behavior" text in a future non-evaluation task to describe the 2 historical warnings as a floor/minimum rather than an exact count, since the true count depends on which other prompts happen to be mid-evaluation at the time this benchmark runs. Not changed here, since evaluation runs must not modify benchmark prompt wording.

Follow-up Actions:
- Proceed to 17.4 (tracking guard catches missing coverage row) next per the planned run order.
- Confirm after Task A/B (INDEX.md and benchmark-coverage.md updates) that the 4 orphaned-run-file warnings and the remaining "Not Run" warnings for 17.1-17.6 all clear, leaving only the 2 genuinely historical warnings — this is the expected post-update outcome described in this batch's own instructions.
