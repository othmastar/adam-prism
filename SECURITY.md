# Security Policy

## Supported Versions

| Version | Supported          | End of Support |
|---------|--------------------|----------------|
| 2.0.x   | :white_check_mark: | TBD            |
| 1.x.x   | :x:                | 2026-12-31     |
| < 1.0   | :x:                | 2025-12-31     |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Adam Prism takes security seriously. We appreciate your efforts to responsibly
disclose your findings and will make every effort to acknowledge your contributions.

### How to Report

Send a detailed report to: **othmastar@gmail.com**

Please include:
1. **Description** of the vulnerability
2. **Steps to reproduce** (proof-of-concept if possible)
3. **Affected versions** (commit SHA, tag, or branch)
4. **Impact assessment** (what an attacker could achieve)
5. **Suggested fix** (if you have one)
6. **Your name/handle** (for credit in security advisories, optional)

### What to Expect

| Timeline | Action |
|----------|--------|
| **< 48 hours** | Initial acknowledgment of your report |
| **< 7 days**   | Detailed response with impact assessment and planned fix timeline |
| **< 30 days**  | Fix released in a patch version, or disclosure of why not |
| **< 90 days**  | Public CVE assignment (if applicable) and security advisory |

### Safe Harbor

We will not pursue legal action against researchers who:
- Make a good-faith effort to avoid privacy violations
- Only interact with accounts they own or have explicit permission to access
- Stop testing immediately if they encounter user data
- Do not exploit a vulnerability beyond what is necessary to demonstrate it
- Report vulnerabilities to us before disclosing them publicly

### Recognition

Security researchers who report valid vulnerabilities will be:
- Credited in the security advisory (if desired)
- Listed in our [Hall of Fame](https://github.com/othmastar/adam-prism/security/policy)
- Eligible for our bug bounty program (if applicable, see below)

## Security Best Practices for Users

When deploying Adam Prism:

1. **Always change the default API key:**
   ```bash
   export ADAM_API_KEY=$(openssl rand -hex 32)
   ```

2. **Enable production mode:**
   ```bash
   export ADAM_PRODUCTION=1
   export ADAM_ENV=production
   ```

3. **Use HTTPS:** Always run behind TLS (nginx, Caddy, or cloudflare)

4. **Set admin key for MCP:**
   ```bash
   export ADAM_ADMIN_KEY=$(openssl rand -hex 32)
   ```

5. **Set JWT secret for multi-user:**
   ```bash
   export ADAM_JWT_SECRET=$(openssl rand -hex 32)
   ```

6. **Use environment files, not hardcoded values:**
   ```bash
   cp deploy/.env.example deploy/.env
   # Edit deploy/.env and set all CHANGE-ME values
   ```

7. **Regular backups:**
   ```bash
   ./deploy/backup.sh
   ```

8. **Monitor logs:** Pipe JSON logs to your log aggregator (Loki, Splunk, etc.)
   ```bash
   export ADAM_LOG_JSON=1
   ```

9. **Run as non-root:** All Docker images have non-root users by default

10. **Keep updated:** Watch releases and apply security patches promptly

## Security Architecture

Adam Prism implements defense-in-depth:

### 1. Input Security
- **InputGuard:** 14+ injection patterns detected (Arabic + English)
- **Pydantic validation:** All routes use typed models
- **Rate limiting:** Per-IP throttling (60 req/min default)

### 2. Output Security
- **OutputGuard:** PII masking, system prompt leak detection
- **HTML escaping:** All user-generated content is escaped
- **Content Security Policy:** Strict CSP headers in Web UI + Electron + VS Code

### 3. Tool Security
- **Whitelist:** Only allowed shell commands can execute
- **Sandboxing:** Python code runs with restricted globals
- **Path validation:** File operations restricted to allowed directories

### 4. Ethics Gate
- **4 laws:** Justice / Learning / Survival / Creativity (weighted)
- **Fail-closed:** Returns low scores on evaluation failure
- **Audit trail:** Every decision logged

### 5. Authentication
- **JWT:** PyJWT with HMAC-SHA256
- **Bcrypt:** Password hashing (PBKDF2 fallback)
- **API keys:** Hashed with SHA-256
- **WebSocket:** Token-based auth with query param

### 6. Transport Security
- **HTTPS:** TLS 1.2+ only, strong ciphers
- **HSTS:** Strict-Transport-Security headers
- **CORS:** Configurable allowed origins (no wildcard in production)

### 7. Container Security
- **Non-root user:** UID 1001 in all Docker images
- **Read-only filesystem:** Where possible
- **No new privileges:** `no-new-privileges` flag

## Known Limitations

- **API key in query string:** WebSocket auth uses `?token=` query param (logged by proxies)
  - Mitigation: Use HTTPS to encrypt URL
  - Future: Move to header-based auth (tracked in issue #XX)

- **Ollama local-only:** When using Ollama, the LLM runs on the same machine
  - Mitigation: Run Ollama on a dedicated GPU host
  - Future: Remote Ollama cluster support (planned)

- **No rate limiting on Qdrant:** Direct Qdrant queries are not rate-limited
  - Mitigation: Run Qdrant behind a reverse proxy with rate limits
  - Future: Built-in Qdrant rate limiting (planned)

## Acknowledgments

We thank the following security researchers for their contributions:

- (List will be added as reports come in)

## Contact

- **Email:** othmastar@gmail.com
- **GitHub Security Advisories:** https://github.com/othmastar/adam-prism/security/advisories
- **PGP Key:** (To be added)

---

Last updated: 2026-06-14
