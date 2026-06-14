#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Adam Prism — Database Backup Script
# ينشئ نسخة احتياطية من:
#   1. Qdrant vector database
#   2. SQLite databases (memory, chat history, etc.)
#   3. Adam configuration
# ═══════════════════════════════════════════════════════════

set -e

# Configuration
BACKUP_DIR="${ADAM_BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="adam_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
RETENTION_DAYS="${ADAM_BACKUP_RETENTION:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[BACKUP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check dependencies
command -v docker >/dev/null 2>&1 || { err "docker required"; exit 1; }
command -v tar >/dev/null 2>&1 || { err "tar required"; exit 1; }

# Create backup directory
mkdir -p "$BACKUP_PATH"
log "Backup directory: $BACKUP_PATH"

# 1. Backup Qdrant
log "Backing up Qdrant..."
if docker ps | grep -q adam-qdrant; then
    docker exec adam-qdrant tar cf - /qdrant/storage 2>/dev/null | tar xf - -C "$BACKUP_PATH/qdrant" 2>/dev/null || \
    docker cp adam-qdrant:/qdrant/storage "$BACKUP_PATH/qdrant" 2>/dev/null || \
    warn "Qdrant backup skipped (container or volume issue)"
    log "Qdrant backup complete"
else
    warn "Qdrant container not running, skipping"
fi

# 2. Backup SQLite databases
log "Backing up SQLite databases..."
DATA_DIR="${ADAM_DATA_DIR:-./data}"
if [ -d "$DATA_DIR" ]; then
    find "$DATA_DIR" -name "*.db" -o -name "*.sqlite*" 2>/dev/null | while read -r db; do
        rel_path="${db#$DATA_DIR/}"
        target_dir="$BACKUP_PATH/sqlite/$(dirname "$rel_path")"
        mkdir -p "$target_dir"
        # Use sqlite3 .backup for safe online backup
        if command -v sqlite3 >/dev/null 2>&1; then
            sqlite3 "$db" ".backup '$BACKUP_PATH/sqlite/$rel_path'"
        else
            cp "$db" "$BACKUP_PATH/sqlite/$rel_path"
        fi
        log "  ✓ $rel_path"
    done
else
    warn "Data directory not found: $DATA_DIR"
fi

# 3. Backup configuration
log "Backing up configuration..."
CONFIG_DIR="${ADAM_CONFIG_DIR:-./config}"
if [ -d "$CONFIG_DIR" ]; then
    cp -r "$CONFIG_DIR" "$BACKUP_PATH/config"
    log "  ✓ config/"
fi

# Backup notebook
if [ -d "$DATA_DIR/notebook" ]; then
    cp -r "$DATA_DIR/notebook" "$BACKUP_PATH/notebook"
    log "  ✓ notebook/"
fi

# 4. Backup custom skills
SKILLS_DIR="${HOME}/.adam/skills"
if [ -d "$SKILLS_DIR" ]; then
    cp -r "$SKILLS_DIR" "$BACKUP_PATH/skills"
    log "  ✓ skills/"
fi

# 5. Create manifest
log "Creating manifest..."
cat > "$BACKUP_PATH/MANIFEST.txt" << EOF
Adam Prism Backup Manifest
═══════════════════════════
Timestamp: ${TIMESTAMP}
Hostname: $(hostname)
Adam version: $(cat VERSION 2>/dev/null || echo "unknown")

Contents:
$(find "$BACKUP_PATH" -type f | sed "s|$BACKUP_PATH/||" | sort)

Restore instructions: see deploy/RESTORE.md
EOF

# 6. Compress
log "Compressing backup..."
tar czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
BACKUP_SIZE=$(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)
log "Backup size: $BACKUP_SIZE"

# 7. Cleanup
rm -rf "$BACKUP_PATH"
log "Removed uncompressed backup"

# 8. Retention
log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "adam_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(find "$BACKUP_DIR" -name "adam_backup_*.tar.gz" | wc -l)
log "Backups remaining: $REMAINING"

echo
log "✅ Backup complete: ${BACKUP_PATH}.tar.gz"
log "   To restore: tar xzf ${BACKUP_PATH}.tar.gz && ./deploy/restore.sh ${BACKUP_NAME}/"
