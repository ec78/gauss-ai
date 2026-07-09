# Best Practices

Practices the Software Engineering Expert should promote across agents that consult it.

- Prefer small, focused procedures/functions over large ones that mix several responsibilities (`BODY_OF_KNOWLEDGE.md`, Modularity and Decomposition).
- Use clear, meaningful names rather than terse or misleading ones (`BODY_OF_KNOWLEDGE.md`, Naming and Readability).
- Give each unit explicit inputs and outputs rather than relying on hidden shared state (`BODY_OF_KNOWLEDGE.md`, Modularity and Decomposition).
- Separate data preparation, modeling, diagnostics, and reporting into distinguishable stages instead of one undifferentiated block (`BODY_OF_KNOWLEDGE.md`, Code Organization).
- Avoid duplicated logic — extract repeated blocks into a shared helper instead of copy-pasting (`BODY_OF_KNOWLEDGE.md`, Common Anti-Patterns).
- Preserve original behavior during refactoring unless a behavior change is explicitly requested and stated (`BODY_OF_KNOWLEDGE.md`, Refactoring).
- Add tests or comparison checks before risky changes, not after (`BODY_OF_KNOWLEDGE.md`, Testing and Validation Strategy).
- Handle edge cases explicitly — missing data, empty inputs, unexpected dimensions — rather than assuming only the common path occurs (`BODY_OF_KNOWLEDGE.md`, Error Handling and Edge Cases).
- State assumptions explicitly, especially ones a recommendation depends on (`reasoning.md`).
- Avoid premature optimization — establish correctness and clarity before optimizing, and identify actual bottlenecks before addressing them (`BODY_OF_KNOWLEDGE.md`, Performance Tradeoffs).
- Document non-obvious decisions so a future reader understands why, not just what (`BODY_OF_KNOWLEDGE.md`, Naming and Readability).
- Prefer incremental changes over large, hard-to-review rewrites when the risk of a change is uncertain (`BODY_OF_KNOWLEDGE.md`, Safe Change Management).
- Label pseudocode clearly whenever a structural example is not verified GAUSS syntax (`EXPERT.md`, Response Behavior).
- Defer exact GAUSS syntax to the GAUSS Language Expert and its evidence requirements — never invent GAUSS constructs to fit a recommended structure (`EXPERT.md`, Relationship to GAUSS Language Expert).
- Defer methodological and statistical claims to the Econometrics Expert — clean code is never evidence of methodological or causal validity (`EXPERT.md`, Relationship to Econometrics Expert).
