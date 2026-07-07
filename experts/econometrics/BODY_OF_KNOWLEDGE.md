# Econometrics Body of Knowledge

## Purpose

This document organizes the structured knowledge domains the Econometrics Expert draws on. It is scoped to what a later operational profile needs — activation triggers, decision rules, refusal conditions — not a comprehensive econometrics reference. Depth should grow only as far as benchmark evaluation (planned as category `16.x`) actually requires.

This domain does not attempt to reproduce a statistics or econometrics textbook. It defines how a GAUSS-focused agent should reason about model choice, assumptions, diagnostics, and interpretation, and where that reasoning must hand off to the GAUSS Language Expert for implementation.

## Domain 1 — Problem Framing

Before any model or estimator is chosen, the question and data structure must be framed clearly.

Key framing questions:

- What is the dependent variable, and what type is it (continuous, binary, count, categorical, duration)?
- What are the candidate explanatory variables, and what role does each play (of interest vs. control)?
- What is the unit of observation (individual, firm, country, time period, transaction)?
- Is the goal causal (estimating an effect), predictive (forecasting an outcome), or descriptive (summarizing a relationship)?
- What is the data context: cross-sectional, time-series, panel, or experimental/quasi-experimental?

Agent guidance:

- Do not proceed to model choice before the goal (causal vs. predictive vs. descriptive) is at least provisionally stated or assumed explicitly.
- State the assumed unit of observation and data structure when the user hasn't specified them, rather than picking a model that silently presumes one.

Common failure modes:

- Jumping to an estimator before the question is framed.
- Assuming a causal goal when the user only asked for a predictive or descriptive summary, or vice versa.

## Domain 2 — Model and Estimator Selection

Model and estimator choice should follow from the framing in Domain 1, not from which command happens to be familiar or available.

| Data/Goal Shape | Candidate Methods |
|---|---|
| Continuous outcome, linear relationship | OLS |
| Binary/count/non-normal outcome | GLM, logistic/probit |
| Time-dependent single series | Time-series models (ARIMA-family) |
| Multiple time series with feedback | VAR/SVAR |
| Repeated observations per unit | Panel models (fixed/random effects) |
| Endogenous regressor | IV/2SLS, GMM |
| Effects across the outcome distribution, not just the mean | Quantile regression |
| Out-of-sample prediction is the goal | Forecasting models, evaluated by forecast error, not in-sample fit alone |

Agent guidance:

- Match the estimator to the outcome type and data structure identified in Domain 1 before considering estimation convenience.
- State why a method fits, referencing the specific data/goal shape, not just naming the method.
- Do not treat this table as exhaustive or as a lookup that replaces judgment about the specific case.

Common failure modes:

- Recommending OLS by default regardless of outcome type or data structure.
- Ignoring panel or time-series structure when a method that assumes independent observations is applied to non-independent data.

## Domain 3 — Assumptions and Threats

Every model/estimator relies on assumptions; part of this expert's job is naming which ones matter for the case at hand.

Core assumption categories:

- Linearity (of the functional form, where assumed)
- Exogeneity (regressors uncorrelated with the error term)
- Independence (across observations, unless explicitly modeled otherwise)
- Homoskedasticity vs. heteroskedasticity (constant vs. non-constant error variance)
- Serial correlation (errors correlated across time)
- Multicollinearity (explanatory variables correlated with each other)
- Stationarity (for time-series methods)
- Missing-data mechanisms (missing completely at random, at random, or not at random)

Threats to valid inference:

- Omitted variable bias
- Selection bias
- Endogeneity (including reverse causality)

Agent guidance:

- Name the assumptions most likely to be violated given the stated context, not a generic list recited regardless of relevance.
- Distinguish assumptions that affect efficiency (e.g., heteroskedasticity, typically addressed with robust standard errors) from assumptions that affect consistency (e.g., exogeneity, which cannot be fixed by a standard-error adjustment alone).

Common failure modes:

- Treating heteroskedasticity-robust standard errors as if they also fix an endogeneity problem.
- Ignoring the missing-data mechanism when it could bias the estimated relationship, not just reduce sample size.

## Domain 4 — Diagnostics and Validation

Diagnostics should be chosen based on which assumptions from Domain 3 are most at risk, not applied as a fixed checklist.

- Residual checks (patterns suggesting misspecification, heteroskedasticity, or non-normality)
- Goodness of fit (R-squared and analogues, interpreted with their known limitations)
- Out-of-sample validation and cross-validation (for predictive goals specifically)
- Forecast error metrics (for forecasting goals specifically — not the same as in-sample fit)
- Specification tests (appropriate to the model class, e.g., tests for omitted variables or functional form)
- Robustness and sensitivity checks (does the conclusion hold under reasonable alternative specifications)

Agent guidance:

- Recommend diagnostics tied to the specific assumptions flagged as fragile in Domain 3, not a generic list.
- For predictive/forecasting goals, prioritize out-of-sample performance over in-sample fit measures.

Common failure modes:

- Treating a high R-squared as sufficient evidence of a well-specified or causally valid model.
- Validating a forecasting model only on in-sample fit.

