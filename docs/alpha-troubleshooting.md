# Alpha Troubleshooting

**Status: Alpha — intended for controlled testing.**

Run `gauss-ai doctor` first for most of these — it diagnoses the majority of the issues below automatically, with an actionable next step.

## `tgauss` not found

`gauss-ai doctor` reports `WARN gauss_executable_configured` if nothing is configured, or `FAIL gauss_executable_valid` if a configured path doesn't exist. Fixes:

- Run `gauss-ai init` to search common installation locations and PATH.
- If your installation is in a nonstandard location, find the terminal executable manually (it is named `tgauss` or `tgauss.exe`, distinct from the GUI `gauss.exe`/`wgauss.exe`) and run `gauss-ai config set gauss-executable <full path>`.
- Fake-mode testing (`gauss-ai repair <file> --fake-result ...`, or the default `--runner fake`) never needs a configured executable at all.

## GUI executable selected accidentally

`gauss-ai config set gauss-executable`, `gauss-ai init`, and `gauss-ai doctor` all explicitly reject `gauss.exe`/`wgauss.exe`/any non-`tgauss` basename with a clear error ("GUI executables such as gauss.exe cannot run in non-interactive batch mode"). This is not a bug to work around — the GUI executable genuinely cannot run GAUSS scripts non-interactively, so real-mode execution requires the terminal executable specifically. If `gauss-ai init`'s auto-discovery only finds a GUI executable, it will not offer it as a candidate; you'll need to locate the terminal executable (usually in the same installation directory) and configure it manually.

## Working-directory problems

The productized `gauss-ai` entry point does not depend on your current directory — it can be run from anywhere once installed (`pip install -e .`). The guided `gauss-ai repair <file>` command resolves the file path you give it relative to your **current** working directory, exactly like any ordinary command-line tool; if it reports the file doesn't exist, check that your relative path is correct for wherever you're running the command from, or use an absolute path.

## Permissions

- **Workspace-parent not writable**: `gauss-ai doctor`'s `workspace_parent` check will `FAIL` with the exact directory and error. Choose a different, writable directory via `gauss-ai config set workspace-parent <path>`.
- **Config file (`~/.gauss-ai/config.json`) not writable**: `gauss-ai config set`/`gauss-ai init` will report the error directly when they attempt to save.

## Confirmation failures

Every execution (original and verification) requires an exact `confirm <request_hash>` matching the hash shown by the most recent `plan`/`verify-repair` output — this is intentional, digest-bound protection against confirming a stale or different request. In the guided workflow, this is handled for you automatically once you answer "yes" to the relevant confirmation prompt; you never need to type a hash yourself. If you're using the lower-level REPL directly (`python scripts/gauss_code_assistant_cli.py`) and see a hash-mismatch error, re-run `plan` (or `show-verification-request`) to see the current, correct hash.

## Stale source

Repair Draft, Application Gate, and Repair Application all independently re-verify the source file's content hash immediately before acting, and fail closed (blocked, never silently applied) if the file has changed since the draft was built. In the guided workflow, this surfaces as: "The application gate did not pass every checkable precondition" or "The repair was not applied (outcome=blocked)." This means something external modified the workspace copy between drafting and applying — start a fresh `gauss-ai repair <file>` run.

## Completed workspace

A workspace supports exactly one execution attempt in its lifecycle; trying to `plan`/`execute` again against an already-completed workspace is refused. The guided workflow always creates a fresh workspace per `gauss-ai repair` invocation, so this should not surface directly through it. Using the lower-level REPL, run `workspace create` again (or `reset`) before a new attempt.

## Output file reading

The lower-level REPL never reads output-file contents automatically — use `outputs` to see metadata, then `read <relative-path>` explicitly. The guided workflow does not create or read arbitrary output files at all; it only ever reads the one `.gss` file you named on the command line (copied into its own workspace) and shows execution stdout/stderr/interpretation/diagnosis inline as part of its own step-by-step output.

## Repair application blockers

`gauss-ai repair`'s own output shows exactly which precondition blocked, in the `check-repair-application-gate`/`apply-repair` output. Common causes: a declined approval earlier in the same session (the guided workflow will have already stopped by that point), or a stale source hash (see above). Nothing is ever silently retried — start a fresh guided-repair run once the underlying issue is resolved.

## Reset behavior

The lower-level REPL's `reset` command clears the current session's pending request, execution result, and repair/verification-review state, but retains the active workspace and its own configuration. It does not undo an already-applied repair (the backup created by `apply-repair` is the only recovery mechanism for that, and restoring from it is a manual step — no automatic rollback exists in this repository). The guided workflow does not expose a `reset` subcommand of its own; each `gauss-ai repair <file>` invocation starts a genuinely fresh session and workspace.

## Windows path issues

- Prefer forward slashes or raw strings for paths containing backslashes when typing at a shell prompt, to avoid accidental escape-sequence interpretation (e.g. `C:/gauss26/tgauss.exe` or `C:\gauss26\tgauss.exe` both work; avoid partial escapes like `C:\gauss26\newfile.gss` in contexts where `\n` would be interpreted).
- Paths with spaces must be quoted: `gauss-ai config set gauss-executable "C:\Program Files\GAUSS26\tgauss.exe"`.
- `gauss-ai doctor`/`gauss-ai config show` always print the exact, fully-resolved path in effect — use that output to confirm what was actually configured if a path looks unexpected.

## Still stuck?

Run `gauss-ai doctor` and include its full output, plus the exact command you ran and its output, in your report — see [docs/alpha-tester-guide.md](alpha-tester-guide.md) for how to file one, and [docs/alpha-feedback-template.md](alpha-feedback-template.md) for the structured template.
