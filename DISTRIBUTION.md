# Adam Prism — Private Distribution Guide

This document describes how the **full version** of Adam Prism is
distributed to selected developers and organizations.

**The full version is NOT on GitHub.** It is distributed only via
encrypted packages to recipients with a signed NDA and a valid license.

---

## Overview

```
┌──────────────────────────────────────────────────────────────┐
│  ADAM (maintainer)                                           │
│  Owns: source code, training data, model weights             │
│      │                                                       │
│      │ 1. Recipient requests access (email)                  │
│      │ 2. Adam sends NDA template                            │
│      │ 3. Recipient signs NDA (or e-signs)                   │
│      │ 4. Adam verifies, signs license key                   │
│      │ 5. Adam creates encrypted package                     │
│      │ 6. Sends package + key via different channels         │
│      ▼                                                       │
│  Recipient gets:                                             │
│    - .enc file (via Tresorit / Keybase)                      │
│    - decryption key (via phone / Signal)                     │
│    - license.key (signed, JSON)                              │
│    - NDA (signed) archived by both parties                   │
│      │                                                       │
│      │ 7. Recipient decrypts and runs                        │
│      │ 8. Recipient verifies license.key                     │
│      ▼                                                       │
│  Recipient uses: full version under private license          │
└──────────────────────────────────────────────────────────────┘
```

---

## Step-by-step

### Step 1: Recipient requests access

Recipient emails **othman@adam-prism.local** with:
- Name / organization
- Intended use case
- Desired tier (startup / growth / enterprise / custom)
- Number of MAU expected
- Timeline

### Step 2: Adam sends NDA

If approved, Adam sends `templates/NDA.md` for the recipient to sign.
The recipient signs (DocuSign, HelloSign, or scanned PDF).

### Step 3: License key generation

Adam runs:
```bash
bash bin/sign-license.sh acme-corp enterprise 365
```

This creates:
- `recipients/acme-corp/license.key` — signed JSON license
- `recipients/acme-corp/public.pem` — recipient's public key (for future encrypted packages)
- `recipients/acme-corp/private.pem` — recipient's private key (kept by them, NOT sent)
- `recipients/acme-corp/distribution.log` — distribution history

### Step 4: Package encryption

Adam runs:
```bash
bash bin/encrypt-package.sh acme-corp
```

This creates:
- `dist/adam-prism-full-YYYYMMDD.tar.gz.enc` — encrypted package
- `dist/adam-prism-full-YYYYMMDD.sha256` — checksum

The package contains the FULL main branch (with all data, weights, configs).

### Step 5: Send to recipient

Send via **TWO different channels**:

**Channel A (the .enc file):**
- Tresorit (https://tresorit.com)
- Keybase (https://keybase.io)
- Or any secure file transfer service with end-to-end encryption

**Channel B (the decryption key):**
- Phone call (read the key aloud)
- Signal message (with disappearing messages enabled)
- In-person handoff (if feasible)

**NEVER send both in the same email/chat!**

### Step 6: Recipient decrypts

```bash
# 1. Receive the .enc file
# 2. Receive the decryption key
# 3. Decrypt:
bash bin/decrypt-package.sh ./adam-prism-full-20260115.tar.gz.enc
```

### Step 7: Recipient verifies license

```bash
bash bin/verify-license.sh acme-corp-license.key
```

Should print: `✓ Signature is VALID` and `✓ License is valid for X more days`

### Step 8: Recipient runs

```bash
cd decrypted-package/
bash bin/install-full.sh
```

This installs the full version (with the proprietary training pipeline,
LoRA weights, real subagents, real tenant configs, etc.).

---

## What recipients MUST do

1. **Sign the NDA** before receiving any code
2. **Verify the license.key** signature
3. **Not redistribute** the package to anyone
4. **Not push to public repos**
5. **Not use for commercial purposes** beyond what's in the license
6. **Report any security issues** to security@adam-prism.local
7. **Comply with export control laws** of their jurisdiction
8. **Notify** if their situation changes (acquisition, bankruptcy, etc.)

## What recipients MAY do

✅ Use the full version for the licensed purpose
✅ Modify the code locally for their use
✅ Run it on their own infrastructure
✅ Integrate with their own systems
✅ Train their own models on top of it (with separate license)

## What recipients MUST NOT do

❌ Redistribute the package or any part of it
❌ Reverse-engineer proprietary algorithms (except for the Purpose)
❌ Train competing products
❌ Disclose the source code publicly
❌ Use beyond the license expiration date
❌ Transfer the license to another entity

---

## What happens on license expiration?

- The license.key will fail verification (if you check it)
- The recipient should contact Adam to renew
- If not renewed, the recipient must:
  1. Stop using the full version
  2. Delete the decrypted package
  3. Delete all training data and weights received
  4. Confirm deletion in writing

## Termination for breach

If a recipient breaches the NDA:
1. License is revoked immediately
2. Recipient must delete all materials within 30 days
3. Licensor may seek injunctive relief and damages
4. Material breach may result in legal action

---

## File structure (maintainer side)

```
adam-prism/  (this repo, on the maintainer's machine only)
├── bin/
│   ├── encrypt-package.sh     # Step 4
│   ├── decrypt-package.sh     # Recipient side
│   ├── sign-license.sh        # Step 3
│   ├── verify-license.sh      # Recipient side
│   ├── install-full.sh        # Recipient side
│   └── install.sh             # Public showcase install
├── templates/
│   └── NDA.md                 # Step 2
├── recipients/                # One folder per recipient
│   ├── acme-corp/
│   │   ├── license.key
│   │   ├── public.pem
│   │   ├── private.pem        # ← They keep this, you delete yours
│   │   └── distribution.log
│   └── globex-inc/
│       ├── license.key
│       └── ...
├── keys/
│   ├── maintainer-signing.pem       # For signing licenses
│   └── maintainer-signing.pem.pub   # Public key (recipient gets this)
├── dist/                            # Output of encrypt-package.sh
│   ├── adam-prism-full-20260115.tar.gz.enc
│   └── adam-prism-full-20260115.sha256
└── docs/
    └── DISTRIBUTION.md              # This file
```

---

## Recipient side (after decryption)

```
adam-prism-full/
├── LICENSE-PROPRIETARY.txt    # Custom proprietary license
├── NDA-SIGNED.pdf             # Signed NDA (recipient's copy)
├── license.key                # Signed license
├── README.md                  # Full version readme
├── bin/
│   ├── install-full.sh
│   ├── verify-license.sh      # Re-verify
│   └── ...
├── data/                      # Training data
├── checkpoints/               # Model weights
├── notebook/                  # Real conversations
└── adam/                      # Full source code
```

---

## Security best practices

1. **Always use a dedicated signing key** for the maintainer (not your daily-use key)
2. **Rotate the maintainer's signing key** every 2 years
3. **Backup `recipients/`** to encrypted offline storage
4. **Use hardware tokens** (YubiKey) for the signing key in production
5. **Audit distribution** annually
6. **Keep distribution.log** for at least 7 years (tax / legal)
7. **Two-person rule** for signing high-tier licenses (optional, recommended)
8. **Use a different passphrase** for each package encryption

---

## Legal disclaimer

This is a procedural guide, not legal advice. Consult an attorney
in your jurisdiction (and the recipient's jurisdiction) for:
- NDA enforceability
- Export control compliance
- Tax implications
- Local data protection laws
- Industry-specific regulations (HIPAA, PCI-DSS, etc.)

---

*Last updated: June 15, 2026*
*Maintainer: Mohamed Othman — othman@adam-prism.local*
