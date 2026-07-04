# Evaluation Result

Date: 2026-07-04
Evaluator: Claude
Agent Version: Current repository state on 2026-07-04 (v0.5.0 Retrieval Integration and Response Quality milestone)
Prompt ID: 12.2
Prompt Category: Retrieval Integration
Prompt Text:

A user found a GAUSS command name in old code and asks for exact syntax and an example. The command-specific lookup returns no matching official documentation. Can you give exact syntax and an example?

Expected behavior:

- Classifies this as a retrieval-backed command documentation task.
- States that command-specific docs were not found.
- Refuses to invent exact syntax, arguments, defaults, return fields, or examples.
- Does not pretend that category membership, old code, or memory is enough to verify syntax.
- Offers safe next steps: check spelling, check whether it is package-specific, check GAUSS version compatibility, search package/source repositories, inspect old code context, retry official docs lookup with alternate names.
- Provides high-level guidance only.
- Clearly distinguishes unverified command names from verified command usage.
- Does not claim code was executed.

Generated Code Assistant Response:

This is a retrieval-backed command documentation task, and the outcome here is `workflows/retrieval-backed-response-pattern.md` state C: official docs not found. I'm not going to give you exact syntax or an example for this command, and here's specifically why and what to try instead.

**Retrieval status.** I ran (or would run) `scripts/command_doc_lookup.py <command_name> --docs-root <path>` against the local official documentation checkout, and it returned no matching `.rst` page — no exact file-name match, no heading match, no anchor match. That means `status: not_found` in the lookup tool's terms: command-specific documentation could not be verified in this context.

**What that does — and doesn't — tell us.** Finding the command name in old code tells us it was valid *at the time that code was written*, for *some* GAUSS version or package configuration — nothing more. It doesn't confirm the command still exists, what its current argument order is, what its defaults are, or what it returns. I'm also not treating my own general knowledge of GAUSS as a substitute here: if I can't point you at a retrieved, current official source for this exact command, giving you a syntax block would just be a guess dressed up as an answer, and a wrong guess here is worse than no answer, because you'd trust it.

**Why I won't provide exact syntax or an example.** Per `workflows/command-documentation-retrieval.md`, when command-specific docs cannot be retrieved, the right move is to say so and avoid exact syntax — not to fall back on category membership, old code context, or memory as if any of those verified current behavior.

**Safe next steps, in the order I'd try them:**

1. **Check spelling and capitalization.** A single typo or an old alias can make an otherwise-real command miss an exact file-name match.
2. **Check whether it's package-specific rather than base GAUSS.** If it came from a package (not core GAUSS), its documentation likely lives in that package's own docs tree, not the base `docs_root` the lookup searched — pointing the lookup at the package's docs (if you have them locally) may resolve it.
3. **Check GAUSS version compatibility.** The command may have existed in an older GAUSS version and since been renamed, deprecated, or replaced; if you know which GAUSS version the old code targeted, that's worth checking against release notes or a changelog for that version.
4. **Search relevant package or source repositories** you have access to for the literal command name, in case it's defined in `.src`/`.e` source rather than documented in `.rst` reference pages.
5. **Inspect the old code's context** — surrounding comments, `library` statements, or `use` declarations often name the package or module the command came from, which narrows where to look next.
6. **Retry the documentation lookup with alternate spellings or likely renamed equivalents**, if the surrounding code or a changelog suggests one, rather than assuming the first guess was exactly right.

None of these steps verify exact syntax by themselves — they're ways to find the real documentation, or to confirm the command is package-specific/version-specific, so that a future lookup can succeed. Until one of them turns up an actual command-specific page (or you paste one in), I can only describe the command as "an unverified name found in old code," not as a command with confirmed usage.

**If you want to move forward now anyway:** I can help you find a verified alternative — for example, if you tell me what the old code was trying to accomplish, I can check whether a current, documented command covers that same task, and verify its syntax properly before giving you an example.

I haven't run any code or retrieval tool in this conversation; the "not found" status above describes what the lookup process would report, not a result I'm claiming to have executed.

Response Summary:

The response correctly treats this as a documentation-retrieval task that failed (state C), states plainly that command-specific docs were not found for the named command, and explicitly refuses to provide exact syntax, arguments, or an example. It draws a clear line between "this name appeared in old code" (unverified) and "this is a verified command" (not established), and does not treat category membership, old code, or general memory as sufficient verification. It offers six concrete, appropriately-ordered next steps (spelling, package-specific docs, version compatibility, source repo search, old-code context, retry with alternates) while explicitly noting that none of them substitute for actually finding the real documentation. It offers a constructive alternative (find a verified current command for the same task) instead of leaving the user with nothing. It does not claim to have executed any tool.

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
- GAUSS Syntax Correctness: marked N/A. The correct response deliberately contains no GAUSS code or syntax block, since giving one would contradict the expected "refuse exact syntax" behavior; there's nothing to check for syntax validity.
- Data Structure Reasoning: marked N/A. No specific data structure is discussed because the command itself is unverified and unnamed in terms of its actual argument/return types.
- Dimension and Numerical Awareness: marked N/A. No dimensions, conformability, or numerical behavior are discussed for the same reason.
- Maintainability and Best Practices: marked N/A. This is a retrieval-failure explanation, not code the user will maintain.
- Testing or Validation: marked N/A. There is no code or claimed result to validate; the response's "next steps" are retrieval/discovery steps, not a testable claim about a fix.

Blocking Issues:
None. No automatic failure condition applies: no invented syntax, no invented example, no return fields, and no claim that retrieval or execution was performed when it was not.

Suggested Improvements:
None blocking. The response could be marginally more concrete about what a resolved retrieval would look like (e.g., "once a match is found, I'd apply state A of the response pattern") to close the loop for the user, but this is a nice-to-have, not a gap in the required behavior.

Follow-up Actions:
- This confirms the retrieval-backed response pattern's state C (docs not found) is handled safely, completing evaluation coverage for the two "hard failure" states most likely to tempt invented syntax (state B truncation in run 003, state C absence here).
- Consider running Prompt 12.3 (ambiguous command match) next, since state D (multiple plausible matches) remains the last untested "difficult" retrieval outcome from the original four core states in `workflows/retrieval-backed-response-pattern.md`.
- Prompt 12.4 (curated note vs. official docs) remains untested and specifically exercises a scenario this repository has real material for (the existing `experts/gauss-language/commands/olsmt.md` curated note), so it's a good candidate after 12.3.
