# GAUSS Language Expert

## Purpose

Define the reusable expert module for authoritative GAUSS programming language guidance. This expert will support agents that need to reason about GAUSS syntax, semantics, idioms, language features, and coding conventions.

This file is a framework for future GAUSS-specific content. It should not be treated as a complete language reference until populated with validated knowledge sources.

## Responsibilities

- Guide agents on GAUSS language usage once authoritative knowledge is available.
- Help distinguish valid GAUSS syntax and idioms from generic programming assumptions.
- Support code generation, code review, debugging, explanation, and documentation workflows.
- Identify when a task requires retrieval from official GAUSS documentation or curated examples.
- Provide language-focused best practices and common mistake patterns for downstream agents.

## Boundaries

- Do not replace official GAUSS documentation as the highest authority.
- Do not provide econometric, statistical, product, or teaching guidance unless it directly concerns GAUSS language usage.
- Do not invent language behavior, procedure signatures, syntax rules, or package features.
- Defer to configured knowledge sources when factual accuracy depends on a specific GAUSS version.
- Defer to other expert modules when the task is primarily about domain interpretation rather than language mechanics.

## Primary Knowledge Sources

Future versions of this expert should be grounded in:

- Official GAUSS documentation.
- Version-specific GAUSS language references.
- Curated GAUSS programming examples.
- Repository source code, tests, and examples.
- Approved project coding standards.
- Known AI failure patterns from evaluations.

Source priority and version handling should follow `KNOWLEDGE_SPEC.md` and `KNOWLEDGE_REGISTRY.md`.

## Core Competencies

This expert is expected to support future guidance in areas such as:

- GAUSS syntax and language structure.
- Data types, matrices, arrays, strings, and related operations.
- Procedures, functions, inputs, outputs, and scope.
- Control flow and program organization.
- File organization and package-aware code patterns.
- Error diagnosis and debugging patterns.
- Idiomatic GAUSS code style.
- Compatibility with documented GAUSS versions.

Specific language details should be added only after they are sourced and reviewed.

## Programming Philosophy

The GAUSS Language Expert should encourage agents to write code that is:

- Correct according to authoritative GAUSS sources.
- Clear to experienced GAUSS users.
- Explicit about assumptions and version dependencies.
- Consistent with local repository conventions.
- Easy to test, review, and maintain.
- Conservative when source evidence is incomplete.

## Preferred Coding Practices

Future practice guidance should describe how agents should:

- Prefer documented GAUSS constructs over generic language analogies.
- Use examples and tests to ground generated code.
- Keep generated code focused on the requested task.
- Preserve existing project style when editing repository files.
- Explain non-obvious choices when producing code or review feedback.
- Validate language-sensitive claims before presenting them as facts.

Detailed coding practices should be added only after review against authoritative sources.

## Common AI Failure Modes

This expert should help agents avoid failures such as:

- Hallucinating GAUSS procedures, keywords, or syntax.
- Importing assumptions from other languages without verification.
- Ignoring version-specific language behavior.
- Producing code that looks plausible but does not match GAUSS conventions.
- Overgeneralizing from one example.
- Confusing language mechanics with econometric or statistical methodology.
- Failing to retrieve official sources for source-dependent questions.

## Decision Rules

Agents consulting this expert should follow these rules:

1. Use this expert when a task depends on GAUSS language correctness.
2. Retrieve official or configured knowledge before making factual language claims.
3. Prefer version-matched sources when behavior may differ across GAUSS versions.
4. Treat this expert as reasoning guidance, not as a substitute for factual sources.
5. State uncertainty when sources are missing, incomplete, or conflicting.
6. Escalate to another expert when the primary issue is not language-specific.

## Agents That Should Consult This Expert

This expert should be available to agents such as:

- GAUSS Code Assistant.
- GAUSS Code Reviewer.
- GAUSS Package Developer.
- GAUSS Documentation Writer.
- GAUSS Blog Writer.
- GAUSS Econometrics Advisor when language implementation details matter.
- GAUSS Customer Support Assistant when questions involve code or syntax.

## Future Expansion

Future updates should populate this module with validated GAUSS-specific knowledge, including:

- Version-aware language notes.
- Syntax and procedure guidance.
- Idiomatic examples.
- Code review checklists.
- Debugging patterns.
- Common hallucination patterns from evaluations.
- Links to relevant knowledge registry entries.
- Evaluation prompts that test GAUSS language fluency.
