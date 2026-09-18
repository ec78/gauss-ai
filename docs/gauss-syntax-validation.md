# GAUSS Syntax Validation

**Status: `v0.77.0`.** Extends [docs/pre-execution-validation.md](pre-execution-validation.md) (`v0.74.0`/`v0.75.0`). Read that first — this page covers the deterministic syntax-validation layer, `gauss_pre_execution_validation.validate_syntax(...)`. See [docs/differential-syntax-validation.md](differential-syntax-validation.md) for `v0.77.0`'s systematic differential-testing methodology and evidence trail behind every rule change below.

## Why this exists

`v0.75.0`'s own live evaluation (`evaluations/runs/2026-09-12-code-assistant-universal-code-validation-run-008.md`, scenario `65.8b`) asked for `chol` on an invalid matrix. The real model wrote:

```
x = {-1 0; 0 -1};
```

`;` is not GAUSS's row separator — the documented, verified form (`let.rst`: `let x = { 1 2 3, 4 5 6, 7 8 9 };`) uses `,`. The existing precondition checker correctly, conservatively declined to guess at this unparseable literal and reported the `chol` precondition `UNVERIFIED`. That is the *safe* response to "I can't check this," but it is the wrong response to "this input is not well-formed GAUSS syntax at all" — and real `tgauss.exe -b` execution (this milestone's own development session) confirmed the gap is worse than a loud parse error:

```
x = {-1 0; 0 -1};   ->  one row, 5 elements: -1  0  +DEN  0  -1   (exit 0, NO error)
x = {-1 0, 0 -1};   ->  correct 2x2 matrix                        (exit 0)
```

GAUSS silently misparses the `;`-separated form into a malformed single row containing a denormal/garbage element, rather than rejecting it. `validate_syntax(...)` closes this gap by treating it as its own deterministic evidence, distinct from precondition checking.

## What it checks — and how it's sourced

Deliberately **not a parser**. Every rule is small, bounded, and textual, with its own recorded provenance (`gauss_pre_execution_validation._SYNTAX_RULE_REGISTRY`):

| Rule | What it catches | Source |
|---|---|---|
| `matrix_literal_row_separator` | `{1 2; 3 4}` — `;` used as a row separator | `let.rst` (official docs) + real `tgauss.exe -b` execution |
| `matrix_literal_row_shape` | `{1 2 3, 4 5}` (ragged rows), `{1 2, , 3 4}` (empty row) | `let.rst` (official docs) |
| `balanced_delimiters` | Unmatched/mismatched `{}`/`()`/`[]`, including an incomplete call like `meanc(` | Structural convention across every real syntax example in this repository's own fixtures |
| `dangling_assignment` | `x = ;` | Real `tgauss.exe -b` execution: `error G0105: Bad expression or missing arguments` |
| `unterminated_string` | A `"` opened but not closed on the same line | `let.rst`'s own `"dog""cat"` example — double quotes are GAUSS's unambiguous string delimiter. A single quote is deliberately **not** checked: it is overwhelmingly the transpose operator (`x'`) in generated code, and treating it as a string delimiter would be a real false-positive risk. |
| `bare_multi_token_literal_requires_let_or_braces` | `x = -1 0;` — a bare, brace-less, non-`let` list of two-or-more numeric tokens | A live CLI smoke test of the semicolon-matrix regression through the installed `gauss-ai` binary produced this exact shape from a real model. Real `tgauss.exe -b` execution: `x = -1 0;` alone raises `error G0063: Operator expected before '0'`; the identical literal prefixed with `let` (`let x = -1 0;`) executes successfully, matching `let.rst`'s own documented convention. Structurally scoped (two-or-more bare numeric tokens, no `let`, no `{...}`) so it can never match a real expression (`x = a + b;`), a real call (`x = meanc(y);`), or a single scalar (`x = 5;`). |
| `call_argument_missing_separator` (**new in `v0.77.0`**) | `reshape(5 3)`, `rndn(n n)`, `sprintf("..." pi)` — two tokens inside one call argument separated only by whitespace, no comma, no operator | `v0.77.0`'s own differential baseline corpus run (real `tgauss.exe -b`, 2026-09-18): five independent mutated snippets sharing this shape were real syntax false negatives; real GAUSS rejects every one with `error G0063: Operator expected` — the same underlying grammar gap `bare_multi_token_literal_requires_let_or_braces` already caught for an assignment right-hand side, generalized to call arguments. Masks matrix-literal (`{...}`) and indexing (`[...]`) spans first so a legitimate literal or index list is never mistaken for this violation. |

