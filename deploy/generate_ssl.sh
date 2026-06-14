#!/bin/bash
# Generate self-signed SSL certificates for nginx
# Usage: ./generate_ssl.sh

set -e

SSL_DIR="./ssl"
mkdir -p "$SSL_DIR"

CERT_FILE="$SSL_DIR/adam-prism.crt"
KEY_FILE="$SSL_DIR/adam-prism.key"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates already exist at $SSL_DIR"
    exit 0
fi

echo "Generating self-signed SSL certificates..."

# Generate private key
openssl genrsa -out "$KEY_FILE" 2048

# Generate certificate signing request
openssl req -new -key "$KEY_FILE" -out "$SSL_DIR/adam-prism.csr" -subj "/C=EG/ST=Cairo/L=Cairo/O=Adam Prism/OU=IT/CN=localhost"

# Generate self-signed certificate valid for 365 days
openssl x509 -req -in "$SSL_DIR/adam-prism.csr" -signkey "$KEY_FILE" -out "$CERT_FILE" -days 365 -sha256

# Set permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

# Clean up CSR
rm -f "$SSL_DIR/adam-prism.csr"

echo "SSL certificates generated at $SSL_DIR"
echo "Certificate: $CERT_FILE"
echo "Key: $KEY_FILE"