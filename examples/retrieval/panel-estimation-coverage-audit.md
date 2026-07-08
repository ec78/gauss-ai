# Panel Estimation Coverage Audit

## Purpose

This audit documents whether local official GAUSS docs currently provide verified command evidence for panel estimation, prompted by `v0.9.0` evaluation `16.4` (`evaluations/runs/2026-07-05-code-assistant-multi-expert-routing-run-008.md`), which found no panel-estimation command in a preliminary check limited to `experts/gauss-language/COMMAND_CATEGORIES.md`'s core Panel Data category. This audit systematically extends that check to package-level documentation before drawing a conclusion.

## Summary Finding

**A verified general-purpose panel-estimation command was found.** `tscsFit`, from the commercial **TSMT** (Time Series MT) package, estimates a pooled time-series-cross-section regression model and returns both fixed-effects (dummy-variable) and random-effects (error-components) estimates from a single call. Real schema-aligned evidence has been generated and validated: `examples/retrieval/schema-aligned/tscsfit.evidence.json`.

This corrects the preliminary `16.4` finding, which did not search package-level documentation beyond `bhatlib` and `tspdlib`. `tscsFit` lives under `tsmt/`, a package directory `16.4`'s check did not reach.

**Important qualification:** TSMT is a separately licensed commercial package ("contact us for pricing and installation information," requires GAUSS/GAUSS Engine v25+) — it is not bundled with base GAUSS. This is a real package/base-GAUSS distinction the GAUSS Language Expert must state explicitly whenever `tscsFit` is recommended, per its existing decision rule to state package dependencies.

## Audit Method

**Files/paths searched:**
- `experts/gauss-language/COMMAND_CATEGORIES.md`'s Panel Data category (the `16.4` preliminary check's original scope).
- The full local docs checkout (`C:/Users/eclow/Documents/GitHub/docs/docs`), searched recursively across all `.rst` files, not limited to the `cc/` core category index.
- Package-level directories discovered during the search: `tsmt/` (Time Series MT), `tspdlib/` (time series/panel data library), `bhatlib/` (including its `archived/` subdirectory).

**Search terms used** (grouped by the categories specified for this audit):
- Panel structure: `panel`, `longitudinal`, `repeated`, `group`, `individual`, `entity`, `time index`.
- Panel estimators: `fixed effect`, `random effect`, `within estimator`, `between estimator`, `pooled`, `Hausman`, `panel regression`, `panel model`, `dynamic panel`, `Arellano`, `GMM panel`.
- Command naming possibilities: `pd`, `panel`, `xt`, `fe`, `re` (as filename/heading substrings, cross-checked against actual purpose text rather than treated as a match on their own).
- Testing/stationarity: `unit root`, `stationarity`, `cointegration`, `panel unit root`.

**Evidence files inspected:** `examples/retrieval/schema-aligned/pdsummary.evidence.json` (existing, real) and the newly generated `examples/retrieval/schema-aligned/tscsfit.evidence.json`.

**Distinction criteria applied:** a command was only classified as an "estimation command" if its documented `Format`/`Purpose` explicitly describes fitting/estimating model parameters (coefficients, effects) from data — not if it only manages, describes, tests, or transforms panel-structured data. A command mentioning "fixed effects" or "random effects" in a parameter description was not assumed to be an estimator on that basis alone; each candidate's actual `Purpose` and `Format` sections were read directly before classification (this caught, for example, that `lsdvFit`'s name suggests a classic fixed-effects technique but its documented purpose is a generic AR-error regression, not explicitly a panel fixed-effects estimator).

## Findings Table

