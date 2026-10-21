# Evaluation Result

Date: 2026-10-21
Evaluator: Claude (Opus 5.5, VS Code Claude Code extension), driven live as the MCP client in one conversation (`c60c77d5…`); the human asked each task in plain words, one at a time, and answered every run prompt themselves. All thirteen tasks ran on 2026-10-21, 19:10-19:30 local (23:10-23:30 UTC). During the tasks the client read GAUSS documentation files and the installed package's `package.json` directly from disk, but no gauss-ai source file, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md` or planning doc; `CLAUDE.md` and one memory note were in its context from the start (v0.88 plan §11.7).
Agent Version: v0.88.0 (released: tag `v0.88.0`, commit `be3df16`, pushed and published on GitHub at 18:57 local, before the tasks), editable install of this checkout (`gauss-ai version` = 0.88.0).
Prompt ID: 79.3
Prompt Category: MCP Search and Grounding Recall of v0.88.0 (Live Client)
Evidence source: Real `gauss-ai-mcp` v0.88.0 over stdio (two `gauss-ai-mcp.exe` processes, PIDs 34308 and 17696, both started 19:09:47 local, after the v0.88.0 install at 19:04:56; which one served the conversation was not determined, but every response carries v0.88.0-only fields such as `omitted_topics` and the `derived_from_docs`/`statement_page`/`non_defining_page` candidate origins). Real config (docs_root = `C:/Users/Owner/.gauss-ai/docs`, the published copy; runner = gauss, `C:\gauss26\tgauss.exe`). One server session (`4120e487…`) served all tasks; `gauss_session_start` reported `real_gauss_allowed: true`, and 79.1's prepare rendered a prompt. The client model wrote every query and snippet itself. Post-run: the recording session (the same conversation, after the tasks) re-ran every search query and snippet by calling each archive's own `gauss_mcp_server` tool functions on `git archive`s of v0.88.0 (`be3df16`) and v0.87.0 (`4103280`), each archive's modules asserted imported. **All 24 live responses (13 searches, 11 validations) are identical to the v0.88.0 re-run in every field** (excerpt text, candidates, reasons, gaps, `code_sha256`; `validation_id` aside). Each non-candidate verdict was also diagnosed with `validate_code(...)` directly (`pre_execution.coverage`, `parameter_role_checks`). Real-GAUSS evidence: `tgauss.exe -b` (GAUSS 26.1.4) runs of every client snippet except 79.4's `dllcall` (its DLL does not exist), each from its own new empty directory.
Prompt Text:

"I want to run a unit root test that allows a structural break"

Search `unit root test with structural break` (live, identical on the v0.88.0 re-run): **ungrounded**
- sources: none
- unmatched: ['unit', 'root', 'structural']; ambiguous: ['test']
- candidates (truncated): `mvnTest` (ambiguous_resolution), `grangerTest` (ambiguous_resolution), `cdTest` (ambiguous_resolution), `break` (statement_page), `adf_1break` (derived_from_docs), `adf_2breaks` (derived_from_docs), `Fourier_ADF` (derived_from_docs), `fourier_gls` (derived_from_docs)
- v0.87.0, same query: **partially_grounded**; sources: `break` (break.rst); unmatched: ['unit', 'root']; ambiguous: ['test']; candidates: `mvnTest` (ambiguous_resolution), `grangerTest` (ambiguous_resolution), `cdTest` (ambiguous_resolution)

Search `adf_1break` (live, identical on the v0.88.0 re-run): **grounded**
- sources: `adf_1break` (tspdlib/docs/adf_1br.rst)
- unmatched: none; ambiguous: none
- candidates: `adf_2breaks` (derived_from_docs), `Fourier_ADF` (derived_from_docs), `qr_fourier_adf` (derived_from_docs)
- v0.87.0, same query: **grounded**; sources: `adf_1break` (tspdlib/docs/adf_1br.rst); unmatched: none; ambiguous: ['adf_1break']; candidates: `adf_2breaks` (ambiguous_resolution), `Fourier_ADF` (ambiguous_resolution), `qr_fourier_adf` (ambiguous_resolution)

Search `Zivot Andrews unit root test` (live, identical on the v0.88.0 re-run): **partially_grounded**
- sources: `zandrews` (tsmt/zandrews.rst)
- unmatched: ['unit', 'root']; ambiguous: ['test']
- candidates: `mvnTest` (ambiguous_resolution), `grangerTest` (ambiguous_resolution), `cdTest` (ambiguous_resolution)
- v0.87.0, same query: **partially_grounded**; sources: `andrews` (tsmt/zandrews.rst), `zandrews` (tsmt/zandrews.rst); unmatched: ['zivot']; ambiguous: ['test']; candidates: `mvnTest` (ambiguous_resolution), `grangerTest` (ambiguous_resolution), `cdTest` (ambiguous_resolution)

