# Evaluation Result

Date: 2026-10-28
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`a3570b26…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-81x`), as in 80.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, answered every run prompt themselves, and answered three of the client's own numbered options ("2", "1", "1"). All tasks ran on 2026-10-28, 06:01-06:19 local (11:01-11:19 UTC). The client used only gauss-ai tools: no file read, no shell command, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.90.0 (tag `v0.90.0`, commit `1ee121c`, pushed 2026-10-24; not yet on PyPI), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.90.0).
Prompt ID: 81.10
Prompt Category: MCP Call-Form Alignment of v0.90.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.90.0 over stdio, registered at user scope with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (the 2026-10-23 fetch), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session served every task; `gauss_session_start` reported `server_version: 0.90.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 25 search, read and validation calls through `gauss_mcp_server`'s tool functions at `v0.90.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.89.3` (`328dffa`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all eight approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory.
Prompt Text:

"Check this code for me: plotScatter("a", "b", "c");"

Code (#40): `plotScatter("a", "b", "c");`
Captured output (live, identical on the v0.90.0 re-run): **not_ready**.
Reasons: "plotScatter (argument 1): the argument's literal category (string) does not match the documented type for parameter 'myPlot' (control) in `plotScatter([myPlot, ]x, y)`, or any other documented form"; "plotScatter (argument 2): the argument's literal category (string) does not match the documented type for parameter 'x' (matrix) in `plotScatter([myPlot, ]x, y)`, or any other documented form"; "plotScatter (argument 3): the argument's literal category (string) does not match the documented type for parameter 'y' (matrix) in `plotScatter([myPlot, ]x, y)`, or any other documented form".
v0.89.3: not_ready too, but its reasons named no form.

Expected behavior: not_ready, naming the form (plan §7).

Observed behavior: as expected; the client relayed each argument and type.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
