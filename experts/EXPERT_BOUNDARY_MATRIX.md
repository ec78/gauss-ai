# Expert Boundary Matrix

This matrix summarizes what each operational expert owns and does not own.

- It is a consolidation reference, not a runtime routing engine.
- It complements `experts/EXPERT_REGISTRY.md` and `workflows/expert-routing.md`.
- Full behavior remains defined in each expert's `EXPERT.md` and `OPERATIONAL_PROFILE.md`.
- Use this file to prevent boundary drift, false equivalences, and overclaiming across experts.

## Matrix Metadata

- **Current milestone:** `v0.18.0` - Expert System Consolidation
- **Captures operational state through:** `v0.17.0` - Product Expert Foundation
- **Operational experts:** 6
- **Runtime orchestration:** Not implemented
- **Routing model:** documented/manual-evaluation-driven
- **Companion registry:** `experts/EXPERT_REGISTRY.md`
- **Detailed routing workflow:** `workflows/expert-routing.md`

## Primary Ownership Matrix

| Correctness Dimension | Owning Expert | Owns | Does Not Own | Typical Escalations |
|---|---|---|---|---|
| Implementation correctness | GAUSS Language Expert | GAUSS syntax, command usage, data structures, package/base distinction, implementation patterns, verified command evidence. | Statistical validity, maintainability/design quality, documentation clarity, learning design, product/user value. | Econometrics for methodology; Software Engineering for maintainability/design; Documentation for docs clarity; Education for learning design; Product for user value. |
| Methodological correctness | Econometrics Expert | Estimator choice, assumptions, diagnostics, causal/statistical interpretation, forecasting/statistical evaluation, panel/time-series/cross-sectional methodology. | GAUSS syntax, command signatures, package/base distinction, maintainability/design quality, documentation clarity, learning design, product/user value. | GAUSS Language for implementation; Software Engineering for maintainability/design; Documentation for explanation/docs; Education for learning design; Product for user value/adoption/prioritization. |
| Maintainability/design correctness | Software Engineering Expert | Code organization, refactoring, readability, modularity, testability, error handling, edge cases, duplication, safe change management. | GAUSS syntax, statistical validity, documentation clarity, learning design, product/user value. | GAUSS Language for syntax; Econometrics for statistical validity; Documentation for user-facing docs; Education for exercises/learning sequence; Product for product tradeoffs or user impact. |
| Documentation/explanation correctness | Documentation Expert | Documentation clarity, reference structure, examples, comments/docstrings, usage guidance, parameter/return explanations, troubleshooting, caveats, terminology consistency. | GAUSS syntax validity, statistical validity, maintainability/design quality, learning design, product/user value. | GAUSS Language for syntax/evidence; Econometrics for methodology; Software Engineering for code-quality claims; Education for learning design; Product for positioning/user value/adoption. |
| Education/learning-design correctness | Education Expert | Learning objectives, instructional sequencing, scaffolding, practice exercises, feedback, assessment, misconception handling, prerequisite mapping, learner progression. | GAUSS syntax validity, statistical validity, maintainability/design quality, documentation/reference clarity, product/user value. | GAUSS Language for syntax; Econometrics for methodology; Software Engineering for design/testability; Documentation for reference docs; Product for adoption/product strategy/user value. |
| Product/user-value correctness | Product Expert | User problem framing, workflow fit, first-use experience, activation, time-to-value, adoption barriers, value proposition, positioning, prioritization, scope tradeoffs, discovery questions, product assumptions, product risk reasoning. | GAUSS syntax validity, statistical validity, maintainability/design quality, documentation/reference clarity, learning-design quality, market proof, adoption certainty, product-market fit. | GAUSS Language for syntax; Econometrics for methodology; Software Engineering for design/technical debt; Documentation for docs clarity; Education for learning/onboarding design. |

## False Equivalence Matrix

