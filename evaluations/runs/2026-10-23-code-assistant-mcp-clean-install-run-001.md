# Evaluation Result

Date: 2026-10-23
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension 2.1.309), driven live as the MCP client in a fresh conversation (`0819d226…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-80x`), so neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's own memory directory is empty). An earlier conversation in the same folder (`ee5f3edc…`, 06:53 local) only started a session before the real-GAUSS opt-in was registered (`runner: fake`, `real_gauss_allowed: false`). The human asked each task in plain words, one at a time, and answered every run prompt themselves. All tasks ran on 2026-10-23, 06:59-07:18 local (10:59-11:18 UTC). During the tasks the client read no gauss-ai source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`, and read no GAUSS documentation file from disk; it ran `gauss-ai doctor` and two directory listings in PowerShell, and in 80.14 read the user's own `dccelib` package (`C:\gauss26\pkgs\dccelib`, an additional working directory of that Claude Code setup) from disk.
Agent Version: v0.89.1 (tag `v0.89.1`, commit `f6b9c6f`), installed as a stranger would: `pip install "gauss-ai[mcp] @ git+https://github.com/ec78/gauss-ai@v0.89.1"` into the user's Python 3.12 after `pip uninstall` of the editable install, with `~/.gauss-ai/` moved aside first (`gauss-ai version` = 0.89.1).
Prompt ID: 80.1
Prompt Category: MCP Clean-Install Walkthrough of v0.89.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.89.1 over stdio, registered at user scope (`claude mcp add --transport stdio --scope user gauss-ai -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`). Fresh config written by the quickstart: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (a new `gauss-ai docs fetch` on 2026-10-23), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss, no workspace parent. One server session (`e28987e1…`) served every task; `gauss_session_start` reported `server_version: 0.89.1` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run: the recording session (this repository's own Claude Code session) re-ran every one of the 33 search, read and validation calls (8 searches, 11 reads, 14 validations) by calling `gauss_mcp_server`'s tool functions at the `v0.89.1` tag and on a `git archive` of `v0.88.0` (each archive's modules asserted imported), against the same docs copy. **Every live response equals the v0.89.1 re-run in every field** (`validation_id`, digests and the session id aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) re-runs of every approved snippet and of the probes, each from its own new empty directory under the recording session's scratchpad.
Prompt Text:

"Install gauss-ai as a stranger would, following only the README's Quickstart; then start a session and run `print 1+1;`."

Part A, the user's friction log (each Quickstart step):
1. **Install:** worked, with the one planned deviation (a `git+https` URL, since the package is not on PyPI yet). The user found it "a little confusing where I had to do the different installs" (which Python, which terminal, and the separate `claude mcp` step).
2. **Docs:** `gauss-ai docs fetch` worked; the user interrupted it once with a keystroke and had to start over (the fetch is all-or-nothing by design, so nothing partial was left).
3. **Doctor:** `Overall: WARN`, the only warning `workspace_parent: no workspace parent configured`. The README does not say this warning is expected; the handoff never uses a workspace parent (live: the client offered to set it, the user declined).
4. **Connect:** `claude mcp add --transport stdio --scope user gauss-ai -- gauss-ai-mcp` worked.
5. **Real GAUSS:** **the README's command failed as written.** `claude mcp add --transport stdio --scope user -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 gauss-ai -- gauss-ai-mcp` gave `error: missing required argument 'commandOrUrl'`: `-e` takes several values, so it also consumed `gauss-ai`. With the name before `-e` it worked, and `claude mcp get` showed the variable.
6. **Confirm:** the first conversation (`ee5f3edc…`, before step 5) reported `runner: fake`, `real_gauss_allowed: false`; the second reported `server_version: 0.89.1`, `runner: gauss`, `real_gauss_allowed: true`.

Part B, the first run. The recording session's walkthrough told the user to run `print 1+1;` as the trivial check. Live (calls #1-#4):
- `print 1+1;` → **not_ready**: "no documented GAUSS function call was found to ground this code against" (the no-documented-call policy, disclosed since v0.86.0);
- `print sumc(1|1);` and `x = 1|1; print sumc(x);` → **review_required** (`argument_expression` / `argument_assigned_from_expression`: expressions are never evaluated, disclosed);
- `x = { 1, 1 }; print sumc(x);` → handoff_candidate.

Execution handoff (prepare #5, `request_id` `c86d4ae5-fc5d-4da3-827d-b6548df9bd1d`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
x = { 1, 1 };
print sumc(x);
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: af191cda52ac5ba3a1c78f77e1feb1732df2674ab54aaa773b7241377acee9d4

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes". Passed verbatim with that `request_id` (decide #6): outcome `success`, launched True; stdout:
```
2.0000000
```
Real GAUSS (`tgauss.exe -b`, recording session): byte-identical stdout.
v0.88.0, same four snippets: identical verdicts.

Expected behavior: a stranger can install, fetch the docs, connect and opt in from the README alone; the opt-in is confirmed by `real_gauss_allowed: true` and one prompt.

Observed behavior: install, docs, connect and the opt-in all worked, and real GAUSS ran on the first approved prompt. Two real problems for a stranger: **the README's opt-in command is wrong** (finding 1), and the first thing a person naturally types, `print 1+1;`, is refused with a reason a newcomer will not expect (finding 3; the walkthrough's choice of check made it worse). The client reached a runnable form on its own, and asked before changing the user's code.

Pass/fail: Fail
Defect severity: Medium (documentation: the README's real-GAUSS command fails as written)
Remediation: Fix the `claude mcp add ... -e` line in `README.md` and `docs/pypi-readme.md` before the PyPI upload; say in the Quickstart that the workspace-parent WARN is expected; use a documented call as the first-run example.

Overall Score: 3.0
Decision: Fail
