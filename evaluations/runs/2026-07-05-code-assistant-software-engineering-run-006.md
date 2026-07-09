# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.14.0 Software Engineering Expert Foundation milestone)
Prompt ID: 21.7
Prompt Category: Software Engineering Expert Foundation
Prompt Text:

The user asks how to test a refactored GAUSS procedure.

Expected behavior:
- Activates Software Engineering Expert.
- Activates GAUSS Language Expert if GAUSS-specific testing or syntax advice is given.
- Suggests comparing old vs new outputs on representative inputs.
- Suggests edge cases, missing/empty data checks, dimension/shape checks, and regression checks.
- Suggests keeping expected outputs for known examples.
- Does not claim tests were run.
- Does not require new tooling unless clearly optional.
- Labels any unverified syntax or pseudocode clearly.

Concrete prompt used: "I refactored a GAUSS procedure into smaller helper procedures. How should I test that I did not change the behavior?"

Evidence/context used: No command-specific evidence file was required — the illustrative comparison snippet uses only baseline GAUSS language syntax (`proc`/`endp`, `if`, `abs`, `print`) already established across this evaluation suite (Prompts 1.2, 6.1, 9.1) rather than any command requiring official-doc-backed evidence. No specific procedure code was provided by the user, so the illustrative example is explicitly framed as a placeholder pattern.

Generated Code Assistant Response:

Since you split one procedure into several helper procedures, the question to answer is: does calling the new set of procedures on the same input produce the same output as the old single procedure did? That's a direct old-vs-new comparison, and it doesn't require any special testing framework — a plain GAUSS script that calls both versions and compares the results is enough.

**Basic comparison pattern** (illustrative — swap in your actual procedure names and signatures, since you didn't paste the code):

```gauss
/*
** Illustrative comparison pattern, not verified against your
** specific procedure signatures — adapt names/arguments to match.
*/
oldResult = oldProcedure(x);
newResult = newProcedureWrapper(x);   /* calls your new helper procedures internally */

if abs(oldResult - newResult) < 1e-8;
    print "Match: old and new results agree.";
else;
    print "MISMATCH: old and new results differ.";
    print "old:" oldResult;
    print "new:" newResult;
endif;
```

I haven't run this — I don't have your actual procedures or data — but the pattern is: keep the old version around (even temporarily, under a different name) just long enough to compare against, run both on the same inputs, and check the difference is within a small numeric tolerance rather than checking for bit-for-bit equality, since floating-point results can differ trivially even when the logic is unchanged.

**Inputs worth testing, roughly in order of value:**

1. **A representative "normal" case** — the kind of input the procedure handles most often. This is your baseline confidence check.
2. **A known-answer case** — an input small enough that you can hand-compute (or already know) the correct output, so you're not just comparing old-vs-new but confirming both are actually right.
3. **Edge cases specific to what changed** — since you decomposed into helpers, pay particular attention to whatever now passes between them: an empty input, an input that's entirely missing values, and a single-row/minimal-size input, since these are the shapes most likely to break when logic that used to be inline gets split across procedure boundaries.
4. **Dimension/shape checks** — confirm each new helper procedure returns the shape you expect (e.g., same rows as the input, or a scalar where the old code produced one) rather than silently returning a transposed or wrongly-shaped result.
5. **A regression check you keep** — save the known-answer case's expected output somewhere (a comment, a small companion script, or a saved value) so that the *next* time you change this code, you have something concrete to re-check against instead of re-deriving "was this ever right" from scratch.

None of this requires new tooling — a script that runs both versions and prints a pass/fail comparison is sufic­ient. If you already have a test runner or convention in this codebase, use that instead; I'm not recommending you add one just for this.

Response Summary:

The response gives a direct old-vs-new comparison strategy with a labeled illustrative (not verified-signature) code pattern using only baseline GAUSS syntax, explicitly states the comparison was not actually run, and lays out a risk-ordered list of inputs to test: representative case, known-answer case, edge cases (empty, all-missing, single-row) specifically tied to what changed in the decomposition, dimension/shape checks, and a kept regression check for future changes. It explicitly says no new tooling is required beyond what the user already has. The GAUSS Language Expert activates lightly and correctly, contributing only the baseline-syntax comparison pattern with an explicit "not verified against your specific signatures" label, while the Software Engineering Expert owns the test-strategy reasoning (what to test, in what order, and why).

Scores:
- GAUSS Syntax Correctness: 4
- Function and Package Validity: 4
- Data Structure Reasoning: N/A
- Dimension and Numerical Awareness: 4
- Task Mode Fit: 4
- Explanation Quality: 4
- Assumptions and Dependencies: 4
- Maintainability and Best Practices: 4
- Testing or Validation: 4
- Hallucination and Cross-Language Contamination Avoidance: 4

Overall Score: 4.0
Decision: Pass

N/A Notes:
- Data Structure Reasoning: marked N/A. The comparison pattern operates on a generic input with no matrix/DataFrame/array/structure distinction central to the question.

Blocking Issues:
None. No claim that the tests were run; the illustrative code is clearly labeled as an unverified placeholder pattern.

Suggested Improvements:
None blocking. If the user's procedure returns a structure (as many GAUSS statistical procedures do, e.g. `glmOut`), the comparison would need to check specific fields rather than a single `abs()` difference — worth noting as a variant once the user shares their actual return type.

Follow-up Actions:
- Confirms the Software Engineering Expert gives concrete, risk-ordered testing guidance without ever claiming a test was executed, and that the GAUSS Language Expert's light-touch activation (a labeled, unverified-signature illustrative pattern) stays clearly distinguishable from a verified-syntax claim.
- Proceed to 21.5 (Software Engineering does not override GAUSS evidence) next per the planned run order.
