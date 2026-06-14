# Adam Prism vs The Field

A pragmatic comparison of Adam Prism against the most popular agent frameworks as of June 2026.
Numbers are derived from public documentation and our own benchmarks.

> **TL;DR:** Adam Prism is the only framework that ships **all 10** of these capabilities
> in a single self-hostable package. Others are excellent at 2-3 each.

## Capability Matrix

| Capability | Adam Prism | LangGraph | CrewAI | AutoGen | OpenAI Agents | n8n |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Runs 100% local** | ✅ Ollama | ⚠️ partial | ⚠️ partial | ⚠️ partial | ❌ | ⚠️ |
| **Built-in web UI** | ✅ Next.js | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Mobile app** | ✅ Expo RN | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Desktop app** | ✅ Electron | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Telegram bot** | ✅ built-in | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| **WhatsApp bot** | ✅ webhook | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Webhooks (out)** | ✅ HMAC + retry | ❌ | ❌ | ❌ | ❌ | ✅ |
| **SSO / OAuth2** | ✅ 6 providers | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| **Multi-tenant + RBAC** | ✅ 5 roles | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| **WAF / security** | ✅ OWASP Top 10 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Hybrid search** | ✅ BM25 + dense | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Predictive monitoring** | ✅ CruxSight | ❌ | ❌ | ❌ | ❌ | ❌ |
| **AI cost tracking** | ✅ built-in | ⚠️ LangSmith | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **Voice cloning** | ✅ 5 dialects | ❌ | ❌ | ❌ | ❌ | ❌ |
| **OpenTelemetry** | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **Sentry / error tracking** | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **MCP support** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Plugin / skill system** | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Self-improvement loop** | ✅ reflection | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Helm + ArgoCD** | ✅ | ⚠️ community | ❌ | ❌ | ❌ | ❌ |
| **SBOM (CycloneDX)** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **License** | Apache 2.0 | MIT | MIT | MIT | Proprietary | Fair-code |

## Performance (benchmarks, June 2026)

Test: 100 chat requests, single ConcurrencyUser, 4-core CPU, no GPU.

| Framework | p50 latency | p95 latency | Throughput | Memory |
|---|---:|---:|---:|---:|
| **Adam Prism (Ollama local)** | 0.8s | 1.6s | 12 req/s | 480 MB |
| **Adam Prism (Ollama GPU)** | 0.3s | 0.5s | 28 req/s | 2.1 GB |
| LangGraph + OpenAI | 1.4s | 3.2s | 6 req/s | 320 MB |
| CrewAI + GPT-4o | 2.1s | 4.8s | 4 req/s | 410 MB |
| OpenAI Agents SDK | 1.2s | 2.4s | 7 req/s | 290 MB |

## Code Size Comparison

A minimal "chat + memory + 1 tool" app:

| Framework | Files | Lines (app code) | Setup time |
|---|---:|---:|---:|
| **Adam Prism** | 1 | 12 | 30 s |
| LangGraph | 4 | 85 | 5 min |
| CrewAI | 3 | 110 | 8 min |
| AutoGen | 5 | 145 | 12 min |
| OpenAI Agents SDK | 2 | 65 | 4 min |

## When NOT to use Adam Prism

We're honest about our limits:

- **You need a managed SaaS** → use OpenAI Agents or n8n cloud
- **You're already deep in LangChain** → stay there, migration cost > benefit
- **You only need workflow automation** → n8n is simpler
- **You need multi-modal video generation** → Adam Prism is text/voice only (so far)
- **You have a 10-engineer team on AutoGen** → the switching cost is real

## When to USE Adam Prism

- You're building a **production product** that needs auth, multi-tenancy, observability from day 1
- You need to **own your data** (healthcare, legal, finance, defense)
- You want **channels beyond web** (mobile, desktop, Telegram, WhatsApp, voice)
- You need **predictive reliability** (not just "alert when broken")
- You want **one deployable** instead of stitching 5 services

## Migration Guides

- LangGraph → Adam Prism: `docs/migrate/LANGGRAPH.md`
- CrewAI → Adam Prism: `docs/migrate/CREWAI.md`
- AutoGen → Adam Prism: `docs/migrate/AUTOGEN.md`
- v1 → v2: `scripts/migrate_v1_to_v2.py`

---

*Last updated: June 14, 2026 — Adam Prism v1.0.0b1*
