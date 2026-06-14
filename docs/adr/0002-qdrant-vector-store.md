# ADR-002: Qdrant as the primary vector store

**Status:** Accepted (2026-04-15)
**Context:** Need a vector database for semantic memory, RAG, and hybrid search.
**Decision:** Qdrant (with in-memory + SQLite fallback for dev).

## Rationale
- **Self-hostable** — runs as a single Docker container, no managed-service lock-in
- **Rust performance** — 2-5x faster than FAISS for similar accuracy
- **Built-in filtering** — payload indexes let us combine vector + metadata queries
- **Hybrid search** — supports dense + sparse in one query (BM25 + embeddings)
- **Open source (Apache 2.0)** — matches our license

## Alternatives Considered
- **Pinecone** — managed, fast, but vendor lock-in + cost
- **Weaviate** — great features but heavier deploy (~3GB RAM minimum)
- **Chroma** — too immature for production
- **FAISS** — library, not a service, no multi-tenant support

## Consequences
- (+) Production-ready at 100k+ vectors per tenant
- (+) Easy to back up (snapshot API)
- (-) Needs 1GB RAM minimum (but we ship a 256MB profile for small deployments)
- (-) No GraphQL API (only gRPC + REST)
