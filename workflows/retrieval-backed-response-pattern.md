# Retrieval-Backed Response Pattern

## 1. Purpose

This workflow standardizes how the GAUSS Code Assistant responds to command-specific tasks: it defines one reusable response structure, one set of wordings for stating what is verified versus unresolved, and one set of rules for each retrieval outcome, so that retrieval-backed responses behave consistently across task modes and commands instead of being re-derived per prompt.

This workflow does not replace `workflows/command-documentation-retrieval.md` or `workflows/native-command-selection.md`. It assumes retrieval has already been attempted (or deliberately not attempted, with a stated reason) and defines how the resulting answer should be written.

Core principles carried through every section below:

- Official GAUSS documentation is the source of truth.
- Command categories (`experts/gauss-language/COMMAND_CATEGORIES.md`) are discovery only.
- Exact syntax, defaults, return fields, control options, and examples require command-specific documentation, not category membership or general knowledge.
- Curated notes (`experts/gauss-language/commands/`) are convenience references, not replacements for official docs.
- If lookup evidence is incomplete, the assistant states what is verified and what is unresolved. It does not fill gaps by guessing.
- The assistant never invents GAUSS syntax, arguments, defaults, return fields, or examples.

## 2. When This Pattern Applies

Use this pattern whenever a response depends on command-specific behavior, including:

- The user asks for exact syntax of a native GAUSS command.
- The user asks about defaults or control-structure options (for example, what a control field defaults to, or what its accepted values mean).
- The user asks about return values or output-structure fields.
- The user asks to translate code from another language into GAUSS using a native command.
- The user asks to debug code whose root cause may depend on documented command behavior.
- The user asks about not-found, missing-value, intercept, formula, or dimensional behavior tied to a specific command.
- The user asks for an example using a specific command.

If none of these apply — for example, a purely conceptual question, or a request for manual/custom code where no native command is relevant — this pattern is not required; use the ordinary response workflow in `workflows/code-assistant-response.md`.

## 3. Retrieval States

Each state below defines the required response behavior. States correspond to outcomes the retrieval prototype (`scripts/command_doc_lookup.py`) can already report, plus curated-note scenarios that sit alongside it.

**A. Official docs found and complete.** The lookup matched a command-specific page with high confidence and no relevant `unresolved_questions`/`extraction_warnings`. Present the verified syntax, defaults, return fields, and behavior as fact, cite the source file, and proceed to a concrete example and validation step.