**Removed in `v0.77.0`: `call_argument_separator`** (previously flagged `f(a,,b)`/`f(a,)`/`f(,a)` as invalid). This rule was never backed by real-runtime evidence — only a structural assumption ("no documented signature shows an empty slot"). `v0.77.0`'s differential baseline corpus run directly contradicted it: real `tgauss.exe -b` execution of `x = ones(3,, 2); print x;` and `x = meanc(rndu(1e5,, 4)); print rows(x);` showed GAUSS silently and **correctly** collapses the doubled/trailing comma — the computed result is identical to the single-comma form, not a silent misparse. The rule was removed entirely rather than patched, per this milestone's own "prefer measurable disagreement over intuition-driven rule expansion" discipline.

Operates on already comment-stripped code, the same convention every other check in this module follows.

## Status vocabulary

- **`VALIDATED`** — no syntax violation was found within this version's implemented, deliberately bounded coverage. **This is not a claim that the code is fully correct GAUSS** — only that nothing this checker knows how to look for was wrong.
- **`INVALID`** — at least one deterministic rule above was actually violated.
- **`PARTIAL`** — some constructs were checked and passed, but at least one other construct in the code (e.g. a `do`/`while`/`proc` block body) is outside this version's coverage.
- **`UNKNOWN`** — nothing checkable was found in the code at all.

## What's explicitly NOT attempted

No full GAUSS grammar. `do`/`while`/`for`/`if`/`proc` block bodies, string concatenation (`$+`), complex/scientific-notation literal validation, and character-element matrix literals (beyond the two structural rules above, which apply regardless of element type) are all left unchecked — recorded honestly in `unknown_constructs`, never silently ignored and never guessed at as passing.

## Call parsing

`extract_generated_calls(...)` already extracted nested calls correctly before this milestone (`meanc(reshape(x, 2, 3))` yields two independent `GeneratedCall`s, each with its own correctly-bounded argument list) — confirmed by reading the existing implementation before adding anything new, rather than duplicating it. `v0.76.0` hardens the shared argument-splitter (`_split_top_level_args`) to also respect double-quoted string boundaries, so a string argument containing a comma (e.g. `sprintf("%s, %s", a, b)`) is no longer mistaken for two arguments.

## Examples

Invalid (the exact regression):

```
Validation:
- Function chol: documented; signature: compatible
- Preconditions:
  - chol: unverified -- the input is a runtime value or expression, not a literal matrix ...
- Syntax: invalid
  - GAUSS matrix literal uses unsupported row separator `;` -- rows must be separated by `,` (a `;`-separated literal is not rejected by GAUSS; it is silently misparsed into a malformed single row instead) (line 1)
- Execution eligibility: eligible_for_validation
  (This means only that deterministic checks found no known problem -- not that the code is correct, safe, methodologically appropriate, or approved to run.)
- Validation coverage: symbols=complete, signature=complete, parameter roles=not_applicable, preconditions=unknown, syntax=complete, predicted output=not_applicable
- Execution handoff readiness: not_ready
  - syntax: GAUSS matrix literal uses unsupported row separator `;` -- ...
  (This code has not been executed. This is not an approval to run it.)
```

Note: `pre_execution_eligibility` itself stays `eligible_for_validation` here — nothing about the precondition checker's own conservative `UNVERIFIED` behavior changed. The syntax problem is caught as its own, separate, additional evidence, and it alone is enough to keep the code off the handoff-candidate path (see [docs/execution-handoff-readiness.md](execution-handoff-readiness.md)).

Valid (the correctly formatted equivalent):

```
- Syntax: validated
- Execution handoff readiness: handoff_candidate
  - grounded and symbol-supported
  - documented call signatures are compatible
  - syntax was validated with no known violation
  - no documented precondition is known to be violated
  - validation coverage is broad
  (This code has not been executed. This is not an approval to run it.)
```

## Known limitations

- Bounded to the constructs listed above — not a real parser, and never will be without new, specific evidence that a construct is both common in real generated output and reliably checkable.
- Matrix-literal element-count/ragged-row checking only applies when every row is purely numeric tokens; a literal with character elements (`{ dog cat }`, a real documented GAUSS form) is checked only for the two structural rules (row separator, empty row) that apply regardless of element type.
- No cross-line matrix-literal or call-argument tracking beyond what the existing `_find_literal_matrix_for_argument`/`extract_generated_calls` machinery already does.
