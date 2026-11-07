# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`f9c5e81c…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-83x`), as in 80.x-82.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes"). Tasks were proposed by the recording session. All tasks ran on 2026-11-06, 19:47-21:34 local (2026-11-07 00:47-02:34 UTC), with a pause between 00:49 and 02:17 UTC and a client-side API outage (`ENOTFOUND`, 02:17-02:20 UTC) during 83.4. The client used gauss-ai tools plus, in 83.6, 83.7, 83.8 and 83.10, `Read`, `Grep` and `Bash` on the installed packages' sources and indexes (all read-only, all disclosed in its report); it read no source of this repository, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.92.0 (tag `v0.92.0`, commit `e3a995d`; published to PyPI on 2026-11-06, run `42319052456`), the editable install of this checkout after the running servers were stopped (`gauss-ai version` = 0.92.0).
Prompt ID: 83.5
Prompt Category: MCP Installed Libraries of v0.92.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.92.0 over stdio, registered at local scope for the folder under both drive-letter spellings with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe` (GAUSS 26.1.4), `default_runner` = gauss. One server session (`046a4026…`) served every task; `gauss_session_start` reported `server_version: 0.92.0`, `real_gauss_allowed: true` and `installed_libraries` allowed `cmlmt, comt, gml, maxlikmt, optmt, sslib, tsmt, tspdlib`, not allowed `coint, dccelib, pubtable, qardl, quaids, timeseries, pgraph`. The client model wrote every query and snippet itself. Post-run, the recording session re-ran all 22 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.92.0`: **every live response equals the re-run in every field** (ids and digests aside). It compared every one with a `git archive` of `v0.91.1` (`696259d`), diagnosed each non-candidate verdict with `validate_code(...)` directly, and re-ran all five approved snippets with `tgauss.exe -b`, each from its own new empty directory.
Prompt Text:

"Cluster 150 random 2-D points into 3 groups with k-means and print how many points are in each group."

`gauss_search_docs("kmeansFit k-means clustering")`, `gauss_read_doc("kmeansfit.rst", "Examples")`.

Code (c04):
```gauss
new;
library gml;

// Set seed for repeatable results
rndseed 4417;

// Simulate 150 random 2-D points
X = rndn(150, 2);

// Fit k-means with 3 clusters
struct kmeansModel mdl;
mdl = kmeansFit(X, 3);

// Count the points assigned to each cluster
cluster_id = { 1 2 3 };
n_per_cluster = sumc(mdl.assignments .== cluster_id);

print "Cluster and number of points:";
print cluster_id'~n_per_cluster;
```
Captured output (live, identical on the v0.92.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `kmeansFit` argument 1 (parameter `X`): no documented `:type` line was matched to this parameter"; "parameter role unknown -- `sumc` argument 1 (parameter `x`): `mdl.assignments .== cluster_id` is an expression whose category could not be determined: `.assignments` is not a modelled numeric operator or operand"
v0.91.1: **not_ready**.

Expected behavior: a GML k-means fit with `library gml;` gets past the library rule.

Observed behavior: library accepted; review_required for two gaps. (1) `kmeansFit`'s first parameter has no matched `:type`: `kmeansfit.rst`'s syntax line names it `X` but its parameter list says `X_train` (a documentation inconsistency, for Aptech). (2) `mdl.assignments .== cluster_id` contains member access, an unmodelled operand (v0.91.0 disclosed). Not run. At v0.91.1: not_ready.

Pass/fail: Pass
Defect severity: Low
Remediation: Structure-member operands (plan v0.92 §12, finding 3); report `kmeansfit.rst`.

Overall Score: 3.6
Decision: Pass