Code (call #13):
```gauss
library tspdlib;

// Simulated series: stationary AR(1) with a level shift at t = 120
rndseed 42;
T = 200;
e = rndn(T, 1);
y = zeros(T, 1);
for t (2, T, 1);
    y[t] = 0.5 * y[t-1] + e[t];
endfor;
y[120:T] = y[120:T] + 5;

// Model 1: break in level (use 2 for level and trend)
model = 1;

// ADF with one endogenous break; defaults: pmax = 8, ic = 3 (t-sig), trimm = 0.10
{ tstat, tb, lags, cv } = adf_1break(y, model);

print "ADF min t-stat:     " tstat;
print "Estimated break at: " tb;
print "Lags selected:      " lags;
print "Critical values (1%, 5%, 10%):";
print cv;
```

Captured output (live, reproduced exactly on v0.88.0): **not_ready**; preconditions: none.
Reasons: "line 1: `library` is a system-touching statement (source_inclusion) -- controlled execution only runs self-contained snippets that compute in memory"
Coverage gaps: parameter_role/rndn arg 1 `argument_untraced`; parameter_role/zeros arg 1 `argument_untraced`
System statements: `library` (source_inclusion, line 1)
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no error; the directory held only `prog.gss` afterwards. Stdout:

```text

Test:                                                    ADF 
Ho:                                                Unit root 
Number of breaks:                                          1 
Lag selection:                          T-stat lag selection 
Trimming rate (%):                                        10 
Model:                                        Break in level 
==============================================================
ADF-stat:                                             -7.792
Chosen Lags:                                               6

Critical Values:
                            1%             5%            10%
                        -5.340         -4.800         -4.580
==============================================================

Estimated break dates:
                                         Date       Fraction
First break:                          1.2e+02          0.595
==============================================================
Reject the null hypothesis of a unit root at the 1% level.

ADF min t-stat:           -7.7918823 
Estimated break at:        119.00000 
Lags selected:             6.0000000 
Critical values (1%, 5%, 10%):

      -5.3400000 
      -4.8000000 
      -4.5800000 
```

The client renamed `T` to `nobs` and the loop counter `t` to `i`, explaining that GAUSS names are case-insensitive so `T` and `t` were "the same variable". It corrected that explanation unprompted in 79.5 (the `for` page says the counter is local to the loop).

Code (call #14):
```gauss
library tspdlib;

// Simulated series: stationary AR(1) with a level shift at obs 120
rndseed 42;
nobs = 200;
e = rndn(nobs, 1);
y = zeros(nobs, 1);
for i (2, nobs, 1);
    y[i] = 0.5 * y[i-1] + e[i];
endfor;
y[120:nobs] = y[120:nobs] + 5;

// Model 1: break in level (use 2 for level and trend)
model = 1;

// ADF with one endogenous break; defaults: pmax = 8, ic = 3 (t-sig), trimm = 0.10
{ tstat, tb, lags, cv } = adf_1break(y, model);

print "ADF min t-stat:     " tstat;
print "Estimated break at: " tb;
print "Lags selected:      " lags;
print "Critical values (1%, 5%, 10%):";
print cv;
```

Captured output (live, reproduced exactly on v0.88.0): **not_ready**; preconditions: none.
Reasons: "line 1: `library` is a system-touching statement (source_inclusion) -- controlled execution only runs self-contained snippets that compute in memory"
Coverage gaps: none.
System statements: `library` (source_inclusion, line 1)
v0.87.0, same snippet: identical in every field.
Real GAUSS (`tgauss.exe -b`): exit 0, no error; the directory held only `prog.gss` afterwards. Stdout:

```text

Test:                                                    ADF 
Ho:                                                Unit root 
Number of breaks:                                          1 
Lag selection:                          T-stat lag selection 
Trimming rate (%):                                        10 
Model:                                        Break in level 
==============================================================
ADF-stat:                                             -7.792
Chosen Lags:                                               6

Critical Values:
                            1%             5%            10%
                        -5.340         -4.800         -4.580
==============================================================

Estimated break dates:
                                         Date       Fraction
First break:                          1.2e+02          0.595
==============================================================
Reject the null hypothesis of a unit root at the 1% level.

ADF min t-stat:           -7.7918823 
Estimated break at:        119.00000 
Lags selected:             6.0000000 
Critical values (1%, 5%, 10%):

      -5.3400000 
      -4.8000000 
      -4.5800000 
```

Expected behavior: No false grounding on `break.rst` (§3.8: a prose word on a statement page); labeled candidates instead, including the TSPDLIB pages; `library` is `source_inclusion`, so not_ready, a correct block.

Observed behavior: v0.88.0 behaved as designed. The plain question is ungrounded; `test` is ambiguous (the disclosed KL item: `mvnTest`, `grangerTest`, `cdTest`); and the candidates list `break` (statement_page) and `adf_1break`, `adf_2breaks`, `Fourier_ADF`, `fourier_gls` (derived_from_docs). On v0.87.0 the same query is partially_grounded **on `break.rst`** (the `break` loop statement), a false source. The client followed the `adf_1break` candidate to its grounded page and wrote the code from its signature. Both snippets are not_ready for one reason only, `library` (source_inclusion), a correct block. The first also had two `argument_untraced` gaps for `T`. Real GAUSS: both versions print identical output (ADF min t-stat -7.79 against a 1% critical value of -5.34; break at 119, for a shift that starts at observation 120). The client said "a break near observation 120" and "you would expect a rejection": both true. It did not mention that `adf_1break` prints its own results table. **Client error, self-corrected in 79.5:** the gap was not a bug. Probes p1 (`T = 5; print t;` prints 5) and p2 (`T = 200; for t (1, 3, 1); endfor; print T;` prints 200) show that GAUSS names are case-insensitive but the counter is local, so the original code was already correct. The validator's `argument_untraced` gap is its own tracing limit. Recording-session probes show that a `for t` loop anywhere in the code, even after the use, makes an earlier `T` untraced, while a later `t = 3;` or a `for i` loop does not; v0.87.0 behaves the same. It is safe-direction (review_required instead of handoff_candidate), pre-existing, and not in `KNOWN_LIMITATIONS.md` (finding 2).

Search: **followed a candidate back to a grounded page** (`adf_1break`, listed with origin `derived_from_docs`, then searched by name: grounded). The parallel "Zivot Andrews unit root test" query was **steered by prior knowledge**: it grounds `zandrews` through the `zivot and andrews` alias (v0.87.0 grounded it via a stray `andrews` token as well).

Pass/fail: Pass
Defect severity: None (client explanation error, corrected by the client)
Remediation: None

Overall Score: 3.6
Decision: Pass
