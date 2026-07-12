# Expert System Maintenance Guide

This guide explains how to maintain the six-expert system after `v0.17.0`.

- It is a process guide, not a runtime routing engine.
- It should be used when experts are added, retired, renamed, operationalized, or when routing, benchmarks, evaluations, or release-readiness docs change.
- It complements:
  - `experts/EXPERT_REGISTRY.md`
  - `experts/EXPERT_BOUNDARY_MATRIX.md`
  - `workflows/expert-routing.md`
  - `workflows/expert-routing-cheatsheet.md`
  - `evaluations/EVALUATION_DASHBOARD.md`
  - `planning/v0.18.0-operational-profile-audit.md`

## Guide Metadata

- **Current milestone:** `v0.18.0` - Expert System Consolidation
- **Captures operational state through:** `v0.17.0` - Product Expert Foundation
- **Operational experts:** 6
- **Runtime orchestration:** Not implemented
- **Routing model:** documented/manual-evaluation-driven
- **Expert registry:** `experts/EXPERT_REGISTRY.md`
- **Boundary matrix:** `experts/EXPERT_BOUNDARY_MATRIX.md`
- **Routing cheat sheet:** `workflows/expert-routing-cheatsheet.md`
- **Evaluation dashboard:** `evaluations/EVALUATION_DASHBOARD.md`
- **Profile audit:** `planning/v0.18.0-operational-profile-audit.md`

## When to Use This Guide

Use this guide when:

- Adding a new expert.
- Retiring an expert.
- Renaming an expert.
- Operationalizing a placeholder/narrative expert.
- Changing an expert's ownership boundaries.
- Changing routing patterns.
- Changing Code Assistant workflow routing.
- Adding benchmark prompts.
- Running benchmark evaluations.
- Updating benchmark coverage.
- Updating the run index.
- Preparing a readiness checklist.
- Updating `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md`.
- Investigating stale wording.
- Resolving strict-mode warnings or historical exceptions.
- Preparing a release.

## Core Maintenance Principle

Every expert-system change should preserve six separations unless intentionally and explicitly changed:

1. Implementation correctness.
2. Methodological correctness.
3. Maintainability/design correctness.
4. Documentation/explanation correctness.
5. Education/learning-design correctness.
6. Product/user-value correctness.

- Do not let one correctness dimension imply another.
- Do not let product value imply syntax, statistical, design, documentation, or education correctness.
- Do not let syntax imply methodology or maintainability.
- Do not let documentation imply learning effectiveness or product value.
- Do not let education imply implementation correctness or product value.
- Do not claim execution unless code/tests actually ran.
- Label pseudocode or unverified syntax.
- Label product hypotheses when evidence is missing.
- The strictest applicable evidence/context requirement wins.

These separations are what `experts/EXPERT_BOUNDARY_MATRIX.md`'s False Equivalence Matrix and Escalation Matrix already encode; treat any maintenance change that would blur one of them as a change to be flagged, not applied silently.

## Adding or Operationalizing an Expert

1. Create or update the milestone's planning doc.
2. Create the narrative foundation:
   - `EXPERT.md`
   - `BODY_OF_KNOWLEDGE.md`
   - `reasoning.md`
   - `best_practices.md`
   - `common_mistakes.md`
   - `knowledge.md` compatibility placeholder
3. Create `OPERATIONAL_PROFILE.md` following `tools/operational_expert_interface.md`.
4. Update `experts/EXPERT_REGISTRY.md`.
5. Update `experts/EXPERT_BOUNDARY_MATRIX.md`.
6. Update `workflows/expert-routing.md`.
7. Update `workflows/expert-routing-cheatsheet.md`.
8. Update `workflows/code-assistant-response.md`.
9. Update `agents/code-assistant/task_modes.md`.
10. Update `prompts/code_assistant_system.md`.
11. Audit all `OPERATIONAL_PROFILE.md` files for stale expert-count and future-expert wording.
12. Add benchmark prompts.
13. Add benchmark coverage rows.
14. Run evaluations and create run files.
15. Update `evaluations/runs/INDEX.md`.
16. Update `evaluations/EVALUATION_DASHBOARD.md`.
17. Update `README.md`, `ROADMAP.md`, `KNOWN_LIMITATIONS.md`.
18. Update `CHANGELOG.md`.
19. Create the milestone's readiness checklist.
20. Run guards:
    - `python scripts/validate_all_evidence.py`
    - `python scripts/check_evaluation_tracking.py`
    - `python scripts/check_release_readiness.py`