## Domain 5 — Interpretation

Correct interpretation is as important as correct estimation.

- Coefficients: what a one-unit change in the regressor implies for the outcome, given the model's functional form.
- Marginal effects and elasticities: required for nonlinear models (e.g., logistic/probit) where the raw coefficient is not directly interpretable as an effect size.
- P-values: the probability of observing a result this extreme (or more) under the null hypothesis — not the probability the null hypothesis is true, and not the probability the effect is real.
- Confidence intervals: a range for the *parameter*, not a range predicting individual future outcomes.
- Prediction intervals: a range for an individual *future observation*, distinct from a confidence interval.
- Statistical vs. practical significance: a statistically significant effect can be too small to matter practically, and vice versa in underpowered samples.
- Correlation vs. causation: correlation alone never establishes causation without a design or identification strategy from Domain 3.

Agent guidance:

- State interpretations in terms the user's stated audience can act on, without overstating certainty.
- Explicitly flag when a result is statistically significant but practically small, or vice versa.

Common failure modes:

- Misstating what a p-value means.
- Confusing confidence intervals and prediction intervals.
- Presenting correlation as causation without a stated identification strategy.

## Domain 6 — Data Structure and Design Considerations

- Panel vs. repeated cross-section: whether the same units are tracked over time (panel) or different units are sampled each period (repeated cross-section) changes which estimators are valid.
- Time index and frequency: daily, monthly, quarterly, annual — affects both model choice and diagnostic relevance (e.g., seasonality).
- Group identifiers: required for panel/clustered methods; their absence should be flagged, not assumed away.
- Treatment/control structure: relevant whenever a causal comparison is being made.
- Clustering level: standard errors should typically be clustered at the level where the treatment or shock varies, not left as the default.
- Aggregation level: whether the analysis is at the individual, group, or aggregate level affects both interpretation and potential ecological-fallacy risk.
- Missingness and sample definition: how the analytic sample was constructed (dropped rows, imputed values) should be stated, since it can silently change what the result represents.

Agent guidance:

- Ask for or state assumptions about panel identifiers, clustering level, and sample construction when they are not provided and materially affect the answer.

Common failure modes:

- Ignoring clustering when the natural grouping in the data is known.
- Not documenting how missing data was handled before presenting a result.

## Domain 7 — Method-Specific Notes

Brief, non-exhaustive notes per method family — depth here should grow only as benchmark evaluation requires:

- **OLS**: assumes linearity and exogeneity; sensitive to omitted variable bias and outliers.
- **Logistic/probit**: for binary outcomes; coefficients are not directly interpretable as marginal effects.
- **GLM** (general): extends linear modeling to non-normal outcome distributions via a link function; the appropriate family/link depends on the outcome type from Domain 1.
- **Panel fixed effects**: controls for time-invariant unit-level unobservables; cannot estimate effects of time-invariant regressors.
- **Panel random effects**: more efficient than fixed effects if the random-effects assumption (unit effects uncorrelated with regressors) holds; that assumption is often the weakest link.
- **Time series / ARIMA**: requires attention to stationarity; non-stationary series typically need differencing or an alternative specification.
- **VAR/SVAR**: models feedback among multiple time series; identification of structural shocks requires additional assumptions beyond the reduced-form model.
- **GMM**: generalizes method-of-moments estimation; useful when instruments or moment conditions are available but full likelihood specification is not desired.
- **IV**: addresses endogeneity given a valid instrument; validity (relevance and exogeneity of the instrument) must be argued, not assumed.
- **Quantile regression**: estimates effects at different points of the outcome distribution, not just the conditional mean.

## Domain 8 — Interaction with GAUSS Implementation

This domain is the explicit handoff boundary to the GAUSS Language Expert.

- A methodological recommendation is separate from GAUSS command syntax. Naming an appropriate method (Domain 2) is an Econometrics Expert claim; the exact GAUSS call to implement it is a GAUSS Language Expert claim, backed by official-doc-backed evidence per `schemas/command_lookup_evidence.schema.json`.
- Exact GAUSS implementation requires the GAUSS Language Expert and command-specific evidence — this expert does not verify or invent GAUSS syntax under any circumstance.
- This expert can say what method is needed without knowing (or asserting) whether a verified GAUSS command exists for it. If no such command evidence is available, that must be stated as a separate, unresolved fact.
- If a method is appropriate but GAUSS command evidence is missing, state both facts separately and explicitly: "this method is appropriate because..." and "I don't have verified GAUSS syntax for it — that requires retrieval" — never blend the two into a single claim that implies both are settled.

## Domain 9 — Common Decision Frameworks

A compact set of questions to work through before finalizing methodological guidance:

- Is the goal causal, predictive, descriptive, or diagnostic?
- What is the data structure (cross-sectional, time-series, panel, experimental/quasi-experimental)?
- What assumptions are most fragile given this specific context?
- What diagnostics are needed to check those fragile assumptions?
- What robustness checks would change the conclusion if they failed?
- What can and cannot be interpreted from the result, given the design and data actually available?

These questions are the backbone of this expert's reasoning workflow — see `reasoning.md` for how they map onto a step-by-step process.
