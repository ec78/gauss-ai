# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (started after `/clear`); the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session. During the tasks the session read neither the planning doc nor PROJECT_STATUS.md; it read one source file once (76.18) and several published `.rst` pages directly (v0.86 plan §11.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `a0e007c`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0). The live server's own output carries v0.86.0-only behavior (member literals, word operators and `struct` definitions are no longer INVALID; see the v0.85.0 comparison in each file).
Prompt ID: 76.12
Prompt Category: Structure Members, Word Operators and Structure Definitions (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 process over stdio (PID 34332, started 2026-10-19 05:43:25); real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). **The server was NOT started with GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**: the local-scope override is stored under the project key `C:/Users/eclow/Documents/GitHub/gauss-ai`, but this VS Code session ran under `c:/Users/eclow/Documents/GitHub/gauss-ai`, whose entry has no MCP servers, so the tracked `.mcp.json` (empty `env`) was used (plan §11.6, finding 1). Session afd166cb225b49f1abef66fa937dab95. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 19 live verdicts reproduced exactly on the v0.86.0 archive (state, gap causes, and `code_sha256` where issued). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs and spot checks e01-e08, from a scratch directory. These are recording-session runs, not handoff runs: no code executed through the handoff in 76.x.
Prompt Text:

"Compute the eigenvalues of a symmetric 3x3 matrix."

Searches:
```
search_docs("eigh eigenvalues symmetric matrix") -> partially_grounded: eigh.rst; `eigenvalues`, `symmetric` unmatched
```

Code (S12): `x = {2 1 0, 1 2 1, 0 1 2}; va = eigh(x); print va;` The client chose a tridiagonal Toeplitz matrix so the
answer has a closed form (2 - √2, 2, 2 + √2) and said it had not checked the output order.

Captured output: **`handoff_candidate`**, no gaps; `validation_id` c3847e2ad7154e399e669a320cb7fee9 (never prepared:
the user did not ask to run it and the opt-in was still absent).

Diagnosis (direct `validate_code`): identical. The client observed that the validator registers no symmetry
precondition for `eigh` (unlike `invpd`) and labelled it an observation, not a defect.

v0.85.0, same snippet: identical in every field.

Real GAUSS (S12 verbatim): `0.58578644 2.0000000 3.4142136` (ascending), as computed. Spot check e07: a non-symmetric
input runs without error and returns the eigenvalues of the matrix built from its lower triangle, so a non-symmetric
literal would reach handoff_candidate and print the wrong matrix's eigenvalues. `eigh.rst` says "Computes the eigenvalues
of a complex hermitian or real symmetric matrix"; the precondition registry covers `invpd`, `solpd` and `chol` only
(finding 6).

Expected behavior: handoff_candidate; correct values.

Observed behavior: As expected.

Pass/fail: Pass
Defect severity: None (observation: finding 6)
Remediation: Candidate precondition-registry entry for `eigh` (finding 6).

Overall Score: 4.0
Decision: Pass
