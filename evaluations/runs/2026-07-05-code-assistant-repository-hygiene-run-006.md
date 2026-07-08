# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.11.0 Repository Hygiene and Evaluation Policy Cleanup milestone)
Prompt ID: 18.5
Prompt Category: Repository Hygiene and Evaluation Policy Cleanup
Prompt Text:

The user asks whether command_doc_lookup.py can now distinguish core official docs from official package docs.

Expected behavior:
- Uses `scripts/command_doc_lookup.py`, `scripts/README.md`, and evidence examples.
- Explains the schema already supported official package source types.
- Explains the implementation now uses an `applications.rst`-derived package directory list.
- Confirms core docs such as `glm` remain `official_docs`/`official_local_rst`.
- Confirms package docs such as `tscsfit` now classify as `official_package_docs`/`official_package_rst`.
- Explains the remaining limitation: the package directory list is a hardcoded snapshot and should be refreshed if the Applications index changes.
- Does not claim live parsing exists if it does not.
- Does not overstate package classification as licensing verification.

Concrete prompt used: "Can command_doc_lookup.py now distinguish core official docs from official package docs?"

Evidence/context used: `scripts/command_doc_lookup.py`'s `PACKAGE_DOC_DIRECTORIES` constant and `classify_source()` function; `scripts/README.md`'s "Core vs. package source classification" paragraph; `examples/retrieval/schema-aligned/glm.evidence.json` and `examples/retrieval/schema-aligned/tscsfit.evidence.json`'s current `source_authority`/`source_type` fields.

Generated Code Assistant Response:

Yes. This was fixed in `v0.11.0` — the schema already supported the distinction before this fix; what was missing was the tool actually assigning it.

Before `v0.11.0`, `command_doc_lookup.py` labeled every local `.rst` match `official_docs`/`official_local_rst` regardless of where the file lived. The schema (`schemas/command_lookup_evidence.schema.json`) already defined `official_package_docs` and `official_package_rst` as distinct enum values — the gap was purely in the tool's extraction/classification logic, not the schema.

The fix adds a `PACKAGE_DOC_DIRECTORIES` constant and a `classify_source()` function to `command_doc_lookup.py`. The directory list is derived from the official GAUSS Applications index (`docs_root/applications.rst`) — that file lists every separately-distributed package with a `:link:` target naming its top-level directory (for example, `TSMT (Time Series MT)` links to `tsmt/index`). A matched file is classified as `official_package_docs`/`official_package_rst` if its docs-root-relative path starts with one of those known package directories; otherwise it's classified as core documentation (`official_docs`/`official_local_rst`), the same as before.

Confirmed directly from the committed evidence files:
- `examples/retrieval/schema-aligned/glm.evidence.json` — `glm.rst` is a top-level, core-docs file, and its `source_authority`/`source_type` remain `official_docs`/`official_local_rst`, unchanged by the fix.
- `examples/retrieval/schema-aligned/tscsfit.evidence.json` — `tsmt/tscsfit.rst` is under the `tsmt/` package directory, and its `source_authority`/`source_type` now read `official_package_docs`/`official_package_rst`, having been regenerated after the fix.

**Remaining limitation, stated plainly:** the package directory list is a hardcoded snapshot of `applications.rst` as read during `v0.11.0`, not a live parse of that file at lookup time. It should be refreshed if the Applications index changes. A directory missing from the snapshot falls back to core classification by default, so a stale snapshot can only under-classify a newer package as core — it cannot mis-classify real base-GAUSS documentation as a package.

Two things this fix does **not** do: it does not implement live parsing of `applications.rst` — that would be a further, not-yet-done step. And a file being labeled `official_package_docs` is not, by itself, a licensing verification — whether a package requires a separate license (as TSMT does) is a fact that must still be stated explicitly in a response, the same as before this fix; the classification only improves the evidence file's own labeling accuracy.

Response Summary:

The response confirms the classification now works, correctly attributes the pre-existing gap to the tool's extraction logic rather than the schema, accurately describes the `applications.rst`-derived implementation without overstating it as live parsing, cites the real, current `source_authority`/`source_type` values for both `glm` (unchanged) and `tscsfit` (now correctly package-classified), states the hardcoded-snapshot limitation and its safe failure direction, and explicitly declines to treat the new classification as licensing verification.

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
- GAUSS Syntax Correctness, Data Structure Reasoning, Dimension and Numerical Awareness, Maintainability and Best Practices, Hallucination and Cross-Language Contamination Avoidance: marked N/A. This prompt concerns tooling classification behavior, not GAUSS code, data structures, or cross-language content.
- Function and Package Validity: scored (not N/A) at 4, since the response makes real, verifiable claims about how the classification tool and evidence fields behave without inventing anything.
- Testing or Validation: marked N/A. This is a tooling-behavior confirmation question, not a request for a new validation step.

Blocking Issues:
None.

Suggested Improvements:
None blocking.

Follow-up Actions:
- This completes the planned 18.6, 18.1, 18.2, 18.3, 18.4, 18.5 run order for this batch.
- Proceed to Task A (update `evaluations/runs/INDEX.md`), Task B (update `evaluations/benchmark-coverage.md`), and Task C (re-run the tracking guard to confirm the 6 transient "Not Run" warnings clear once tracking is updated).