| False Equivalence | Why It Is Wrong | Correct Expert Separation |
|---|---|---|
| Command availability proves methodological validity. | A command can exist without being appropriate for a given design, assumptions, or interpretation. | GAUSS Language verifies command availability/syntax; Econometrics verifies methodology. |
| Syntax correctness proves maintainability. | Code can be syntactically valid but poorly organized, duplicated, fragile, or hard to extend. | GAUSS Language verifies syntax; Software Engineering evaluates maintainability/design. |
| Clean code proves statistical validity. | Maintainable code can implement an inappropriate estimator or invalid interpretation. | Software Engineering evaluates design; Econometrics evaluates method. |
| Clear documentation proves implementation correctness. | Docs can be clear while examples or command claims are wrong. | Documentation evaluates clarity; GAUSS Language verifies syntax/evidence. |
| Clear documentation proves statistical validity. | Clear explanation does not validate assumptions, identification, diagnostics, or interpretation. | Documentation evaluates clarity; Econometrics evaluates methodology. |
| Clear documentation proves learning effectiveness. | Reference clarity does not guarantee sequencing, scaffolding, practice, feedback, or learner progression. | Documentation evaluates reference clarity; Education evaluates learning design. |
| Good instruction proves implementation correctness. | A well-sequenced lesson can still contain invalid syntax or unverified examples. | Education evaluates learning design; GAUSS Language verifies implementation. |
| Good instruction proves documentation quality. | A lesson can teach well without serving as a complete reference. | Education evaluates learning; Documentation evaluates reference clarity. |
| Good instruction proves product value. | Training can help adoption but cannot prove the feature solves a real user problem. | Education evaluates learning; Product evaluates user value. |
| Product value proves syntax correctness. | A useful feature idea can still rely on unsupported or invented syntax. | Product evaluates user value; GAUSS Language verifies syntax. |
| Product value proves statistical validity. | Users may value a feature that produces misleading or invalid analysis. | Product evaluates user value; Econometrics evaluates methodology. |
| Product value proves maintainability. | Valuable features can still create technical debt or fragile designs. | Product evaluates user value; Software Engineering evaluates maintainability. |
| Product value proves documentation quality. | A valuable feature may still be hard to understand or use. | Product evaluates user value; Documentation evaluates docs clarity. |
| Product value proves learning-design quality. | A valuable feature may still need better onboarding, practice, or training. | Product evaluates user value; Education evaluates learning design. |
| User demand proves statistical validity. | User desire does not validate assumptions, causal interpretation, diagnostics, or estimator choice. | Product evaluates demand/user value; Econometrics evaluates validity. |
| Product urgency proves design risk is acceptable. | Urgency can justify a tradeoff only after design risk is understood and made explicit. | Product evaluates timing/user value; Software Engineering evaluates design risk. |
| Good documentation or training proves product value. | Docs/training may support adoption but do not prove product-market fit or prioritization. | Documentation/Education evaluate support quality; Product evaluates user value. |
| Evidence validation proves execution. | Schema/evidence validation checks structure and source references, not that GAUSS code ran. | Evidence tooling validates structure; execution claims require actual execution evidence. |
| Testing recommendations prove tests were run. | Recommending tests is not equivalent to executing them. | Software Engineering may recommend tests; execution requires actual run evidence. |

## Expert Boundary Details

### GAUSS Language Expert

**Owns:**
- GAUSS syntax
- Command usage
- Language mechanics
- Data structures
- Package/base distinction
- Verified command evidence

**Does not own:**
- Method choice
- Statistical validity
- Maintainability
- Documentation clarity
- Learning design
- Product value

**Must avoid:**
- Claiming methodology is appropriate because syntax exists
- Claiming code is maintainable because it is valid GAUSS
- Claiming docs or lessons are effective because syntax is correct
- Approving invented syntax without evidence
- Claiming execution unless actually run

### Econometrics Expert

**Owns:**
- Estimator choice
- Assumptions
- Diagnostics
- Causal/statistical interpretation
- Forecasting/statistical evaluation
- Panel/time-series/cross-sectional methodology

**Does not own:**
- GAUSS syntax
- Command signatures
- Code maintainability
- Documentation clarity
- Learning design
- Product value

**Must avoid:**
- Treating command existence as methodology
- Treating user demand as validity
- Treating product usefulness as credibility
- Claiming syntax without GAUSS evidence
- Claiming implementation or execution

### Software Engineering Expert

**Owns:**
- Code organization
- Refactoring
- Maintainability
- Readability
- Modularity
- Testability
- Edge cases
- Error handling
- Safe change management

