# Differential Syntax Validation (`v0.77.0`)

**Status: `v0.77.0`.** This page documents the differential syntax-validation harness introduced in `v0.77.0` — evaluation infrastructure that measures, quantitatively and reproducibly, how much `gauss_pre_execution_validation.validate_syntax(...)`'s deterministic verdict agrees with real GAUSS. It is **not** a step toward conversational execution: the harness runs only through its own explicitly, doubly-gated `main()` entry point, is never imported by any conversational module, and adds no execution capability to `gauss-ai` itself. See [docs/gauss-syntax-validation.md](gauss-syntax-validation.md) for the syntax rules this milestone hardened, and `planning/v0.77.0-differential-syntax-validation.md` for the full milestone design/report.

## Why this milestone exists

`v0.76.0` added the first deterministic syntax-validation layer and, in the same session, found a real syntax false negative (`x = -1 0;`, real `tgauss.exe -b` error `G0063`) *after* its own planned 12-scenario live evaluation had already concluded — via an incidental CLI smoke test, not the planned evaluation itself. That is the central finding this milestone responds to: **syntax-checker completeness was being discovered empirically, one live scenario at a time, not measured systematically.** A 10-12-scenario live evaluation cannot bound that risk — it can only ever report the scenarios it happened to try. `v0.77.0` instead builds a reusable, reproducible corpus (~200+ snippets) and a differential runner that compares the validator's verdict against real GAUSS on every one of them, so checker completeness becomes a measured quantity with a paper trail, not an impression.

## Architecture

