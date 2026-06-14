# ADR-006: HMAC-SHA256 for webhook signatures (not JWT)

**Status:** Accepted (2026-05-22)
**Context:** Need to sign outgoing webhooks so receivers can verify authenticity.
**Decision:** Use HMAC-SHA256 with a shared secret per subscription.

## Rationale
- **Simple** — every language has HMAC-SHA256 built in
- **Compact** — single header `X-Adam-Signature: sha256=...` (64 hex chars)
- **Constant-time compare** — receivers can use `hmac.compare_digest` to avoid timing attacks
- **Per-subscription secret** — can be rotated independently

## Alternatives Considered
- **JWT** — more flexible (claims, expiration) but heavier, requires key management
- **RSA signatures** — strongest but slow and over-engineered for this use case
- **mTLS** — best for service-to-service, but webhooks are typically over plain HTTPS

## Consequences
- (+) Trivial to implement on the receiver side
- (+) Rotating a secret doesn't break all subscriptions
- (-) Receiver must securely store the secret (we document this in `docs/WEBHOOKS.md`)
- (-) No built-in replay protection (we mitigate with timestamp + nonce headers)
