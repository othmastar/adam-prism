# ADR-005: License change from GPLv3 to Apache 2.0

**Status:** Accepted (2026-05-10)
**Context:** Original license was GPLv3, but this created friction with corporate adoption.
**Decision:** Switch to Apache 2.0.

## Rationale
- **Permissive** — companies can use Adam Prism in commercial products without open-sourcing their work
- **Patent grant** — Apache 2.0 includes an explicit patent grant (GPLv3 does too, but Apache's is more business-friendly)
- **Industry standard** — used by Kubernetes, TensorFlow, Swift, etc.
- **Trademark clarity** — Apache 2.0 is clear about trademark usage

## Alternatives Considered
- **Stay GPLv3** — maximizes copyleft but limits adoption
- **MIT** — even more permissive but no patent grant
- **BSL (Business Source License)** — non-OSI, complex

## Consequences
- (+) Broader adoption (Fortune 500 can use it without legal review)
- (+) More contributors (corporate-friendly)
- (-) Less copyleft protection (derivative works can be proprietary)
- (-) Must add explicit LICENSE + NOTICE files
