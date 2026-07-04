# Evaluation Result

Date: 2026-07-04
Evaluator: Claude
Agent Version: Current repository state on 2026-07-04 (v0.5.0 Retrieval Integration and Response Quality milestone)
Prompt ID: 12.4
Prompt Category: Retrieval Integration
Prompt Text:

A curated command note says one thing about a GAUSS command, but the official command-specific docs say something different. Which source should the assistant trust?

Expected behavior:

- Classifies this as a retrieval-backed source-conflict task.
- States that official command-specific docs are authoritative.
- States that curated command notes are convenience references only.
- Does not blend conflicting details.
- Does not let the curated note override official docs.
- Flags the inconsistency.
- Recommends updating or correcting the curated note.
- Uses official docs for user-facing syntax, defaults, return fields, and behavior.
- Clearly distinguishes official evidence from curated notes.
- Does not invent command behavior.
- Does not claim code was executed.

Generated Code Assistant Response:

This is a retrieval-backed source-conflict question, and the answer is unconditional: **official command-specific documentation wins, every time.** This is `workflows/retrieval-backed-response-pattern.md` state G (curated note conflicts with official docs), and both `workflows/command-documentation-retrieval.md` ("If cached notes conflict with official docs, official docs win") and the curated note format itself (`experts/gauss-language/commands/olsmt.md`'s own "Authority note": *"If this note conflicts with official GAUSS documentation, the official documentation wins"*) already state this rule in writing.

**Why the hierarchy is fixed, not case-by-case.** A curated note (like `experts/gauss-language/commands/olsmt.md`) exists only as a short, convenience summary — it names its official source and a "last verified" date, but it is not re-checked against official docs every time it's read. Official docs are the primary, current source of truth. So when the two disagree, that disagreement is evidence the curated note has gone stale (or was wrong when written), not evidence that there are two equally valid answers to choose between.

**What I will not do.** I will not average, blend, or split the difference between the two versions of the fact — for example, I won't present a default value, argument order, or return field as "somewhere between" what each source says. I also won't silently prefer whichever source is more convenient to quote, or silently drop the curated note without saying why.

**What I will do instead, concretely:**

1. **State the conflict explicitly** — name both sources, and say plainly what each one claims.
2. **Use the official docs' version of the fact** for anything user-facing: syntax, defaults, return fields, control options, or behavior.
3. **Flag the curated note as stale or incorrect** on this specific point, rather than treating the whole note as untrustworthy — a conflict on one field doesn't necessarily invalidate the rest of the note.
4. **Recommend the curated note be corrected or removed** for the conflicting point, referencing the official doc as the source to re-sync it against.

**Worked illustration (hypothetical, not a real conflict currently present in this repo).** As of this session, `experts/gauss-language/commands/olsmt.md` and the retrieved `examples/retrieval/olsmt.lookup.json` agree on every point I've checked (syntax forms, `ctl.con` default of `1`, formula `-1` meaning no-intercept) — I'm not aware of an actual conflict between them right now. But to illustrate the mechanics: if the curated note claimed `ctl.con` defaults to `0` while the official docs said the default is `1`, I would state the official docs' `1` as the verified default, say explicitly that the curated note appears to be wrong or outdated on that point, and recommend it be corrected — I would not present `0` as a possibility, a fallback, or an "alternate default."

**Boundary case worth naming.** If official docs cannot be retrieved at all in a given session (state F, not this one), the curated note becomes the best available evidence — but even then, it's used with an explicit freshness caveat ("consistent with official docs as of `<date>`, not re-verified this session"), never presented with the same confidence as a fresh official-docs match.

No code was run and no actual conflict was detected in this session; this response describes the resolution policy and its mechanics, not a specific verified discrepancy found right now.

Response Summary:

The response correctly classifies this as a source-conflict question and states unconditionally that official command-specific docs are authoritative over curated notes, citing the same rule already written into `workflows/command-documentation-retrieval.md` and the curated note's own authority disclaimer. It explicitly refuses to blend or average conflicting details, describes a concrete four-step resolution procedure (state the conflict, use official docs' version, flag the specific stale point rather than discrediting the whole note, recommend correcting it), and — notably — uses a hypothetical, clearly-labeled illustration built from real repository facts (`olsmt`'s actual `ctl.con` default) rather than fabricating or overstating an actual conflict that doesn't currently exist between `olsmt.md` and `olsmt.lookup.json`. It also names the adjacent boundary case (curated note used alone when official docs are unavailable) to show it isn't overgeneralizing "official always wins" into "curated notes are worthless." It does not claim execution.

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
- GAUSS Syntax Correctness: marked N/A. The response is a source-hierarchy policy answer with no GAUSS code; the hypothetical `ctl.con` example is a described value, not a code block.
- Data Structure Reasoning: marked N/A. No specific data structure choice is discussed.
- Dimension and Numerical Awareness: marked N/A. No dimensions or numerical computation are involved.
- Maintainability and Best Practices: marked N/A. This is a source-authority policy question, not code the user will maintain.
- Testing or Validation: marked N/A. There is no code or claimed result to validate.

Blocking Issues:
None. No automatic failure condition applies: no fact was invented, no conflicting details were blended, and no claim of execution or of an actual detected conflict was made.

Suggested Improvements:
None blocking. The response is careful to label its `ctl.con` illustration as hypothetical, which is the correct call — but it's worth double-checking in future evaluations that this restraint holds even when a prompt more strongly implies a real, specific conflict exists (this prompt was abstract/general, so restraint was low-cost here; a more pointed prompt would be a better stress test).

Follow-up Actions:
- This completes evaluation coverage for all originally drafted Retrieval Integration prompts (12.1-12.6): 12.1 (incomplete extraction), 12.2 (not found), 12.3 (ambiguous), 12.4 (curated-vs-official conflict), 12.5 (translation validation step), 12.6 (debugging return-behavior retrieval) — all Pass.
- Update `evaluations/runs/INDEX.md`, `evaluations/benchmark-coverage.md`, and `CHANGELOG.md` to reflect all six new Retrieval Integration runs, consistent with how `v0.4.0`'s three Retrieval runs were tracked.
- Consider a `v0.5.0` readiness check now that both the response-pattern document and its full benchmark coverage are in place, similar to the `v0.4.0` readiness checklist precedent.
- The suggested stress test above (a prompt with a concrete, specific, strongly-implied real conflict) would be a good candidate for a future benchmark addition if source-conflict handling needs deeper coverage beyond this abstract case.
