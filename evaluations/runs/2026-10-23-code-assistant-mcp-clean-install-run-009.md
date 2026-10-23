# Evaluation Result

Date: 2026-10-23
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension 2.1.309), driven live as the MCP client in a fresh conversation (`0819d226…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-80x`), so neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's own memory directory is empty). An earlier conversation in the same folder (`ee5f3edc…`, 06:53 local) only started a session before the real-GAUSS opt-in was registered (`runner: fake`, `real_gauss_allowed: false`). The human asked each task in plain words, one at a time, and answered every run prompt themselves. All tasks ran on 2026-10-23, 06:59-07:18 local (10:59-11:18 UTC). During the tasks the client read no gauss-ai source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`, and read no GAUSS documentation file from disk; it ran `gauss-ai doctor` and two directory listings in PowerShell, and in 80.14 read the user's own `dccelib` package (`C:\gauss26\pkgs\dccelib`, an additional working directory of that Claude Code setup) from disk.
Agent Version: v0.89.1 (tag `v0.89.1`, commit `f6b9c6f`), installed as a stranger would: `pip install "gauss-ai[mcp] @ git+https://github.com/ec78/gauss-ai@v0.89.1"` into the user's Python 3.12 after `pip uninstall` of the editable install, with `~/.gauss-ai/` moved aside first (`gauss-ai version` = 0.89.1).
Prompt ID: 80.9
Prompt Category: MCP Clean-Install Walkthrough of v0.89.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.89.1 over stdio, registered at user scope (`claude mcp add --transport stdio --scope user gauss-ai -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`). Fresh config written by the quickstart: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (a new `gauss-ai docs fetch` on 2026-10-23), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss, no workspace parent. One server session (`e28987e1…`) served every task; `gauss_session_start` reported `server_version: 0.89.1` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run: the recording session (this repository's own Claude Code session) re-ran every one of the 33 search, read and validation calls (8 searches, 11 reads, 14 validations) by calling `gauss_mcp_server`'s tool functions at the `v0.89.1` tag and on a `git archive` of `v0.88.0` (each archive's modules asserted imported), against the same docs copy. **Every live response equals the v0.89.1 re-run in every field** (`validation_id`, digests and the session id aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) re-runs of every approved snippet and of the probes, each from its own new empty directory under the recording session's scratchpad.
Prompt Text:

"Check this code for me: y = colMedianz(rndn(10, 2)); print y;"

Code (#27):
```gauss
y = colMedianz(rndn(10, 2)); print y;
```
Captured output (live, identical on the v0.89.1 re-run): **not_ready**.
Reasons: "unresolved/unsupported call symbol(s): colMedianz".
Coverage gaps: signature/colMedianz arg None (`None`) `call_undocumented`
Unknown symbols: `colMedianz`
v0.88.0: identical.

The client searched `median of each column` (#28, `median` via the curated alias), proposed `median`, validated it (#29: handoff_candidate) and, after the user's "yes" to its offer, showed the prompt (prepare #30, `request_id` `abb0e62d-7e7c-4304-8939-5dd511da1552`). The user's own reply: "yes" (decide #31): outcome `success`, launched True; stdout:
```
0.11468631 
      0.34301880
```
Real GAUSS: same 2×1 shape; the values differ, as the snippet has no `rndseed` (the client said so before the run).

Expected behavior: not_ready, naming `colMedianz` (plan §7).

Observed behavior: as expected.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
