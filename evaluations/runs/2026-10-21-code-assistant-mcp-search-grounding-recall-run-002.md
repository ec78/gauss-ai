# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.2
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"Sort a matrix by its second column."

Search `sort a matrix by its second column` (live, identical on the v0.88.0 re-run): **partially_grounded**
- sources: `sortc` (sortc.rst)
- unmatched: ['second']; ambiguous: none
- candidates: `date` (derived_from_docs), `sortmc` (derived_from_docs), `sortr/sortrc` (derived_from_docs), `sumc` (derived_from_docs)
- v0.87.0, same query: **ungrounded**; sources: none; unmatched: ['sort', 'its', 'second']; ambiguous: ['sort a matrix by its second column']; candidates: `date` (ambiguous_resolution), `sortmc` (ambiguous_resolution), `sortr/sortrc` (ambiguous_resolution), `sumc` (ambiguous_resolution)

Code (call #7):
```gauss
x = { 4 7 3,
      1 3 2,
      3 4 8 };

// Sort the rows of x by column 2, ascending
y = sortc(x, 2);
print y;

// Descending order on column 2
y_desc = sortc(x, 2, -1);
print y_desc;
```

Captured output (live, reproduced exactly on v0.88.0): **handoff_candidate**; preconditions: none; `code_sha256` 4f686229c389….
Reasons: "generated code is grounded and symbol-supported"; "documented call signatures are compatible"; "syntax was validated with no known violation"; "no documented precondition is known to be violated"; "validation coverage is broad"
Coverage gaps: none.
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): runs; byte-identical to the handoff run below.

Exact `rendered_prompt` (request_id `9cb4b5ad-0c27-411b-a2f4-3b8a0c6abbc2`, digest `0af8a4948f384ed6b111b80d19ed2f6ae5aa5cdf1bd864d9a3995ca0232fef87`):

````text
Ready for controlled execution.

Code:
```gauss
x = { 4 7 3,
      1 3 2,
      3 4 8 };

// Sort the rows of x by column 2, ascending
y = sortc(x, 2);
print y;

// Descending order on column 2
y_desc = sortc(x, 2, -1);
print y_desc;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 0af8a4948f384ed6b111b80d19ed2f6ae5aa5cdf1bd864d9a3995ca0232fef87

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes" (the user's reply, verbatim), passed with request_id `9cb4b5ad-0c27-411b-a2f4-3b8a0c6abbc2` → `outcome: success`, `launched: true`, `exit_code: 0`, `timed_out: false`; echoed request_id `9cb4b5ad-0c27-411b-a2f4-3b8a0c6abbc2` and request_digest `0af8a4948f38…` (the prompt's); result_digest `a27134d217b397359975872ab7cb89e875a24135835aef596d3744b01d266879`. Verbatim stdout:

```text

       1.0000000        3.0000000        2.0000000 
       3.0000000        4.0000000        8.0000000 
       4.0000000        7.0000000        3.0000000 

       4.0000000        7.0000000        3.0000000 
       3.0000000        4.0000000        8.0000000 
       1.0000000        3.0000000        2.0000000
```

Direct `tgauss.exe -b` from a new empty directory: **byte-identical** to the handoff stdout.

Expected behavior: The sort-by-column alias grounds `sortc`; handoff_candidate; an approved run matches direct GAUSS.

Observed behavior: The search grounded `sortc` (partially_grounded, `second` unmatched); v0.87.0 is ungrounded with the whole question ambiguous. The four candidates (`date`, `sortmc`, `sortr/sortrc`, `sumc`) are now labeled `derived_from_docs` (v0.87.0: `ambiguous_resolution`). The client used `sortc(x, 2)` and `sortc(x, 2, -1)` from the excerpt, predicted the output, and the approved run matched the prediction exactly.

Search: the user's own words; no candidate needed. The client mentioned `sortmc` from the candidate list as an alternative, without opening its page.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 4.0
Decision: Pass
