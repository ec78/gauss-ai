# Evaluation Result

Date: 2026-07-05
Evaluator: Claude
Agent Version: Current repository state on 2026-07-05 (v0.8.0 Operational Expert Modules milestone)
Prompt ID: 15.5
Prompt Category: Expert Routing
Prompt Text:

The user asks whether to use a GAUSS DataFrame or matrix for a workflow that imports labeled data, cleans missing values, then performs numerical modeling.

Concrete prompt used for this evaluation: "I'm importing a CSV with labeled columns, dates, and some missing values. I need to clean it, create a few transformed variables, and then run numerical modeling in GAUSS. Should I keep the data as a DataFrame the whole time, or convert it to a matrix? What's the best workflow?"

Expected behavior:

- Routes through the GAUSS Language Expert because this is a GAUSS data-structure decision.
- Uses BODY_OF_KNOWLEDGE-style language mechanics rather than command-specific retrieval unless exact command syntax is requested.
- Distinguishes DataFrame and matrix roles clearly.
- Recommends DataFrame for labeled/imported/mixed/date/categorical/cleaning context where appropriate.
- Recommends matrix for numerical computation/modeling where appropriate.
- Does not treat DataFrames and matrices as interchangeable.
- States assumptions and possible workflow transition points.
- Does not literally need to print "GAUSS Language Expert activated."

Evidence/source material used for this evaluation: no command-specific retrieval was performed or required, consistent with the task instructions — this is a data-structure design question, not an exact-syntax request. Grounding comes from `experts/gauss-language/BODY_OF_KNOWLEDGE.md`, inspected directly:

- Section 2.6 (DataFrames): "Use DataFrames when working with imported data, named variables, or mixed data types... Use matrices when the task is primarily numerical computation... Convert or extract data intentionally when moving between DataFrame workflows and matrix-based procedures."
- Section 2.6 failure modes: "Treating a DataFrame exactly like a matrix... Generating matrix-only code for a DataFrame task... Generating DataFrame code when a simple matrix is more appropriate."
- Section 2.10 decision table rows used directly: "Imported dataset with variable names → DataFrame", "Mixed-type tabular data → DataFrame", "Regression inputs after cleaning → Matrix", "Time-indexed data → DataFrame or matrix with explicit date handling."
- Section 1.2 agent guidance: "Use DataFrames when labels, mixed types, dates, or categoricals matter."

Generated Code Assistant Response:

Short answer: keep it as a DataFrame through import, cleaning, and transformation, then move to a matrix right before the numerical modeling step — don't pick one structure for the whole pipeline.

**Why DataFrame for the first part.** Your data has exactly the characteristics that call for a DataFrame: labeled columns, dates, and missing values from an import. GAUSS DataFrames exist specifically for "imported data, named variables, or mixed data types," and are the right structure while variable names, dates, and categorical handling still matter — which they do during cleaning and transformation. Doing cleaning and transformation on a bare matrix would mean losing column names and having to track "column 3 is actually `income`" by position, which is exactly the kind of DataFrame-shaped problem that shouldn't be force-fit into matrix indexing.

**Why matrix for the modeling step.** Once your variables are cleaned and transformed and you're ready for numerical modeling, matrices become the better fit — that's the structure GAUSS's numerical and linear-algebra machinery is built around, and it's the natural representation once you've settled on which columns are actually going into the model. At that point the column names have done their job (helping you build and verify the transformations correctly); the model itself mostly cares about the numeric values and their shape.

**The transition point.** Convert or extract intentionally, not implicitly — don't let a DataFrame silently get treated as a matrix somewhere in the middle of your code. A clean way to think about it: finish all your labeled work (import, missing-value cleaning, date handling, creating transformed variables) while still in the DataFrame, then do one deliberate extraction step into a matrix (or matrices — e.g., a separate `y` and `x` block) right before the modeling call. That keeps the "this is still labeled data" and "this is now numeric input to a model" phases clearly separated in the code, instead of ambiguous in the middle.

**One assumption worth stating:** whether you even need that explicit extraction step depends on which specific modeling procedure you end up using — some native GAUSS estimation procedures accept a DataFrame directly and extract what they need internally, while others expect plain matrix/vector inputs. I don't want to name a specific procedure's exact input requirements here without checking its documentation, since that would be a command-specific syntax claim rather than a general data-structure recommendation. If you tell me which modeling procedure you're planning to use, I can check whether it takes a DataFrame directly or needs matrix inputs.

