# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.11.0 Repository Hygiene and Evaluation Policy Cleanup milestone)
Prompt ID: 18.3
Prompt Category: Repository Hygiene and Evaluation Policy Cleanup
Prompt Text:

The user asks what the benchmark-authoring guidance says about hardcoded counts in expected behavior.

Expected behavior:
- Uses `workflows/manual-evaluation.md`'s Benchmark Authoring Guidance.
- Explains benchmarks should avoid hardcoding volatile repository counts unless tied to a fixed repository state.
- Explains expected behavior should usually require reporting live tool output accurately.
- Distinguishes stable facts from volatile counts.
- Mentions the 17.5/17.6 precedent.
- Explains baseline, mid-batch, and post-update states.
- Does not weaken evaluation expectations.

Concrete prompt used: "What does the benchmark-authoring guidance say about hardcoded counts in expected behavior?"

Evidence/context used: `workflows/manual-evaluation.md`'s "## 9. Benchmark Authoring Guidance" section (added `v0.11.0`, Deliverable 3), specifically its "Avoid volatile hardcoded counts," "Prefer live tool output," "If exact counts are required," "Batch evaluation states," "Historical precedent," and "Do not weaken expectations" subsections.

Generated Code Assistant Response:

`workflows/manual-evaluation.md`'s "Benchmark Authoring Guidance" section (section 9) covers this directly.

**The core rule:** avoid hardcoding volatile repository counts — number of prompt IDs, coverage rows, run files, index entries, or warnings — in a benchmark's expected-behavior text, unless the benchmark is explicitly and permanently tied to a fixed, frozen repository state. These counts change every time a later milestone adds prompts, runs, or coverage rows, including, in the precedent case, the very act of adding the benchmark's own prompts.

**What to prefer instead:** when a benchmark evaluates a script or guard, expected behavior should usually say to run the tool, report the live output accurately, distinguish errors from warnings, and explain any discrepancy from earlier documented examples or previously-written counts — rather than requiring the response to reproduce one specific number written into the benchmark at authoring time.

**If an exact count is genuinely required:** the guidance says to state the repository state and timing the count applies to, identify whether it's a baseline/mid-batch/post-update figure, say whether transient warnings are expected at that point, and update the benchmark if the repository state changes before it's actually evaluated.

**Batch evaluation states**, explicitly distinguished: **baseline** (before any of the batch's own run files exist), **mid-batch** (some run files created but tracking not yet updated — which can add its own transient warnings, like newly-created but not-yet-indexed run files being flagged as orphaned), and **post-update** (after coverage rows and index entries are updated). A benchmark referencing tool output should say which of these it means.

**The historical precedent it cites:** `v0.10.0` Prompts `17.5` and `17.6` both hardcoded specific counts ("0 errors / 2 warnings," plus specific prompt-ID/coverage-row/run-file/index counts for `17.6`) that were only accurate before the `17.x` category itself existed and was tracked. By the time they were actually evaluated, the real warning count had risen to 8 (at the `17.6` point) and 12 (at the `17.5` point, once several of the batch's own not-yet-tracked run files existed). Both evaluations still passed at 4.0, because the responses correctly reported the true live state and explained the discrepancy instead of reciting the stale numbers — this is called out explicitly as the preferred, rewarded behavior.

**What this guidance does not mean:** it's not a license for benchmarks to become vague. Stable facts — exact file paths, expected pass/fail behavior, and required distinctions like errors vs. warnings or documented historical exceptions vs. new defects — should still be stated explicitly, since those don't drift the way a repository-wide count does. The concern is narrowly about volatile repository-state counts, not precision in general.

Response Summary:

The response accurately summarizes all six subsections of the real Benchmark Authoring Guidance section, correctly distinguishes stable facts (which should stay explicit) from volatile counts (which shouldn't be hardcoded), states the three batch-evaluation states with their real definitions, cites the `17.5`/`17.6` precedent with the real figures (8 and 12 warnings against an originally-written "2"), and explicitly addresses the "does this weaken expectations" concern by quoting the guidance's own clarification.

Scores:
- GAUSS Syntax Correctness: N/A
- Function and Package Validity: N/A
- Data Structure Reasoning: N/A
- Dimension and Numerical Awareness: N/A
- Task Mode Fit: 4
- Explanation Quality: 4
- Assumptions and Dependencies: 4
- Maintainability and Best Practices: N/A
- Testing or Validation: N/A
- Hallucination and Cross-Language Contamination Avoidance: N/A

Overall Score: 4.0
Decision: Pass

N/A Notes:
- GAUSS Syntax Correctness, Function and Package Validity, Data Structure Reasoning, Dimension and Numerical Awareness, Maintainability and Best Practices, Hallucination and Cross-Language Contamination Avoidance: marked N/A. This prompt concerns benchmark-authoring process guidance, not GAUSS code, functions, data structures, or cross-language content.
- Testing or Validation: marked N/A. This is a documentation-summary question, not a request for a validation step.

Blocking Issues:
None.

Suggested Improvements:
None blocking.

Follow-up Actions:
- Proceed to 18.4 (Econometrics knowledge.md disposition is clear) next per the planned run order.
