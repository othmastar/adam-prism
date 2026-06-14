# ADR-003: Ollama as the default LLM runtime

**Status:** Accepted (2026-04-18)
**Context:** Need a local LLM backend that supports the largest set of open models.
**Decision:** Ollama as default, OpenAI/Anthropic as optional cloud providers.

## Rationale
- **One-binary install** — single `curl | sh` gets you up and running
- **Model variety** — Llama, Qwen, Mistral, Phi, Gemma, DeepSeek all supported
- **OpenAI-compatible API** — drop-in replacement for cloud APIs
- **GPU + CPU** — runs on a 16GB laptop or a 80GB H100
- **Modelfile** — easy to customize system prompts + parameters

## Alternatives Considered
- **llama.cpp directly** — too low-level, no model management
- **vLLM** — excellent performance but Python-only, heavier
- **LocalAI** — similar to Ollama but less mature
- **LM Studio** — great UX but closed-source, desktop only

## Consequences
- (+) Users can swap models without code changes
- (+) No API costs for self-hosted deployments
- (-) Performance ceiling on consumer hardware (but acceptable for chat workloads)
- (-) Need to ship a model recommendation (we use `qwen2.5:3b` as default)
