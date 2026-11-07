# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.11
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Draw an old-style xy line plot of sin(x) for x from 0.1 to 10."

`gauss_search_docs("xy pgraph graph X vs Y")` (ungrounded; candidate pages only).

Code (c11):
```gauss
new;
library pgraph;
graphset;

x = seqa(0.1, 0.1, 100);
y = sin(x);

title("sin(x)");
xlabel("x");
ylabel("sin(x)");
xy(x, y);
```
Captured output (live, identical on the v0.92.0 re-run): **not_ready**.
Reasons beyond the standard ones: "line 2: `library` names `pgraph`, whose index (C:\gauss26\lib\pgraph.lcg) is not an installed package; GAUSS's legacy graphics (`pgraph`) write `graphic.tkf` files (planning v0.92 §9) (source_inclusion) -- controlled execution only runs self-contained snippets that compute in memory"; "line 8: `title` is defined by the installed library `pgraph`, which controlled execution does not load (see `installed_libraries.not_allowed`) -- without it GAUSS would stop with G0025 (undefined symbol)"; "line 9: `xlabel` is defined by the installed library `pgraph`, which controlled execution does not load (see `installed_libraries.not_allowed`) -- without it GAUSS would stop with G0025 (undefined symbol)"; "line 10: `ylabel` is defined by the installed library `pgraph`, which controlled execution does not load (see `installed_libraries.not_allowed`) -- without it GAUSS would stop with G0025 (undefined symbol)"; "line 11: `xy` is defined by the installed library `pgraph`, which controlled execution does not load (see `installed_libraries.not_allowed`) -- without it GAUSS would stop with G0025 (undefined symbol)"
v0.91.1: **not_ready** (reasons differ).

Expected behavior: (plan v0.92 §9.2, deviations 1-2) `library pgraph;` and `pgraph` calls are not_ready.

Observed behavior: as expected: the `library pgraph;` line is refused (its graphics write `graphic.tkf`), and `title`, `xlabel`, `ylabel` and `xy` are each `library_required`. The client pointed out an inconsistency in wording: the first reason says `pgraph`'s index "is not an installed package", the others call it "the installed library `pgraph`". Both are true (installed, but not a package under `pkgs`); the first should say so.

Pass/fail: Pass
Defect severity: None (wording)
Remediation: Say "installed, but not a package" (plan v0.92 §12, finding 5).

Overall Score: 3.8
Decision: Pass