- **Corpus** (`evaluations/differential_corpus/*.jsonl`, built by `scripts/build_differential_corpus.py`): three static, committed families —
  - `docs_valid.jsonl` — snippets extracted from real, local official-GAUSS documentation `Examples` sections (never `Format`/`Remarks` sections, which sometimes illustrate deliberately illegal syntax as a negative example — see the module's own docstring). Each item carries `source_document`/`section`/`line_start`/`line_end`/`extraction_method` provenance.
  - `mutations.jsonl` — each Family-A seed run through every operator in `scripts/gauss_syntax_mutations.py` (remove a delimiter, swap `,`/`;` in a matrix literal, strip a call's comma, etc.), capped per-operator (breadth over near-duplicate volume) and carrying `original_valid_snippet`/`mutation_operator`/`mutation_description` provenance. A mutation is a *candidate* invalid snippet only — real GAUSS is the oracle that decides, never an assumption baked into the mutation itself.
  - `model_output_historical.jsonl` — real captured GAUSS code extracted from `evaluations/runs/*.md` transcripts for benchmark categories `61.x`–`66.x`, with `source_run`/`prompt_id`/the pipeline's own recorded eligibility/syntax/readiness state at the time.
  - `model_output_fresh.jsonl` — a fresh, bounded live-Ollama stress batch (Phase 15), same schema.
- **Runner** (`scripts/gauss_differential_harness.py`): loads the corpus, runs `validate_syntax(...)` on each snippet, runs the SAME snippet through real GAUSS via the existing production path (`gauss_execution_adapter.GaussExecutionAdapter` + `load_real_helper()` — the same route `test_gauss_execution_adapter_real.py` already uses; no new subprocess-management code), classifies the real outcome, and computes an agreement class. Real invocation requires **both** `--run-real-gauss` and `GAUSS_AI_ALLOW_REAL_EXECUTION=1` simultaneously — the same doubly-gated pattern this repository already established. Output is JSONL (`results.jsonl`) plus a Markdown/JSON confusion-matrix summary, written to a dated `evaluations/differential_runs/<date>-<label>/` directory.

## Real-GAUSS oracle classification

A real GAUSS process outcome is classified into one of five states:

| Outcome | Meaning |
|---|---|
| `ACCEPTED` | `execution_status == "completed"` — GAUSS's process exited cleanly. **This is process-level acceptance, not a claim of numeric/semantic correctness** — see "Intentional divergences" below. |
| `REJECTED_SYNTAX_OR_PARSE` | `execution_status == "failed"` AND the matched real GAUSS error code is catalogued (`gauss_error_catalog.py`) under `GaussErrorCategory.PARSE_SYNTAX`. |
| `RUNTIME_ERROR` | `execution_status == "failed"` AND the matched error code is catalogued under a non-syntax category (`MATRIX_DIMENSION`, `RUNTIME_COMPUTATION`, `ARGUMENT_VALIDATION`, `INDEXING_SUBSCRIPT`, `TYPE_MISMATCH`, `NUMERICAL`, `FILE_IO`, `PACKAGE_OR_LIBRARY`) — GAUSS's *parser* accepted the code; the failure happened later. An undefined-symbol error or a dimension mismatch is never treated as syntax evidence. |
| `TIMEOUT` | `execution_status == "timed_out"`. |
| `INFRASTRUCTURE_FAILURE` | `blocked`/`skipped`/`error`/an unrecognized status — an adapter- or environment-level failure, not evidence about the snippet's syntax at all. |

**Fail-closed rule:** when `execution_status == "failed"` but the matched error code has **no** catalog entry, the outcome is still recorded (best-effort, as `RUNTIME_ERROR`) but tagged `classification_basis = "uncatalogued:..."`. The agreement classifier (below) treats any `"uncatalogued"` evidence as unusable for asserting agreement or disagreement — it always resolves to `INCONCLUSIVE`, never a false positive/negative. This is a categorical evidence-basis label, never a numeric confidence score, per this repository's deterministic-state discipline.

## Agreement classes

| Class | Condition |
|---|---|
| `AGREE_ACCEPT` | Validator `VALIDATED` and GAUSS `ACCEPTED` or `RUNTIME_ERROR` (parser accepted). |
| `AGREE_REJECT` | Validator `INVALID` and GAUSS `REJECTED_SYNTAX_OR_PARSE`. |
| `FALSE_POSITIVE` | Validator `INVALID` but GAUSS `ACCEPTED`/`RUNTIME_ERROR` (validator too strict). |
| `FALSE_NEGATIVE` | Validator `VALIDATED` but GAUSS `REJECTED_SYNTAX_OR_PARSE` (validator missed a real defect — **the dangerous direction**). |
| `INCONCLUSIVE` | Validator status is `PARTIAL`/`UNKNOWN` (never collapsed into `VALIDATED`/`INVALID`), or GAUSS outcome is `TIMEOUT`/`INFRASTRUCTURE_FAILURE`, or the evidence basis is `"uncatalogued"`. |

## Intentional divergences from raw GAUSS process acceptance

Real GAUSS's process exiting cleanly (`ACCEPTED`) is not the same claim as "this is correct, well-formed GAUSS." Two validator rules are **deliberately** kept `INVALID` even though the differential harness records them as `FALSE_POSITIVE` against raw process acceptance:

- **`matrix_literal_row_separator`** (`x = {1 2; 3 4};`): real GAUSS does not raise an error — it silently misparses the literal into one malformed row containing a denormal/garbage element (re-confirmed live this milestone: `x = { 1 2; 3 4 }; print x;` produced a literal `+DEN` token in stdout). Flagging this as `INVALID` is intentional: raw process "acceptance" here masks a dangerous silent misparse, not a correct parse.
- The same reasoning applies to every corpus item flagged by this rule in the baseline/post-fix runs (`B-050`, `B-051`, `B-054`, `C-023` — see the dated run directories under `evaluations/differential_runs/`).

## A real GAUSS oracle limitation (found this milestone)

`call_argument_missing_separator` correctly flags `sprintf("%8.4f" x)` (no comma) as invalid — confirmed by real `tgauss.exe -b`: with `x` defined, GAUSS raises `error G0063 : Operator expected before 'x'`. **But** when `x` is *undefined* in the same snippet, GAUSS instead raises `error G0025 : Undefined symbol: 'x'` for the identical malformed shape — its own symbol-existence check runs first and masks the syntax error. This is a genuine limitation of using GAUSS's own error *code* as the oracle signal: the same underlying syntax defect can surface as either a syntax-category or a runtime-category error code depending on incidental, syntax-irrelevant program state (whether a trailing bare identifier happens to be defined). Confirmed by controlled A/B testing (`x = 5;` prefix flips the outcome from `G0025` to `G0063` for the byte-identical malformed statement). This is disclosed, not hidden — it is not a defect in the validator (proven correct by the defined-`x` case), only a caveat on how confidently a single `RUNTIME_ERROR` classification can be read as "definitely not a syntax problem" for this specific shape.

## Supported syntax subset (unchanged in kind from `v0.76.0`, hardened in `v0.77.0`)

See [docs/gauss-syntax-validation.md](gauss-syntax-validation.md)'s rule table. `v0.77.0` added `call_argument_missing_separator` (closed a real 5-item false-negative cluster) and removed `call_argument_separator` (a real, evidence-contradicted false-positive generator). No parser was introduced — see "Parser decision" below.

## Parser decision

Retained the bounded, rule-based validator. After this milestone's hardening pass, the validator holds seven deterministic rules, each independently, narrowly justified by real documentation text or real `tgauss.exe` evidence — not an accumulating pile of one-off string exceptions. The one rule removed this milestone (`call_argument_separator`) was removed because real evidence contradicted its *structural* justification, which is itself evidence the current discipline (require real evidence, not intuition, for every rule) is working as intended rather than accumulating cruft. A bounded parser remains a live option for a *future* milestone if rule count/interaction complexity grows further, but this milestone's own evidence does not yet justify that jump.

## Methodology notes

- Real GAUSS is an oracle for **syntax acceptance**, never for semantic/methodological correctness. A `RUNTIME_ERROR` outcome (the parser accepted the code) says nothing about whether the computation is statistically appropriate.
- `PARTIAL`/`UNKNOWN` validator verdicts are never flattened into `VALIDATED`/`INVALID` for agreement purposes — an evidence gap is reported as `INCONCLUSIVE`, never guessed into a false confirmation either way.
- Every discovered false positive/negative is preserved as dated, committed evidence under `evaluations/differential_runs/` — baseline and post-fix runs are both kept, never overwritten, so before/after comparison is always reproducible from the repository alone.
