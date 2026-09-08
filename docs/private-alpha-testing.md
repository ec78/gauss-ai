# Private Alpha Testing

**Status: `v0.71.0` — Private Alpha.** The GAUSS Code Assistant has been validated end to end against real GAUSS 26.1.1, through the installed `gauss-ai` product, exactly as you will use it. `gauss-ai` (no subcommand) now also launches a conversational GAUSS Q&A assistant, which can use a free, local Ollama model (no API key) or Anthropic's cloud API — see [docs/conversational-qa.md](conversational-qa.md).

This page is the entry point for this phase. It does not repeat what the other alpha docs already cover — follow the links below in order.

## Alpha feedback status

The first alpha-feedback cycle is complete: five real observations from the first private alpha session (`v0.68.0`) were **addressed in implementation and verified through `v0.69.0`'s own real-GAUSS and installed-CLI evaluation** — this is not a claim that every UX question is now permanently solved, only that these specific findings were fixed and re-tested. A second round of testing (including of the new conversational assistant below) may surface further feedback, exactly as the first round did; that is expected and welcome. See `evaluations/benchmark-prompts.md`'s `59.x` category for the full evidence.

## 1. Install

[docs/alpha-installation.md](alpha-installation.md) — prerequisites, `pip install -e .`, configuration, supported environment.

## 2. First run

[docs/alpha-quickstart.md](alpha-quickstart.md) — `gauss-ai init` → `gauss-ai doctor` → a full guided repair in under 10 minutes, fake mode first, then real GAUSS. Or just run `gauss-ai` with no arguments and ask it a question — see [docs/conversational-qa.md](conversational-qa.md).

## 3. What real-GAUSS validation actually covered

`v0.68.0` ran the installed product against real GAUSS 26.1.1 (never a fake substitute) for:

- A successful execution (`gauss_ran: true`, real duration measured).
- `G0105`, `G0036`, and `G0025` — each reproduced against real GAUSS and matching this repository's own verified error catalog exactly.
- A complete repair cycle: real execution → diagnosis → strategy approval → draft → draft approval → application approval → application gate → repair application → real verification execution → human review — all through `gauss-ai repair <file.gss> --runner gauss`.
- Real output-file creation and explicit reading (`outputs` for metadata, `read <path>` for content).

Everything else (cancelled approvals, blocked application from a stale source, completed-workspace rejection, `reset` behavior) was validated through the installed CLI in fake mode, since these are pipeline mechanics, not GAUSS-specific — real GAUSS was used only where it was actually needed. See `evaluations/benchmark-prompts.md`'s `58.x` category and its ten `evaluations/runs/2026-08-09-code-assistant-real-alpha-validation-run-*.md` files for the full, real evidence.

**One real defect was found and fixed during this validation**: `examples/alpha-demo/broken.gss` had never actually been run against real GAUSS before — it had only ever been exercised in fake mode (where `--fake-result` makes actual file content irrelevant). Running it for real for the first time found it reproduced a *different*, uncataloged error, not the `G0105` it claimed. The pipeline itself behaved correctly throughout (it disclosed the uncataloged code honestly and fabricated nothing); only the example file's content was wrong. It has been corrected to the catalog's own exact verified trigger and re-confirmed against real GAUSS. This is exactly the kind of gap real validation is meant to surface — see `examples/alpha-demo/README.md`'s own correction note.

## 4. Expected workflow

For a real repair, on your own file:

```
gauss-ai config set gauss-executable <path to your tgauss/tgauss.exe>
gauss-ai doctor
gauss-ai repair <your-file.gss> --runner gauss
```

You will be asked to explicitly confirm execution, approve a repair strategy, describe and approve a draft, approve applying it, and record a review of the verification evidence — every step is yours to decide; nothing is inferred. Add `--export-session <path>` to also write a diagnostic bundle you can attach to a bug report (see below).

## 5. If something looks wrong

[docs/alpha-troubleshooting.md](alpha-troubleshooting.md) covers the common setup and workflow problems first. If that doesn't resolve it, see "How to report issues" below.

## 6. Known limitations for this phase

[docs/known-alpha-limitations.md](known-alpha-limitations.md) — read this before assuming something is broken; several things are deliberately not implemented yet.

## How to report issues

[docs/reporting-bugs.md](reporting-bugs.md) — the process. [docs/alpha-feedback-template.md](alpha-feedback-template.md) — the structured template to fill in, including how to attach a `--export-session` diagnostic bundle.

## What this phase does not include

Durable sessions (chat or otherwise), rollback, multi-file repair, cloud execution, new approval layers, new repair intelligence, autonomous repair, automatic retries, telemetry, analytics, conversational execution, or conversational code generation/repair. Every guarantee from `v0.62.0` onward (explicit confirmation before execution, independent digest-bound approval at every layer, no file read without explicit authorization, no file write except through the approved application transaction, no fabricated review) was re-proven against real GAUSS in `v0.68.0`, not merely assumed to still hold, and remains untouched — zero diff — through `v0.70.0`'s new conversational layer.
