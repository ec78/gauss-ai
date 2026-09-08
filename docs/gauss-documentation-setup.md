# Setting up local GAUSS documentation for grounding

**Status: Alpha, added in `v0.71.0`.**

Conversational GAUSS Q&A (see [conversational-qa.md](conversational-qa.md)) can ground its answers in real official GAUSS documentation instead of a model's general knowledge — but only if you point `docs-root` at a real local copy of that documentation. `gauss-ai` does not download, scrape, or bundle any GAUSS documentation itself.

## What `docs-root` should point to

`docs-root` must be the top-level directory of a local checkout of the official GAUSS documentation source, in its native `.rst` (reStructuredText) form — the same format the docs are authored in. Under the hood, `gauss-ai` (via `command_doc_lookup.py`) searches recursively for a file named `<command>.rst` (for example, `reshape.rst`) anywhere under `docs-root`. It is not sensitive to how deeply nested the file is, so the ordinary directory structure of a documentation checkout works as-is — nothing needs to be flattened or renamed.

`docs-root` does **not** need to be:

- HTML, PDF, or any built/rendered output — only the `.rst` source is read.
- A copy specific to `gauss-ai` — pointing at an existing checkout you already have for another purpose works fine, since lookups are strictly read-only.

## How to obtain a copy

`gauss-ai` does not automate this step. You are responsible for obtaining official GAUSS documentation source through channels you already have access to (for example, a documentation repository provided by Aptech, or a local export you maintain yourself). If you don't have one, conversational answers about specific commands will simply be ungrounded — clearly labeled as such — rather than blocked.

## Configuring it

```
gauss-ai config set docs-root "C:\path\to\your\gauss-docs\checkout"
```

Precedence follows the same rule as every other `gauss-ai` setting: `--docs-root` (CLI flag) > `GAUSS_AI_DOCS_ROOT` (environment variable) > this config value > unset.

## Verifying it's working

Run `gauss-ai doctor` — it reports whether `docs-root` is configured (it does not verify the directory's contents; grounding only fails at answer time if a specific lookup finds nothing). Then ask the assistant about a command you know is documented there, for example:

```
> What does reshape do?
```

A correctly working setup shows:

```
[Grounded in local official GAUSS documentation: reshape]
```

If instead you see the general "not grounded" disclosure for a command you know is documented, double-check that `docs-root` points at the directory that actually *contains* the `.rst` files (not a parent or sibling directory), and that the file is genuinely named `<command>.rst`.

## What this does not do

- No web scraping, no download, no bundled snapshot of GAUSS documentation ships with `gauss-ai`.
- No indexing or caching — every lookup reads the filesystem directly, so edits to your local checkout are reflected immediately.
- No write access — this is a strictly read-only lookup; nothing under `docs-root` is ever modified.
