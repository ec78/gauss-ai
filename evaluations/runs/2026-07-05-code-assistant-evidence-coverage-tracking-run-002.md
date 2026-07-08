# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.10.0 Evidence Coverage and Routing Regression Guards milestone)
Prompt ID: 17.1
Prompt Category: Evidence Coverage and Tracking Guards
Prompt Text:

The user asks whether local schema-aligned evidence now exists for GAUSS `glm` and whether it validates.

Expected behavior:
- Confirms `examples/retrieval/schema-aligned/glm.evidence.json` exists.
- Reports it was generated from local official `glm.rst`, not hand-written.
- Reports single-file validation passes.
- Reports validate-all default passes.
- Reports validate-all JSON mode passes.
- Notes strict mode fails only because reviewed HDF5 URI path-warning false positives are promoted to failures, now affecting both `glm` and `olsmt`.
- Does not claim schema validation proves GAUSS semantic correctness or execution.
- Mentions any extraction warnings/unresolved questions accurately.

Concrete prompt used: "Do we now have local schema-aligned evidence for GAUSS `glm`, and does it validate?"

Evidence/context used: `examples/retrieval/schema-aligned/glm.evidence.json` (real, generated from local official `glm.rst` via `scripts/command_doc_lookup.py --schema-output --redact-docs-root`); live execution of `python scripts/validate_lookup_evidence.py examples/retrieval/schema-aligned/glm.evidence.json`; live execution of `python scripts/validate_all_evidence.py` in default, `--json`, and `--strict` modes.

Generated Code Assistant Response:

Yes. `examples/retrieval/schema-aligned/glm.evidence.json` exists, and it was generated from the local official `glm.rst` documentation via `scripts/command_doc_lookup.py --schema-output --redact-docs-root` — it is retrieved evidence, not hand-written.

Single-file validation: `python scripts/validate_lookup_evidence.py examples/retrieval/schema-aligned/glm.evidence.json` reports `Result: PASS`, `Schema: valid`, with 4 warnings, all "Unredacted local absolute path found at ..." warnings. All 4 point at the same official documentation example — an HDF5-URI path (`h5://C:/gauss23/examples/testdata.h5/mydata`) that appears verbatim in the official docs — not a real local-machine path leak. This is a reviewed false positive of the same class already documented for `olsmt.evidence.json`.

Aggregate validation: `python scripts/validate_all_evidence.py` (default) reports `Checked 14 file(s): 14 as expected, 0 unexpected`, `Total warnings across all files: 6`, `Overall: PASS`. `--json` mode reports the equivalent structured result (`"overall_pass": true`, `"unexpected_count": 0`). `--strict` reports `Overall: FAIL`, flagging exactly 2 unexpected files: `glm.evidence.json` and `olsmt.evidence.json` — both fail only because their reviewed HDF5-URI path warnings are promoted to failures under strict mode. This is the same documented strict-mode exception policy already recorded in `scripts/README.md` and `schemas/README.md`, now extended to name `glm` alongside `olsmt`.

Extraction notes: the evidence file's `retrieval_status` is `found_incomplete`, with one recorded extraction warning: "no keyword hits for: returns." This is a keyword-search miss, not a real content gap — the `returns_section` field was still fully captured through the `.. function::`/list-table parsing path (visible directly in the evidence file's `returns_section` and `outputs_section` fields), independent of the keyword-search step that produced the warning.

To be precise about what this does and doesn't establish: schema validation confirms the evidence file is structurally well-formed and conforms to `schemas/command_lookup_evidence.schema.json`. It does not confirm that the described `glm` behavior is currently accurate beyond what the official docs snapshot says, and no GAUSS code was executed to produce or check this evidence — everything above comes from static extraction and schema/structure validation only.

Response Summary:

The response confirms the evidence file's existence and real (not hand-written) provenance, reports accurate single-file and aggregate validation results across all three modes (default, `--json`, `--strict`) matching the actual tool output, correctly attributes the two strict-mode failures to the documented HDF5-URI false-positive pattern now covering both `glm` and `olsmt`, accurately explains the one extraction warning without overstating it as a real gap, and explicitly distinguishes schema validation from GAUSS semantic correctness and execution.

Scores:
- GAUSS Syntax Correctness: N/A
- Function and Package Validity: 4
- Data Structure Reasoning: N/A
- Dimension and Numerical Awareness: N/A
- Task Mode Fit: 4
- Explanation Quality: 4
- Assumptions and Dependencies: 4
- Maintainability and Best Practices: N/A
- Testing or Validation: 4
- Hallucination and Cross-Language Contamination Avoidance: 4

Overall Score: 4.0
Decision: Pass

N/A Notes:
- GAUSS Syntax Correctness, Data Structure Reasoning, Dimension and Numerical Awareness, Maintainability and Best Practices: marked N/A. No GAUSS code was generated or reviewed in this response; it concerns evidence-file existence and schema validation only.
- Function and Package Validity: scored (not N/A) at 4, since the response makes real claims about the `glm` function's documented family/link options without inventing anything.

Blocking Issues:
None.

Suggested Improvements:
None blocking.

Follow-up Actions:
- Proceed to 17.2 (logistic regression response uses local glm evidence) next per the planned run order.
