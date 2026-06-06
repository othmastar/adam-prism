# Data Pipeline — OthMastar Digital Twin

## RAW FILES (untouched, original)
```
deepseek_all_348.json     5.5 MB   → 348 conversations from DeepSeek web
gemini_othmastar.json     6.1 MB   → 413 conversations from Gemini (335 full + 78 URLs)
```

## PROCESSED (generated)
```
classified/classification.json
    → 761 conversations classified by phase + layer + filter
    → 300 DeepSeek usable + 277 Gemini usable = 577 usable

raw_training_v2/
    train.jsonl (316)  /  val.jsonl (40)  /  test.jsonl (40)
    → 396 conversation examples with roles swapped:
        assistant (training target) = engineer message
        user (context)              = AI response
    → 1199 engineer message targets, median 60 chars
```

## KNOWLEDGE BASE
```
web_research_knowledge_base.md   28 KB
    → 10 sections from web search findings (security, AI/ML, CI/CD, code review, etc.)
    → Ready to convert into training data when needed
```

## KAGGLE PACKAGES
```
othmastar_v2.zip   396 conversations
    → RAW from DeepSeek (filtered + swapped)
    → MAX_LENGTH=4096, rank=16, cosine LR

othmastar_v3.zip   599 conversations
    → v2 (584) + 15 DEEP educational (code + CVEs + fix + practice)
    → model: othmastar-v3 (Ollama, gemma4:e4b base)

othmastar_v4.zip   1799 conversations
    → v3 (599) + 1200 DEEP template-generated
    → 18 domains: Linux Kernel, C/C++ Memory Safety, Rust, Docker,
      Kubernetes, Databases, Security, System Architecture, Cloud,
      Frontend, CI/CD, Observability, AI/ML, Networking, DevOps,
      Software Engineering, Embedded Systems, Cryptography
```

## DEEP FRAMEWORK (for generated educational conversations)
```
D (Discover)  = سؤال حقيقي + سياق عملي من HTB/CVE/GitHub/CISA
E (Explain)   = سبب جذري، trade-offs، كيف يشتغل (مش مجرد "ماذا")
Err (Error)   = خطأ شائع واحد واقعي + CVE حقيقية (بالسنة والرقم)
P (Practice)  = أداة/كود + خطوات + تحذير production
```

## MODEL IDENTITY
```
data/training/MODEL_IDENTITY.md
  → سكشن كامل: ماهية النموذج، مصادر المعرفة، DEEP framework،
    هيكل الحوار، مبادئ التوليد، حدود النموذج
```

## GENERATORS (يدوية — كل محادثة من مصدر حقيقي)
```
scripts/gen_batch1.py → batch1_total.json    (50 DEEP)
scripts/gen_batch2.py → batch2_total.json    (50 DEEP)
scripts/gen_batch3.py → batch3_total.json    (50 DEEP)
scripts/gen_batch4.py → batch4_total.json    (35 DEEP)
scripts/gen_batch5.py → batch5_total.json    (39 DEEP)
scripts/gen_batch6.py → batch6_total.json    (41 DEEP — IPv6, Email, K8s, OS, Crypto, Cloud, Mobile, Exploitation, Certificates, Networking, Forensics, Management, Hardware)
scripts/gen_batch7.py → batch7_total.json    (37 DEEP — Event-Driven, Service Mesh, CQRS, Clean/Hexagonal Architecture, rustls, libsodium, Falco, OPA, Sigstore, AD Lab, HTB, THM, C2, BloodHound, Burp, Web/API/Mobile/Cloud/Malware Labs, CIS Linux/Windows, Wazuh, Osquery, Auditd, SELinux, Docker Security, Kali, Metasploit, Ghidra, Frida, SOC, Ansible, Terraform, Docker, Elastic Fleet)
scripts/gen_batch8.py → batch8_total.json    (25 DEEP — ZeroLogon, PrintNightmare, PetitPotam, NoPac, Certifried, SSRF→RCE, Deserialization Chains, RCE Chains, GraphQL Deep, JWT Deep, AWS/Azure/GCP Pentesting, K8s Pod Escape, Cloud Forensics, Memory/Disk/Network/Container/Browser Forensics, OSINT Advanced, Supply Chain, Compliance Automation, NIST CSF 2.0, ISO 27001)
```

