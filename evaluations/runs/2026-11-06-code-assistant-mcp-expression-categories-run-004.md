# Evaluation Result

Date: 2026-11-06
Evaluator: Claude (`claude-opus-5-5`, VS Code Claude Code extension), driven live as the MCP client in a fresh conversation (`8ab50628…`) opened in an **empty folder outside the repository** (`C:\Users\Owner\Documents\gauss-ai-82x`), as in 80.x and 81.x: neither this repository's `CLAUDE.md` nor its memory notes nor its `.mcp.json` were in the client's context (that folder's memory directory is empty). The human asked each task in plain words, one at a time, and answered every run prompt themselves (five "yes", one "no") and one of the client's own numbered options ("1"). Tasks 82.1-82.9 were proposed by the recording session; 82.10-82.14 were the user's own. All tasks ran on 2026-11-06, 06:34-06:53 local (11:34-11:53 UTC). The client used gauss-ai tools plus five PowerShell commands that checked paths, listed folders and read executable version numbers (82.9, 82.12, 82.14); it read no file's contents, no source, planning doc, `PROJECT_STATUS.md` or `KNOWN_LIMITATIONS.md`.
Agent Version: v0.91.0 (tag `v0.91.0`, commit `5b07a28`; published to PyPI on 2026-11-06, run `42206846915`), the editable install of this checkout (`gauss-ai version` = 0.91.0).
Prompt ID: 82.4
Prompt Category: MCP Expression Categories of v0.91.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.91.0 over stdio, registered at local scope for the folder under both drive-letter spellings (`C:/…` and `c:/…`) with `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Config: `docs_root` = `C:\Users\Owner\.gauss-ai\docs`, `gauss_executable` = `C:\gauss26\tgauss.exe`, `default_runner` = gauss. One server session (`f7274c39…`) served every task; `gauss_session_start` reported `server_version: 0.91.0` and `real_gauss_allowed: true`. The client model wrote every query and snippet itself. Post-run, the recording session (this repository's own Claude Code session) re-ran all 37 search, read and validation calls through `gauss_mcp_server`'s tool functions at a `git archive` of `v0.91.0`: **every live response equals the re-run in every field** (`validation_id`, digests and the session id aside). It compared every one with a `git archive` of `v0.90.0` (`1ee121c`), diagnosed each non-candidate verdict with `validate_code(...)` directly, re-ran all five approved snippets with `tgauss.exe -b` (GAUSS 26.1.4), each from its own new empty directory, and ran every other non-blocked snippet the same way.
Prompt Text:

"From those same kinds of numbers, keep only the values between 3 and 7 and print them."

Code (c07):
```gauss
// Reproducible draws
rndseed 20261106;

// 50 uniform draws on [0, 10)
x = 10 * rndu(50, 1);

// Keep only values between 3 and 7 (inclusive)
keep = selif(x, (x .>= 3) .and (x .<= 7));

print "Values between 3 and 7:";
print keep;
print "Number kept:";
print rows(keep);
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `selif` argument 2 (parameter `e`): the argument (an expression whose every operand is numeric; its shape is not computed) is numeric, but the documented type for parameter 'e' (vector) does not accept every numeric matrix; an expression's category is not precise enough to confirm or refute it"; "parameter role unknown -- `rows` argument 1 (parameter `x`): the argument (traced to `keep = ...`, a call whose documented return type is string/dataset/matrix) may not fit the documented type for parameter 'x' (matrix); a documented return type is not precise enough to call this a mismatch"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

Code (c08):
```gauss
// Reproducible draws
rndseed 20261106;

// 50 uniform draws on [0, 10)
x = 10 * rndu(50, 1);

// 50x1 indicator: 1 where 3 <= x <= 7, else 0
mask = (x .>= 3) .and (x .<= 7);

// Keep only the flagged rows
keep = selif(x, mask);

print "Values between 3 and 7:";
print keep;
print "Number kept:";
print sumc(mask);
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `selif` argument 2 (parameter `e`): the argument (traced to `mask = ...`, an expression whose every operand is numeric; its shape is not computed) is numeric, but the documented type for parameter 'e' (vector) does not accept every numeric matrix; an expression's category is not precise enough to confirm or refute it"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

The client looked up `indexcat` (`gauss_search_docs("indexcat")`, grounded):

Code (c09):
```gauss
// Reproducible draws
rndseed 20261106;

// 50 uniform draws on [0, 10)
x = 10 * rndu(50, 1);

// Indices of values in the range 3 < x <= 7
v = { 3, 7 };
idx = indexcat(x, v);

// Keep only those values
keep = x[idx];

print "Values between 3 and 7:";
print keep;
print "Number kept:";
print rows(idx);
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `indexcat` argument 1 (parameter `x`): the argument (traced to `x = ...`, an expression whose every operand is numeric; its shape is not computed) is numeric, but the documented type for parameter 'x' (vector) does not accept every numeric matrix; an expression's category is not precise enough to confirm or refute it"
v0.90.0: **review_required** (reasons differ: v0.90.0 says the expression is never evaluated).

It then rescaled the bounds to literals (0.3, 0.7) to pass the raw `rndu` draw:

Code (c10):
```gauss
// Reproducible draws
rndseed 20261106;

// 50 uniform draws on [0, 1); scaled by 10 they are uniform on [0, 10)
u = rndu(50, 1);

// Indices where 3 < 10*u <= 7, i.e. 0.3 < u <= 0.7
v = { 0.3, 0.7 };
idx = indexcat(u, v);

// Keep only those values, on the 0-10 scale
keep = 10 * u[idx];

print "Values between 3 and 7:";
print keep;
print "Number kept:";
print rows(idx);
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "validation coverage is partial (incomplete: parameter roles partial), short of the broad evidence required for handoff candidacy"; "parameter role unknown -- `indexcat` argument 1 (parameter `x`): the argument (traced to `u = ...`, a call whose documented return type is matrix) may not fit the documented type for parameter 'x' (vector); a documented return type is not precise enough to call this a mismatch"
v0.90.0: identical.

It then tried a loop:

Code (c11):
```gauss
// Reproducible draws
rndseed 20261106;

n = 50;

// 50 uniform draws on [0, 10)
x = 10 * rndu(n, 1);

// Collect values with 3 <= x <= 7
keep = zeros(n, 1);
nk = 0;
for i(1, n, 1);
    if x[i] >= 3 and x[i] <= 7;
        nk = nk + 1;
        keep[nk] = x[i];
    endif;
endfor;

print "Number kept:";
print nk;
if nk > 0;
    print "Values between 3 and 7:";
    print keep[1:nk];
else;
    print "No values between 3 and 7.";
endif;
```
Captured output (live, identical on the v0.91.0 re-run): **review_required**.
Reasons beyond the standard ones: "syntax validation coverage is partial -- not all generated constructs could be deterministically checked (unmodelled construct(s): control_flow_block)"; "validation coverage is partial (incomplete: syntax partial), short of the broad evidence required for handoff candidacy"
v0.90.0: identical.

And finally a sort-and-slice:

Code (c12):
```gauss
// Reproducible draws
rndseed 20261106;

// 50 uniform draws on [0, 10)
x = 10 * rndu(50, 1);

// Sort ascending; values in [3, 7] form one contiguous block
s = sortc(x, 1);
lo = sumc(x .< 3);
hi = sumc(x .<= 7);

// Rows lo+1 .. hi of the sorted draws are exactly the values in [3, 7]
keep = s[lo+1:hi];

print "Number kept:";
print hi - lo;
print "Values between 3 and 7 (sorted):";
print keep;
```
Captured output (live, identical on the v0.91.0 re-run): **handoff_candidate**.
Reasons: the five standard handoff reasons, ending "validation coverage is broad".
v0.90.0: **review_required**.
  v0.90.0 reasons: "parameter role unknown -- `sortc` argument 1 (parameter `x`): `x` is assigned from an expression (`10 * rndu(50, 1)`), which is never evaluated"; "parameter role unknown -- `sumc` argument 1 (parameter `x`): `x .< 3` is an expression, and expressions are never evaluated"; "parameter role unknown -- `sumc` argument 1 (parameter `x`): `x .<= 7` is an expression, and expressions are never evaluated"

Execution handoff (prepare, `request_id` `603568fb-51f4-4655-b53b-03c6e825bcc2`). The prompt shown to the user:
~~~~text
Ready for controlled execution.

Code:
```gauss
// Reproducible draws
rndseed 20261106;

// 50 uniform draws on [0, 10)
x = 10 * rndu(50, 1);

// Sort ascending; values in [3, 7] form one contiguous block
s = sortc(x, 1);
lo = sumc(x .< 3);
hi = sumc(x .<= 7);

// Rows lo+1 .. hi of the sorted draws are exactly the values in [3, 7]
keep = s[lo+1:hi];

print "Number kept:";
print hi - lo;
print "Values between 3 and 7 (sorted):";
print keep;

```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: f40459f0bad30749d42750854e3a1697ea2db6b39b6cb8a0368464b17dfc4eb9

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
~~~~
The user's own reply: "yes", passed verbatim with that `request_id`: outcome `success`; stdout:
```
Number kept:
       19.000000 
Values between 3 and 7 (sorted):

       3.0749035 
       3.1686467 
       3.3144891 
       3.6957081 
       3.8364342 
       3.8516334 
       4.2292634 
       4.4150961 
       4.6384380 
       5.1905300 
       5.2835017 
       5.5911364 
       5.6192539 
       5.8174925 
       6.0034707 
       6.0413011 
       6.5706609 
       6.6014535 
       6.7740612
```
Real GAUSS (`tgauss.exe -b`, recording session, own new empty directory): byte-identical stdout; no file created.

Expected behavior: (plan v0.91 §7) the element-wise filter reaches `handoff_candidate` when its operands are traced.

Observed behavior: **reached only through a workaround.** The natural code, `selif(x, (x .>= 3) .and (x .<= 7))`, stays review_required because `selif`'s `e` and `indexcat`'s `x` are documented as `vector`, and a numeric-matrix category cannot confirm a vector parameter (decision 1a; `KNOWN_LIMITATIONS.md` names only `scalar`). A `for` loop stays review_required as an unmodelled `control_flow_block`. The client reached a prompt by sorting and slicing (`s[lo+1:hi]`), which v0.91.0 accepts (v0.90.0: review_required). It ran, byte-identical, keeping 19 values. All six versions run in GAUSS with no error. The final code has an edge case the client did not mention: when no value is in range, `lo = hi` and `s[lo+1:hi]` is a reversed two-row range, not an empty one (recording-session spot check e01: `s[3:2]` prints rows 3 and 2). With this seed it did not occur. The client's report discloses the 0.3/0.7 literal rewrite.

Pass/fail: Pass
Defect severity: Low (validator); client code fragile
Remediation: Vector-typed parameters are the same class as decision 1c's scalar case; see plan §12, finding 2.

Overall Score: 3.4
Decision: Pass