| Candidate command/file | Source path | Category | What it appears to support | Estimation command? | Evidence status | Notes |
|---|---|---|---|---|---|---|
| `pdSummary` | `cc/panel-data.rst` (base GAUSS) | Verified panel summary/descriptive utility | Overall/between-group/within-group descriptive statistics for long-form panel data | No | Verified — `examples/retrieval/schema-aligned/pdsummary.evidence.json` (real, `v0.7.0`) | Confirms panel structure (balance, group/date vars) but does not estimate a model. |
| `pdLag`, `pdBalance`, `pdSort`, `pdIsBalanced`, `pdAllBalanced`, `pdAllConsecutive`, `pdDiff`, `pdTimeSpans`, `pdSize`, `dfLonger`, `dfWider` | `cc/panel-data.rst` (base GAUSS) | Verified panel data-management utility | Reshaping, lagging, sorting, balance-checking for panel/long-form data | No | Verified via category listing; not individually schema-aligned yet | Data preparation tools, not estimators. |
| **`tscsFit`** | `tsmt/tscsfit.rst` (TSMT package) | **Potential panel-estimation command → confirmed** | Estimates a pooled time-series-cross-section regression model; returns both fixed-effects (dummy-variable) and random-effects (error-components) coefficient estimates from one call, controlled via `tsc.model` | **Yes** | **Verified — `examples/retrieval/schema-aligned/tscsfit.evidence.json` (real, generated for this audit)** | Requires the commercial TSMT package (separately licensed, GAUSS/GAUSS Engine v25+). Not base GAUSS. |
| `tscsPredict` | `tsmt/tscspredict.rst` (TSMT package) | Panel forecast/prediction utility | Computes forecasts using estimation results obtained from `tscsFit` | No (companion to an estimator, not itself an estimator) | Not yet generated; candidate for future coverage | Confirms `tscsFit`'s role as the estimation entry point for this package's panel workflow. |
| `lsdvFit` | `tsmt/lsdvfit.rst` (TSMT package) | Unclear / possibly panel-adjacent | Documented purpose: "estimates coefficients of a regression model with autoregressive errors of any specified order," using `series_length`/`num_lags` parameters | Unclear | Not generated | Name suggests the classic Least-Squares-Dummy-Variable fixed-effects technique, but the documented purpose does not explicitly frame it as a panel fixed/random-effects estimator the way `tscsFit` is. Not classified as a confirmed panel estimator without further reading beyond this audit's scope. |
| `breitung`, `ips`, `cdtest`, `httest` | `tsmt/*.rst` (TSMT package) | Verified panel test/statistical diagnostic | Panel unit-root tests (`breitung`, `ips`, Harris-Tzavalis via `httest`) and a cross-sectional-dependence test (`cdtest`) | No | Verified via direct inspection (`httest.rst` purpose text confirmed) | Diagnostics on panel time-series properties, not model estimation. |
| `panel_fisher`, `panel_surwald`, `panel_zhnc` | `tspdlib/docs/*.rst` (tspdlib package) | Verified panel test/statistical diagnostic | Testing for Granger causality in heterogeneous mixed panels with bootstrap critical values | No | Verified via direct inspection of each file's Purpose section | Initially assumed (by filename pattern) to be unit-root tests; direct inspection corrected this — they test Granger causality, not stationarity. Diagnostics, not estimators, either way. |
| `gcmlpanel` | `bhatlib/archived/gcmlpanel.rst` (bhatlib package, archived) | Package-specific helper or archived helper | Computes the gradient for panel data composite marginal likelihood estimation (returns four gradient-component matrices) | No | Verified via direct inspection; explicitly archived | An internal computational helper for a specific estimation technique, not a general-purpose, user-facing panel estimator. Archived status noted explicitly. |

## Verified Panel Data-Management / Summary Coverage

- `pdSummary` — real schema-aligned evidence exists (`pdsummary.evidence.json`), confirming overall, between-group, and within-group descriptive statistics for long-form panel data.
- Other panel data-management utilities (`pdLag`, `pdBalance`, `pdSort`, `pdIsBalanced`, `pdAllBalanced`, `pdAllConsecutive`, `pdDiff`, `pdTimeSpans`, `pdSize`, `dfLonger`, `dfWider`) are verified as real, category-listed base-GAUSS commands per `experts/gauss-language/COMMAND_CATEGORIES.md`, but do not yet have individual schema-aligned evidence files — a candidate for future coverage if a specific benchmark or task needs one verified beyond category membership.

## Panel Tests / Diagnostics

- **Panel unit-root and cross-sectional-dependence tests** (TSMT package): `breitung` (panel series unit-root testing), `ips` (Im-Pesaran-Shin panel unit-root test), `httest` (Harris-Tzavalis panel unit-root test), `cdtest` (cross-sectional dependence test).
- **Panel Granger-causality tests** (tspdlib package): `panel_fisher`, `panel_surwald`, `panel_zhnc` — all documented as testing for Granger causality in heterogeneous mixed panels with bootstrap critical values.

These are real, verifiable diagnostic/test commands operating on panel data, but **they are not panel regression estimators** — they test a statistical property (stationarity, cross-sectional dependence, or Granger causality) rather than fitting a fixed/random-effects model. They should never be presented as an alternative to, or confused with, `tscsFit`.

## Panel Estimation Coverage

**A verified panel-estimation command was found: `tscsFit`.**

