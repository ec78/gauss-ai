# Known Alpha Limitations

**Status: Alpha — intended for controlled testing.** This is a tester-facing summary of what to expect right now. See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) at the repository root for the full, per-milestone historical record.

## Scope

- **Single-file repair only.** One `.gss` file per guided session. No multi-file repair exists or is planned for this phase.
- **No autonomous repair.** Every strategy approval, draft approval, application approval, and verification review requires your own explicit, real-time decision. Nothing is inferred on your behalf.
- **No rerun or rollback beyond one backup.** `apply-repair` always creates exactly one, never-overwritten backup before writing. There is no automated restore-from-backup, no automatic retry, and no rollback mechanism of any kind.
- **No durable sessions.** Each `gauss-ai` process is stateless once it exits. There is no way to resume a guided session across a process restart, and `--export-session` does not create one — it writes a one-time, read-only snapshot, not a resumable session.

## Environment

- **Real GAUSS execution verified on Windows with GAUSS 26.1.1 only.** Other GAUSS 24/25/26 installations are supported by the discovery/execution logic but have not been independently verified by this repository's own testing. macOS/Linux real-GAUSS execution is not claimed or supported.
- **Fake-mode testing (packaging, CLI, guided workflow, doctor, init, config) has no OS-specific dependency**, but has only been exercised on Windows so far.
- **Python 3.10+ required.**

## Product behavior

- **`gauss-ai version`/`gauss-ai doctor` never launch GAUSS to report its version** — the version is parsed from the configured executable's own path string, and is reported as unknown when the path carries no parseable version number (e.g. a custom install directory name).
- **`gauss-ai init` never silently picks among multiple discovered GAUSS executables** — you must explicitly select one, type a path manually, or skip.
- **The Application Gate has no automated backup-restore, rollback-path-verification, application-consumer-authorization, or audit-record check** — these are explicitly disclosed as `not_applicable_checks` in gate output, not silently assumed satisfied.
- **A verification review cannot be revoked or corrected** once recorded — a mis-recorded decision requires a fresh `gauss-ai repair` session (a full `reset` in the lower-level REPL), not an edit-in-place.
- **No telemetry, analytics, or network reporting of any kind.** Nothing about your session is ever sent anywhere automatically.

## Known example-content history

`examples/alpha-demo/broken.gss` was corrected in `v0.68.0` after real-GAUSS validation found it reproduced a different, uncataloged error than the `G0105` it originally claimed (it had only ever been exercised in fake mode before). This is now fixed and re-verified against real GAUSS — noted here as a reminder that even this repository's own example content is only as trustworthy as its most recent real verification, exactly like any GAUSS script you bring yourself.

## If you hit something not listed here

It may be a genuine defect — see [docs/reporting-bugs.md](reporting-bugs.md).
