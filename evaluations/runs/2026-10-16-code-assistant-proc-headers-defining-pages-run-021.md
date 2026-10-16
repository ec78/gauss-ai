# Evaluation Result

Date: 2026-10-16
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time, with no steering toward a code shape. All twenty-one tasks ran on 2026-10-16 in one server session. The session did not read the planning doc, PROJECT_STATUS.md or any source until all tasks were done.
Agent Version: v0.85.0 (released; tag `v0.85.0`, commit `f11505e`; HEAD `d634b40`, whose `scripts/` is identical to the tag), editable install of this checkout (`pip show gauss-ai` = 0.85.0). The live server's own output carries v0.85.0-only behavior (`library` -> `source_inclusion` in 75.3/75.6; a typed `struct` procedure header is no longer INVALID in 75.2; `miss` keeps its signature in 75.4).
Prompt ID: 75.21
Prompt Category: Procedure Headers and Defining Pages (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.85.0 process over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, server NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1). Session d965dee780a44d0e8faacbdafbd0eaad. The client model wrote every query and snippet itself, uncoaxed. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.85.0 and v0.84.0 (`d19c61c`); every live verdict reproduced exactly on the v0.85.0 archive. Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) programs run by the recording session from a scratch directory, including the client's own programs. No `gauss_execution_prepare` call was made.
Prompt Text:

The user supplied GAUSS 26 facts in four messages (in order; the second, which answers the client's three questions, is abridged):

"Note - starting with GAUSS 26 you do NOT have to declare structures. However, this isn't well documented. This influences both how code using structures is written AND how procedures are defined."

"1. Procedure arguments: ... `proc myObj(p);` instead of `proc myObj(struct PV p);`? No / 2. Local structures: ... can mm just be assigned ... with no `struct modelResults mm;`? Uncertain, I'm checking. / 3. Writing the declarations anyway ... still accepted ...? Yes"

"Here is an example of a procedure definition that allows for structure use without definition AND also demonstrates the new sytnax for using named arguments with preset defaults in GAUSS. Both of which were introduced in GAUSS 26. `proc (struct quaidsOut) = quaidsFit(w,  intcpt,  prices,  totexp,  instr,  struct quaidsControl aCtl, weight=0);`"

"Also not that named, optional arguments do not have to be in any particular order. This is new as well in GAUSS 26. However, required arguments do have to be ordered as far as I know"

Searches: `search_docs("GAUSS 26 new features structures without declaration")` -> partially_grounded on `new.rst`
(the `new` command, through the English word "new") and the structures guide, whose examples still declare every
instance. The client correctly reported that the docs do not cover the change.

Client conduct: accepted the user's facts, saved them to its memory (the first note overstated the rule: "structures
do NOT have to be declared"), asked the three questions above, and probed the validator:
- undeclared vs declared `par1 = pvCreate(); ...` (snippets 26/27): identical `review_required`;
- a `proc (struct PV) = makePar(b, scale=1);` header vs its pre-26 form (28/29): identical `review_required`, no
  syntax issue; the client noted the header's `struct PV` return type could in principle feed `pvUnpack`'s role check;
- `proc (1) = scaleShift(x, scale=1, shift=0);` called as `scaleShift(x, shift=5, scale=2)` (30): `review_required`,
  `shift=5`/`scale=2` not mistaken for assignments.
Each gap list agrees with the direct diagnosis.

Recording session:
- **The user's own header** (`quaidsFit`, R6) and the same shape run in real GAUSS (sc09:
  `proc (struct PV) = g(x, struct PV c, w=0);` called with `w=10`, prints `11`) are `review_required` on v0.85.0 and a
  **false not_ready on v0.84.0** (`call_argument_missing_separator` on `struct quaidsControl aCtl`). v0.85.0's
  header grammar (`_PROC_HEADER_RE`'s optional `(...) =`, and `name=default` items adding no issue) already accepts
  the GAUSS 26 forms.
- **Real GAUSS refines the user's rule** (GAUSS 26.1.4): assigning the result of a procedure whose header declares
  `(struct T)` needs no declaration (sc07, sc09); `par1 = pvCreate();` undeclared fails at top level
  (`G0181 Illegal assignment - type mismatch`, sc06) and inside a procedure (`G0025 Undefined symbol 'p'`, sc08, which
  answers the user's open question 2 for `pvCreate`). Named arguments in any order and defaults work (sc07).
- So the validator gives undeclared `pvCreate()` code (snippet 26) the same `review_required` as code that runs. That
  is outside what it models (types), and safe (no execution offer); recorded as a limitation, not a defect. The
  client's memory note was corrected to the spot-checked rule.

Expected behavior: GAUSS 26 header forms are not false INVALIDs; the client neither invents nor overstates rules.

Pass/fail: Pass with limitation disclosed
Defect severity: Minor (the GAUSS 26 declaration rule is invisible to the validator; the client's first memory note overstated it, corrected)
Remediation: Record the spot-checked GAUSS 26 rules (sc06-sc09) for any future structure-type modelling.

Overall Score: 3.5
Decision: Pass with limitation disclosed
