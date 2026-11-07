# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.8
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Compute classification metrics for actual labels 1 0 1 1 0 1 0 0 and predicted labels 1 0 0 1 0 1 1 0."

`gauss_search_docs("classificationMetrics accuracy precision recall")`; one `Bash` search of the package indexes and sources (disclosed).

Code (c09):
```gauss
new;
library gml;

y_true = { 1, 0, 1, 1, 0, 1, 0, 0 };
y_pred = { 1, 0, 0, 1, 0, 1, 1, 0 };

// Prints the confusion matrix and per-class and overall metrics
call classificationMetrics(y_true, y_pred);
```
Captured output (live, identical on the v0.92.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.91.1: **not_ready**.

Execution handoff (prepare, `request_id` `272185fb-a117-49f3-a65c-09138a7e0189`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
new;
library gml;

y_true = { 1, 0, 1, 1, 0, 1, 0, 0 };
y_pred = { 1, 0, 0, 1, 0, 1, 1, 0 };

// Prints the confusion matrix and per-class and overall metrics
call classificationMetrics(y_true, y_pred);
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Library: gml (C:\gauss26\pkgs\gml\lib\gml.lcg)
Request digest: cf6ad4cabba35589f199ea636bd59be478301294bba8a4c903c8abf949c9cfc8

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`; stdout:
```
===================================================
                             Classification metrics
===================================================
       Class   Precision  Recall  F1-score  Support

           0        0.75    0.75      0.75        4 
           1        0.75    0.75      0.75        4 

   Macro avg        0.75    0.75      0.75        8 
Weighted avg        0.75    0.75      0.75        8 

    Accuracy                          0.75        8
```
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): byte-identical stdout; no file created.

Expected behavior: (plan v0.92 §7) a GML call reaches a prompt; the user was to decline this one.

Observed behavior: a candidate on the first validation, with `library gml;`, and it ran; byte-identical to direct `tgauss.exe -b`. The user answered "yes", not the planned "no", so **the decline path was not exercised**. The client's code comment says `classificationMetrics` prints a confusion matrix; it does not, and the client disclosed that, and that the confusion matrix it quoted in its reply was its own calculation.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.8
Decision: Pass
