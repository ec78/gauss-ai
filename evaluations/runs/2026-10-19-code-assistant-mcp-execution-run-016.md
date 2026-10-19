# Evaluation Result

Date: 2026-10-19
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation; the human asked each task in plain words, one at a time. All twenty tasks ran on 2026-10-19 in one server session (handoff runs 07:07-07:26). During the tasks the session read no source, no planning doc, neither PROJECT_STATUS.md nor KNOWN_LIMITATIONS.md, and no `.rst` page outside `gauss_search_docs` (v0.86 plan §12.7).
Agent Version: v0.86.0 (released; tag `v0.86.0`, commit `5bb1eaa`; HEAD `18f6470`, whose `scripts/` is identical to the tag), editable install of this checkout (`gauss-ai version` = 0.86.0).
Prompt ID: 77.16
Prompt Category: MCP Execution Re-evaluation of v0.86.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.86.0 over stdio; real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`; workspace_parent = `C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces`). **The server held GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1**, proven before any task by one `gauss_execution_prepare` that returned a `rendered_prompt` (77.1; 76.x finding 1 is fixed). Session cef3f6beb0d34a8289e2432eb0709fb2. Two `gauss-ai-mcp` processes were running (PIDs 33504 and 35604, started 06:54:51 and 06:56:40); which one served this session was not determined. The client model wrote every query and snippet itself. Post-run diagnosis: `gauss_conversation_engine.validate_code(...)` called directly by the recording session on the same docs, on `git archive`s of v0.86.0 and v0.85.0 (`f11505e`), each archive's own modules asserted imported; all 22 live verdicts reproduced exactly on the v0.86.0 archive (state, every gap, and `code_sha256` for the six that were issued one). Real-GAUSS evidence: print-only `tgauss.exe -b` (GAUSS 26.1.4) runs of the client's programs (all but S15, a file write) and spot checks x01-x07, from a scratch directory. Handoff runs through MCP: four approved (77.9, 77.11, 77.16, 77.17), one declined (77.10).
Prompt Text:

"Sort a matrix by its second column."

The user's reply to the run prompt: "yes".

Searches:
```
search_docs("sortc") -> grounded: sortc.rst
```
The client searched `sortc` by name (prior knowledge). The user's wording does not reach `sortc` (73.12;
re-checked in 76.16 on the same archives).

Code (S16):
```gauss
x = { 4 7 3,
      1 3 2,
      3 9 8,
      6 1 5 };

y = sortc(x, 2);

print "Sorted on column 2 (ascending):";
print y;
```

Captured output: **handoff_candidate**, no gaps; `validation_id` b9a52477ae384f8aa5a0b54ef0a2b671,
`code_sha256` f7ed11b4….

Exact `rendered_prompt` (request_id `2ac4f5cd-ca4c-4761-8ba3-a3dee0d659c8`):

````text
Ready for controlled execution.

Code:
```gauss
x = { 4 7 3,
      1 3 2,
      3 9 8,
      6 1 5 };

y = sortc(x, 2);

print "Sorted on column 2 (ascending):";
print y;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Workspace parent: C:\Users\eclow\OneDrive\Documents\GAUSS-AI-Workspaces
Request digest: 2818ef8c44b6c5b7a5f409347fe148fc660664a373fedb616b6b3354644bd1c3

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
````

Decision: "yes", passed verbatim.

Handoff result (verbatim stdout; `outcome: success`, `launched: true`, `execution_status: completed`, `exit_code: 0`, `timed_out: false`, `workspace_state: null`, `provenance: null`; result_digest `d01d5a07701fcc0afb52a759426fc7b682203994b975732f7054362a1bb61316`; GAUSS job header `inline_sos6egzs.gss ( C:\Users\Owner\AppData\Local\Temp\gauss_ai_handoff_uh51u7eb\.gauss_code_execution_generated ), Mon Oct 19 07:21:14 2026`):
```
Sorted on column 2 (ascending):

       6.0000000        1.0000000        5.0000000
       1.0000000        3.0000000        2.0000000
       4.0000000        7.0000000        3.0000000
       3.0000000        9.0000000        8.0000000 
```

Real GAUSS (S16 via `tgauss.exe -b`): byte-identical stdout; as predicted.

Consumed id: after the tasks, re-submitting b9a52477… to `gauss_execution_prepare` (no decide) returned
`{"error": "unknown_or_used_validation_id"}`.

Diagnosis (direct `validate_code`): identical, same sha. v0.85.0: identical.

Expected behavior: handoff_candidate; approved run matches direct GAUSS; the id is single-use.

Observed behavior: As expected; the known `sortc` recall gap (73.12) applies to the user's wording.

Pass/fail: Pass
Defect severity: None (known search gap)
Remediation: v0.87.0 search milestone.

Overall Score: 3.6
Decision: Pass
