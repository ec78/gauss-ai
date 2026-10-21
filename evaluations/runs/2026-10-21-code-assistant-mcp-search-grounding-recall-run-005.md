# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.5
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"Show me a for loop in GAUSS"

Search `for` (live, identical on the v0.88.0 re-run): **grounded**
- sources: `for` (for.rst)
- unmatched: none; ambiguous: none
- v0.87.0, same query: **ungrounded**; sources: none; unmatched: none; ambiguous: none; candidates: none

Code (call #18):
```gauss
// Basic loop: sum of squares 1..5
total = 0;
for i (1, 5, 1);
    total = total + i^2;
endfor;
print "Sum of squares: " total;

// Counting down by 2
for j (10, 1, -2);
    print j;
endfor;

// Filling a vector, with continue and break
x = zeros(10, 1);
for k (1, 10, 1);
    if k == 3;
        continue;      // skip k = 3
    endif;
    if k > 6;
        last_k = k;    // counter is local to the loop: save it before break
        break;
    endif;
    x[k] = k * 10;
endfor;
print x';
print "Stopped at k = " last_k;
```

Captured output (live, reproduced exactly on v0.88.0): **review_required**; preconditions: none.
Reasons: "syntax validation coverage is partial -- not all generated constructs could be deterministically checked (unmodelled construct(s): control_flow_block)"; "validation coverage is partial (incomplete: syntax partial), short of the broad evidence required for handoff candidacy"
Coverage gaps: syntax/- `unmodelled_construct`
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no error; the directory held only `prog.gss` afterwards. Stdout:

```text
Sum of squares:        55.000000 
       10.000000 
       8.0000000 
       6.0000000 
       4.0000000 
       2.0000000 
       10.000000        20.000000        0.0000000        40.000000        50.000000        60.000000        0.0000000        0.0000000        0.0000000        0.0000000 
Stopped at k =        7.0000000 
```

Expected behavior: `for` opens as a one-word stopword query (§3.3; v0.87.0: unreachable); the loop body with `if … endif` is `control_flow_block`, so review_required (the disclosed v0.82 limit).

Observed behavior: `for` grounded on `for.rst` (v0.87.0: ungrounded with nothing). review_required, for one reason only: `control_flow_block` (the `if` blocks inside the loop). Real GAUSS printed exactly the client's hand-worked prediction: 55; 10, 8, 6, 4, 2; 10 20 0 40 50 60 0 0 0 0; 7. In the same reply the client corrected 79.3's explanation from the page's "the counter is strictly local to the loop".

Search: a one-word query chosen by the client (the user said "for loop"); grounded directly.

Pass/fail: Pass
Defect severity: None
Remediation: None

Overall Score: 3.9
Decision: Pass
