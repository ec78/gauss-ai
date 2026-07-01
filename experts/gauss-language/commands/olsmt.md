# olsmt

Purpose:
Short curated note for a high-value OLS command used in Code Assistant translation benchmarks.

Official source:
Official GAUSS command documentation file `olsmt.rst` from a local official documentation checkout, inspected on 2026-07-01.

Last verified:
2026-07-01, from the local official GAUSS documentation RST file.

Verified summary:

- `olsmt` computes a least squares regression.
- Official documented formats include:
  - `out = olsmt(data, formula[, ctl])`
  - `out = olsmt(data, depvar, indvars[, ctl])`
- `data` may be a dataset name, a DataFrame in memory, or an empty string.
- Formula syntax is documented for `olsmt`, including model strings such as a dependent variable regressed on named independent variables.
- The optional `ctl` argument is an `olsmtControl` structure.
- The return value is an `olsmtOut` structure.

Usage guidance:

- For standard OLS workflows, consider `olsmt` before manual matrix OLS.
- Verify the command-specific documentation before giving production code that depends on detailed options, output members, covariance settings, missing-value behavior, or version-specific behavior.
- Manual matrix OLS may still be useful for teaching the mechanics or custom estimators.

Authority note:
This is a short cache note, not a documentation mirror. If this note conflicts with official GAUSS documentation, the official documentation wins.
