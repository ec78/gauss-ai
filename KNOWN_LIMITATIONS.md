# Known Limitations

These limitations apply as of the `v0.4.0` Retrieval Prototype milestone.

- The framework does not yet execute GAUSS code.
- Command-specific documentation retrieval now has a lightweight local script prototype (`scripts/command_doc_lookup.py`), not just a workflow/design pattern. That said, it is not a full semantic search system, it does not execute GAUSS code, and it depends on having a local official GAUSS documentation checkout available on disk.
- The lookup script uses heuristic pattern matching (heading underlines, `.. function::` directives, keyword substring search) rather than a full reStructuredText parser, so it can misparse unusual formatting.
- Extraction may truncate long sections; not every documented field (for example, every member of a large output structure) is guaranteed to be captured.
- Keyword search can miss conceptually relevant text when the official wording differs from the requested keyword (for example, a doc that says "no occurrence is found" will not match a literal search for "not found").
- The retrieval prototype has been tested end-to-end on a small pilot set of commands (`olsmt` and `strindx`); broader command coverage is unverified.
- Generated lookup JSON output is evidence used to support evaluation and response-writing, not a replacement for official GAUSS documentation, which remains authoritative.
- Curated command notes are a small convenience cache, not a replacement for official GAUSS documentation.
- The Code Assistant must not invent syntax when official docs are unavailable.
- Benchmark coverage is growing but not exhaustive.
- Preview quickstart materials exist, but they should still be tested by users who were not part of the design process.
- Manual evaluation runs are useful evidence, but automated regression evaluation is not implemented yet.
- Any tracked local machine-specific configuration should be removed, renamed, or clearly documented before broader public use.
