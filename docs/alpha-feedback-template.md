# Alpha Test Observation

## Date

## Task Attempted

What you were trying to do (e.g. "repair a missing-semicolon error via the guided workflow").

## Source / Error Type

The GAUSS error code involved, if any (e.g. `G0105`), or "none -- successful execution" / "not GAUSS-related."

## Setup

`gauss-ai` version, install method (`pip install -e .` / `pip install .`), Python version, OS, real GAUSS version if used (`gauss-ai version`'s own output is the easiest way to capture this).

## Scenario

## Goal

## Commands Entered

## Execution Backend

FAKE / REAL_GAUSS

If REAL_GAUSS: executable path, `gauss_ran`, exit code, timeout state, and generated script path.

## Expected Behavior

## Observed Behavior

## What Worked

## What Felt Confusing

The specific step, prompt, or message that was unclear -- quote it if possible.

## Safety or Trust Concern

Did anything appear to execute, approve, read, write, verify, or review something without your explicit action? See [docs/alpha-tester-guide.md](alpha-tester-guide.md)'s "Current safety boundaries" -- any apparent violation is Critical severity regardless of anything else in this report.

## Repair Usefulness

If a repair strategy or draft was proposed: was it relevant, correct, and clearly explained? Would you have accepted it without this tool's help?

## Verification Outcome

The `comparison` value from `show-verification-request` / the guided workflow's own output (e.g. `succeeded_after_failure`, `same_error`), if verification was reached.

## Final Review

Your own recorded decision (`accepted` / `rejected` / `inconclusive`) and why.

## Session Summary

Paste the full output of `show-repair-session` (or the guided command's own closing summary) here. This is the single most useful artifact for reproducing what you saw.

## Exported Diagnostic Bundle

If you ran with `--export-session <path>` (see [docs/reporting-bugs.md](reporting-bugs.md)), attach the resulting JSON file here, or paste its contents. This is the preferred way to share configuration, runner, workspace, and full transcript in one artifact -- prefer it over manually retyping the above sections when available.

## Error Output

## Reproduction Steps

Exact commands, in order, from a fresh session.

## Screenshots (optional)

Attach only if something in the terminal output is easier to show than to describe (e.g. formatting/wrapping issues). Not required -- text evidence above is normally sufficient.

## Severity

Critical / High / Medium / Low

## Suggested Improvement

## Possible Benchmark
