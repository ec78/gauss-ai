# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.8
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"Compute the mean of each column of a matrix made by putting two random 10×2 matrices side by side."

Code (c19):
```gauss
// Reproducible draws
rndseed 20261106;

// Two random 10x2 matrices (standard normal)
a = rndn(10, 2);
b = rndn(10, 2);

// Put them side by side: 10x4
c = a ~ b;

// Mean of each column (4x1), printed as a row
print "Column means (a1, a2, b1, b2):";
print meanc(c)';
```
Captured output (live, identical on the v0.91.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.90.0: **review_required**.
  v0.90.0 reasons: "parameter role unknown -- `meanc` argument 1 (parameter `x`): `c` is assigned from an expression (`a ~ b`), which is never evaluated"

Execution handoff (prepare, `request_id` `ec91982d-273a-4450-9589-bb2036840ef8`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
// Reproducible draws
rndseed 20261106;

// Two random 10x2 matrices (standard normal)
a = rndn(10, 2);
b = rndn(10, 2);

// Put them side by side: 10x4
c = a ~ b;

// Mean of each column (4x1), printed as a row
print "Column means (a1, a2, b1, b2):";
print meanc(c)';

```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: ed46ad25a3d357a8c1ef6a48120424cc88e238c276e893cad0e038965307ec79

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`; stdout:
```
Column means (a1, a2, b1, b2):
     -0.74469052      -0.27109630      0.027164317      -0.30728647
```
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): byte-identical stdout; no file created.

Expected behavior: (81.8's `meanc(x ~ y)` class) a column mean of a concatenation reaches `handoff_candidate`.

Observed behavior: as expected, on the first try. The client assigned `c = a ~ b` and called `meanc(c)`; the traced concatenation was accepted (v0.90.0: review_required, "`c` is assigned from an expression (`a ~ b`), which is never evaluated"). The run is byte-identical. The client then corrected its own expected range (±0.6) honestly when one mean fell outside it.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
