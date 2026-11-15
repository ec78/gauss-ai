# GAUSS documentation and package issues found by gauss-ai (November 2026)

Prepared for Aptech's developers. Every item below was found while testing gauss-ai, an MCP server that checks AI-written GAUSS code against the published documentation. Each one is confirmed against GAUSS 26.1.4 (`tgauss.exe -b`) or the docs source (github.com/aptech/docs, as downloaded 2026-10-23), unless marked otherwise. The items are grouped by how much they affect someone reading the docs.

## A. The documentation gives an answer GAUSS rejects

### A1. `gmmfit.rst`: wrong output member names

The page lists the output members as `gOut.parEst` and `gOut.numParms`. GAUSS 26.1.4 rejects both with `G0504` (undefined structure member). It accepts `gOut.paramEst` and `gOut.numParams`, the names on `gmmFitIV.rst`.

Suggested fix: rename the two members on `gmmfit.rst` to `paramEst` and `numParams`.

### A2. `tspdlib/docs/adf_1br.rst`: missing `outlier` argument

The page documents `adf_1break(y, model [, pmax, ic, trimm])`. The installed `ADF_1break` reads its optional arguments as `{ outlier, pmax, ic, trimm } = dynargsGet(1|4, 1, 8, 3, 0.10)`, so a call written from the page shifts every optional argument by one. The documented five-argument call stops inside tspdlib with `G0152` (`getlag.src`, line 77). With `outlier` supplied first, it runs.

Suggested fix: add `outlier` as the first optional argument, with its default and meaning.

### A3. `logical-or.rst`: points to a function that does not exist

The page says element-wise logic uses "``.*`` with comparison operators or the ``dotor`` function". There is no `dotor` page or function. The operator that works, `.or`, is not mentioned there, although `operators.rst` documents it. (Jason confirmed this one on 2026-10-21 and asked for an issue on aptech/docs.)

Suggested fix: replace `dotor` with `.or` and link to the operators page.

## B. The documentation is right but cannot be read by a tool

These pages read correctly to a person. They omit the structured fields (`:type`, `:rtype`) that the rest of the docs use, so any tool reading the docs, including gauss-ai and assistants using `aptech/gauss-llm-reference`, cannot tell what goes in and what comes out.

### B1. `trainTestSplit.rst`, `splitData.rst`, `cvSplit.rst`: outputs have no `:rtype`

The outputs are described in prose ("(*train_pct* \* *N*) x *P* matrix", "the remaining observations from the original *y*") but have no `:rtype` lines. GAUSS shows each output keeping its input's column count, as a numeric matrix: `y` 100x1 → `y_train` 70x1, and `X` 100x3 → `X_train` 70x3.

Effect: nothing downstream of a train/test split can be type-checked, so every GML train/test program written by an assistant stays "needs review" in gauss-ai.

Suggested fix: add an `:rtype` per output (for example `y_train`: `(train_pct*N)xK matrix`, the same column count as `y`).

### B2. `kmeansfit.rst`: two names for one parameter

The syntax line calls the first parameter `X`, and the parameter list calls it `X_train`. A tool matching the two cannot find the parameter's `:type`.

Suggested fix: use one name in both places.

### B3. `tsmt/simarmamt.rst`: parameters in a grid table

The parameters are typed in a reStructuredText grid table (`+-------+---...`) instead of the `:param` / `:type` lines used elsewhere, so none of its eight arguments has a machine-readable type.

Suggested fix: convert it to the standard parameter list.

## C. Output and packaging

### C1. `tsmt/arimafit.rst`: log-likelihood equal to the AIC

Every example output on the page prints the same number for the log-likelihood and the AIC: `764.556` and `764.556`, `761.464` and `761.464`, `200.167` and `200.167`. Since AIC = -2 logL + 2k, the two cannot be equal. Either the printed summary or the example outputs are wrong. Not re-run in GAUSS: the legacy `arimaFit` is shadowed (C3).

### C2. `lassoFit`: printed summary labels

In GAUSS 26.1.4, `lassoFit(y, X, 0.1)` with a five-column `X` prints every coefficient row as `X1`, and prints `DF 2` next to `# Non-zero Vars 3`. The coefficients themselves are correct. The labels should presumably be `X1` ... `X5`, and the DF line should match the non-zero count (or its meaning should be stated).

### C3. `library tsmt;` loads the timeseries alias, not the legacy tsmt

With both `pkgs\timeseries` and `pkgs\tsmt` installed, `library tsmt;` loads `pkgs\timeseries\lib\tsmt.lcg`, the backward-compatibility alias that timeseries generates, because `timeseries` sorts first. Functions and structures that only the legacy library defines are then missing: `adjRsq`, `chowfcst` and `simarmamt` stop with `G0025`, and `struct arimamtOut` with `G0507`. The `tsmt/` docs still document them.

Question for Aptech: is the legacy tsmt documentation still current, and should the alias include these functions or should the docs say they moved?
