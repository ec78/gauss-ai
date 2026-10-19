# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.5
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Define my own structure to hold regression results (coefficients, standard errors and a label), fill it with OLS estimates from simulated data, and print it."

Follow-ups: "Run it." -> "Leave it as review_required and move on to the next task."

Searches:
```
search_docs("define structure struct members matrix string") -> partially_grounded: structures guide; `define`, `struct`, `members` unmatched
search_docs("invpd diag sqrt rows cols") -> grounded: diag.rst, sqrt.rst, rows.rst, cols.rst  (invpd silently dropped; 76.x finding 5)
```
The client noticed in its own reasoning that `invpd` came back neither as a source nor as unmatched, relied on
`validate_code`'s grounding of `invpd` (`invinvpd.rst`) instead, and **did not tell the user** about the omission.

Code (S04):
```gauss
struct regResults {
    matrix b;
    matrix se;
    string label;
};

rndseed 24601;
n = 200;
x1 = rndn(n, 1);
x2 = rndn(n, 1);
y = 1 + 0.5 * x1 - 2 * x2 + rndn(n, 1);
X = ones(n, 1) ~ x1 ~ x2;

xxi = invpd(X'X);
bhat = xxi * X'y;
e = y - X * bhat;
s2 = (e'e) / (rows(X) - cols(X));

struct regResults res;
res.b = bhat;
res.se = sqrt(diag(s2 * xxi));
res.label = "OLS: y on constant, x1, x2";

print res.label;
print "Coefficients:";
print res.b;
print "Standard errors:";
print res.se;
```

Captured output: **review_required**; precondition `invpd` `unverified` (`runtime_dependent`); role gaps
`invpd` (`X'X`), `sqrt`, `diag` `argument_expression`; `rows`, `cols` `argument_assigned_from_expression`.
Syntax `validated`, no issues.

"Run it.": no `validation_id` existed, so nothing was prepared. The client did **not** pass "Run it." to
`gauss_execution_decide` (the only pending request was 77.1's `det` prompt, which the user had not been shown
for this code), explained why, and offered (1) disclosed restructuring or (2) leaving it. The user chose (2).

Diagnosis (direct `validate_code`): identical. Client explanation right. Two "observations" it raised were
designed behavior, labelled as undiagnosed at the time: the struct definition passing syntax (v0.86.0 §3.3,
`struct_definition`), and `regResults`/`res` missing from `user_defined_symbols` (that list holds only
statement-leading assignment targets and `proc` names, for the unknown-symbol check; a bare declaration is
neither).

v0.85.0, same snippet: not_ready, syntax INVALID (`matrix_literal_row_separator` on the definition, line 1).

Real GAUSS (S04): `1.1290817 0.47362853 -2.1266152`, SEs `0.0740 0.0660 0.0775` (true 1, 0.5, -2).

Expected behavior: review_required; no `validation_id`, so "Run it." cannot run anything; no decide call.

Observed behavior: As expected. The client re-surfaced 76.x finding 5 (silent fifth-symbol drop) in its reasoning but did not disclose it.

Pass/fail: Pass
Defect severity: Minor (search, known: 76.x finding 5)
Remediation: v0.87.0 search milestone (76.x finding 5).

Overall Score: 3.8
Decision: Pass