21. Confirm no runtime orchestration is implied unless intentionally implemented.
22. Confirm no release tag was created before readiness.

This is the seven-step pattern already followed for `v0.14.0`-`v0.17.0` (narrative foundation, operational profile, routing extension, Code Assistant integration, benchmarks, evaluation, readiness checklist), expanded here into the full checklist of files each step actually touches.

## Routing Update Checklist

Use this checklist for any change to routing behavior that does not add a whole new expert (for example, a new activation trigger, a boundary clarification, or a new escalation path).

- Update `workflows/expert-routing.md`.
- Update `workflows/expert-routing-cheatsheet.md`.
- Update `experts/EXPERT_REGISTRY.md` if ownership or activation changes.
- Update `experts/EXPERT_BOUNDARY_MATRIX.md` if boundaries or false equivalences change.
- Update `workflows/code-assistant-response.md` if Code Assistant routing changes.
- Update `agents/code-assistant/task_modes.md` if task-mode activation changes.
- Update `prompts/code_assistant_system.md` if system-level routing guidance changes.
- Audit all `OPERATIONAL_PROFILE.md` files for:
  - Old expert-count wording.
  - Old routing-count wording.
  - Future-expert wording.
  - Pending-integration wording.
  - Related-file omissions.
  - Stale benchmark tense.
- Update `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md` if current capability changes.
- Add or update benchmarks if routing behavior changes.
- Update `CHANGELOG.md`.

## Stale Wording Search Checklist

These phrase patterns have actually gone stale in this project — this list is grounded in the real recurring failures found during the `v0.16.0`, `v0.17.0`, and `v0.18.0` audits, not a hypothetical list. Search for:

- "future Expert"
- "future Product Expert"
- "future Education Expert"
- "once operationalized"
- "not yet operationalized"
- "narrative-only"
- "placeholder"
- "pending integration"
- "integration remains pending"
- "routing not yet implemented"
- "three-expert routing"
- "four-expert routing"
- "five-expert routing"
- "six-expert routing" (if the expert count changes later)
- "two experts"
- "three experts"
- "four experts"
- "five experts"
- "six experts" (if the expert count changes later)
- "not yet run"
- "will be evaluated"
- "future benchmark"
- "planned benchmark"
- "current milestone" (when release status changes)
- "current expert count" (when the expert count changes)

Notes:

- Do not blindly replace these terms.
- Inspect context and fix only genuine stale wording.
- If a match is intentionally historical (for example, a readiness checklist describing what was true at the time it was written, or a documented historical exception), leave it unchanged and document why — do not "fix" a legitimate historical record into looking current.

## Benchmark Maintenance Checklist