**B. Official docs found but extraction incomplete.** The match is confident, but part of the answer (for example, a long struct's later fields) was truncated or not extracted. Present only what was actually extracted, name what's missing explicitly, and do not infer the missing part from the field name or general knowledge.

**C. Official docs not found.** No matching command-specific page was found, or no docs root was available in this context. State plainly that command-specific verification could not be performed. If a category-level candidate exists, name it as unverified. Do not give exact syntax.

**D. Multiple plausible docs matches found.** The lookup reports ambiguity (close scores between top candidates, or more than one same-named match). State that more than one candidate matched, list them, and ask the user to confirm which applies rather than silently picking the top-scored one.

**E. Category-only command candidate.** The command appears in `COMMAND_CATEGORIES.md` but no command-specific retrieval has been attempted or has succeeded yet. State that category membership only confirms the command is a plausible candidate — not its syntax, arguments, defaults, or return values — and offer to retrieve or recommend retrieval before giving exact usage.

**F. Curated note available but official docs unavailable.** A short curated note exists (`experts/gauss-language/commands/<command>.md`) but official docs cannot be retrieved in this session. Use the note as a convenience summary, state its last-verified date and source, and flag that it has not been freshly re-verified against official docs this session.

**G. Curated note conflicts with official docs.** Both sources are available and disagree. State the conflict explicitly, prefer the official docs text as authoritative for the answer, and recommend that the curated note be corrected or removed rather than silently picking one source without comment.

**H. Lookup JSON exists but may be stale.** A previously generated `examples/retrieval/*.lookup.json` (or equivalent retrieved evidence) is available, but its freshness relative to the current official docs has not been confirmed in this session (for example, it predates a docs update, or its generation circumstances are unclear). Use it as evidence but note that it has not been freshly re-verified, similar to state F; if the question at hand is high-stakes (production code, published documentation), recommend re-running the lookup before relying on it.

## 4. Standard Response Structure

Use this structure for any response covered by Section 2, adapting length to the question's complexity:

1. **Task classification.** Note the task mode (translation, debugging, generation, documentation, etc.) briefly if it affects the response shape.
2. **Candidate command discovery, if relevant.** Name the category the command comes from when discovery is part of the answer (state E), or skip this step when a command is already named and confirmed.
3. **Retrieval status.** State which of the eight states in Section 3 applies and the source used (official docs file, curated note, or both).
4. **Verified facts.** State only what the retrieved evidence actually supports, using the wording patterns in Section 5.
5. **Safe recommendation or code.** Provide a concrete example or recommendation built only from verified facts, per the Code Examples Policy in Section 6.
6. **Unverified or unresolved items.** List anything the retrieval did not confirm, per the incomplete-extraction and ambiguous-match states.
7. **Validation step.** Include the validation guidance from Section 7 when the response includes runnable code or a diagnosis.
8. **Optional fallback or next retrieval step.** When exact syntax isn't verified, name the safe next step (e.g., `scripts/command_doc_lookup.py <command> --docs-root <path>`) or a labeled teaching/manual fallback.

Not every step needs its own heading in the final response — short answers can fold steps together — but the order and content should still be present in substance.

## 5. Verified Facts Language

Use language that makes the evidence source and confidence level explicit rather than implicit:

- "Verified from official local documentation: ..." — for state A/B facts.
- "The lookup found the command page, but the extracted section did not include ..." — for state B gaps.
- "I could not find command-specific documentation for this command in the current context, so I can't give verified syntax yet." — for state C.
- "More than one documentation candidate matched this command name; I don't want to guess which one applies." — for state D.
- "The command appears in a category list, but category membership does not verify syntax, arguments, or return values." — for state E.
- "The curated note (last verified <date>) is consistent with official docs on this point." — for state F/G agreement.
- "The curated note should not override official docs; on this point, the official documentation says ..." — for state G conflict.
- "This lookup result exists from an earlier session and has not been freshly re-verified; treat it as a starting point, not a final answer, for production use." — for state H.

## 6. Code Examples Policy

- Only show code using syntax verified by official docs (states A/B) or an approved curated note (state F, with the freshness caveat stated).
- Do not fill in missing arguments, defaults, or optional parameters from memory or convention in another language.
- Do not invent output/return fields beyond what was actually extracted; if a struct's fields are only partially known (state B), show only the known fields and say the rest are unverified.
- If exact syntax is not verified (states C, D, or E), provide pseudocode, a high-level description of the approach, or a description of what to check for — not a concrete GAUSS call that looks verified but isn't.
- Clearly label manual matrix or custom implementations as teaching/custom fallbacks whenever a verified native command is available for the same task, per `workflows/native-command-selection.md`. Manual code should never silently substitute for a native command recommendation.

## 7. Validation Step Requirement

- **Code translation responses** must include a validation step: a concrete way to confirm the GAUSS translation matches the source language's behavior on the same input.
- **Debugging responses** must include a check or minimal test that would confirm the fix actually addresses the diagnosed cause, not just that the code runs without error.
- **Modeling translations** specifically should suggest comparing coefficients, dimensions, return values, or printed report output against a known reference implementation when one is available (for example, the source language's fitted model).
- **Example:** when translating an R `lm()` model to `olsmt`, suggest comparing GAUSS's `out.b` against R's `coef(model)` on the same data as the validation step, rather than presenting the translation as self-evidently correct.

## 8. Examples

**`olsmt` — docs found and verified intercept behavior (state A).**

> Verified from official local documentation (`olsmt.rst`): `out = olsmt(data, formula[, ctl])` or `out = olsmt(data, depvar, indvars[, ctl])`. A formula containing `-1` (e.g., `"y ~ -1 + x1 + x2"`) means a no-intercept model. Separately, `ctl.con` defaults to `1`; `ctl.con = 1` adds a constant term and `ctl.con = 0` removes it. Since R's `lm(y ~ x1 + x2, data = df)` includes an intercept by default and `olsmt`'s defaults already match, `out = olsmt(df, "y ~ x1 + x2")` is the direct translation — no `ctl` needed unless you want to drop the intercept. Validation step: compare `out.b` against R's `coef(model)` on the same data.

**`strindx` — docs found and verified not-found behavior (state A).**

> Verified from official local documentation (`strindx.rst`): `idx = strindx(haystack, needle [, start])` returns the index of the first occurrence of `needle`, or `0` if it is not found. This differs from Python's `.find()`, which returns `-1`. Check `idx == 0`, not `idx == -1` or `idx < 0`.

**Category-only candidate — exact syntax must not be given yet (state E).**

> The command you're referring to appears in the relevant category list, so it's a plausible native candidate for this task. That only confirms it's a real, category-appropriate command — it does not confirm its argument order, defaults, or return structure. Before I give exact syntax, I'd want to run `scripts/command_doc_lookup.py <command> --docs-root <path>` or have you share the command-specific documentation.

**Docs found but extraction incomplete (state B).**

> Verified from official local documentation (`olsmt.rst`): `out` is an `olsmtOut` structure, and I can confirm `out.vnam` (variable names), `out.m` (the moment matrix), and `out.b` (parameter estimates) from the extracted text. The extraction is truncated after `out.b`, so I can't confirm the field names for statistics shown in the docs' example output (R-squared, standard errors, t-values) — treat those as unresolved until a fuller extraction or the raw doc page is checked.

## 9. Failure Modes

- Inferring syntax, arguments, defaults, or return fields from category membership alone.
- Treating a curated note as authoritative over official docs, or not flagging a conflict when one exists.
- Ignoring incomplete extraction and presenting a partial field list as if it were exhaustive.
- Saying "check the docs" or "you should verify this" when retrieval evidence is already available in context and could have been checked directly.
- Giving translation or debugging code without any validation step.
- Using Python, R, MATLAB, or other non-GAUSS syntax inside a GAUSS example, including as a "close enough" substitute when exact GAUSS syntax isn't verified.
- Claiming code was executed, or that a fix was confirmed, when no tool actually ran it.

## 10. Relationship to Existing Workflows

- `workflows/command-documentation-retrieval.md` defines the hybrid retrieval strategy (categories for discovery, official docs for syntax, curated notes as a small cache) and when to retrieve. This document assumes that strategy has already been applied and defines how to phrase the resulting answer.
- `workflows/native-command-selection.md` defines when to prefer a native command over manual code. This document's Code Examples Policy (Section 6) and Failure Modes (Section 9) enforce that decision at the response-writing stage.
- `workflows/code-assistant-response.md` defines the assistant's general response workflow across all task modes. This document is the specialization to apply within that workflow's Step 3 (retrieval need) and Step 5 (generate/debug/translate) whenever a command-specific question is in play.
- `tools/command_doc_lookup.md` documents the retrieval tool whose output states (found, ambiguous, not found, incomplete) map directly to Section 3 of this document.
- `agents/code-assistant/task_modes.md` defines per-mode response patterns; its Code Translation and Debugging modes now point to this document's validation-step requirement (Section 7).
- `workflows/expert-routing.md` and `experts/gauss-language/OPERATIONAL_PROFILE.md` determine *when* the GAUSS Language Expert activates and what evidence a task requires; this document determines *how* retrieved evidence states, once retrieval happens, shape the response.

## 11. Maintenance Notes

Update this document when the retrieval script's reported states change (`scripts/command_doc_lookup.py`), when new failure modes are found through evaluation, or when new task modes need retrieval-backed guidance beyond translation and debugging.
