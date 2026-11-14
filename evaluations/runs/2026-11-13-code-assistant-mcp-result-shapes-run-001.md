# Evaluation Result

Date: 2026-11-13
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`bdd196f2…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-84x`), as in 80.x-83.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). Tasks were proposed by the recording session. Tasks 84.1-84.11 ran on 2026-11-13 about 06:30-07:14 local; 84.12-84.13 ran in the same conversation at 19:17-19:43 local (2026-11-14 00:17-00:43 UTC), after the first server session had expired. The client used gauss-ai tools plus read-only `Bash` (folder listings, a search for `prices.csv`, and `C:\Users\Owner\.gauss-ai\config.json`, `docs-manifest.json` and `docs\kmeansfit.rst`), all disclosed in its report; it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.93.0 (tag `v0.93.0`, commit `c52001e`; published to PyPI on 2026-11-13, run `43413821923`), the editable install of this checkout (`gauss-ai version` = 0.93.0).
Prompt ID: 84.1
Prompt Category: MCP Result Shapes and Members of v0.93.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.93.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. Server sessions `8facf350…` (84.1-84.11) and `eeeeb117…` (84.12-84.13); both reported `server_version: 0.93.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation at `v0.93.0` (every verdict, reason and non-matching role check equal to the live response) and at a `git archive` of `76fa779` (the code of `v0.92.1`), and re-ran all eight approved snippets with `tgauss.exe -b`, each from its own new empty directory. The four searches and two reads were not re-run.
Prompt Text:

"Start a GAUSS session and check whether you can run code on my GAUSS installation. Prepare a run of print 1; but don't run it yet. Show me the prompt."

Code:
```gauss
print 1;
```

Captured output (live, equal to the v0.93.0 re-run): **not_ready**.
v0.92.1 code: **not_ready**.

Expected behavior: (recording session's setup step) `real_gauss_allowed: true`, and a prepared prompt the user would decline.

Observed behavior: `gauss_session_start` reported `server_version: 0.93.0`, `real_gauss_allowed: true` and the installed libraries. `print 1;` is **not_ready**: it calls no documented function, so it has nothing to ground on and is never eligible (by design since long before this milestone; v0.92.1 the same). No prompt could be prepared, so this step did not test the opt-in or the decline; the opt-in was first proved by 84.2's prompt and run. **The setup step was the recording session's error**, not a defect: a snippet with no documented call was a bad choice for a prepare. The client explained the verdict correctly and did not work around it.

Pass/fail: Pass
Defect severity: None (task design error, recording session)
Remediation: Use a snippet with a documented call for the opt-in prepare (e.g. `print sumc(1|2);`).

Overall Score: 3.8
Decision: Pass
