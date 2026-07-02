# Command Documentation Retrieval

## Purpose

This workflow defines the hybrid documentation strategy for GAUSS command documentation. The goal is to help the GAUSS Code Assistant find exact command details when needed without turning this repository into a mirror of the official GAUSS documentation.

## Core Rules

- `experts/gauss-language/COMMAND_CATEGORIES.md` is a lightweight discovery index.
- Official GAUSS command-specific documentation is the source of truth for exact syntax, inputs, outputs, examples, return values, and version behavior.
- The assistant should retrieve official command docs dynamically when exact command details are needed.
- When official command-specific documentation is available in context or through retrieval tools, the assistant should retrieve or inspect it before telling the user to verify command behavior manually.
- A small curated command cache may exist only for high-value or frequently evaluated commands.
- Cached command files must be short reference notes, not copied full documentation pages.
- If cached notes conflict with official docs, official docs win.
- If command-specific docs cannot be retrieved, the assistant should avoid exact syntax and say verification is needed.
- Do not create command files for every command.

## Retrieval Decision Process

1. Use `COMMAND_CATEGORIES.md` to discover candidate native GAUSS commands.
2. Check whether a short curated note exists in `experts/gauss-language/commands/`.
3. If exact syntax, defaults, inputs, outputs, options, return fields, examples, or version behavior matter and official documentation is available, retrieve or inspect the official command-specific documentation.
4. Use curated notes only as a convenience summary and citation pointer.
5. Do not merely tell the user to check documentation when the assistant can check it.
6. If retrieval succeeds, summarize the verified behavior and identify the source.
7. If retrieval fails or official documentation is unavailable, state what remains unverified and recommend checking official docs.

## Curated Cache Policy

The curated command cache is optional. It should only include short verified notes for commands that are high-value, failure-prone, or repeatedly evaluated in benchmarks.

Each cached note should include:

- Command name.
- Why the note exists.
- Official source used.
- Last verified date or repository state.
- Short verified syntax summary, if known.
- Important caveats.
- Reminder that official docs remain authoritative.

Cached notes should not include copied full examples, long parameter tables, or large sections of official documentation.

## Response Policy

Use clear source-status language:

- "I verified this from official docs: ..."
- "I found the command but not the command-specific details."
- "I cannot access the docs in this context."

When exact syntax is verified:

- Mention the native command.
- Provide a concise example or call pattern.
- State key assumptions.
- Summarize verified defaults, options, return behavior, or caveats when they are relevant to the user's question.
- Identify whether the source was official docs or a curated note.
- Avoid copying documentation text.

When exact syntax is not verified:

- Mention the candidate native command if discovered.
- Say that command-specific documentation must be retrieved before production syntax is given.
- Explain whether retrieval failed, documentation was unavailable, or the assistant lacked access to the needed source.
- Provide only high-level workflow guidance or a clearly labeled teaching fallback.

## Integration Points

- `experts/gauss-language/COMMAND_CATEGORIES.md` discovers candidate commands.
- `experts/gauss-language/commands/` may contain short curated notes for selected commands.
- `workflows/native-command-selection.md` decides whether to use native commands or manual implementations.
- `workflows/knowledge-loading.md` defines source resolution and local-first retrieval.
- `prompts/code_assistant_system.md` gives runtime guidance to the Code Assistant.
- Official GAUSS documentation remains authoritative in all conflicts.
