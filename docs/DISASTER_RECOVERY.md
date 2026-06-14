# Disaster Recovery Runbook

This document covers how to recover Adam Prism from the most common
disaster scenarios. Every operator should read it once.

## RTO / RPO targets

| Tier | RTO (downtime) | RPO (data loss) | Strategy |
|---|---|---|---|
| **Single-node (dev)** | 30 min | 1 hour | Local backup + rebuild |
| **Multi-node (prod)** | 5 min | 1 min | Hot standby + streaming replication |
| **Multi-region** | 30 sec | 0 | Active-active + CRDT |

## Backup strategy

### Daily full backup
```bash
# Cron at 02:00 UTC
0 2 * * * cd /opt/adam-prism && python -m adam.cli.backup create \
    --output /var/backups/adam/$(date +\%Y\%m\%d).tar.gz
```

### Hourly incremental (Qdrant)
```bash
0 * * * * curl -X POST http://qdrant:6333/collections/adam/snapshots
```

### Retention
- Daily backups: 30 days
- Weekly backups: 12 weeks
- Monthly backups: 12 months (encrypted, offsite)

## Disaster scenarios

### 1. Database corruption

**Symptoms:** `sqlite3.DatabaseError`, `relation does not exist`, etc.

**Recovery:**
```bash
# 1. Stop the API
docker compose -f deploy/docker-compose.yml stop api

# 2. Restore from latest backup
python -m adam.cli.backup restore --input /var/backups/adam/latest.tar.gz

# 3. Verify
python -m adam.cli.backup verify --input /var/backups/adam/latest.tar.gz

# 4. Restart
docker compose -f deploy/docker-compose.yml start api
```

**RTO:** 5-10 min
**RPO:** Up to 1 hour (last full backup)

### 2. Qdrant vector store lost

**Symptoms:** `Connection refused :6333`, `Collection not found`

**Recovery:**
```bash
# 1. Re-create collection
curl -X PUT http://qdrant:6333/collections/adam \
    -H "Content-Type: application/json" \
    -d @deploy/qdrant/schema.json

# 2. Re-index from knowledge base
docker exec adam-api python -c "
from adam.knowledge import rebuild_index
rebuild_index()
print('Reindex done')
"
```

**RTO:** 15-60 min (depends on corpus size)
**RPO:** Last successful snapshot

### 3. Complete node loss

**Symptoms:** Server is unreachable, hardware failure

**Recovery:**
```bash
# 1. Provision new node (same OS, Docker installed)
# 2. Restore from offsite backup
scp backup-server:/backups/adam/latest.tar.gz /tmp/
tar -xzf /tmp/latest.tar.gz -C /opt/adam-prism/

# 3. Start stack
cd /opt/adam-prism && docker compose -f deploy/docker-compose.yml up -d

# 4. Update DNS / load balancer
```

**RTO:** 30-60 min
**RPO:** Up to 1 day (depending on offsite backup cadence)

### 4. Security breach (RCE / data exfil)

**Steps:**
1. **Isolate** — `docker compose stop api web-ui` (preserve evidence)
2. **Snapshot** — copy `data/`, logs, `docker inspect` output to a secure location
3. **Rotate secrets** — generate new `ADAM_API_KEY`, JWT secret, DB passwords
4. **Audit logs** — `tail -1000 data/audit.log | grep -i "exfil\|unauthorized\|escalation"`
5. **Notify** — per your data breach policy (GDPR: 72 hours)
6. **Restore** — from clean backup (not the compromised one)
7. **Post-mortem** — within 7 days

### 5. Ollama model gone / corrupted

**Symptoms:** `model not found`, `inference timeout`

**Recovery:**
```bash
# Re-pull the model
docker exec adam-ollama ollama pull qwen2.5:3b

# Or restore from model cache backup
rsync -av /var/cache/ollama/ root@new-server:/var/cache/ollama/
```

**RTO:** 5-30 min (depends on bandwidth)

## Testing the plan

**Quarterly drill (every 3 months):**
1. Spin up a fresh VM
2. Restore from last week's backup
3. Run smoke tests: `pytest tests/integration/ -q`
4. Time it. Update RTO numbers.
5. Document in `docs/drills/YYYY-Q1.md`

## Monitoring

- **Backup success** — alert if no new backup file in 26 hours
- **Backup size** — alert if size drops >50% (might mean partial backup)
- **Replication lag** — alert if >60 seconds
- **Disk space** — alert if backup volume <20% free

## Contacts

| Role | Contact | Backup |
|---|---|---|
| On-call engineer | PagerDuty | +1-555-0100 |
| Security team | security@ | sec-team@ |
| Management | CTO | deputy-cto@ |

## Related docs

- `CHANGELOG.md` — what changed in each release
- `SECURITY.md` — disclosure policy
- `TROUBLESHOOTING.md` — common issues
- `bin/install.sh` — clean install procedure