- **Evidence file:** `examples/retrieval/schema-aligned/tscsfit.evidence.json` (real, generated from local official docs via `scripts/command_doc_lookup.py`, not hand-written).
- **Verified syntax:** `tso = tscsFit(y, x, grp[, tsc])` and `tso = tscsFit(dataset, formula, grp[, tsc])`.
- **Verified scope:** estimates a pooled time-series-cross-section regression model from panel data (a stacked dataset with a group/unit identifier, `grp`); returns, in one call, both fixed-effects (dummy-variable model: `tso.bdv`, `tso.fixedEffects`, `tso.sefixedEffects`) and random-effects (error-components model: `tso.bec`, `tso.randomEffects`) coefficient estimates; `tsc.model` controls whether both are estimated or the random-effects model is skipped.
- **Verified dependency:** requires the TSMT package, which is separately licensed (not bundled with base GAUSS) and requires GAUSS/GAUSS Engine v25 or higher.
- **Validation results:** single-file `validate_lookup_evidence.py` — `PASS`, schema valid. Aggregate `validate_all_evidence.py` default — `PASS`, 14 files checked, 0 unexpected, 6 total warnings (unchanged from before adding this file — `tscsFit`'s evidence introduced zero new warnings). `--json` confirms the same. `--strict` — still fails only on the same two previously known files (`olsmt.evidence.json`, `glm.evidence.json`); `tscsfit.evidence.json` passes cleanly under `--strict` as well.
- **Known extraction gap:** `retrieval_status` is `found_incomplete` due to a keyword-search miss on "returns" (the same known non-gap pattern already established for `strindx`/`olsmt`/`glm` — the `returns_section` field itself was fully captured via the `.. function::`/list-table parsing path, not actually missing). The `outputs_section` extraction truncates after `tso.fixedEffects`; confirmed fields beyond that point (`tso.sefixedEffects`, `tso.randomEffects`, `tso.y_hat_dv`, `tso.y_hat_ec`, `tso.res_dv`, `tso.res_ec`) were still captured in the `keyword_hits`/inputs excerpts even though the dedicated `outputs_section` field truncates — a future re-extraction with different keyword targeting could capture the full field list in the primary `outputs_section` field itself.
- **Tooling limitation, since fixed (`v0.11.0`):** at the time of this audit, `scripts/command_doc_lookup.py` assigned `source_authority: official_docs` to every match with `source_type: official_local_rst`, regardless of whether the matched file lived in a package-specific directory (like `tsmt/`) or the core GAUSS documentation tree, even though the schema already defined a distinct `official_package_docs` value for exactly this case. This was fixed in `v0.11.0` (`planning/v0.11.0-repository-hygiene-and-evaluation-policy-cleanup.md`, Deliverable 5): the tool now classifies a match as `official_package_docs`/`official_package_rst` when its docs-root-relative path starts with a known GAUSS Application (package) directory, derived from the official Applications index. `tscsfit.evidence.json` was regenerated and its `source_authority`/`source_type` now correctly read `official_package_docs`/`official_package_rst`. The Code Assistant must still state the TSMT package dependency explicitly whenever `tscsFit` is recommended — this classification is a labeling improvement, not a substitute for that statement.

## Implications for Code Assistant Responses

- The Code Assistant may give full methodological panel guidance (fixed vs. random effects, identification, clustering, diagnostics) via the Econometrics Expert regardless of GAUSS implementation status — this audit's findings do not change that.
- It may discuss verified panel data-management utilities (`pdSummary` and its neighbors) when evidence exists, using the real, already-validated evidence.
- **It may now also recommend `tscsFit` for panel regression estimation with verified, evidence-backed syntax** — but must state explicitly that this requires the separately licensed TSMT package, not base GAUSS, per the GAUSS Language Expert's package/base-GAUSS distinction decision rule.
- It must not invent panel-estimation command syntax for any command not covered by real evidence (for example, `lsdvFit`'s applicability to panel fixed effects remains unclear per this audit and should not be asserted).
- It must separate panel methodology (Econometrics Expert) from verified GAUSS implementation availability (GAUSS Language Expert) exactly as `v0.9.0`'s `16.4` already established — this audit changes *what* is verified on the implementation side, not the coordination rule itself.
- If a user asks for exact panel-estimation syntax for a scenario `tscsFit` does not cover (for example, dynamic panel GMM, which was searched for and not found anywhere in the local docs), route to retrieval or state that verification is needed, exactly as for any other unverified command.

## Follow-ups

- Revisit official docs or package docs for panel estimation support beyond `tscsFit` — specifically, clarify `lsdvFit`'s actual applicability to panel fixed-effects estimation (this audit left it "unclear" rather than asserting either way).
- Generate schema-aligned evidence for `tscsPredict` (the `tscsFit` companion forecast command) if a future task needs verified panel forecasting coverage.
- ~~Consider improving `scripts/command_doc_lookup.py` to assign `source_authority: official_package_docs` when a matched file's path indicates a package directory (e.g., `tsmt/`, `tspdlib/`, `bhatlib/`) rather than the core documentation tree~~ — **done in `v0.11.0`**; see the updated "Known tooling limitation" note above.
- Add a benchmark prompt exercising `tscsFit` recommendation (methodology + package-dependency disclosure together) if useful for a future benchmark category.
- Consider adding curated notes for `tscsFit` only after this evidence has been exercised by at least one real evaluation, consistent with `commands/README.md`'s "high-value, failure-prone, or frequently evaluated" policy — not assumed necessary yet.
- No dynamic-panel-GMM or Arellano-Bond-style command was found anywhere in the searched local docs; this remains an open, unresolved item, not a "not yet checked" one — if such a command exists in GAUSS, it was not found in this specific audit's search scope.
