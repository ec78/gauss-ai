# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.7
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"What is the tspdlib library and what does it cover?"

No gauss-ai tool was called. The client listed `C:\gauss26\pkgs`, read the installed package's `package.json`, and read `tspdlib/docs/tspdlib-landing.rst` and `changelog.rst` directly from the docs directory.

Expected behavior: Plan §7: "opening a listed candidate by name (a hyphenated guide page)". The `tspdlib-landing` page is reachable: a recording-session probe on v0.88.0 shows `tspdlib` → ungrounded with candidate `tspdlib-landing` (keyword_match), and `tspdlib-landing` → grounded (§3.4).

Observed behavior: The answer is accurate against the landing page (every function group and the citation), but **the client bypassed the server entirely**, so the plan's hyphenated-candidate path was not exercised live. The recording-session probe above shows it would have worked.

Search: none through the tool. The client went straight to the files it could see on disk, steered by knowing where the docs live (from `CLAUDE.md`'s description of `docs_root` and the 79.3 search results).

Pass/fail: Pass
Defect severity: Minor (client conduct: the server was not used; disclosed)
Remediation: None to the server.

Overall Score: 3.5
Decision: Pass
