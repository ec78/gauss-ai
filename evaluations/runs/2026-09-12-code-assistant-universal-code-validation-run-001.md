# Evaluation Result

Date: 2026-09-12
Evaluator: Claude (v0.75.0 Validation Coverage & Universal Code Eligibility milestone)
Agent Version: Current repository state on 2026-09-12 (`v0.74.0` + in-progress `v0.75.0`)
Prompt ID: 65.1
Prompt Category: Validation Coverage & Universal Code Eligibility
Prompt Text:

"What does invpd do, and can you show a quick example?" -- deliberately phrased to avoid every `_CODE_GENERATION_KEYWORDS` trigger phrase.

Objective: confirm THE core `v0.75.0` objective -- a `QA`-classified turn whose answer contains real GAUSS code now receives the same deterministic validation/eligibility pipeline a `CODE_GENERATION` turn already gets.
Evidence source: real Ollama service, real `qwen2.5-coder:7b` model, real local GAUSS documentation checkout.
Model provider: **OllamaProvider, real local model.**

Captured output (first attempt, before a real defect was found and fixed -- see below):
```
[elapsed: 81.72s]
intent=qa
generation_policy=clarify
generated_code_blocks=1
pre_execution_eligibility=requires_clarification
pre_execution_issues=('ambiguous topic(s) remain unresolved: What does invpd do, and can you show a quick example?',)
```

**A real, live defect was found here**: the documentation-derived concept index (`gauss_doc_concept_index.py`, added in `v0.74.0`) scored the WHOLE question against every indexed page's own keyword set and found two unrelated pages (`dbqueryisforwardonly.rst`, `dbsetdatabasename.rst`) tied at the minimum overlap threshold, purely because both happen to use the ordinary English words "you"/"can" in their own second-person-styled Purpose text -- confirmed by direct reproduction: `resolve_derived_concepts(...)` returned exactly `[('dbQueryIsForwardOnly', ('can','you')), ('dbSetDatabaseName', ('can','you'))]`. This is a NEW failure mode the existing `MAX_DOC_FREQUENCY_FRACTION` safety net does not catch -- "can"/"you" appear in only 14 and 2 of 2,105 real indexed entries (well under the 5% corpus-generic threshold), so they are not corpus-generic in the statistical sense, just topically empty English filler.

**Root cause**: `_GENERIC_DOC_WORDS` in `gauss_doc_concept_index.py` was curated purely from GAUSS-documentation-prose frequency analysis (`v0.74.0`'s own `64.1` finding) and never included ordinary pronouns/modal auxiliary verbs, since those are not typically "GAUSS-domain" words. This bug existed in `v0.74.0` too, but was INERT for `QA`-classified turns before this milestone's own universal-routing fix, since `gate`/`ambiguous_topics` were never computed for `QA` intent at all -- `v0.75.0`'s own routing fix is precisely what exposed it.

**Fix**: extended `_GENERIC_DOC_WORDS` with a small, fixed, general-English pronoun/modal-auxiliary list (`you`, `your`, `yours`, `can`, `could`, `would`, `should`, `shall`, `must`, `may`, `might`, `we`, `our`, `they`, `their`, `does`, `did`) -- corpus-frequency-independent, since these words carry zero topical signal regardless of how rare they happen to be in any specific corpus. Added `test_09b_pronoun_and_auxiliary_verb_overlap_never_produces_false_ambiguity` (`test_gauss_doc_concept_index.py`) reproducing this exact case with a small synthetic fixture. Full suite re-run: no regression.

Captured output (after the fix, re-run live):
```
[elapsed: 52.47s]
intent=qa
generation_policy=supported_only
generated_code_blocks=1
pre_execution_eligibility=eligible_for_validation
pre_execution_issues=()
call_validations=[('invpd', True, 'compatible')]
precondition_checks=[('invpd', 'unverified')]
```

```gauss
// Set random seed
rndseed 90701980;

// Create a symmetric and positive definite matrix
a = { 4 2; 2 3 };

// Compute the inverse
a_inv = invpd(a);

// Display the result
print "The inverse of a is:" a_inv;
```

Expected behavior: classified `QA`; code detected; universal validation runs; eligibility computed (not left `None`).

Observed behavior: matches, after the fix. A secondary, minor, non-blocking observation: the model's own generated literal uses `;` as a row separator (`{4 2; 2 3}`), not GAUSS's real `,` row-separator convention -- this is a real, disclosed model syntax quirk (plausibly MATLAB-style cross-language contamination), not a validator defect; `_find_literal_matrix_for_argument(...)` correctly declined to guess at this non-standard literal and reported the `invpd` precondition honestly `UNVERIFIED` rather than fabricating `SATISFIED`.

Pass/fail: Pass (after the live fix)
Defect severity: Major (a real, disclosed false-ambiguity bug that would have confused a QA-route user with an incorrect "ambiguous" verdict on a perfectly fine, correctly-grounded example) -- found and fixed within this same milestone
Remediation: Done (see above)

Scores:
- Task Mode Fit: 4.0
- Explanation Quality: 3.8
- Assumptions and Dependencies: 4.0
- Testing or Validation: 4.0
- Hallucination and Cross-Language Contamination Avoidance: 3.6 (the `;`-vs-`,` row-separator quirk, disclosed above)

Overall Score: 3.9
Decision: Pass