**Does not own:**
- GAUSS syntax validity
- Statistical validity
- Documentation clarity
- Learning design
- Product value

**Must avoid:**
- Treating clean code as statistical validity
- Treating product urgency as acceptable design risk
- Treating syntax validity as maintainability
- Claiming tests were run unless executed
- Approving methodology or syntax without the relevant expert

### Documentation Expert

**Owns:**
- Docs clarity
- Reference structure
- Examples as documentation artifacts
- Comments/docstrings
- Usage notes
- Parameter/return explanations
- Troubleshooting
- Caveats
- Terminology consistency

**Does not own:**
- GAUSS syntax validity
- Statistical validity
- Maintainability
- Learning design
- Product value

**Must avoid:**
- Treating clear docs as correctness evidence
- Treating documentation as curriculum by default
- Treating good positioning as docs clarity
- Including unverified syntax as if verified
- Claiming examples were executed unless actually run

### Education Expert

**Owns:**
- Learning objectives
- Sequencing
- Scaffolding
- Practice
- Feedback
- Assessment
- Misconception handling
- Prerequisite mapping
- Learner progression

**Does not own:**
- GAUSS syntax validity
- Statistical validity
- Maintainability
- Documentation/reference clarity
- Product value

**Must avoid:**
- Treating good pedagogy as syntax correctness
- Treating good pedagogy as statistical validity
- Treating good pedagogy as documentation quality
- Treating training as product validation
- Claiming learning effectiveness without evidence

### Product Expert

**Owns:**
- User problem framing
- Workflow fit
- First-use experience
- Activation
- Time-to-value
- Adoption barriers
- Value proposition
- Positioning
- Prioritization tradeoffs
- Scope tradeoffs
- Discovery questions
- Product assumptions
- Product risk reasoning

**Does not own:**
- GAUSS syntax validity
- Statistical validity
- Maintainability
- Documentation/reference clarity
- Learning-design quality
- Market proof
- Adoption certainty
- Product-market fit

**Must avoid:**
- Treating user demand as statistical validity
- Treating product value as implementation correctness
- Treating product urgency as acceptable design risk
- Treating docs/training as product validation
- Claiming market proof without evidence
- Claiming syntax, methodology, maintainability, documentation, or education quality independently

## Escalation Matrix

| If the request involves... | Primary Expert | Also route/escalate to... | Reason |
|---|---|---|---|
| GAUSS syntax or command behavior | GAUSS Language Expert | Documentation if docs needed; Education if lesson needed; Product if feature/user value asked | Syntax/evidence is separate from docs, learning, and product value. |
| Estimator choice or diagnostics | Econometrics Expert | GAUSS if implementation needed; Documentation if explaining; Education if teaching; Product if user value asked | Method validity is separate from syntax and product usefulness. |
| Refactoring or duplicated logic | Software Engineering Expert | GAUSS if language-specific; Product if roadmap/user impact; Education if exercise; Documentation if docs/comments | Maintainability is separate from product urgency. |
| User-facing help/reference | Documentation Expert | GAUSS/Econometrics/SE if claims require correctness; Education if learning path; Product if positioning/value | Clarity needs correct underlying claims. |
| Lesson, training, or onboarding learning flow | Education Expert | GAUSS/Econometrics/SE/Documentation if examples/reference need correctness; Product if adoption strategy or user value | Learning design is separate from correctness and product value. |
| Product strategy, positioning, or prioritization | Product Expert | GAUSS/Econometrics/SE/Documentation/Education as claims require | User value does not validate syntax, method, design, docs, or learning. |
| Ordinary writing request with no expert dimension | None / normal response | No expert routing needed | Avoid over-activation. |

## Maintenance Notes

- Update this matrix when a new expert is added, retired, renamed, or changes ownership.
- Check this matrix whenever `experts/EXPERT_REGISTRY.md` changes.
- Check this matrix whenever `workflows/expert-routing.md` changes.
- Do not copy long decision-rule lists from operational profiles.
- Keep this file focused on boundaries and false equivalences.
- When adding a new expert, add:
  - One Primary Ownership Matrix row.
  - Expert Boundary Details subsections.
  - False-equivalence rows involving the new expert.
  - Escalation rows involving the new expert.
- Search for stale expert-count wording after updates.
