# Choosing an Ollama model for GAUSS AI

**Status: Alpha, added in `v0.71.0`.** This is a recommendation, not a requirement — `gauss-ai config set chat-model <any Ollama model name>` accepts any model you have pulled. Nothing in `gauss-ai` hardwires a single model name; `qwen2.5-coder:7b` is simply the documented, tested default.

## Recommended default: `qwen2.5-coder:7b`

- **License**: Apache 2.0.
- **Size**: ~4.7 GB on disk.
- **Parameters**: 7.6B.
- Chosen for a strong balance of coding/instruction-following quality against a size that is practical on typical development hardware (8 GB+ of RAM recommended; a GPU helps latency but is not required).

```
ollama pull qwen2.5-coder:7b
gauss-ai config set chat-provider ollama
gauss-ai config set chat-model qwen2.5-coder:7b
```

If you don't set `chat-model` explicitly, `gauss-ai`'s Ollama provider applies this same default itself.

## Lighter-hardware fallback: `qwen2.5-coder:3b`

- **License**: Apache 2.0 (same family).
- **Size**: ~1.9 GB on disk.
- Recommended if `qwen2.5-coder:7b` is too slow or won't fit comfortably in available RAM. Conversational answer quality is lower than the 7b model, but it remains usable for straightforward questions.

```
ollama pull qwen2.5-coder:3b
gauss-ai config set chat-model qwen2.5-coder:3b
```

## Using a different model

Any chat-capable model you have pulled through `ollama pull <name>` can be used:

```
gauss-ai config set chat-model <name>
```

Model quality directly affects conversational answer quality (fluency, correctness of unsourced general-knowledge claims, ability to follow the system prompt's constraints). It does **not** affect `gauss-ai`'s own safety architecture: grounding, the execution boundary, and every existing repair/verification/approval workflow are enforced entirely outside the model, in `gauss-ai`'s own code, regardless of which model answers a question. See [conversational-qa.md](conversational-qa.md) and the distribution note below.

## Hardware and licensing

`gauss-ai` does not detect your hardware or estimate whether a given model will run acceptably — this document's size/RAM figures are the model publisher's own approximate figures, not a `gauss-ai` measurement or guarantee. Before pulling and using any model, review its own license yourself; `gauss-ai` does not evaluate, redistribute, or bundle model weights of any kind (see [conversational-qa.md](conversational-qa.md) for the full provider architecture, and the distribution note referenced from the `v0.71.0` release notes for `gauss-ai`'s own ownership boundary relative to any model it talks to).
