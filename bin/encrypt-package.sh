#!/usr/bin/env bash
# Adam Prism — Package Encryption
# Encrypts the FULL version (main branch) for distribution to
# selected developers with signed NDA.
#
# Usage:
#   bash bin/encrypt-package.sh
#
# Output:
#   dist/adam-prism-full-YYYYMMDD.tar.gz.enc
#   dist/adam-prism-full-YYYYMMDD.sha256
#
# The .enc file is encrypted with AES-256-CBC.
# The key is sent separately (via a different channel — e.g. encrypted email).
#
# Requirements:
#   - openssl
#   - Recipient's RSA public key (in recipients/<id>/public.pem)

set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*" >&2; exit 1; }

command -v openssl >/dev/null 2>&1 || fail "openssl not found"

DIST_DIR="dist"
RECIPIENT="${1:-}"
[[ -z "$RECIPIENT" ]] && fail "Usage: $0 <recipient-id>"

RECIPIENT_DIR="recipients/${RECIPIENT}"
[[ -d "$RECIPIENT_DIR" ]] || fail "Recipient dir not found: $RECIPIENT_DIR"
[[ -f "${RECIPIENT_DIR}/public.pem" ]] || fail "Public key not found: ${RECIPIENT_DIR}/public.pem"

DATE=$(date +%Y%m%d)
OUTPUT="${DIST_DIR}/adam-prism-full-${DATE}.tar.gz.enc"
SHA_OUTPUT="${DIST_DIR}/adam-prism-full-${DATE}.sha256"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

mkdir -p "$DIST_DIR"

ok "creating tarball (excluding ignored files)..."

# Create tar.gz from the LOCAL main branch (NOT from git tracking)
# We use git archive to get a clean snapshot of the main branch
git archive main --format=tar.gz --output="${TMPDIR}/package.tar.gz" 2>/dev/null \
    || tar -czf "${TMPDIR}/package.tar.gz" \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.pytest_cache' \
        --exclude='.ruff_cache' \
        --exclude='*.pyc' \
        --exclude='*.log' \
        --exclude='docker-data' \
        --exclude='build' \
        --exclude='dist' \
        --exclude='.env' \
        --exclude='.env.*' \
        --exclude='*.egg-info' \
        --exclude='.mypy_cache' \
        .

PACKAGE_SIZE=$(du -h "${TMPDIR}/package.tar.gz" | cut -f1)
ok "tarball created: $PACKAGE_SIZE"

# Generate a random symmetric key (32 bytes = 256 bits)
SYMMETRIC_KEY="${TMPDIR}/key.bin"
openssl rand 32 > "$SYMMETRIC_KEY"

# Encrypt the package with the symmetric key (AES-256-CBC)
ok "encrypting with AES-256-CBC..."
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
    -in "${TMPDIR}/package.tar.gz" \
    -out "${TMPDIR}/package.enc" \
    -pass file:"$SYMMETRIC_KEY"

# Encrypt the symmetric key with the recipient's RSA public key
ok "encrypting symmetric key with recipient's RSA public key..."
openssl rsautl -encrypt -pubin -inkey "${RECIPIENT_DIR}/public.pem" \
    -in "$SYMMETRIC_KEY" \
    -out "${TMPDIR}/key.enc"

# Combine: package.enc + key.enc + manifest
cat "${TMPDIR}/package.enc" "${TMPDIR}/key.enc" > "$OUTPUT"
# Add a JSON manifest at the end (with size info)
{
    echo ""
    echo "# ════════════════════════════════════════════════════════════════"
    echo "# Adam Prism — Full Version Distribution Package"
    echo "# Recipient:    ${RECIPIENT}"
    echo "# Date:         $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# Package SHA:  $(sha256sum "${TMPDIR}/package.tar.gz" | cut -d' ' -f1)"
    echo "# Key SHA:      $(sha256sum "$SYMMETRIC_KEY" | cut -d' ' -f1)"
    echo "# Version:      $(git describe --tags 2>/dev/null || echo '1.0.0b1-main')"
    echo "# License:      PROPRIETARY — All rights reserved"
    echo "# ════════════════════════════════════════════════════════════════"
} >> "$OUTPUT"

# Generate standalone SHA-256
sha256sum "$OUTPUT" > "$SHA_OUTPUT"

# Compute and show recipient-readable fingerprint
FINGERPRINT=$(openssl pkey -in "${RECIPIENT_DIR}/public.pem" -pubin -outform DER 2>/dev/null \
    | sha256sum | cut -d' ' -f1 | head -c 16)

# Output summary
cat <<EOF

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
  Encrypted package ready
${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

  📦 Package:     $OUTPUT
  🔐 SHA-256:     $(cat "$SHA_OUTPUT" | cut -d' ' -f1)
  👤 Recipient:   $RECIPIENT (key fingerprint: ${FINGERPRINT}…)
  📅 Date:        $(date -u +%Y-%m-%dT%H:%M:%SZ)
  📜 License:     PROPRIETARY (All rights reserved)

${YELLOW}Next steps:${NC}
  1. Send the .enc file to ${RECIPIENT} via:
     - Secure file transfer (e.g., Tresorit, Keybase)
     - Or split into chunks via email

  2. Send the decryption passphrase (or symmetric key) via:
     - DIFFERENT channel (phone call, in-person, Signal, etc.)
     - NOT in the same email as the .enc file

  3. Recipient runs:
     \$ bash bin/decrypt-package.sh ${OUTPUT}

${YELLOW}Security notes:${NC}
  - Keep the .enc file in a secure location
  - Delete the file from your local disk after sending
  - Track distribution in recipients/${RECIPIENT}/distribution.log

EOF

# Log the distribution
LOG_FILE="${RECIPIENT_DIR}/distribution.log"
mkdir -p "${RECIPIENT_DIR}"
{
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] PACKAGED $OUTPUT"
    echo "  SHA: $(sha256sum "$OUTPUT" | cut -d' ' -f1)"
    echo "  Package size: $(du -h "$OUTPUT" | cut -f1)"
    echo "  Version: $(git describe --tags 2>/dev/null || echo '1.0.0b1-main')"
} >> "$LOG_FILE"

ok "distribution logged to $LOG_FILE"
