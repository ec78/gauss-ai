# Setting up local GAUSS documentation for grounding

**Status: Alpha, added in `v0.71.0`; one-command download added in `v0.80.0`.**

Conversational GAUSS Q&A (see [conversational-qa.md](conversational-qa.md)), and code validation through the MCP server (see [mcp-server.md](mcp-server.md)), ground themselves in real official GAUSS documentation instead of a model's general knowledge. To do that, `docs-root` has to point at a local copy of the documentation. Searching it is always local and offline; nothing is ever bundled with or redistributed by `gauss-ai`.

## The easy way: `gauss-ai docs fetch`

```
gauss-ai docs fetch
```

This downloads the source of every page published at [docs.aptech.com/gauss](https://docs.aptech.com/gauss/), about 1,800 small text files, into `~/.gauss-ai/docs/`. Expect it to take a few minutes: the site rate-limits, so `gauss-ai` downloads two files at a time and backs off when asked to. If `docs-root` isn't already set, it points `docs-root` at that copy. You don't need git or a clone.

- **It runs only when you ask.** It is the one network download in `gauss-ai` besides a model provider you enable yourself. Nothing is uploaded, and nothing is fetched while you ask questions.
- **It's all or nothing.** If any page fails to download, the whole fetch is aborted and your previous copy is left untouched, so you never end up with a partial set.
- **It never overrides your own choice.** If `docs-root` already points somewhere else (for example, your own clone), it is left alone, and the command prints how to switch.
- **Refreshing:** run it again any time. `gauss-ai docs status` shows which docs are in use and when they were fetched.

You download the documentation directly from Aptech's public site for your own local use. `gauss-ai` never bundles, mirrors or redistributes it: the published package contains no documentation (a packaging test checks this), searches run locally, and excerpts and page sections go only to your own MCP client. The `aptech/docs` repository declares no license, so the documentation stays Aptech's; gauss-ai only automates the download each user would otherwise do by hand. Each request identifies itself as `gauss-ai/<version>`.

## Alternative: point at a copy you already have

Any local checkout of the official documentation source in its native `.rst` form works, for example a clone of the public `aptech/docs` repository:

```
gauss-ai config set docs-root "C:\path\to\docs\docs"
```

Precedence follows the same rule as every other `gauss-ai` setting: `--docs-root` (CLI flag) > `GAUSS_AI_DOCS_ROOT` (environment variable) > this config value > unset.

`gauss-ai` (via `command_doc_lookup.py`) searches recursively for a file named `<command>.rst` (for example `reshape.rst`) anywhere under `docs-root`, so the normal directory structure works as-is. Only `.rst` source is read; HTML or PDF output is not used.

## Verifying it's working

Run `gauss-ai doctor`. Its `docs_root` check reports:

- **PASS** when the folder exists and contains `.rst` files;
- **FAIL** when the path is missing or contains no `.rst` files;
- **WARN** when nothing is configured.

Then ask about a documented command:

```
> What does reshape do?
```

A working setup shows:

```
[Grounded in local official GAUSS documentation: reshape]
```

## What this does not do

- No per-question network access. Every lookup reads the local filesystem.
- No bundled or redistributed snapshot of GAUSS documentation ships with `gauss-ai`.
- No write access to `docs-root`. Lookups are strictly read-only, and only `gauss-ai docs fetch` writes, into its own `~/.gauss-ai/docs/` folder.
