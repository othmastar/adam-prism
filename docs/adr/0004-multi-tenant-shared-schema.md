# ADR-004: Multi-tenant with single-database, shared-schema

**Status:** Accepted (2026-05-02)
**Context:** Need to support multiple customers/tenants in a single deploy.
**Decision:** Single PostgreSQL database, shared schema, `tenant_id` column on every tenant-owned row.

## Rationale
- **Cost-efficient** — one DB instance, one connection pool, one backup pipeline
- **Schema migrations** — applied once, not per tenant
- **Cross-tenant analytics** — easier (for the operator)
- **Tenant isolation enforced at query layer** — every ORM query wraps with `WHERE tenant_id = :tid`

## Alternatives Considered
- **Database-per-tenant** — strongest isolation but expensive at scale (>100 tenants = 100 DBs)
- **Schema-per-tenant** — middle ground, but migrations get hairy
- **Row-level security (PostgreSQL RLS)** — promising but adds complexity, harder to debug

## Consequences
- (+) Easy to start (just set `tenant_id` when creating rows)
- (+) Single migration pipeline
- (-) Higher blast radius if a query forgets the `tenant_id` filter (mitigated by tests + lint)
- (-) Need to enforce tenant_id in ORM queries (we use a session-level filter)
