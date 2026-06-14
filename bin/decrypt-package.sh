#!/usr/bin/env bash
# Adam Prism — Package Decryption
# Decrypts a package that was created with encrypt-package.sh
#
# Usage:
#   bash bin/decrypt-package.sh path/to/package.tar.gz.enc
#
# Requires:
#   - The .enc file
#   - The symmetric key (sent separately)
#   - Your private RSA key (matching the public key used to encrypt)

set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*" >&2; exit 1; }

command -v openssl >/dev/null 2>&1 || fail "openssl not found"

INPUT="${1:-}"
[[ -z "$INPUT" ]] && fail "Usage: $0 <encrypted-package>"
[[ -f "$INPUT" ]] || fail "File not found: $INPUT"

# Determine recipient (from filename or env)
RECIPIENT_ID="${ADAM_RECIPIENT_ID:-$(basename "$INPUT" | grep -oP 'recipient-\K[a-z0-9-]+' || echo 'unknown')}"

# Find the private key
PRIVATE_KEY=""
for path in \
    "recipients/${RECIPIENT_ID}/private.pem" \
    "$HOME/.adam-prism/${RECIPIENT_ID}/private.pem" \
    "private.pem"; do
    if [[ -f "$path" ]]; then
        PRIVATE_KEY="$path"
        break
    fi
done

[[ -z "$PRIVATE_KEY" ]] && fail "Private key not found. Set ADAM_RECIPIENT_ID or place private.pem in recipients/<id>/"

# Find the symmetric key
SYMMETRIC_KEY=""
for path in \
    "keys/${RECIPIENT_ID}.key" \
    "$HOME/.adam-prism/keys/${RECIPIENT_ID}.key"; do
    if [[ -f "$path" ]]; then
        SYMMETRIC_KEY="$path"
        break
    fi
done

[[ -z "$SYMMETRIC_KEY" ]] && warn "Symmetric key not found in standard locations."
echo -n "Enter path to symmetric key file: "
read -r SYMMETRIC_KEY
[[ -f "$SYMMETRIC_KEY" ]] || fail "Key file not found: $SYMMETRIC_KEY"

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# The last part of the file is the encrypted symmetric key
# The structure is: [package.enc] [key.enc] [manifest text]
# We need to split. Simplest: find the boundary.
# Since manifest starts with "# ═══" we'll search backward.
PACKAGE_SIZE=$(stat -c%s "$INPUT" 2>/dev/null || stat -f%z "$INPUT")

# Find the manifest boundary (search for "# ═══")
# For simplicity, we just try to decrypt from the end backwards.
# The key.enc is 256 bytes (for 2048-bit RSA), so:
#   [package.enc ... package.enc (variable)] [key.enc (256 bytes)] [manifest]

# First pass: extract manifest text from end
ok "extracting manifest..."
# Find first occurrence of "# ═══" from end
awk '/^# ═══/{found=1; lines[NR]=$0; next} found{lines[NR]=$0} END{for(i=1;i<=NR;i++) if(i in lines) print lines[i]}' "$INPUT" > "${TMPDIR}/manifest.txt" 2>/dev/null || {
    # Fallback: just use the last 2KB as manifest
    tail -c 2000 "$INPUT" > "${TMPDIR}/manifest.txt"
}

cat "${TMPDIR}/manifest.txt"
echo

# The key.enc starts at PACKAGE_SIZE - 256 - manifest_size
# We need to compute manifest_size
MANIFEST_SIZE=$(wc -c < "${TMPDIR}/manifest.txt")
KEY_ENC_SIZE=256  # for 2048-bit RSA

# Calculate where the package ends
PACKAGE_END=$((PACKAGE_SIZE - MANIFEST_SIZE - KEY_ENC_SIZE))
KEY_ENC_START=$((PACKAGE_END + 1))
KEY_ENC_END=$((PACKAGE_END + KEY_ENC_SIZE))

ok "extracting package (offset 0 to ${PACKAGE_END}) and key (offset ${KEY_ENC_START} to ${KEY_ENC_END})..."
dd if="$INPUT" of="${TMPDIR}/package.enc" bs=1 count=$PACKAGE_END status=none
dd if="$INPUT" of="${TMPDIR}/key.enc" bs=1 skip=$PACKAGE_END count=$KEY_ENC_SIZE status=none

# Decrypt the symmetric key with the RSA private key
ok "decrypting symmetric key with RSA private key..."
openssl rsautl -decrypt -inkey "$PRIVATE_KEY" \
    -in "${TMPDIR}/key.enc" \
    -out "${TMPDIR}/key.bin" \
    || fail "RSA decryption failed (wrong private key?)"

# Decrypt the package with the symmetric key
ok "decrypting package with AES-256-CBC..."
openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 \
    -in "${TMPDIR}/package.enc" \
    -out "${TMPDIR}/package.tar.gz" \
    -pass file:"${TMPDIR}/key.bin"

# Extract
OUTPUT_DIR="${INPUT%.enc}"
mkdir -p "$OUTPUT_DIR"
ok "extracting to $OUTPUT_DIR..."
tar -xzf "${TMPDIR}/package.tar.gz" -C "$OUTPUT_DIR"

cat <<EOF

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
  ✓ Decryption complete
${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

  📂 Extracted to:  $OUTPUT_DIR

${YELLOW}Next steps:${NC}
  1. cd $OUTPUT_DIR
  2. Read LICENSE-PROPRIETARY.txt and SIGN the NDA if not already
  3. Run: bash bin/install-full.sh

${YELLOW}Restrictions:${NC}
  - DO NOT distribute the decrypted files to anyone
  - DO NOT push to any public Git repository
  - DO NOT use for commercial purposes without an explicit agreement
  - Contact othman@adam-prism.local for any questions

EOF
