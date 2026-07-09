# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.12.0 GAUSS Language Knowledge Cleanup and CI Guard Prep milestone)
Prompt ID: 19.4
Prompt Category: GAUSS Language Knowledge Cleanup and CI Guard Prep
Prompt Text:

The user asks how PACKAGE_DOC_DIRECTORIES should be refreshed when the GAUSS Applications index changes.

Expected behavior:
- Uses `scripts/README.md` and `scripts/command_doc_lookup.py`.
- Explains `PACKAGE_DOC_DIRECTORIES` is derived from the official `applications.rst` index.
- Explains it is a maintained snapshot, not live parsing.
- Gives refresh steps: inspect `applications.rst`, compare package directory targets, update only directories actually present, regenerate/validate affected package evidence if needed, run `validate_all_evidence.py`.
- States classification is source classification, not licensing verification.
- Does not claim live parsing exists.

Concrete prompt used: "How should PACKAGE_DOC_DIRECTORIES be refreshed when the GAUSS Applications index changes?"

Evidence/context used: `scripts/command_doc_lookup.py`'s `PACKAGE_DOC_DIRECTORIES` constant and its derivation comment; `scripts/README.md`'s "PACKAGE_DOC_DIRECTORIES refresh process" section (added `v0.12.0`); `examples/retrieval/panel-estimation-coverage-audit.md`'s original `applications.rst` findings for `tsmt`/`tspdlib`.

Generated Code Assistant Response:

`PACKAGE_DOC_DIRECTORIES`, in `scripts/command_doc_lookup.py`, is a hardcoded set of top-level docs-root directory names (currently 17: `ad`, `bet`, `bhatlib`, `cf`, `cmlmt`, `comt`, `dc`, `ds`, `fanpac`, `llmt`, `lpmt`, `lrmt`, `mlmt`, `optmt`, `sslib`, `tsmt`, `tspdlib`) derived from the official GAUSS Applications index, `docs_root/applications.rst`. That file lists every separately-distributed "Application" (package) with a `.. card::` entry whose `:link:` target names the package's top-level directory — for example, `TSMT (Time Series MT)` links to `tsmt/index`, so `tsmt` is in the set.

**It is a maintained snapshot, not live parsing.** The tool does not read `applications.rst` at lookup time; it checks a matched file's path against this fixed, in-code set. If the Applications index gains or loses an entry, `PACKAGE_DOC_DIRECTORIES` will not automatically reflect that until someone updates it.

**Refresh steps**, as documented in `scripts/README.md`:
1. Inspect the current `docs_root/applications.rst` and list its `.. card::` entries' `:link:` targets — each target's first path segment is a package directory (e.g., `tsmt/index` -> `tsmt`).
2. Compare that list against the current `PACKAGE_DOC_DIRECTORIES` set in `scripts/command_doc_lookup.py`.
3. Update the set to add any new package directory found, or remove one the index no longer lists — only add a directory name that is actually present in the Applications index, never one that merely looks package-like by name.
4. Regenerate and validate affected evidence only if needed — that is, only for existing committed evidence files whose classification would actually change (a file under a newly-added or newly-removed package directory). Don't regenerate unrelated evidence as part of this refresh.
5. Run `python scripts/validate_all_evidence.py` (and `--strict`) afterward to confirm the refresh introduced no new unexpected result or warning beyond the already-documented two.

**This is source classification, not licensing verification.** A file being labeled `official_package_docs`/`official_package_rst` tells you it lives in a separately-distributed Applications directory in the docs structure — it does not by itself confirm licensing terms, pricing, or version requirements (for example, `tscsFit`'s TSMT dependency, which requires GAUSS/GAUSS Engine v25+). The Code Assistant must still state a package's actual licensing/version dependency explicitly whenever it recommends a package-sourced command, regardless of this classification.

To be clear about current tooling limits: there is no live parsing of `applications.rst` implemented anywhere in this repository today — the refresh above is a manual process a person (or a future automated check) performs when the index changes, not something the lookup tool does automatically on every run.

Response Summary:

The response accurately describes `PACKAGE_DOC_DIRECTORIES` as a hardcoded, `applications.rst`-derived snapshot (not live parsing), gives the real five-step refresh process verbatim from `scripts/README.md`, correctly distinguishes source classification from licensing verification with a concrete example (`tscsFit`/TSMT), and explicitly states no live-parsing capability exists rather than implying one might.

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
- Hallucination and Cross-Language Contamination Avoidance: N/A

Overall Score: 4.0
Decision: Pass

N/A Notes:
- Data Structure Reasoning, Dimension and Numerical Awareness, Maintainability and Best Practices, Hallucination and Cross-Language Contamination Avoidance: marked N/A. This prompt concerns tooling-maintenance process, not GAUSS code, data structures, or cross-language content.
- Function and Package Validity: scored (not N/A) at 4, since the response makes real, verifiable claims about the classification tool's actual current directory list and behavior without inventing anything.
- Testing or Validation: marked N/A. This is a process-documentation question, not a request for a new validation step to run now.

Blocking Issues:
None.

Suggested Improvements:
None blocking.

Follow-up Actions:
- This completes the planned 19.5, 19.1, 19.2, 19.3, 19.4 run order for this batch.
- Proceed to Task A (update `evaluations/runs/INDEX.md`), Task B (update `evaluations/benchmark-coverage.md`), Task C (re-run the tracking guard), and Task D (re-run release readiness) to confirm the batch's own transient warnings clear once tracking is updated.
