# Common Mistakes

Common AI and user failure modes the Econometrics Expert should help agents avoid.

- Treating any regression as causal, regardless of whether a design or identification strategy supports that claim.
- Choosing a model or estimator because a matching command exists, rather than because it fits the research question and data structure.
- Ignoring panel or time-series structure when it materially affects which estimators are valid.
- Ignoring clustering or serial correlation when computing standard errors, when the natural grouping or time-dependence in the data is known.
- Misinterpreting p-values — for example, treating a p-value as the probability the null hypothesis is true.
- Confusing confidence intervals (a range for the parameter) with prediction intervals (a range for an individual future observation).
- Ignoring the missing-data mechanism when it could bias the result rather than merely reduce sample size.
- Treating a high R-squared as proof of a correctly specified or causally valid model.
- Overclaiming from small samples or unrepresentative data as though the result generalizes broadly.
- Translating code or a model from another language/tool without checking whether the underlying method is still appropriate for the target data and question.
- Inventing GAUSS syntax while attempting to give econometric advice — methodological recommendations must stay separate from unverified implementation claims (`EXPERT.md`, Relationship to GAUSS Language Expert).
- Letting GAUSS command evidence (schema-valid, official-doc-backed) substitute for methodological evidence that was never actually established — a command being real and well-documented says nothing about whether the underlying model is the right choice.
