# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.10
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Estimate a quantile ARDL model with the qardl package on simulated data."

`gauss_search_docs("qardl quantile autoregressive distributed lag")` (`qardl` unmatched); then two `Bash` commands listing and reading `C:\gauss26\pkgs\qardl\src` (disclosed).

Code (c10):
```gauss
new;
library qardl;

// Set seed for repeatable results
rndseed 31415;

// Simulate x as a random walk and y as an ARDL process tied to it
T = 500;
x = cumsumc(rndn(T, 1));
e = rndn(T, 1);
y = zeros(T, 1);
for t(2, T, 1);
    y[t] = 0.5 * y[t-1] + 0.3 * x[t] + 0.2 * x[t-1] + e[t];
endfor;

// Long-run effect of x on y is (0.3 + 0.2) / (1 - 0.5) = 1
data = y~x;

// QARDL(1, 1) at the 25th, 50th and 75th percentiles
tau = { 0.25, 0.5, 0.75 };
struct qardlOut qOut;
qOut = qardl(data, 1, 1, tau);

print "Long-run parameter at each quantile (true value 1):";
print qOut.bigbt;
```
Captured output (live, identical on the v0.92.0 re-run): **not_ready**.
Reasons beyond the standard ones: "line 2: `library` names `qardl`, which has no pages of its own in the fetched GAUSS documentation, so its functions cannot be checked (planning v0.92 §8.1) (source_inclusion) -- controlled execution only runs self-contained snippets that compute in memory"
v0.91.1: **not_ready** (reasons differ).

Expected behavior: (plan v0.92 §8.1) a package with no pages of its own stays not_ready, saying why.

Observed behavior: as expected: "`library` names `qardl`, which has no pages of its own in the fetched GAUSS documentation", and `qardl` itself is an unknown symbol. The client wrote the call from the installed source, not from documentation, and said so.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
