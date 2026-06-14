# Adam Prism — Rights, Restrictions, and Legal Notice

This document clarifies **what you may and may not do** with Adam Prism
under both the free (AGPL v3) and commercial licenses. It is not a
replacement for the LICENSE file — it is a plain-language summary.

---

## Quick decision tree

```
                Are you using Adam Prism?
                            │
              ┌─────────────┴─────────────┐
              │                           │
          Free (AGPL v3)            Commercial
              │                           │
        Are you providing it            Pay fee
        as a service to users?          (see COMMERCIAL_LICENSE.md)
              │
        ┌─────┴──────┐
        │            │
       NO           YES
        │            │
    Free use    You must publish
    (no fee)    source code to
                your users
                (or get commercial license)
```

---

## Under AGPL v3 (FREE) — what you MAY do

1. **Use Adam Prism for any purpose** — personal, educational, research, internal
2. **Modify the source code** — change anything, add features, fix bugs
3. **Distribute your modifications** — share them with the world
4. **Run Adam Prism on your own server** — for yourself or your company
5. **Use Adam Prism internally at a company** — even a Fortune 500
6. **Fork the project** — create your own version under a different name
7. **Study how it works** — full source access, no obfuscation
8. **Use commercially INTERNALLY** — as long as you don't serve it externally
9. **Embed in non-distributed software** — e.g., a private tool at your company
10. **Contribute back** — submit PRs, translations, docs

## Under AGPL v3 (FREE) — what you MAY NOT do

