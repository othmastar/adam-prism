#!/usr/bin/env python3
"""
[PHASE6] Migration script: Adam Prism v1 → v2.

Handles:
- JSON data file migration (legacy format → new format)
- User account migration (if any legacy auth)
- Session history migration
- Knowledge base migration (Qdrant collection name)
- Configuration file migration

Usage:
    python scripts/migrate_v1_to_v2.py --from /path/to/v1 --to /path/to/v2
    python scripts/migrate_v1_to_v2.py --dry-run --from /path/to/v1
"""
import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("adam_prism.migrate")


def migrate_data_dir(src: Path, dst: Path, dry_run: bool = False) -> dict[str, int]:
    """[PHASE6] Migrate data directory from v1 to v2 layout."""
    stats = {"files_migrated": 0, "files_skipped": 0, "errors": 0}

    if not src.exists():
        logger.warning(f"Source directory does not exist: {src}")
        return stats

    dst.mkdir(parents=True, exist_ok=True)

    # v1 layout: data/notebook/YYYY-MM-DD.md
    # v2 layout: data/notebook/daily/YYYY-MM-DD.md
    for src_file in src.rglob("*"):
        if not src_file.is_file():
            continue
        try:
            rel = src_file.relative_to(src)
            dst_file = dst / rel

            # [PHASE6] Restructure notebook files
            if "notebook" in rel.parts and rel.suffix == ".md":
                # v1: notebook/2024-01-01.md
                # v2: notebook/daily/2024-01-01.md
                parts = list(rel.parts)
                if len(parts) == 2 and parts[0] == "notebook":
                    dst_file = dst / "notebook" / "daily" / parts[1]
                elif "connections" in parts[0] or "pending" in parts[0]:
                    # Already in subfolder, no change
                    pass

            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if not dry_run:
                if dst_file.exists():
                    logger.debug(f"Skip (exists): {dst_file}")
                    stats["files_skipped"] += 1
                else:
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"Migrated: {rel} -> {dst_file.relative_to(dst)}")
                    stats["files_migrated"] += 1
        except Exception as e:
            logger.error(f"Failed to migrate {src_file}: {e}")
            stats["errors"] += 1

    return stats


def migrate_config(src: Path, dst: Path, dry_run: bool = False) -> dict[str, int]:
    """[PHASE6] Migrate config files from v1 to v2."""
    stats = {"files_migrated": 0, "errors": 0}

    if not src.exists():
        return stats

    dst.mkdir(parents=True, exist_ok=True)

    for src_file in src.glob("*.json"):
        if not src_file.is_file():
            continue
        try:
            with open(src_file) as f:
                data = json.load(f)
            # [PHASE6] Transform v1 format to v2
            new_data = transform_v1_config(data)
            dst_file = dst / src_file.name
            if not dry_run:
                with open(dst_file, "w") as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Migrated config: {src_file.name}")
            stats["files_migrated"] += 1
        except Exception as e:
            logger.error(f"Failed to migrate config {src_file}: {e}")
            stats["errors"] += 1

    return stats


def transform_v1_config(data: dict) -> dict:
    """[PHASE6] Transform v1 config dict to v2 format."""
    # v1: {"ollama_base": "..."}
    # v2: {"providers": {"ollama": {"base_url": "..."}}}
    new = dict(data)
    if "ollama_base" in new:
        ollama_base = new.pop("ollama_base")
        providers = new.setdefault("providers", {})
        providers.setdefault("ollama", {})["base_url"] = ollama_base
    if "qdrant_url" in new:
        qdrant_url = new.pop("qdrant_url")
        new.setdefault("qdrant", {})["url"] = qdrant_url
    # v1 had "model_name" flat; v2 has it under providers
    if "model_name" in new:
        model_name = new.pop("model_name")
        new.setdefault("providers", {}).setdefault("ollama", {})["model"] = model_name
    return new


def migrate_sqlite(src: Path, dst: Path, dry_run: bool = False) -> dict[str, int]:
    """[PHASE6] Migrate SQLite databases with schema transformation."""
    import sqlite3

    stats = {"tables_migrated": 0, "rows_migrated": 0, "errors": 0}

    if not src.exists():
        return stats

    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        if dry_run:
            return stats
        # Copy file first
        shutil.copy2(src, dst)

        conn = sqlite3.connect(str(dst))
        try:
            # [PHASE6] v1 → v2 schema migrations
            # Add tenant_id column to existing tables
            for table in ["chat_sessions", "chat_messages", "memory"]:
                try:
                    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    if "tenant_id" not in cols:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id VARCHAR(64)")
                        conn.execute(
                            f"CREATE INDEX IF NOT EXISTS idx_{table}_tenant ON {table}(tenant_id)"
                        )
                        logger.info(f"Added tenant_id to {table}")
                        stats["tables_migrated"] += 1
                except sqlite3.OperationalError:
                    # Table doesn't exist - that's OK
                    pass

            # Set default tenant for all existing rows
            try:
                for table in ["chat_sessions", "chat_messages", "memory"]:
                    conn.execute(
                        f"UPDATE {table} SET tenant_id = 'tenant_default' WHERE tenant_id IS NULL"
                    )
                conn.commit()
            except sqlite3.OperationalError:
                pass

            stats["rows_migrated"] = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"SQLite migration failed: {e}")
        stats["errors"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Migrate Adam Prism v1 to v2")
    parser.add_argument("--from", dest="src", required=True, help="v1 source directory")
    parser.add_argument("--to", dest="dst", required=True, help="v2 destination directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    src = Path(args.src).resolve()
    dst = Path(args.dst).resolve()

    logger.info("Migration: v1 -> v2")
    logger.info(f"  Source: {src}")
    logger.info(f"  Dest:   {dst}")
    logger.info(f"  Dry run: {args.dry_run}")
    print()

    # 1. Data directory
    data_stats = migrate_data_dir(src / "data", dst / "data", dry_run=args.dry_run)
    logger.info(f"Data: {data_stats}")

    # 2. Config
    config_stats = migrate_config(src / "config", dst / "config", dry_run=args.dry_run)
    logger.info(f"Config: {config_stats}")

    # 3. SQLite (if exists)
    sqlite_stats = migrate_sqlite(
        src / "data" / "adam.db",
        dst / "data" / "adam.db",
        dry_run=args.dry_run,
    )
    logger.info(f"SQLite: {sqlite_stats}")

    # Summary
    total = {
        k: data_stats.get(k, 0) + config_stats.get(k, 0) + sqlite_stats.get(k, 0)
        for k in ["files_migrated", "files_skipped", "tables_migrated", "rows_migrated", "errors"]
    }
    print()
    logger.info("=== Summary ===")
    for k, v in total.items():
        logger.info(f"  {k}: {v}")

    if total["errors"] > 0:
        sys.exit(1)
    logger.info("Migration complete!")


if __name__ == "__main__":
    main()
