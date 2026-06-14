#!/bin/bash
# Nginx entrypoint - dynamically configure HTTPS if SSL certs exist

set -e

SSL_DIR="/etc/nginx/ssl"
CERT_FILE="$SSL_DIR/adam-prism.crt"
KEY_FILE="$SSL_DIR/adam-prism.key"
NGINX_CONF="/etc/nginx/nginx.conf"
NGINX_CONF_HTTPS="/etc/nginx/nginx-https.conf"

# If SSL certs exist, generate HTTPS config and include it
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates found - enabling HTTPS"

    cat > "$NGINX_CONF_HTTPS" << 'EOF'
# ─── HTTPS server (production) ─────────────────────────────
server {
    listen 443 ssl;
    server_name _;

    # [M14] TLS configuration
    ssl_certificate     /etc/nginx/ssl/adam-prism.crt;
    ssl_certificate_key /etc/nginx/ssl/adam-prism.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;

    # Static files للـ Web UI
    location /_next/static {
        proxy_pass http://web_upstream;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    location /static {
        proxy_pass http://web_upstream;
        expires 30d;
    }

    # API reverse proxy — [M13] with rate limiting
    location /api/ {
        limit_req zone=adam_api burst=60 nodelay;
        limit_req_status 429;

        proxy_pass http://api_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket للـ chat — [M13] with rate limiting
    location /ws/ {
        limit_req zone=adam_ws burst=20 nodelay;

        proxy_pass http://api_upstream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
    }

    # SSE stream
    location /api/engine/stream {
        proxy_pass http://api_upstream;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding on;
        proxy_read_timeout 86400s;
    }

    # Health endpoint
    location /api/engine/health {
        proxy_pass http://api_upstream;
    }

    # WhatsApp webhook (POST + GET للتأكيد)
    location /webhook/whatsapp {
        proxy_pass http://api_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # باقي المسارات → Web UI
    location / {
        proxy_pass http://web_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    access_log /var/log/nginx/adam-prism-access.log;
    error_log /var/log/nginx/adam-prism-error.log;
}
EOF

    # Include HTTPS config in main nginx.conf
    echo "include $NGINX_CONF_HTTPS;" >> "$NGINX_CONF"
else
    echo "SSL certificates not found - running HTTP only (development mode)"
    echo "To enable HTTPS, run: ./deploy/generate_ssl.sh"
fi

# Start nginx
exec nginx -g "daemon off;"