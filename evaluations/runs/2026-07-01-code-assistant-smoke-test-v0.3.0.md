# v0.3.0 Code Assistant Smoke Test

Date: 2026-07-02

Purpose:
Verify that the Code Assistant quickstart and onboarding documentation provide enough context for a new user to get a safe, GAUSS-native answer before tagging `v0.3.0` - Code Assistant Preview.

## Context Files Used

- `README.md`
- `agents/code-assistant/README.md`
- `agents/code-assistant/QUICKSTART.md`
- `agents/code-assistant/AGENT.md`
- `agents/code-assistant/task_modes.md`
- `prompts/system_prompt.md`
- `prompts/code_assistant_system.md`
- `experts/gauss-language/BODY_OF_KNOWLEDGE.md`
- `experts/gauss-language/COMMAND_CATEGORIES.md`
- `workflows/native-command-selection.md`
- `workflows/command-documentation-retrieval.md`
- `evaluations/scoring.md`
- `planning/v0.3.0-readiness-checklist.md`

## Smoke-test Prompt

I am translating this R model to GAUSS:

```r
model <- lm(y ~ x1 + x2, data = df)
summary(model)
```

Can you show me the safest GAUSS-native way to approach this?

## Generated Response

The safest GAUSS-native approach is to translate the modeling intent, not the R API.

In R, `lm(y ~ x1 + x2, data = df)` combines a formula interface, model fitting, and later `summary()` reporting. In GAUSS, I would first look for a native estimation procedure rather than recreating OLS manually. The native command discovery guidance points to the estimation category, where `olsmt` is the relevant GAUSS OLS procedure.

A short curated note in this repository says the official `olsmt` documentation includes these formats:

```gauss
out = olsmt(data, formula[, ctl]);
out = olsmt(data, depvar, indvars[, ctl]);
```

So the GAUSS-native pattern is:

```gauss
// Verify exact syntax and reporting details in the official olsmt docs
// before using this in production code.
out = olsmt(df, "y ~ x1 + x2");
```

Assumptions:

- `df` is a GAUSS DataFrame or another data source accepted by `olsmt`.
- `y`, `x1`, and `x2` are column names in `df`.
- The formula interface is appropriate for this model.
- The intercept behavior should be checked in the official `olsmt` documentation before production use.
- Missing-value handling and row alignment should be verified before trusting the fitted model, especially if any of `y`, `x1`, or `x2` contain missing values.

Do not translate this as:

```gauss
model = lm(y ~ x1 + x2, df);
summary(model);
```

That carries R functions and formula behavior into GAUSS without verification.

For production code, I would verify the command-specific `olsmt` documentation for:

- the exact accepted formula syntax,
- whether `df` can be passed directly in your GAUSS version,
- intercept defaults and how to change them,
- missing-value handling,
- the fields available in the returned `olsmtOut` structure,
- and the recommended way to print or report results.

Manual matrix OLS, such as building `y` and `x` matrices and computing `(x'x)^(-1)x'y`, is useful for teaching the mechanics or custom estimators. It should not be the first production translation when `olsmt` fits the standard workflow.

## Assessment

The quickstart provided enough context to produce a safe answer. It clearly directed the trial toward task classification, relevant context files, native command discovery, official documentation verification, known GAUSS failure modes, and optional evaluation recording.

The generated response:

- avoided inventing R-style `lm()` or `summary()` APIs in GAUSS,
- used native command discovery to identify `olsmt`,
- used the curated `olsmt` note only for the verified high-level call formats,
- stated that official command-specific documentation remains required for production details,
- explained DataFrame/formula assumptions,
- mentioned intercept and missing-value assumptions,
- treated manual matrix OLS as a teaching fallback,
- and clearly stated what should be verified before production use.

Decision: Pass with minor revision

## Documentation Gaps Found

The response correctly avoided hallucination, identified `olsmt`, used the curated note only for verified high-level formats, and kept official command-specific documentation authoritative.

However, it was too passive about retrieval responsibility. It said the user should check intercept behavior in the official `olsmt` documentation before production use. When official command-specific documentation is available to the assistant, the assistant should retrieve or inspect it and answer the user's question directly. It should only tell the user to verify details manually when documentation is unavailable, retrieval fails, or the assistant does not have access to the needed source.

Follow-up action:

- Update command documentation retrieval guidance so the assistant owns retrieval when official docs are available.

The smoke test confirms that the quickstart and onboarding docs are usable for this representative translation task, with a minor revision needed around retrieval responsibility. Future responses should attempt command-specific documentation retrieval before saying the user should verify details manually.

## Rerun After Retrieval-Responsibility Update

Date: 2026-07-02

Purpose:
Re-run the same smoke-test prompt after updating retrieval guidance. The response should either retrieve `olsmt` intercept behavior from official command-specific documentation or explicitly say that official command-specific docs were not accessible in the test context.

### Generated Response

The safest GAUSS-native approach is to translate the modeling intent, not the R API.

I would not create GAUSS calls named `lm()` or `summary()`. Those are R APIs, and carrying them into GAUSS would be a cross-language hallucination risk.

Using the native command selection workflow, this is a standard OLS/regression task, so the first GAUSS-native candidate is `olsmt`. The command category inventory lists `olsmt` under estimation-related commands, and the curated `olsmt` note in this repository says it is a native least-squares procedure with documented high-level formats:

```gauss
out = olsmt(data, formula[, ctl]);
out = olsmt(data, depvar, indvars[, ctl]);
```

Given that verified curated note, the closest GAUSS-native shape is:

```gauss
out = olsmt(df, "y ~ x1 + x2");
```

Source status:

- I verified the high-level `olsmt` call formats from the curated `experts/gauss-language/commands/olsmt.md` note.
- I found `olsmt` as the relevant native command candidate through the command category guidance.
- I cannot access the official command-specific `olsmt` documentation in this smoke-test context, so I cannot verify intercept defaults, missing-value behavior, output fields, reporting options, or detailed formula rules here.

Assumptions to resolve before production use:

- `df` must be a DataFrame or other data source accepted by `olsmt`.
- `y`, `x1`, and `x2` must match variables available in that data source.
- Formula syntax is documented for `olsmt`, but detailed formula behavior should be verified from the official command page.
- Intercept behavior is not verified in this test context because the official `olsmt` command-specific docs are not accessible here.
- Missing-value handling and row alignment across `y`, `x1`, and `x2` are not verified in this test context and should be checked from official docs or tested with representative data.

Manual matrix OLS is only a secondary teaching fallback here. It can help explain the mechanics, but it should not replace the native `olsmt` workflow for a standard R `lm()` translation unless you need custom estimation logic or cannot use `olsmt`.

### Assessment

The rerun satisfies the retrieval-responsibility requirement.

The response:

- avoided R-style `lm()` and `summary()` APIs,
- identified `olsmt` as the GAUSS-native OLS candidate,
- used command categories for discovery,
- used the curated `olsmt` note only for verified high-level formats,
- explicitly stated that official command-specific docs were not accessible in the smoke-test context,
- did not invent intercept behavior, missing-value behavior, output fields, or detailed formula rules,
- explained DataFrame/formula assumptions,
- treated manual matrix OLS as a teaching fallback,
- and clearly distinguished verified information from unavailable command-specific details.

Decision: Pass

### Documentation Gaps Found

None blocking.

The updated guidance corrected the earlier retrieval-responsibility issue. The Code Assistant Preview still depends on future retrieval tooling for automatic official-doc lookup, but the manual workflow now tells the assistant to own retrieval when docs are available and to say clearly when docs are not accessible.