1. **Serve Adam Prism as a SaaS to external users without publishing source** —
   this is the key AGPL requirement (Section 13: "Remote Network Interaction; Use
   with the GNU General Public License")
2. **Remove the copyright notice** — keep `Adam Prism © 2024-2026 Mohamed Othman`
3. **Remove the license text** — `LICENSE` must travel with the code
4. **Use the "Adam Prism" trademark** to endorse your fork without permission
5. **Sublicense under different terms** — AGPL is the license
6. **Hold the maintainer liable for damages** — no warranty (Section 15-16)
7. **Patent sue the maintainer** for using Adam Prism — patent grant applies (Section 11)
8. **Add further restrictions** — AGPL Section 7 forbids this

## Under AGPL v3 (FREE) — what you MUST do

1. **Provide source code** to anyone you distribute binaries to (Section 6)
2. **Provide source code to your users** if you serve it over a network
   (Section 13, the AGPL-specific requirement)
3. **License your modifications** under AGPL v3 too (copyleft)
4. **Retain all copyright notices** in all copies (Section 5)
5. **Document your modifications** — `Modified by ... on date ...`
6. **Include the LICENSE file** with any distribution
7. **Install "Installation Information"** if you modify the AGPL-covered
   portions of a "User Product" (Section 6, anti-Tivoization)

## What is "publishing source code" under AGPL?

When you serve Adam Prism as a SaaS, AGPL requires that you make the
"Corresponding Source" available to your users. This means:

- ✅ A public repo with the full server-side code (or a tarball)
- ✅ Written offer (email) to provide the source
- ✅ Source must be the same as what's running in production
- ❌ NOT acceptable: closed source with a "we'll give you the source on request"
- ❌ NOT acceptable: source only for the original unmodified parts

**Corresponding Source includes** (Section 1):
- All source code you used
- Build scripts, configs, installers
- Any libraries that "form a part of the work"
- Documentation needed to install and run

**Corresponding Source does NOT include**:
- Third-party system libraries (kernel, libc, etc.)
- Tools you didn't modify
- The LLM model weights (these are separately licensed)

---

## Under Commercial License — additional rights

If you purchase a commercial license (see `COMMERCIAL_LICENSE.md`), you additionally may:

1. **Serve Adam Prism as SaaS without source disclosure** to your users
2. **Embed Adam Prism in proprietary products**
3. **Modify without publishing modifications** (until license expires)
4. **Use the "Adam Prism" name and logo** for branding
5. **Distribute as part of a larger commercial product**
6. **Receive support, indemnification, and SLAs**

## Under Commercial License — restrictions still apply

1. **No redistribution of the commercial license** — it's between you and the maintainer
2. **No transfer to a third party** without written consent
3. **Tier limits** (MAU, revenue) — must upgrade if exceeded
4. **Termination on non-payment** — 30-day cure period
5. **Trademark guidelines** — must follow the style guide

---

## Contributions — what you agree to

By submitting a contribution (pull request, patch, code, docs, etc.)
to Adam Prism, you agree to:

1. **License your contribution** under AGPL v3, with the same terms as the work
2. **Grant a Contributor License Agreement (CLA)** to the maintainer, allowing:
   - Re-licensing for dual-licensing purposes
   - Inclusion in commercial products
3. **Confirm you have the right** to make the contribution (you wrote it,
   or your employer permitted it, or it's in the public domain)
4. **Not include any code you don't have rights to** — this includes
   proprietary snippets, leaked code, or unlicensed third-party code

We use the [Apache-style CLA](https://en.wikipedia.org/wiki/Contributor_License_Agreement)
(we'll provide a CLA.md when contributions start arriving).

---

## Trademark policy

The following are trademarks of Mohamed Othman and are **not** licensed
under AGPL v3:

- "Adam Prism" (word mark)
- "آدم المنظار" (Arabic word mark)
- The Adam Prism logo
- The "conscious digital twin" tagline
- The Adam Prism mascot / character

You may refer to Adam Prism in your documentation, blog posts, or
academic papers without permission, as long as:

- ✅ You use the name descriptively ("X uses Adam Prism under AGPL v3")
- ✅ You don't suggest endorsement ("Adam Prism recommends X")
- ✅ You don't use the logo in your product UI
- ❌ You don't create derivative product names ("Adam Prism Pro for Lawyers")
- ❌ You don't register a similar trademark

For commercial trademark licensing, see `COMMERCIAL_LICENSE.md`.

---

## AI training and ML use

Adam Prism's source code may be used for:

- ✅ **Fine-tuning other AI models** — you may train a model on Adam's code
- ✅ **Code completion / autocomplete** — IDE features are fine
- ❌ **Scraping for competitive training** — we can't enforce this, but it's
  ethically questionable to clone Adam's code and train a competing product
- ❌ **Reproducing the model weights** — the actual LoRA weights (1.1 GB)
  are separately licensed (commercial only)

The training data (2,317 conversations in the full version) is
**NOT** covered by AGPL v3. It is licensed separately:

- **Free**: You may generate your own training data via the reflection engine
- **Commercial**: You may purchase a license to the curated dataset

---

## Data protection (GDPR / CCPA)

If you operate Adam Prism with user data:

- ✅ You are the **data controller** — your users' data is yours
- ✅ AGPL v3 does NOT impose any data-handling restrictions
- ⚠️ You must still comply with GDPR, CCPA, HIPAA, etc. as applicable
- ⚠️ We provide no warranty that Adam Prism is GDPR-compliant "out of the box"
- 📋 See `SECURITY.md` for our security commitments
- 📋 See `docs/DISASTER_RECOVERY.md` for backup / retention practices

---

## Jurisdiction and dispute resolution

This license is governed by the laws of **Egypt** (the maintainer's jurisdiction),
without regard to conflict-of-laws principles. Disputes will be resolved:

1. **First** by direct negotiation (30 days)
2. **Then** by mediation in Cairo, Egypt
3. **Then** by arbitration under the ICC rules

Nothing in this section limits either party's right to seek injunctive
relief in court for IP infringement.

---

## Contact

**Maintainer:** Mohamed Othman
**Email:** othman@adam-prism.local
**GitHub:** https://github.com/othmastar

For:
- License questions → email subject "License: ..."
- Commercial license → email subject "Commercial: ..."
- Trademark → email subject "TM: ..."
- Security disclosure → email `security@adam-prism.local`

---

*Last updated: June 15, 2026 — Adam Prism v1.0.0b1*

This document is informational and does not replace the binding
LICENSE file. In case of conflict, the LICENSE file prevails.
