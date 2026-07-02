# Evaluation Result

Date: 2026-07-02
Evaluator: Claude
Agent Version: Current repository state on 2026-07-02 (v0.4.0 Retrieval Prototype milestone)
Prompt ID: 11.3
Prompt Category: Retrieval
Prompt Text:

A user asks: "I need a GAUSS command for a standard modeling or string-handling task. I found a command name in the command category list, but I do not have the command-specific documentation yet. Can you give me exact syntax and an example?"

Expected behavior:

- Explains that command categories are useful for discovery but are not enough for exact syntax.
- Attempts or recommends command-specific documentation retrieval before giving exact syntax.
- Does not invent syntax from category membership.
- If command-specific lookup output is unavailable, says the command must be retrieved before production-ready examples can be provided.
- Offers a safe high-level next step, such as running `scripts/command_doc_lookup.py <command> --docs-root <docs-root>`.
- Clearly distinguishes candidate command discovery from verified command usage.
- Avoids making up arguments, return fields, defaults, or examples.

Generated Code Assistant Response:

Finding a command name in `COMMAND_CATEGORIES.md` only tells us that the command is a real, category-appropriate candidate — it does not tell us its exact syntax, argument order, defaults, or return structure. Category files are a discovery index, not a documentation mirror, so I can't give you exact syntax or a working example directly from the category listing alone.

**What category membership does and doesn't verify.** If the command shows up under a category such as Estimation/Modeling or String Handling in `COMMAND_CATEGORIES.md`, that confirms it's a legitimate native GAUSS command worth considering instead of custom code. It does not confirm the argument list, optional arguments, control-structure fields, return-value structure, or missing-value handling — those can only come from the command-specific documentation page.

**What I need before giving exact syntax.** Before I can give you production-ready syntax and an example, I need to retrieve the command-specific documentation for the exact command name you found. Two ways to get that:

1. If you tell me the exact command name, I can attempt a local documentation lookup myself using the retrieval prototype:

   ```text
   python scripts/command_doc_lookup.py <command_name> --docs-root <path to local official GAUSS docs>
   ```

   This searches for a matching `.rst` page (by exact file name, heading, or anchor) and extracts the documented syntax (`.. function::` format lines), inputs/parameters, return/output fields, control-structure fields, formula behavior, missing-value notes, and examples if present. If it finds a confident match, I can then give you a verified syntax block and example. If it can't find the command's page, or the match is ambiguous, it reports that clearly instead of guessing — and so would I.

2. Alternatively, check `experts/gauss-language/commands/` for a short curated note. A small number of high-value, frequently used commands (for example `olsmt`) have a short verified note there, citing the official `.rst` source and last-verified date. That's a convenience cache, not a replacement for the official page — if it ever conflicts with official docs, the official docs win.

**Until one of those succeeds, I will not give you exact syntax, a full argument list, default values, return fields, or a runnable example** for this command, because doing so from category membership alone would risk inventing details that don't match the real command. That would violate the rule against guessing GAUSS syntax and could hand you code that fails at runtime with no verified basis.

**What I can safely say right now:**
- The command is a legitimate candidate for your task based on its category.
- It should be preferred over a manual/custom implementation for standard workflows once its syntax is verified (per `workflows/native-command-selection.md`).
- I have not yet verified its parameter names, argument order, optional arguments, defaults, return structure, or missing-value behavior.

**Next step:** tell me the exact command name (or point me at the local docs root if it differs from the usual path), and I'll run the lookup and come back with either a verified syntax block and example, or a clear statement that command-specific retrieval failed and here's what remains unverified.

Response Summary:

The response treats category membership strictly as candidate discovery and explicitly refuses to produce exact syntax, arguments, defaults, or an example from the category listing alone, matching the "safe" side of the hybrid retrieval model. It offers a concrete, actionable next step (running `scripts/command_doc_lookup.py <command_name> --docs-root <path>`) and a secondary path (checking the curated `experts/gauss-language/commands/` cache), while being explicit that the cache is only a convenience layer and defers to official docs on conflict. It states clearly what remains unverified and why it won't guess, and asks for the one piece of missing information (the exact command name) needed to proceed with retrieval, rather than inventing a plausible-sounding example for an unnamed command.

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
- GAUSS Syntax Correctness: marked N/A. The response deliberately contains no GAUSS code or syntax block, since the whole point of the correct answer is to withhold exact syntax until retrieval succeeds; there is nothing to check for syntax validity.
- Data Structure Reasoning: marked N/A. No specific data structure (matrix, DataFrame, array, structure) is discussed because the command and its inputs are not yet identified or verified.
- Dimension and Numerical Awareness: marked N/A. No dimensions, conformability, or numerical behavior are discussed for the same reason — nothing has been verified about the command yet.
- Maintainability and Best Practices: marked N/A. This is a retrieval-process explanation, not code the user will maintain, so package/API maintainability concerns do not apply.
- Testing or Validation: marked N/A. There is no code or claimed result to validate; the response's "validation step" is the retrieval step itself, which is already covered under Task Mode Fit and Assumptions and Dependencies.

Blocking Issues:
None. No automatic failure condition applies: no invented functions, no invented arguments/return fields, no fabricated example, and no claim that retrieval was performed when it was not (the response asks for the command name before attempting retrieval).

Suggested Improvements:
The response could be slightly more concrete about the two most likely category areas mentioned in the prompt (modeling and string-handling) by naming one real example command from each category already confirmed elsewhere in this repository (e.g., `olsmt` for modeling, `strindx` for string handling) purely as illustrations of "here's the kind of candidate this process would apply to" — without claiming their syntax is what's being asked about here. This would make the abstract explanation slightly more concrete without violating the no-invention rule, since both commands are already verified elsewhere in this repository.

Follow-up Actions:
- This completes the initial three-prompt Retrieval category (11.1, 11.2, 11.3). Consider a short round-up note or coverage summary once tracking files are updated.
- Update `evaluations/runs/INDEX.md` and `evaluations/benchmark-coverage.md` with this run if those trackers are being kept current (not modified in this run per task constraints).
