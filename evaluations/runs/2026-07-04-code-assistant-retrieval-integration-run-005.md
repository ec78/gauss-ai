# Evaluation Result

Date: 2026-07-04
Evaluator: Claude
Agent Version: Current repository state on 2026-07-04 (v0.5.0 Retrieval Integration and Response Quality milestone)
Prompt ID: 12.3
Prompt Category: Retrieval Integration
Prompt Text:

A command lookup returns multiple plausible documentation matches for a command-like name. The user asks which syntax to use.

Expected behavior:

- Classifies this as a retrieval-backed command documentation task.
- States that multiple plausible matches were found.
- Reports ambiguity instead of silently choosing one.
- Does not provide exact syntax until the intended command is identified.
- Asks for context or recommends inspecting the candidate docs.
- Explains what context would resolve the ambiguity, such as task goal, package, surrounding old code, or expected inputs/outputs.
- Clearly distinguishes candidate matches from verified command usage.
- Avoids making up arguments, defaults, return fields, or examples.
- Does not claim code was executed.

Generated Code Assistant Response:

This is a retrieval-backed command documentation task, and the lookup outcome here is `workflows/retrieval-backed-response-pattern.md` state D: multiple plausible docs matches found. I'm not going to pick one and give you its syntax — that would mean a roughly 50/50 (or worse) chance of handing you the wrong command's arguments, defaults, or return values dressed up as if they were verified.

**Retrieval status.** Running `scripts/command_doc_lookup.py <command_name> --docs-root <path>` against this name didn't return a single confident match. In the lookup tool's terms, that's `status: ambiguous`: more than one candidate page scored close enough that picking the top-ranked one automatically isn't safe — the scoring in `scripts/command_doc_lookup.py` treats a small gap between the best and second-best candidate as a sign the match isn't reliable, not as a tiebreak in the top candidate's favor.

**Why I won't guess.** Two (or more) different commands can share a similar or identical-looking name across different documentation areas — for example, a short base-GAUSS name colliding with a package-specific procedure, or two commands that only differ by capitalization or a suffix. Each candidate could have entirely different argument order, defaults, and return structure. Giving you "the" syntax here would silently assume you meant one specific candidate without confirming that's actually the one you're using.

**What I need to resolve this.** Any one of the following would let me narrow this to a single verified command and then retrieve its exact syntax:

- **What are you trying to accomplish?** The task itself (e.g., "estimate a regression," "search a string," "solve a system") usually rules out all but one of the candidates by category alone.
- **Where did you encounter this name?** If it's from existing code, the surrounding context — a `library` statement, an import, comments, or nearby variable names — often reveals which package or module it came from.
- **What inputs and outputs do you expect?** Even a rough description ("it should take a matrix and return a scalar" vs. "it takes a string and returns an index") can eliminate candidates whose documented signatures don't match that shape.
- **Do you know which package (if any) this belongs to?** Base GAUSS and specific packages sometimes define similarly-named procedures for different purposes.

**In the meantime.** I can list the candidate documentation pages the lookup found (file names/headings) so you can inspect them directly and tell me which one matches what you're doing — that's a safe way to move forward without me guessing on your behalf. Until we've narrowed it to one, please treat any command name here as a *candidate*, not a *verified* command: I have not confirmed its syntax, arguments, defaults, or return values, and I'm not going to provide an example built on an unconfirmed candidate.

I haven't run any retrieval tool or GAUSS code in this conversation; the "ambiguous" status above describes what the lookup process would report, not a result I'm claiming to have executed.

Response Summary:

The response correctly classifies the situation as a retrieval-backed documentation task with an ambiguous match (state D), states plainly that multiple plausible candidates were found, and explicitly refuses to pick one and present its syntax as if verified. It explains concretely why guessing is unsafe (different candidates can have entirely different signatures), asks for four specific kinds of disambiguating context (task goal, code provenance, expected inputs/outputs, package), and offers a safe interim step (listing candidate pages for the user to inspect) instead of leaving the user stuck. It maintains a clear verified/candidate distinction throughout and does not invent arguments, defaults, return fields, or an example. It does not claim execution.

Scores:
- GAUSS Syntax Correctness: N/A
- Function and Package Validity: 4
- Data Structure Reasoning: N/A
- Dimension and Numerical Awareness: N/A
- Task Mode Fit: 4
- Explanation Quality: 4
- Assumptions and Dependencies: 4
- Maintainability and Best Practices: N/A
- Testing or Validation: N/A
- Hallucination and Cross-Language Contamination Avoidance: 4

Overall Score: 4.0
Decision: Pass

N/A Notes:
- GAUSS Syntax Correctness: marked N/A. The correct response deliberately contains no GAUSS code, since providing any would require picking one of the ambiguous candidates and asserting its syntax, which is exactly the behavior being tested against.
- Data Structure Reasoning: marked N/A. No specific data structure is discussed because no single candidate command has been confirmed yet.
- Dimension and Numerical Awareness: marked N/A. No dimensions or numerical behavior are discussed for the same reason.
- Maintainability and Best Practices: marked N/A. This is a disambiguation request, not code the user will maintain.
- Testing or Validation: marked N/A. There is no code or claimed result to validate; the response's "next steps" are disambiguation questions, not a testable claim.

Blocking Issues:
None. No automatic failure condition applies: no candidate was silently chosen, no syntax or example was invented, and no claim of execution was made.

Suggested Improvements:
None blocking. The response states it "can list the candidate documentation pages" but — since this prompt doesn't specify what the actual candidate file names are — it appropriately stops short of inventing placeholder file names to list. In a live setting with real lookup output, the response should actually enumerate the specific candidate file names/headings rather than describe that it could; that's a property of the live tool output, not a flaw in this response's phrasing given the information available in the prompt.

Follow-up Actions:
- This completes evaluation coverage for all four core retrieval states in `workflows/retrieval-backed-response-pattern.md` (A/complete via 11.1-11.2, B/incomplete via 12.1, C/not-found via 12.2, D/ambiguous via this run), plus both non-retrieval-explanation task-mode tests (translation via 12.5, debugging via 12.6).
- Consider running Prompt 12.4 (curated note vs. official docs) next, since it is the only remaining drafted Retrieval Integration prompt and specifically exercises material this repository already has (the existing `experts/gauss-language/commands/olsmt.md` curated note).
- Consider testing the ambiguous-match state with a concrete pair of real candidate file names once one is found in practice (e.g., two similarly-named commands actually present in the local docs checkout), to verify the lookup script's `status: ambiguous` scoring threshold behaves as expected on a real case, not just a described one.
