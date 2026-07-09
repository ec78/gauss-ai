# Common Mistakes

Common AI and user failure modes the Software Engineering Expert should help agents avoid.

- Mixing data cleaning, modeling, diagnostics, and reporting in one undifferentiated block instead of separating them into distinguishable stages.
- Using unclear variable names that don't communicate purpose.
- Writing overlong procedures that mix several unrelated responsibilities.
- Introducing hidden dependencies between parts of the code that aren't visible from the interface.
- Duplicating logic instead of extracting a shared helper.
- Omitting input validation, so invalid inputs fail silently or unpredictably.
- Omitting edge-case handling — missing data, empty inputs, unexpected dimensions — and only handling the common path.
- Skipping tests or comparison checks, especially before a risky change.
- Changing behavior during a refactor without saying so, which hides which change caused which effect.
- Optimizing before correctness and readability are established, adding complexity for uncertain benefit.
- Treating syntactically valid code as well-designed code — the two are independent claims, and conflating them lets poor structure hide behind "it works."
- Treating clean, well-organized code as proof of statistical or causal validity — code quality says nothing about whether the underlying method or design is methodologically sound (`EXPERT.md`, Relationship to Econometrics Expert).
- Using Python-like (or other cross-language) constructs in GAUSS code without verification, because they look cleaner — aesthetic preference is never a substitute for verified GAUSS syntax (`EXPERT.md`, Relationship to GAUSS Language Expert).
- Claiming tests were run, passed, or failed when they were not actually executed — a recommended test is not a confirmed result (`reasoning.md`, Testing Reasoning).
