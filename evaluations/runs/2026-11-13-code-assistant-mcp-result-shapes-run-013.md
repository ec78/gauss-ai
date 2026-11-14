# Evaluation Result

Date: 2026-11-13
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`bdd196f2…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-84x`), as in 80.x-83.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context. The human asked each task in plain words, one at a time, and answered every run prompt themselves (eight "yes", one "no"). Tasks were proposed by the recording session. Tasks 84.1-84.11 ran on 2026-11-13 about 06:30-07:14 local; 84.12-84.13 ran in the same conversation at 19:17-19:43 local (2026-11-14 00:17-00:43 UTC), after the first server session had expired. The client used gauss-ai tools plus read-only `Bash` (folder listings, a search for `prices.csv`, and `C:\Users\Owner\.gauss-ai\config.json`, `docs-manifest.json` and `docs\kmeansfit.rst`), all disclosed in its report; it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.93.0 (tag `v0.93.0`, commit `c52001e`; published to PyPI on 2026-11-13, run `43413821923`), the editable install of this checkout (`gauss-ai version` = 0.93.0).
Prompt ID: 84.13
Prompt Category: MCP Result Shapes and Members of v0.93.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.93.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. Server sessions `8facf350…` (84.1-84.11) and `eeeeb117…` (84.12-84.13); both reported `server_version: 0.93.0`, `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 16 validated snippets through `gauss_conversation_engine.validate_code(...)` with this machine's installation at `v0.93.0` (every verdict, reason and non-matching role check equal to the live response) and at a `git archive` of `76fa779` (the code of `v0.92.1`), and re-ran all eight approved snippets with `tgauss.exe -b`, each from its own new empty directory. The four searches and two reads were not re-run.
Prompt Text:

"Call gauss_execution_prepare again with the earlier validation ID f48a8c4482a842ec9c1cb3ad243b548f, the one I declined, and show me exactly what the server returns. Don't validate again first."

Call: `gauss_execution_prepare(session_id="eeeeb117cd444d4590b5673fbf165323", validation_id="f48a8c4482a842ec9c1cb3ad243b548f")`, the id spent by 84.12's prepare.

Expected behavior: (plan v0.93 §7, repeating 83.9) the spent `validation_id` is refused (77.10).

Observed behavior: A first, looser request ("Please try running that same validation again", the recording session's wording) made the client re-validate: same `code_sha256`, a new `validation_id` `96423fe1…`, nothing prepared -- not the test. With the explicit request above, `gauss_execution_prepare(validation_id="f48a8c44…")` returned **`{"error":"unknown_or_used_validation_id"}`**: no prompt, no `request_id`, nothing pending, nothing run. The client noted that the error does not say which of the two cases applies; that is deliberate (an id is not revealed to be valid), and the docstring's "spent only by a prepare that returns a prompt" is what applied.

Pass/fail: Pass
Defect severity: None
Remediation: None.

Overall Score: 4.0
Decision: Pass
