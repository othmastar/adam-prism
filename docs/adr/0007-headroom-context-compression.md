# ADR-007: Use Headroom for context compression

**Status:** Accepted (2026-06-15)
**Context:** Adam Prism's 38 tools often return large payloads. Context windows are finite and expensive. We need to compress without losing quality.
**Decision:** Use the `headroom-ai` library (Apache 2.0) as an optional context compression layer.

## Rationale

- **Token cost:** A single Adam tool call (e.g., browser.py fetching a webpage) can return 10K-50K tokens. Multiplied by 38 tools × 12 consciousness layers × N users, this becomes expensive.
- **Sovereign AI alignment:** For air-gapped deployments, smaller contexts = smaller models possible. A 70B model on a single GPU instead of 8.
- **Open source:** Headroom is Apache 2.0, compatible with our AGPL v3 license.
- **MCP-compatible:** Works with our existing MCP infrastructure.
- **Graceful degradation:** If headroom-ai is not installed, Adam still works (compression is a no-op).

## What Headroom Provides

- **SmartCrusher** — JSON-specific compression (90% reduction typical)
- **CodeCompressor** — Source code compression (preserves semantics)
- **Kompress** — General text compression with ML extras
- **3 modes:** AUDIT (count only), OPTIMIZE (compress), SIMULATE (dry-run)
- **MCP tools:** `headroom_compress`, `headroom_retrieve`, `headroom_stats`
- **Proxy mode:** Transparent LLM-call compression (zero code changes)

## How Adam Uses It

| Integration Point | Compression Type | Expected Savings |
|---|---|---|
| **Layer 2 (Context Engine)** | RAG results (often JSON/markdown) | 70-90% |
| **Layer 4 (Tool Orchestration)** | Tool outputs (logs, files, search results) | 50-90% |
| **Layer 5 (Iron Memory)** | FTS5 + vector recall results | 60-80% |
| **Layer 6 (Learning)** | Reflections, journal entries | 40-60% |
| **Layer 9 (Subagent Teams)** | Inter-agent messages | 50-70% |
| **Layer 12 (Reflection)** | Self-analysis inputs | 40-60% |

## Configuration

Environment variables:
- `ADAM_HEADROOM_MODE` — `audit` (default), `optimize`, or `simulate`
- `ADAM_HEADROOM_STORE_URL` — SQLite URL for storing originals (default: in-memory)

## Trade-offs

### Pros
- ✅ 50-90% token reduction (verified by Headroom's own benchmarks)
- ✅ Compatible with Ollama (Adam's local LLM)
- ✅ Air-gapped (no cloud dependency)
- ✅ Optional — Adam works without it
- ✅ Open source license (Apache 2.0)
- ✅ MCP-compatible (works with our showcase + full versions)

### Cons
- ⚠️ Quality may drop slightly (it's compression, after all)
- ⚠️ Originals require local storage (disk space)
- ⚠️ New dependency (`pip install headroom-ai[mcp]`)
- ⚠️ SmartCrusher is JSON-specific (not all content benefits equally)

## Alternatives Considered

- **LangChain compression** — Less mature, not focused on agent contexts
- **Custom compression** — Reinventing the wheel, lower quality
- **No compression** — Expensive for sovereign AI use cases
- **LLMLingua (Microsoft)** — Good but no MCP integration, no proxy mode

## Consequences

- (+) Significant cost reduction for cloud LLM users
- (+) Enables sovereign AI on smaller hardware
- (+) Compatible with existing Adam architecture
- (-) One more dependency to manage
- (-) Need to monitor compression quality (may affect response accuracy)

## Verification

Run `pytest backend/tests/test_headroom_integration.py -q` — 20 tests, all passing.

Test in production:
```bash
curl http://localhost:8000/api/compression
curl -X POST http://localhost:8000/api/compression/test \
  -H "Content-Type: application/json" \
  -d '{"content": "very long text...", "content_type": "text"}'
```

## References

- Headroom repository: https://github.com/headroom-ai/headroom
- Headroom Zed extension: https://github.com/chopratejas/headroom-zed
- License: Apache 2.0
- Adam integration: `adam/observability/headroom_integration.py`
- Decorator: `adam/observability/compression_decorator.py`

---

*Last updated: June 15, 2026 — Adam Prism v1.0.0b1*
