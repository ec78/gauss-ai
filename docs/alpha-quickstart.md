# Alpha Quickstart

**Status: Alpha — intended for controlled testing.**

**Target: under 10 minutes from an installed project to a successful fake-mode repair workflow.** Real GAUSS execution is a short second section below.

This page walks through the guided *repair* workflow. If you just want to ask GAUSS questions conversationally (`gauss-ai`, no subcommand — no configuration required), see [docs/conversational-qa.md](conversational-qa.md) instead; the two are independent and you can try either first.

## 1. Install (≈1 minute)

```
pip install -e .
gauss-ai version
```

You should see the `gauss-ai` version, your Python version, and platform. No GAUSS installation is needed for this section.

## 2. First-run setup (≈2 minutes)

```
gauss-ai init
```

You will be asked, in order:

1. **A workspace-parent directory.** Press Enter to skip (a fresh temporary directory is used each session), or type a path you want reused across sessions.
2. **A GAUSS executable**, if one is auto-detected. You will always be asked to explicitly confirm — nothing is chosen for you, and if more than one is found, you must pick which one by number. If none is found, you can type a path manually or press Enter to skip; fake-mode testing works either way.
3. **A default runner** (`fake` or `gauss`). Press Enter to keep `fake` for this quickstart.

Re-run `gauss-ai init` any time — it reviews your existing configuration and lets you change it; it never resets what you already set.

## 3. Check your environment (≈30 seconds)

```
gauss-ai doctor
```

Every check reports `PASS`, `WARN`, or `FAIL` with a next step. For this quickstart, `WARN` on the GAUSS-executable checks is expected and fine — fake mode does not need one.

## 4. Run the guided repair workflow (≈5 minutes)

This repository ships a small, two-file demo scenario at `examples/alpha-demo/` (see its own [README](../examples/alpha-demo/README.md) for details). The broken file is missing a semicolon — the exact fault class this repository's verified error catalog documents as `G0105`.

```
gauss-ai repair examples/alpha-demo/broken.gss --fake-result failure
```

`--fake-result failure` is fake-mode-only: since there is no real GAUSS parser behind the fake runner, this tells it what class of result to simulate, so you can see the full repair pipeline rather than the "nothing to repair" path. You will be walked through, and asked to explicitly confirm or approve, each of the following in turn:

1. **Confirm execution** of the proposed plan (`y`).
2. **Approve the repair strategy** GAUSS AI proposes after diagnosing the failure (`y`).
3. **Review the AI-generated candidate.** `broken.gss`'s content matches this repository's own verified `G0105` pattern exactly, so a candidate repair draft is generated automatically and shown — the detected error, the affected line, a proposed replacement, the reasoning, and a confidence level. Type `a` to accept it as-is (`e` lets you edit the replacement text first; `r` falls back to describing the fix by hand, exactly as every prior alpha release required).
4. **Approve the resulting draft** (`y`).
5. **Approve applying** that draft to the file (`y`) — the exact replacement text about to be written is shown once more right before this question.
6. **Choose whether to verify** the repair by executing the repaired file (`y`), then **confirm** that verification execution (`y`).
7. **Record your review** of the verification evidence: `accepted`, `rejected`, or `inconclusive`.

At the end, a complete repair-session summary is shown — every stage reached, in one place. Your original `broken.gss` file is never modified; the repair happens inside a workspace copy created for this session (its location is shown early in the output).

## 5. Try the "nothing to repair" path (≈1 minute)

```
gauss-ai repair examples/alpha-demo/working.gss --fake-result success
```

The original execution succeeds, so `repair-plan` reports there is nothing to repair, and the guided workflow stops immediately after showing the (mostly empty) session summary — proving the pipeline never fabricates a repair when none is needed.

## What you just saw

Every approval you typed `y` (or a decision word) for is a **real, independent, digest-bound decision** recorded by the same approval layers the lower-level command-by-command CLI uses — the guided command adds no shortcut, no auto-approval, and no second engine. Try answering `n` at any approval point in a fresh run to see the workflow stop cleanly, with nothing beyond that point having happened.

## Real GAUSS mode

Once you have a configured, valid terminal executable (`gauss-ai config set gauss-executable <path>`, or via `gauss-ai init`):

```
gauss-ai repair examples/alpha-demo/broken.gss --runner gauss
```

No `--fake-result` flag is used or needed — the real GAUSS runtime determines the actual result of executing the file. Every approval step is identical to fake mode; only the underlying runner changes.

## Next steps

- [docs/alpha-tester-guide.md](alpha-tester-guide.md) — what to test, how to report issues, current safety boundaries.
- [docs/alpha-troubleshooting.md](alpha-troubleshooting.md) — common setup and workflow problems.
- [README.md](../README.md) — the full, low-level command reference (`workspace create`, `plan`, `confirm`, etc.) for advanced or debugging use via `python scripts/gauss_code_assistant_cli.py`.
