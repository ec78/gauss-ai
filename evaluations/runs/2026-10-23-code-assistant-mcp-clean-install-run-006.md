# Evaluation Result

Date: 2026-10-23
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension 2.1.309), driven live as the MCP client in a fresh conversation (`0819d226…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-80x`), so neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's own memory directory is empty). An earlier conversation in the same folder (`ee5f3edc…`, 06:53 local) only started a session before the real-GAUSS opt-in was registered (`runner: fake`, `real_gauss_allowed: false`). The human asked each task in plain words, one at a time, and answered every run prompt themselves. All tasks ran on 2026-10-23, 06:59-07:18 local (10:59-11:18 UTC). During the tasks the client read no gauss-ai source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`, and read no GAUSS documentation file from disk; it ran `gauss-ai doctor` and two directory listings in PowerShell, and in 80.14 read the user's own `dccelib` package (`C:\gauss26\pkgs\dccelib`, an additional working directory of that Claude Code setup) from disk.
Agent Version: v0.89.1 (tag `v0.89.1`, commit `f6b9c6f`), installed as a stranger would: `pip install "gauss-ai[mcp] @ git+https://github.com/ec78/gauss-ai@v0.89.1"` into the user's Python 3.12 after `pip uninstall` of the editable install, with `~/.gauss-ai/` moved aside first (`gauss-ai version` = 0.89.1).
Prompt ID: 80.6
Prompt Category: MCP Clean-Install Walkthrough of v0.89.1 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.89.1 over stdio, registered at user scope (`claude mcp add --transport stdio --scope user gauss-ai -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`). Fresh config written by the quickstart: `docs_root` = `C:\Users\Owner\.gauss-ai\docs` (a new `gauss-ai docs fetch` on 2026-10-23), `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss, no workspace parent. One server session (`e28987e1…`) served every task; `gauss_session_start` reported `server_version: 0.89.1` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run: the recording session (this repository's own Claude Code session) re-ran every one of the 33 search, read and validation calls (8 searches, 11 reads, 14 validations) by calling `gauss_mcp_server`'s tool functions at the `v0.89.1` tag and on a `git archive` of `v0.88.0` (each archive's modules asserted imported), against the same docs copy. **Every live response equals the v0.89.1 re-run in every field** (`validation_id`, digests and the session id aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) re-runs of every approved snippet and of the probes, each from its own new empty directory under the recording session's scratchpad.
Prompt Text:

"Using T = 200 observations, generate T standard normal draws and print their mean. Then add a loop over t from 1 to 3 that prints t. Run it."

Code (#21):
```gauss
rndseed 345567;
T = 200;
x = rndn(T, 1);
print "Mean of draws:";
print meanc(x);

for t(1, 3, 1);
    print t;
endfor;
```
Captured output (live, identical on the v0.89.1 re-run): **handoff_candidate**.
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad".
**v0.88.0, same snippet: review_required** (`rndn` arg 1 `argument_untraced`, the 79.x-2 shape). The v0.89 §3.7 change (a `for` header after a depth-0 call no longer refuses tracing) is the only difference, and it is what moved this snippet.

Execution handoff (prepare #22, `request_id` `37e2fc25-11ba-435a-a3ee-4de4aeb883ad`). The user's own reply: "yes" (decide #23): outcome `success`, launched True; stdout:
```
Mean of draws:
    -0.071986853 
       1.0000000 
       2.0000000 
       3.0000000
```
Real GAUSS: byte-identical.

**Client error (a false claim about GAUSS, told to the user twice):** "the loop overwrites `T` … `T` now holds 3, the loop's last value, instead of 200". Real GAUSS keeps a `for` counter local to the loop: after `endfor`, `T` is 200 again (spot checks fs1, fs4 and fs6, plan §9.2; inside the loop `T` is the counter, fs3). The client read the merged `user_defined_symbols` list (`["t", "x"]`, lower-cased) as evidence that the loop rewrites `T`. The verdict and the run were right; the advice was wrong.

Expected behavior: with the loop after the use, handoff_candidate (plan §7).

Observed behavior: as expected, and the first live confirmation of 79.x finding 2's fix.

Pass/fail: Pass
Defect severity: None (client error: a false claim about GAUSS loop scoping)
Remediation: None in gauss-ai (client conduct, disclosed)

Overall Score: 3.6
Decision: Pass
