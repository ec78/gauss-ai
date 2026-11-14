# Evaluation Result

Date: 2026-11-13
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`bdd196f2…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-84x`), as in 80.x-83.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). Tasks were proposed by the recording session. Tasks 84.1-84.11 ran on 2026-11-13 about 06:30-07:14 local; 84.12-84.13 ran in the same conversation at 19:17-19:43 local (2026-11-14 00:17-00:43 UTC), after the first server session had expired. The client used gauss-ai tools plus read-only `Bash` (folder listings, a search for `prices.csv`, and `C:\Users\Owner\.gauss-ai\config.json`, `docs-manifest.json` and `docs\kmeansfit.rst`), all disclosed in its report; it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.93.0 (tag `v0.93.0`, commit `c52001e`; published to PyPI on 2026-11-13, run `43413821923`), the editable install of this checkout (`gauss-ai version` = 0.93.0).
Prompt ID: 84.11
Prompt Category: MCP Result Shapes and Members of v0.93.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.93.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. Server sessions `8facf350…` (84.1-84.11) and `eeeeb117…` (84.12-84.13); both reported `server_version: 0.93.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation at `v0.93.0` (every verdict, reason and non-matching role check equal to the live response) and at a `git archive` of `76fa779` (the code of `v0.92.1`), and re-ran all eight approved snippets with `tgauss.exe -b`, each from its own new empty directory. The four searches and two reads were not re-run.
Prompt Text:

"Compute the 25th and 75th percentiles of 200 uniform draws."

Code:
```gauss
new;

// Reproducible simulation
rndseed 42;

// 200 draws from Uniform(0, 1)
x = rndu(200, 1);

// 25th and 75th percentiles
probs = { 0.25, 0.75 };
q = quantile(x, probs);

print "Percentiles (25th, 75th):";
print q;
```

Captured output (live, equal to the v0.93.0 re-run): **handoff_candidate**.
v0.92.1 code: **handoff_candidate**.

Execution handoff (validation_id `fe29f945168346df90f50a9c6f8cc261`; prepare `request_id` `e6dc1712-e327-4efd-9350-ae73c7c112f5`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
new;

// Reproducible simulation
rndseed 42;

// 200 draws from Uniform(0, 1)
x = rndu(200, 1);

// 25th and 75th percentiles
probs = { 0.25, 0.75 };
q = quantile(x, probs);

print "Percentiles (25th, 75th):";
print q;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: e35d37a0813970b2bec5c738af9e19714022645ada124424bf46b38bb0368815

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`, exit code 0. stdout:
~~~~text
Percentiles (25th, 75th):

      0.26306081 
      0.71174871 
~~~~
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): the same stdout; no file created.

Expected behavior: (optional) `quantile` with a vector of probabilities.

Observed behavior: **handoff_candidate** (v0.92.1 the same): the client wrote the probabilities as a matrix literal `{ 0.25, 0.75 }`, not the `0.25 | 0.75` concatenation that stays unknown. The run equals `tgauss.exe -b` byte for byte.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