## BATCH SUMMARIES
| Batch | # | Tokens | Topics |
|-------|---|--------|--------|
| 1 | 50 | 62,511 | SCADA/ICS, Docker, K8s, CI/CD, SQLi, XSS, DNS, Email, DNSSEC, Bug Bounty, Supply Chain SLSA, Vault, Web Security, Cloud, AI/ML |
| 2 | 50 | 84,866 | IEC 61850, IEC 104, BloodHound, C2, Kerberos, SSTI, CSRF, Deserialization, IaC, Serverless, Mobile, WiFi, NoSQL, LPE, IoT, Bluetooth, Container Escape, DevSecOps, SBOM, OPA, Memory/Disk/Network Forensics, Post-Quantum |
| 3 | 50 | 23,503 | AI Security, Cloud (GCP/Azure/AWS/K8s), Network (BGP/SDN/DNS/CDN/Zero Trust), System Design (CAP/Raft/Hashing/Microservices), Blockchain, Privacy, Purple/Blue Team, CI/CD, DevSecOps, API Security, Identity, Cryptography |
| 4 | 35 | 25,727 | Threat Modeling, OSINT, Social Engineering, TLS 1.3, WireGuard, Quantum, CAN bus, Medical, Satellite, Purdue/ISA-62443, MPLS, VXLAN/EVPN, Mobile Forensics, Red Team, Adversary Emulation, Vuln Mgmt, SHA/BLAKE, DH/ECDH, CORS/CSP, SRI, Passkeys, SAML/OIDC/LDAP, Cloud Breach, SOLID/Singleton/Factory, Go/Python/Java sec, IPsec, HTTP/2/3, SOAR, CCPA, SAST/DAST/IAST, RASP |
| 5 | 39 | 29,690 | BACnet, Drones, PCI/SWIFT, EDR (ETW/Process Doppelganging), SIEM, SIGMA, STIX/TAXII, Bug Bounty, Recon, gVisor/Kata, runC, eBPF, TEE (SGX/SEV), AI Alignment/XAI, Blockchain Bridges, MEV, Supply Chain (xz), SLSA, Sigstore, Physical Access, Data Centers, ISO 27001, NIST CSF 2.0, SOC 2/HIPAA, API/GraphQL Pentesting, SSDF, TypeScript/Rust sec, Blue OSINT, Deception, CTI, Purple Team, NetFlow/sFlow, Malware Analysis, SOAR Playbooks, Ansible/Salt, Side-channel |
| 6 | 41 | 29,418 | IPv6/NDP/SLAAC, Email (SPF/DKIM/DMARC/MTA-STS/DANE/BIMI), SMTP, Kyverno, Pod Security, Windows Internals, Linux Namespaces, KMS/Vault, PBKDF2/HKDF/Argon2, CSPM, CIEM, DSPM, Android RE, Frida, iOS/SIP/TCC, Binary Exploitation, Fuzzing, ARM, PKI, Certificate Transparency, ACME, DoH/DoT, NTP, BGP Communities, P4, Windows Event Logs, Linux Logs, Volatility, Physical Attacks, Social Engineering, Risk Management (ISO 31000/FAIR), Security Metrics, Firmware, UART/JTAG/SPI, Rowhammer, WebSockets, WASM, 4G/LTE |
| 7 | 37 | 29,190 | Event-Driven/Kafka/RabbitMQ, Service Mesh/Istio/Linkerd, CQRS/ES, Clean Architecture/DDD, Hexagonal, rustls, libsodium, Falco, OPA/Rego, Sigstore/Cosign, AD Lab/GOAD, HTB AD/Forest, THM Path, C2 Sliver/Mythic, BloodHound, Burp Suite, DVWA/Juice Shop, API/vAPI, Mobile Lab (Android/iOS), Cloud Lab (AWS/Pacu), Malware Lab (FlareVM), CIS Linux/Windows, Wazuh, Osquery, Auditd, SELinux/AppArmor, Docker Bench/kube-bench/Trivy, Kali Linux, Metasploit, Ghidra, Frida/Objection, SOC Lab (ELK+Wazuh+TheHive), Ansible Hardening, Terraform/Checkov, Docker Security Tools, Elastic Fleet |
| 8 | 25 | 18,880 | ZeroLogon, PrintNightmare, PetitPotam, NoPac, Certifried, SSRF→RCE, Deserialization Chains, RCE Chains, GraphQL Deep, JWT Deep, AWS/Azure/GCP Pentesting, K8s Pod Escape, Cloud Forensics, Memory/Disk/Network/Container/Browser Forensics, OSINT Advanced, Supply Chain, Compliance Auto (OpenSCAP/InSpec), NIST CSF 2.0, ISO 27001 |
| **Total** | **327** | **~303K** | |

## HOW IT WORKS
1. Generate DEEP conversations manually from real sources (CISA, GitHub, HTB/THM, CVEs, RFCs, docs)
2. Each conversation: system prompt (model identity) + user question (short, Arabic, practical) + assistant answer (DEEP: Discover → Explain → Err → Practice)
3. All batches → combined → convert to JSONL (messages + topic + tokens_est)
4. Split 88/6/6 train/val/test
5. Package as ZIP with train_lora.py + metadata.json
6. train_lora.py → QLoRA on Gemma-4-E4B-it → adapter weights
7. Merge adapter into base model via ollama
8. Model learns engineer personality (short questions, technical, curious, direct)