- Add prompts to `evaluations/benchmark-prompts.md`.
- Add matching rows to `evaluations/benchmark-coverage.md`.
- Keep Prompt IDs unique and sequential.
- Mark new rows `Not Run` until evaluated.
- Use the current active category convention (see `scripts/check_evaluation_tracking.py`'s "current active category" check).
- Do not create run files during a prompt-addition task unless explicitly evaluating.
- When evaluating:
  - Use `workflows/manual-evaluation.md`.
  - Use `evaluations/scoring.md`.
  - Create one run file per prompt.
  - Include prompt ID, expected behavior, generated response, scores, pass/fail, blockers, and follow-ups.
  - Update `evaluations/runs/INDEX.md`.
  - Update `evaluations/benchmark-coverage.md` from `Not Run` to `Passed`/`Failed`.
  - Update `evaluations/EVALUATION_DASHBOARD.md`.
  - Update `CHANGELOG.md`.
- Run `python scripts/check_evaluation_tracking.py` after benchmark updates.
- Do not claim "all passed" unless coverage and run files support it.

See `workflows/manual-evaluation.md`'s "Benchmark Authoring Guidance" section for the related rule against hardcoding volatile repository counts into a benchmark's own expected-behavior text.

## Evaluation and Guard Checklist

```bash
python scripts/validate_all_evidence.py
python scripts/validate_all_evidence.py --json
python scripts/validate_all_evidence.py --strict

python scripts/check_evaluation_tracking.py
python scripts/check_evaluation_tracking.py --json
python scripts/check_evaluation_tracking.py --strict

python scripts/check_release_readiness.py
python scripts/check_release_readiness.py --json
python scripts/check_release_readiness.py --strict
```

Current expected interpretation:

- Default validation should pass before release.
- JSON validation should report `overall_pass: true` where applicable.
- Strict validation may fail for documented warning-promoted-to-failure cases.
- Default release readiness is the release gate.
- Strict failures are informational unless policy changes.
- Default pass does not mean no warnings.
- Evidence validation does not prove semantic correctness or execution.
- Tracking validation does not prove response quality; it verifies prompt/coverage/run/index consistency.

## Readiness Checklist Workflow

1. Create `planning/vX.Y.Z-readiness-checklist.md`.
2. Summarize the release goal and deliverables.
3. Summarize expert/routing changes.
4. Summarize benchmark/evaluation evidence.
5. Summarize guard results.
6. List known warnings and strict-mode behavior.
7. List blockers and non-blocking follow-ups.
8. Audit `README.md`/`ROADMAP.md`/`KNOWN_LIMITATIONS.md`.
9. Audit relevant profiles and workflows for stale wording.
10. Confirm no unsupported claims were introduced.
11. Confirm no runtime orchestration is implied.
12. Confirm no release tag is created during the readiness task.
13. Recommend tagging only after readiness is complete.

## Release Hygiene Checklist

- Final `git status` should contain only expected files.
- `CHANGELOG.md` should have `Unreleased` entries for all milestone work.
- `README.md` should identify the current release accurately.
- `ROADMAP.md` should show completed/current/next milestones accurately.
- `KNOWN_LIMITATIONS.md` should be current.
- The readiness checklist should record default guard passes and strict-mode caveats.
- No benchmark rows should remain `Not Run` for the milestone being released.
- No new warnings should be undocumented.
- No release tag should be created until the user explicitly directs it.
- Suggested release notes should be prepared from the readiness checklist.

## What Not to Overclaim

- Do not claim runtime orchestration unless it exists.
- Do not claim expert routing is automatic unless implemented.
- Do not claim GAUSS code executed unless it was actually run.
- Do not claim evidence validation proves code correctness.
- Do not claim tracking validation proves answer quality.
- Do not claim product value proves implementation, methodology, maintainability, documentation, or education correctness.
- Do not claim documentation quality proves learning effectiveness.
- Do not claim training quality proves product value.
- Do not claim user demand proves statistical validity.
- Do not claim product urgency proves design risk is acceptable.
- Do not claim strict checks pass if strict warnings are still present.
- Do not claim a benchmark passed unless the run file and coverage row support it.

## Suggested Maintenance Cadence

- After each expert milestone: run a profile audit and update the registry, boundary matrix, routing cheat sheet, dashboard, and this maintenance guide if needed.
- After each benchmark category: update the dashboard and run the tracking guard.
- Before each release: run the readiness checklist and the release-readiness guard.
- Periodically: audit stale wording across operational profiles and routing docs, using the Stale Wording Search Checklist above.
- Future possibility: add scripted stale-wording checks (similar in spirit to `scripts/check_evaluation_tracking.py`), but this is not implemented as part of this guide — it remains a non-blocking follow-up.
