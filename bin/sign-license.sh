#!/usr/bin/env bash
# Adam Prism — License Key Generator
# Generates a signed license key for a recipient.
#
# Usage:
#   bash bin/sign-license.sh <recipient-id> <tier> <duration-days>
#
# Example:
#   bash bin/sign-license.sh acme-corp enterprise 365
#
# Output:
#   recipients/<id>/license.key — signed license key (JSON)
#   recipients/<id>/license.key.pub — public key for verification

set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*" >&2; exit 1; }

command -v openssl >/dev/null 2>&1 || fail "openssl not found"

RECIPIENT="${1:-}"
TIER="${2:-}"
DAYS="${3:-365}"

[[ -z "$RECIPIENT" || -z "$TIER" ]] && fail "Usage: $0 <recipient-id> <tier> <days>"

# Tier validation
case "$TIER" in
    startup|growth|enterprise|custom|evaluation|none) ;;
    *) fail "Invalid tier. Must be: startup, growth, enterprise, custom, evaluation, or none" ;;
esac

RECIPIENT_DIR="recipients/${RECIPIENT}"
mkdir -p "$RECIPIENT_DIR"

# Generate maintainer's signing key (only once)
SIGNING_KEY="keys/maintainer-signing.pem"
if [[ ! -f "$SIGNING_KEY" ]]; then
    ok "generating maintainer signing key..."
    mkdir -p keys
    openssl genrsa -out "$SIGNING_KEY" 4096 2>/dev/null
    openssl rsa -in "$SIGNING_KEY" -pubout -out "${SIGNING_KEY}.pub" 2>/dev/null
fi

# Generate recipient-specific public key (id binding)
RECIPIENT_KEY="${RECIPIENT_DIR}/public.pem"
if [[ ! -f "$RECIPIENT_KEY" ]]; then
    ok "generating recipient public key..."
    openssl genrsa -out "${RECIPIENT_DIR}/private.pem" 4096 2>/dev/null
    openssl rsa -in "${RECIPIENT_DIR}/private.pem" -pubout -out "$RECIPIENT_KEY" 2>/dev/null
    chmod 600 "${RECIPIENT_DIR}/private.pem"
fi

# Build license payload
ISSUED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EXPIRES=$(date -u -d "+${DAYS} days" +%Y-%m-%dT%H:%M:%SZ)
LICENSE_ID="LIC-$(date +%Y%m%d)-$(openssl rand -hex 4)"

LICENSE=$(cat <<EOF
{
  "license_id": "${LICENSE_ID}",
  "recipient_id": "${RECIPIENT}",
  "tier": "${TIER}",
  "issued_at": "${ISSUED}",
  "expires_at": "${EXPIRES}",
  "product": "Adam Prism Full Version",
  "version": "1.0.0b1",
  "restrictions": {
    "redistribution": false,
    "modification": true,
    "commercial_use": $([ "$TIER" = "evaluation" ] && echo "false" || echo "true"),
    "saas": $([ "$TIER" = "enterprise" ] || [ "$TIER" = "growth" ] || [ "$TIER" = "startup" ] && echo "true" || echo "false"),
    "training_data": $([ "$TIER" = "enterprise" ] && echo "true" || echo "false"),
    "model_weights": $([ "$TIER" = "enterprise" ] && echo "true" || echo "false")
  },
  "limits": {
    "mau_max": $([ "$TIER" = "startup" ] && echo "100" || ([ "$TIER" = "growth" ] && echo "10000" || echo "-1")),
    "deployments_max": $([ "$TIER" = "startup" ] && echo "1" || ([ "$TIER" = "growth" ] && echo "5" || echo "-1"))
  }
}
EOF
)

LICENSE_FILE="${RECIPIENT_DIR}/license.key"
echo "$LICENSE" > "$LICENSE_FILE"

# Sign with the maintainer's private key
SIGNATURE=$(echo -n "$LICENSE" | openssl dgst -sha256 -sign "$SIGNING_KEY" | base64 -w 0)
{
    echo "$LICENSE"
    echo ""
    echo "-----BEGIN ADAM PRISM LICENSE SIGNATURE-----"
    echo "$SIGNATURE"
    echo "-----END ADAM PRISM LICENSE SIGNATURE-----"
} > "$LICENSE_FILE"

ok "license key generated"
ok "  License ID:  $LICENSE_ID"
ok "  Recipient:   $RECIPIENT"
ok "  Tier:        $TIER"
ok "  Issued:      $ISSUED"
ok "  Expires:     $EXPIRES"
ok "  File:        $LICENSE_FILE"
ok ""
ok "  Public verification key:  keys/maintainer-signing.pem.pub"
ok ""
ok "  Send $LICENSE_FILE to the recipient."
ok "  They can verify it with:"
ok "    bash bin/verify-license.sh $LICENSE_FILE"
