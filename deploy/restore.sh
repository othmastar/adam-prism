#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Adam Prism — Database Restore Script
# يستعيد نسخة احتياطية من:
#   1. Qdrant vector database
#   2. SQLite databases
#   3. Configuration
# ═══════════════════════════════════════════════════════════

set -e

# Configuration
BACKUP_DIR="${ADAM_BACKUP_DIR:-./backups}"
DATA_DIR="${ADAM_DATA_DIR:-./data}"
CONFIG_DIR="${ADAM_CONFIG_DIR:-./config}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[RESTORE]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check args
if [ -z "$1" ]; then
    err "Usage: $0 <backup_name_or_path>"
    err "Example: $0 adam_backup_20260101_120000"
    err "Or: $0 ./backups/adam_backup_20260101_120000/"
    echo
    log "Available backups:"
    ls -1 "$BACKUP_DIR" 2>/dev/null | grep "^adam_backup_" || echo "  (none found)"
    exit 1
fi

BACKUP_INPUT="$1"

# Handle different input formats
if [ -d "$BACKUP_INPUT" ]; then
    BACKUP_PATH="$BACKUP_INPUT"
elif [ -f "${BACKUP_INPUT}.tar.gz" ]; then
    log "Extracting ${BACKUP_INPUT}.tar.gz..."
    tar xzf "${BACKUP_INPUT}.tar.gz" -C "$BACKUP_DIR"
    BACKUP_PATH="$BACKUP_DIR/${BACKUP_INPUT}"
elif [ -f "$BACKUP_INPUT" ] && [[ "$BACKUP_INPUT" == *.tar.gz ]]; then
    BASE=$(basename "$BACKUP_INPUT" .tar.gz)
    log "Extracting $BACKUP_INPUT..."
    tar xzf "$BACKUP_INPUT" -C "$BACKUP_DIR"
    BACKUP_PATH="$BACKUP_DIR/$BASE"
else
    err "Backup not found: $BACKUP_INPUT"
    exit 1
fi

# Verify backup
if [ ! -f "$BACKUP_PATH/MANIFEST.txt" ]; then
    err "Invalid backup: MANIFEST.txt not found"
    exit 1
fi

log "Backup to restore: $BACKUP_PATH"
cat "$BACKUP_PATH/MANIFEST.txt" | head -10
echo

# Confirm
read -p "⚠️  This will OVERWRITE existing data. Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Restore cancelled"
    exit 0
fi

# Stop running services
log "Stopping Adam Prism services..."
docker compose stop api telegram-bot 2>/dev/null || warn "Could not stop services (not running via docker compose?)"

# 1. Restore Qdrant
if [ -d "$BACKUP_PATH/qdrant" ]; then
    log "Restoring Qdrant..."
    if docker ps -a | grep -q adam-qdrant; then
        docker cp "$BACKUP_PATH/qdrant/." adam-qdrant:/qdrant/storage/
        log "  ✓ Qdrant restored"
    else
        warn "Qdrant container not found, skipping"
    fi
fi

# 2. Restore SQLite databases
if [ -d "$BACKUP_PATH/sqlite" ]; then
    log "Restoring SQLite databases..."
    mkdir -p "$DATA_DIR"
    cp -r "$BACKUP_PATH/sqlite/"* "$DATA_DIR/" 2>/dev/null || true
    log "  ✓ SQLite restored"
fi

# 3. Restore configuration
if [ -d "$BACKUP_PATH/config" ]; then
    log "Restoring configuration..."
    mkdir -p "$CONFIG_DIR"
    cp -r "$BACKUP_PATH/config/"* "$CONFIG_DIR/" 2>/dev/null || true
    log "  ✓ Config restored"
fi

# 4. Restore notebook
if [ -d "$BACKUP_PATH/notebook" ]; then
    log "Restoring notebook..."
    mkdir -p "$DATA_DIR/notebook"
    cp -r "$BACKUP_PATH/notebook/"* "$DATA_DIR/notebook/" 2>/dev/null || true
    log "  ✓ Notebook restored"
fi

# 5. Restore skills
if [ -d "$BACKUP_PATH/skills" ]; then
    log "Restoring skills..."
    mkdir -p "$HOME/.adam/skills"
    cp -r "$BACKUP_PATH/skills/"* "$HOME/.adam/skills/" 2>/dev/null || true
    log "  ✓ Skills restored"
fi

# Restart services
log "Restarting services..."
docker compose start api telegram-bot 2>/dev/null || warn "Could not restart services"

echo
log "✅ Restore complete!"
log "   Please verify: docker compose logs -f api"
