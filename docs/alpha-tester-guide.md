# Alpha Tester Guide

**Status: Alpha — intended for controlled testing.**

Thank you for testing the GAUSS Code Assistant. This guide covers what to test, what not to expect yet, how to report what you find, and how to tell a product problem from a problem in your own GAUSS code.

## What to test

- **Installation**: `pip install -e .` in a clean environment, then `gauss-ai version`/`gauss-ai doctor`.
- **Conversational Q&A** (`gauss-ai`, no subcommand — new in `v0.70.0`; local Ollama support added in `v0.71.0`): a basic question, a follow-up question that relies on context ("show me an example"), a known error code (e.g. "what does G0036 mean?"), a question about a command you know isn't real, and trying to get it to "run" or "execute" something (it should redirect you to `gauss-ai repair`, never actually execute anything). Typing a `gauss-ai` command like `gauss-ai doctor` at the chat prompt should also be recognized and redirected, never sent to the model. See [docs/conversational-qa.md](conversational-qa.md).
- **Conversational code generation** (new in `v0.72.0`; grounding-gated generation and function resolution added in `v0.73.0`): ask for GAUSS code directly ("write GAUSS code to reshape a matrix"), a natural-language description with no function name given ("calculate the column means" -- should resolve to the real `meanc`), a request naming two real commands together (grounding should name both), a request for something with no real documentation support (should be refused outright, not fabricated), and a request asking it to run or apply the code it just generated (should still redirect, never execute or edit a file). Treat all generated code as unverified -- a deterministic gate now refuses generation when no documentation supports it, and a post-generation check flags an unsupported symbol if the model still introduces one, but neither guarantees correctness. See [docs/conversational-code-generation.md](conversational-code-generation.md) and [docs/grounding-gated-generation.md](grounding-gated-generation.md).
- **First-run setup**: `gauss-ai init`, including re-running it to confirm it doesn't corrupt prior configuration.
- **The guided workflow** (`gauss-ai repair <file.gss>`), in both fake mode and (if you have GAUSS installed) real mode:
  - A file with a real, reproducible error (start with `examples/alpha-demo/broken.gss`, then try your own).
  - A file that already runs successfully (the "nothing to repair" path).
  - Declining at each individual approval point, one at a time, to confirm the workflow stops cleanly and does not proceed.
  - Whether the plain-language guidance at each step made sense without needing to read this repository's own source code.
- **The lower-level REPL** (`python scripts/gauss_code_assistant_cli.py`), if you want to exercise individual pipeline stages directly rather than through the guided wrapper — see the main [README.md](../README.md) for its full command reference.
- **Doctor's diagnostics** against your own real environment: a valid GAUSS install, a missing one, a GUI executable configured by mistake, and a corrupted config file.

## What not to expect yet

This is an alpha for a **single-file, human-approved repair workflow**. It does not, and is not expected to:

- Repair more than one file per session.
- Retry, roll back, or rerun anything automatically.
- Decide anything on your behalf — every approval, confirmation, and review is yours to make.
- Guarantee that a proposed repair is correct — verification produces evidence, never a correctness verdict (see "Current safety boundaries" below).
- Run on macOS or Linux with real GAUSS execution (fake-mode-only testing works anywhere Python 3.10+ does).
- Persist a session across a process restart (durable sessions — repair or chat — are explicitly out of scope for this milestone).
- Execute anything, apply a repair, or write a file from a conversational chat session — chat can generate GAUSS code on request (`v0.72.0`) but never executes, applies, or saves it; it redirects you to `gauss-ai repair <file.gss>` for anything execution- or repair-shaped, even immediately after generating code.
- Send any data anywhere — there is no telemetry, no analytics, no network reporting of any kind. A real chat provider's API key, if you configure one, is read from your own environment variable only, never stored by `gauss-ai` itself.

If you hit one of these, it's expected, not a bug — see [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) for the complete, current list.

## Current safety boundaries

Every one of the following remains true regardless of how you invoke the tool (guided or lower-level REPL):

- **No execution without explicit confirmation.** A `plan`/`verify-repair` proposal never runs by itself — a matching `confirm <request_hash>` is always required first.
- **No approval decided for you.** Strategy approval, draft approval, application approval, and verification review are each a separate, independent, digest-bound decision — approving one never approves another.
- **No file read without explicit authorization.** The lower-level `read <path>` command is the only way to see file contents; the guided workflow reads only the one file you named on its own command line.
- **No file written except through the approved application transaction**, which always creates a backup first and never overwrites anything outside the workspace it created.
- **No fabricated verification outcome.** A verification review's decision (`accepted`/`rejected`/`inconclusive`) is always exactly what you typed — never inferred from the evidence.
- **No conversational bypass into execution or repair.** Chat (`gauss-ai`, no subcommand) never executes GAUSS code, applies a repair, or writes a file — structurally, not just by prompt wording: the conversational modules import nothing from the execution/repair/verification pipeline at all.

If you ever observe one of these boundaries appear to be crossed, that is a **safety concern** — report it with "Critical" severity (see below) regardless of anything else about the finding.

## How to collect a repair-session summary

At any point in a lower-level REPL session, or automatically at the end of a guided-repair run, `show-repair-session` (or the guided command's own final output) prints the complete, evidence-only state of the current session in one place — every stage reached, the timeline, and the current status. Include this output in full with any bug report; it is the single most useful artifact for reproducing what you saw.

## Distinguishing a product issue from a GAUSS-code issue

- If **diagnosis or the proposed repair strategy is wrong or unhelpful** for a genuine GAUSS error, that is useful feedback about the assistant's reasoning — report it, including the exact error code shown (e.g. `G0105`) and the real GAUSS output if you have it.
- If **the assistant crashes, hangs, produces a Python traceback, silently skips an approval, or otherwise behaves inconsistently with the boundaries above**, that is a product defect — report it as such, with full command-by-command reproduction steps.
- If **your own GAUSS code has a bug the assistant correctly identifies and offers to help with**, that is the system working as intended, not something to report (though feedback on how clear or useful the proposed fix was is still welcome).
- When in doubt, report it anyway — see the feedback template below, which has a field specifically for this distinction.

## How to report bugs

Use [docs/alpha-feedback-template.md](alpha-feedback-template.md) — it now includes fields for task attempted, source/error type, setup, expected vs. observed behavior, the specific step that felt confusing, any safety concern, how useful the proposed repair was, the verification outcome, your final review decision, the full repair-session summary, severity, and exact reproduction steps. No automated tooling collects this for you — reports are manual, structured text, reviewed by a person.
