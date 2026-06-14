#!/usr/bin/env bash
# Adam Prism — License Key Verifier
# Verifies a license.key file against the maintainer's public key.
#
# Usage:
#   bash bin/verify-license.sh path/to/license.key

set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*"; }

INPUT="${1:-}"
[[ -z "$INPUT" ]] && fail "Usage: $0 <license.key>"
[[ -f "$INPUT" ]] || fail "File not found: $INPUT"

PUB_KEY="keys/maintainer-signing.pem.pub"
[[ -f "$PUB_KEY" ]] || fail "Public key not found: $PUB_KEY"

# Extract signature and payload
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

awk '/-----BEGIN ADAM PRISM LICENSE SIGNATURE-----/{exit} {print}' "$INPUT" > "${TMPDIR}/payload.txt"
awk '/-----BEGIN ADAM PRISM LICENSE SIGNATURE-----/{flag=1; next} /-----END ADAM PRISM LICENSE SIGNATURE-----/{flag=0} flag' "$INPUT" | tr -d '\n' | base64 -d > "${TMPDIR}/signature.bin"

# Verify
ok "verifying signature..."
if openssl dgst -sha256 -verify "$PUB_KEY" -signature "${TMPDIR}/signature.bin" "${TMPDIR}/payload.txt" >/dev/null 2>&1; then
    ok "✓ Signature is VALID"
else
    fail "✗ Signature is INVALID (file may be tampered with)"
fi

# Parse and display
echo
ok "License contents:"
cat "${TMPDIR}/payload.txt"
echo
echo

# Check expiration
EXPIRES=$(grep -oP '"expires_at":\s*"\K[^"]+' "${TMPDIR}/payload.txt" || echo "")
if [[ -n "$EXPIRES" ]]; then
    NOW_EPOCH=$(date +%s)
    EXPIRES_EPOCH=$(date -d "$EXPIRES" +%s 2>/dev/null || echo 0)
    if [[ $EXPIRES_EPOCH -lt $NOW_EPOCH ]]; then
        warn "✗ License has EXPIRED ($EXPIRES)"
    else
        DAYS_LEFT=$(( (EXPIRES_EPOCH - NOW_EPOCH) / 86400 ))
        ok "✓ License is valid for $DAYS_LEFT more days"
    fi
fi
