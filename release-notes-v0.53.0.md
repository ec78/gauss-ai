# v0.53.0 - Verified GAUSS Error Knowledge

This release expands the GAUSS error catalog using only verified evidence, adds transparent verification metadata to every entry, documents a genuine documentation-vs-runtime wording disagreement rather than hiding it, and resolves the one Minor finding carried from `v0.52.0`.

## Evaluated

- All ten `44.x` Verified Error Knowledge prompts: 10/10 Pass at 4.0, zero Critical/Major/Minor defects.
- No new real GAUSS invocation was required or performed — both new entries are grounded in already-existing real evidence (`G0014`) or official documentation alone, honestly disclosed as such (`G0290`).

## Added

- Two new catalog entries: `G0014` "File not found" (File I/O, dual-sourced: real runtime + official documentation) and `G0290` "Library not found" (Package or Library, official documentation only — explicitly not yet runtime-confirmed in this repository).
- `VerificationStatus` enum (Real Runtime / Official Documentation / Repository Evidence / Unknown) plus `verification_source` and `documentation_discrepancy` fields on every catalog entry, retrofitted onto the pre-existing three (`G0105`, `G0036`, `G0025`).
- `docs/gauss-error-catalog.md` — a human-readable catalog distinguishing verified entries from explicitly-labeled future placeholders.
- Verification metadata now surfaced through `ExecutionInterpretation` and the CLI's `interpret` command.

## Fixed

- **Timeout wording now truthfully distinguishes simulated from observed evidence** (resolves the `v0.52.0`/`43.4` Minor finding). Injected/fake timeout evidence produces `launch_status: fake_or_non_gauss_runner` (consistent with every other non-real-evidence branch) and explicit wording stating no real GAUSS process was launched; an observed real-launch timeout is worded distinctly.
- **Duplicate-catalog-entry protection.** Catalog construction now raises immediately on a duplicate error code instead of a dict literal's silent last-write-wins behavior.

## Documented, Not Hidden

Official Aptech documentation titles `G0036` "Matrices are not conformable"; every real runtime observation in this repository shows "Matrix dimensions are incompatible." Per this catalog's own policy, runtime evidence remains authoritative for the entry's title/explanation, and the disagreement is recorded as a structured `documentation_discrepancy` field, not silently resolved in either direction.

## Cataloged GAUSS Codes (5 total)

`G0105` (Parse/Syntax), `G0036` (Matrix Dimensions), `G0025` (Runtime Computation), `G0014` (File I/O), `G0290` (Package or Library). Every other GAUSS error code remains preserved and honestly classified `unknown` until independently verified.

## Safety Boundaries (unchanged, re-verified)

The interpreter still launches nothing, retries nothing, edits no code, and reads no files automatically; it contains zero hardcoded GAUSS-specific knowledge outside the catalog (a dedicated structural test asserts this). No execution behavior changed in this release.

## Remaining Limitations

- Only five GAUSS error codes are specially explained; every other code remains generically `unknown` until verified.
- `G0290` has official-documentation backing only, not yet reproduced against a real GAUSS runtime in this repository.
- No durable `ExecutionSession` integration, no autonomous correction, no automatic retry, no code repair.
- Interpretation still cannot establish statistical or methodological correctness from a successful run.

## Next Recommended Milestone

Bounded diagnosis reasoning that consumes the now-richer catalog/verification metadata to help rank likely causes among a cataloged error's known triggers — still strictly short of proposing or applying a code repair, per this project's staged Execution → Interpretation → Knowledge → Diagnosis → Repair progression.