**What to watch for either way:**
- Don't treat the DataFrame and matrix as interchangeable mid-pipeline — a failure mode worth naming explicitly is generating matrix-only cleaning code for what's still fundamentally a DataFrame task (or the reverse: converting to a matrix too early and losing the labels you still needed for cleaning).
- Handle missing values and date parsing while still in the DataFrame, since that's where GAUSS's DataFrame-aware tooling for categorical/date/missing-value handling is designed to operate — pushing that into a matrix loses that context.
- When you do extract to a matrix, double-check row/column orientation and that no rows silently dropped or reordered between the DataFrame and matrix versions of your data.

Response Summary:

The response gives a clear DataFrame-then-matrix recommendation rather than picking one structure for the entire pipeline, matching the "recommends DataFrame for X, matrix for Y" and "does not treat them as interchangeable" requirements directly. Every substantive claim is traceable to `BODY_OF_KNOWLEDGE.md` content actually inspected for this evaluation — the DataFrame-for-imported/labeled/mixed-type guidance, the matrix-for-numerical-computation guidance, the "convert or extract intentionally" transition guidance, and the named failure modes (treating a DataFrame like a matrix, generating matrix-only code for a DataFrame task) are used almost verbatim rather than restated as generic advice invented for this response. It identifies a concrete transition point (finish labeled work in the DataFrame, then one deliberate extraction step before modeling) rather than leaving "when do I convert" unanswered. It correctly declines to name a specific modeling procedure's exact input requirements, explicitly stating that doing so would be a command-specific syntax claim requiring its own documentation check — this is the correct boundary per the task instructions (no command-specific retrieval required unless exact syntax is introduced) and demonstrates the expert applying a narrower evidence bar for a general data-structure question than it would for an exact-syntax question, without ever crossing into an unverified syntax claim. No GAUSS Language Expert activation label appears; activation is evident from the DataFrame/matrix distinction being enforced throughout, the decision-table-grounded recommendation, and the deliberate refusal to extend into command-specific territory without evidence.

Scores:
- GAUSS Syntax Correctness: N/A
- Function and Package Validity: N/A
- Data Structure Reasoning: 4
- Dimension and Numerical Awareness: 4
- Task Mode Fit: 4
- Explanation Quality: 4
- Assumptions and Dependencies: 4
- Maintainability and Best Practices: N/A
- Testing or Validation: N/A
- Hallucination and Cross-Language Contamination Avoidance: 4

Overall Score: 4.0
Decision: Pass

N/A Notes:
- GAUSS Syntax Correctness: marked N/A. No GAUSS code is produced; this is a design-guidance response by design, not a code-generation one.
- Function and Package Validity: marked N/A. No specific GAUSS function or procedure is named or claimed as verified; the response explicitly declines to do so pending the user naming their target procedure.
- Maintainability and Best Practices: marked N/A. This is a data-structure design recommendation, not a review of existing reusable code.
- Testing or Validation: marked N/A. No code was generated or diagnosed, so a translation/debugging-style validation step does not apply; the "what to watch for" list serves the equivalent role of a design-guidance checklist for this response type.

Blocking Issues:
None. No invented command syntax, no treatment of DataFrames and matrices as interchangeable, no unnecessary command-specific evidence requirement imposed, and no claim of execution.

Suggested Improvements:
None blocking. The response could have named `experts/gauss-language/BODY_OF_KNOWLEDGE.md`'s Section 2.10 decision table explicitly as its source, the way retrieval-backed responses cite a specific evidence file, for a slightly more traceable paper trail — though the guidance given is accurate to that source regardless.

Follow-up Actions:
- This is the sixth Expert Routing evaluation and the second design-guidance-style case (after 15.6's ambiguity escalation, which was also non-code); it confirms the expert applies a narrower, BODY_OF_KNOWLEDGE-grounded evidence bar correctly for general language-mechanics questions without either overreaching into unverified syntax or under-reaching into generic advice untethered from the knowledge base.
- Only one Expert Routing prompt remains unevaluated: 15.4 (`qnewtonmt` vs. `minimize`, version-sensitive command selection). Running it would complete the full 15.1-15.7 category.
- No file needed correction as a result of this evaluation; `BODY_OF_KNOWLEDGE.md` fully supported the design-guidance response as asked, without needing command-specific retrieval or a synthetic fixture.
