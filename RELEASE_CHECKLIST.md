# Release Checklist

## v0.2.0 Release Readiness

Target release: `v0.2.0` - Knowledge and Evaluation Foundation.

| Item | Status | Notes |
|---|---|---|
| Benchmark prompts have stable IDs | Ready | `evaluations/benchmark-prompts.md` uses stable section-based Prompt IDs. |
| Scoring rubric includes N/A handling | Ready | `evaluations/scoring.md` defines `N/A` handling and excludes it from averages. |
| Manual evaluation workflow exists | Ready | `workflows/manual-evaluation.md` documents the process and result template. |
| Evaluation runs are indexed | Ready | `evaluations/runs/INDEX.md` summarizes completed runs through run 015. |
| Benchmark coverage tracker is current | Ready | `evaluations/benchmark-coverage.md` reflects completed runs through run 015. |
| Completed evaluation runs are summarized accurately | Ready | Run summaries were checked against the run files during release prep. |
| Native command categories are documented | Ready | `experts/gauss-language/COMMAND_CATEGORIES.md` provides the official-category discovery index. |
| Native command selection workflow exists | Ready | `workflows/native-command-selection.md` defines built-in versus manual implementation selection. |
| Hybrid command documentation retrieval workflow exists | Ready | `workflows/command-documentation-retrieval.md` keeps official docs authoritative. |
| Changelog has an Unreleased entry for v0.2.0 work | Ready | `CHANGELOG.md` summarizes the knowledge and evaluation foundation work. |
| Known limitations or next steps are documented | Ready | `KNOWN_LIMITATIONS.md` and `ROADMAP.md` document current boundaries and next milestones. |
| No machine-specific local paths are committed except intentionally ignored local config examples | Ready | Committed config uses placeholders; local paths belong in ignored local config files. |
| No invented GAUSS syntax or unverified command examples were added | Ready | Command examples are either verified from official docs/cache notes or explicitly marked as requiring verification. |

## Tagging Status

The repository appears ready for a private `v0.2.0` tag after review. This checklist does not create the tag or a GitHub release.
