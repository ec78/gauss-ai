# Reporting Bugs

**Status: Alpha — intended for controlled testing.**

## Before you report

1. Run `gauss-ai doctor` and read its output — many setup issues (missing/misconfigured GAUSS executable, an unwritable workspace parent, a corrupt config file) are diagnosed there directly, with a next step.
2. Check [docs/alpha-troubleshooting.md](alpha-troubleshooting.md) for the specific symptom.
3. Re-read [docs/alpha-tester-guide.md](alpha-tester-guide.md)'s "Distinguishing a product issue from a GAUSS-code issue" — if the assistant correctly identified a real bug in your own GAUSS code, that's the product working as intended, not something to report as a defect (your feedback on how clear or useful the proposed fix was is still welcome).

## What counts as a bug

- The CLI crashes, hangs, or produces a raw Python traceback.
- Any approval, execution, review, or file write appears to happen without your explicit action — report this as **Critical** regardless of anything else, and see [docs/alpha-tester-guide.md](alpha-tester-guide.md)'s "Current safety boundaries" for the exact list of guarantees this would violate.
- The installed `gauss-ai` command behaves differently than documented in [docs/alpha-quickstart.md](alpha-quickstart.md) or [docs/private-alpha-testing.md](private-alpha-testing.md).
- A real GAUSS error is misclassified, or a proposed diagnosis/repair strategy is clearly wrong for the real error shown.
- Confusing wording, an unclear prompt, or a step that doesn't explain what it's asking for.

## How to gather evidence

The single most useful thing you can attach is a **diagnostic bundle**:

```
gauss-ai repair <file.gss> --export-session bug-report-bundle.json
```

(add `--runner gauss` if you were testing real-mode; the flag works the same way in fake mode). This writes a read-only JSON file containing your configuration (no secrets — this repository's configuration model has no field capable of holding one), the runner backend actually used, your workspace identity, and the complete, real transcript of everything the guided command did and showed you. It changes no repair behavior and is written once, at the end of the same run — attach it as-is.

If you were using the lower-level REPL (`python scripts/gauss_code_assistant_cli.py` or `gauss-ai` with no subcommand) instead of the guided command, run `show-repair-session` before exiting and paste its full output instead.

## Where to report

File the issue using [docs/alpha-feedback-template.md](alpha-feedback-template.md) as your template. Fill in every section — especially "Repair Session Summary" (or the exported bundle) and "Reproduction Steps" with the exact commands you ran, in order, from a fresh session.

## What we do with reports

Reports are reviewed manually. No automated telemetry or analytics exists anywhere in this product — nothing is collected unless you explicitly attach it to a report yourself.
