# PROJECT_STATUS.md

Current, temporary project state. For durable repo-wide facts and rules, see `CLAUDE.md` instead. Update this file when a meaningful unit of work completes, or before clearing/starting a new session — it should let a fresh session resume without needing prior chat history.

## Current Objective

Implement **v0.74.0 — Deterministic Pre-Execution Validation & Grounding Coverage Expansion**, per a detailed spec given in chat (not yet saved to `planning/`). Goal: a deterministic layer that validates generated GAUSS code beyond symbol presence — documented call-signature compatibility, documented preconditions (e.g. `invpd` requiring a symmetric positive-definite matrix), and an explicit, conservative execution-eligibility verdict (`INELIGIBLE` / `REQUIRES_CLARIFICATION` / `ELIGIBLE_FOR_VALIDATION`) — without adding any real execution capability to chat.

**Status: research/investigation only. No application code has been written or committed for v0.74 yet.**

## Completed Work

- `v0.70.0`–`v0.73.0` are complete, committed, tagged, pushed, and released (latest tag: `v0.73.0`, commit `b1c1988`). See `README.md`'s "Current Status"/"Previous milestone" chain for what each shipped.
- `v0.73.0` (most recent) added grounding-gated generation (`compute_generation_gate`), natural-language-to-symbol resolution (`resolve_concepts`, a 5-entry curated alias index), and a post-generation symbol checker (`check_generated_symbols`) — see `planning/v0.73.0-grounding-gated-generation.md` for its full readiness assessment.
- For this v0.74 task specifically, so far: reviewed `scripts/gauss_conversation_engine.py` (full, 1339 lines), `scripts/command_doc_lookup.py` (full), `README.md`, `planning/v0.73.0-grounding-gated-generation.md`, and `docs/alpha-tester-guide.md`/`docs/private-alpha-testing.md`. Confirmed the real evaluation environment is available in this session: Ollama is running locally with `qwen2.5-coder:7b` pulled; a real GAUSS install exists at `C:\gauss26\tgauss.exe`; a real docs checkout exists at `C:/Users/eclow/Documents/GitHub/docs/docs` (2,063 `.rst` files, gitignored, machine-specific). Read real doc files for `meanc`, `invpd`/`inv` (`invinvpd.rst`), `tscsFit`, and `tscsmtControlCreate` to ground signature/precondition-extraction design in real documentation formats.

## Decisions

- **Confirmed real regression source material**: `invinvpd.rst` explicitly documents "If the input to `invpd` is not symmetric, it is possible that the function will (erroneously) appear to operate successfully" — direct authoritative support for encoding a machine-checkable symmetric/positive-definite precondition on `invpd`. Confirmed `tscsmtcontrolcreate.rst` exists but no `tscsmtcontrol.rst` does — confirms `tscsmtControl()` (seen live in `v0.73.0` evaluation `63.5`) is a real hallucination of a struct type name as if it were a callable constructor.
- **Signature extraction design sketch** (not yet implemented): two real doc formats exist and both need support — (1) the `.. function:: y = f(x)` directive style (`meanc`, `invpd`, `tscsFit`), already partially parsed by `command_doc_lookup.extract_function_directive_details`; (2) an older plain-text `Format`/`Input`/`Output` heading style with no directive (`tscsmtControlCreate`). Plan: a new module `scripts/gauss_pre_execution_validation.py` (not yet created) that reuses `command_doc_lookup`'s already-extracted `syntax_blocks` and re-parses them for parameter names/counts, treating `[...]`-bracketed trailing args as optional, per-symbol (a page can document more than one symbol, e.g. `invinvpd.rst` documents both `inv` and `invpd`).
- **Documentation-derived concept index design sketch** (not yet implemented): bag-of-keywords overlap scoring (not a vector DB, not model-based) derived from each `.rst` file's "Purpose" section + heading + related-links, requiring a minimum keyword-overlap count before proposing a candidate — every derived candidate must still be re-verified via a real `command_doc_lookup.lookup(...)` call before being trusted, mirroring the existing curated-alias re-verification discipline. Real docs root has 2,063 files; a full-index build needs a file-count bound and likely per-docs_root in-memory caching. Threshold tuning not yet validated against real data.
- No code has been written yet for any of the above — these are design intentions only, captured here so they aren't lost, not committed decisions.

## Tests / Validation

- Last known-good full suite state: **40 test files, 1,241 test functions, all passing**, as of the `v0.73.0` release commit (`b1c1988`). Not re-run in this session yet.
- No automated tests exist yet for v0.74 (nothing has been implemented).
- Live-environment availability confirmed for future v0.74 live evaluation (`64.x` category, per spec): Ollama reachable at `http://localhost:11434` with `qwen2.5-coder:7b`; `tgauss.exe` present at `C:\gauss26\tgauss.exe`; real docs checkout present. These have NOT yet been exercised for v0.74 — only existence/reachability was checked.

## Known Issues

- Carried over from `v0.73.0` (see its planning doc's "Remaining limitations" section): the curated alias index has only 5 entries; the post-generation symbol checker is conservative, not exhaustive (misses semantic/dimensional errors — the `invpd` non-symmetric-matrix example is real evidence); ambiguity detection depends on `command_doc_lookup`'s own scoring producing a genuine near-tie; the model (`qwen2.5-coder:7b`) still hallucinates when ungrounded — v0.74 is a direct response to these.

## Next Steps

1. Implement `scripts/gauss_pre_execution_validation.py`: documentation-derived concept index (supplementing, not replacing, the curated alias index), documented-signature extraction, generated-call extraction, signature-compatibility validation, documented-precondition model + a small set of deterministic validators (square/symmetric/positive-definite matrix checks for literal matrices only — runtime variables must report `UNVERIFIED`, never guessed), and the `PreExecutionValidationResult`/eligibility computation.
2. Add the module to `pyproject.toml`'s `py-modules` list (see `CLAUDE.md`).
3. Wire into `gauss_conversation_engine.ConversationEngine.ask(...)` and rendering in `gauss_ai_chat.py`, without adding any execution capability.
4. Hard regression tests: `invpd` valid-SPD-literal (eligible) vs. invalid-literal (ineligible, precondition violated) vs. runtime-variable (unverified); `tscsmtControl` vs. real `tscsmtControlCreate` (must stay ineligible, no silent correction).
5. New `64.x` live-Ollama evaluation category (10 scenarios per spec) + a bounded set of real `tgauss.exe -b` spot checks, recorded under `evaluations/runs/`.
6. Documentation: `docs/pre-execution-validation.md` (new), updates to `README.md`, `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, alpha tester docs.
7. Full test suite pass → commit → tag `v0.74.0` → confirm with user before push/release (per `CLAUDE.md` workflow rules).
8. Deliver the mandatory 16-section final report specified in the v0.74 brief, ending with an explicit recommendation and **without auto-starting v0.75**.

## Handoff Notes

- The full v0.74.0 spec (28 phases, success criteria, required 16-section final report) was given verbatim in chat and is **not yet saved to any file**. If this session ends before `planning/v0.74.0-*.md` is created, that spec text will only exist in chat history — consider asking the user to re-paste it, or check chat history/scrollback before re-deriving the design from scratch.
- Real-environment paths referenced above (Ollama endpoint, `C:\gauss26\tgauss.exe`, the real docs-root path) are already non-secret and referenced elsewhere in this repo (`README.md`, `scripts/README.md`) — safe to reuse in future sessions on this same machine.
- This `CLAUDE.md`/`PROJECT_STATUS.md` pair was just introduced in this session (previously neither file existed). No application code was touched as part of that work, per the user's explicit instruction.
