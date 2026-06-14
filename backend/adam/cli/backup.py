#!/usr/bin/env python
"""Adam Prism — Backup & Restore CLI.

Usage:
    # Create a full backup (data + config + DB)
    python -m adam.cli.backup create --output ./backups/adam-2026-06-14.tar.gz

    # Restore
    python -m adam.cli.backup restore --input ./backups/adam-2026-06-14.tar.gz

    # List what's in a backup
    python -m adam.cli.backup list --input ./backups/adam-2026-06-14.tar.gz

    # Verify integrity
    python -m adam.cli.backup verify --input ./backups/adam-2026-06-14.tar.gz
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, UTC
from pathlib import Path


def _hash_file(p: Path) -> str:
    """SHA-256 of a file (streaming)."""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _default_roots() -> dict[str, Path]:
    """Find the directories worth backing up, relative to CWD or env ADAM_ROOT."""
    root = Path(os.getenv("ADAM_ROOT", "."))
    return {
        "data": root / "data",
        "notebook": root / "data" / "notebook",
        "config": root / "backend" / ".env",
        "database": root / "data" / "adam.db",
        "qdrant_snapshot": root / "data" / "qdrant",
    }


def _collect(roots: dict[str, Path]) -> list[tuple[Path, str]]:
    """Collect all files to back up, skipping huge / irrelevant paths."""
    skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".next", "build", "dist"}
    items: list[tuple[Path, str]] = []
    for label, p in roots.items():
        if not p.exists():
            continue
        if p.is_file():
            items.append((p, label))
            continue
        for path in p.rglob("*"):
            if path.is_dir():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            rel = path.relative_to(p.parent)
            items.append((path, str(rel)))
    return items


def _make_manifest(items: list[tuple[Path, str]], backup_path: Path) -> dict:
    """Build a manifest with file hashes for verification."""
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "adam_version": "1.0.0b1",
        "file_count": len(items),
        "total_bytes": 0,
        "files": [],
    }
    for path, rel in items:
        try:
            size = path.stat().st_size
            sha = _hash_file(path) if size < 1 << 26 else None  # Hash only files <64MB
            manifest["total_bytes"] += size
            manifest["files"].append({
                "path": rel,
                "size": size,
                "sha256": sha,
            })
        except OSError:
            pass
    return manifest


def create(output: Path, compress: bool = True) -> None:
    """Create a backup archive at `output`."""
    output.parent.mkdir(parents=True, exist_ok=True)
    roots = _default_roots()
    items = _collect(roots)
    if not items:
        print("[backup] nothing to back up (no data files found)", file=sys.stderr)
        sys.exit(1)

    manifest = _make_manifest(items, output)
    mode = "w:gz" if compress else "w"
    with tarfile.open(output, mode) as tar:
        for path, rel in items:
            tar.add(path, arcname=f"files/{rel}")
        # Manifest goes last
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            tmp = f.name
        tar.add(tmp, arcname="manifest.json")
        os.unlink(tmp)

    print(f"[backup] ✓ created {output} ({manifest['file_count']} files, "
          f"{manifest['total_bytes'] / (1 << 20):.1f} MB)")


def restore(input_path: Path, target: Path = Path("."), dry_run: bool = False) -> None:
    """Restore from a backup archive."""
    if not input_path.exists():
        print(f"[restore] ✗ {input_path} not found", file=sys.stderr)
        sys.exit(1)
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    with tarfile.open(input_path, "r:*") as tar:
        # Check manifest first
        try:
            manifest_member = tar.getmember("manifest.json")
            manifest_file = tar.extractfile(manifest_member)
            manifest = json.load(manifest_file) if manifest_file else {}
            print(f"[restore] backup from {manifest.get('created_at', 'unknown')}, "
                  f"{manifest.get('file_count', '?')} files")
        except KeyError:
            print("[restore] ✗ no manifest in backup — aborting", file=sys.stderr)
            sys.exit(1)

        members = [m for m in tar.getmembers() if m.name.startswith("files/")]
        for m in members:
            rel = m.name[len("files/"):]
            dest = target / rel
            print(f"  {'[dry-run] ' if dry_run else ''}restore {dest}")
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                f = tar.extractfile(m)
                if f:
                    with open(dest, "wb") as out:
                        shutil.copyfileobj(f, out)

    print(f"[restore] ✓ {'verified' if dry_run else 'restored'} {len(members)} files")


def list_files(input_path: Path) -> None:
    """List contents of a backup."""
    with tarfile.open(input_path, "r:*") as tar:
        try:
            mf = tar.getmember("manifest.json")
            manifest = json.load(tar.extractfile(mf))
        except KeyError:
            print("[list] no manifest in backup", file=sys.stderr)
            sys.exit(1)
        print(f"Backup created: {manifest.get('created_at')}")
        print(f"Adam version:   {manifest.get('adam_version')}")
        print(f"Files:          {manifest.get('file_count')}")
        print(f"Total size:     {manifest.get('total_bytes', 0) / (1 << 20):.2f} MB")
        print()
        print("Contents (first 20):")
        for entry in manifest.get("files", [])[:20]:
            size = entry.get("size", 0)
            print(f"  {entry['path']:50s} {size:>10,d} bytes")
        if len(manifest.get("files", [])) > 20:
            print(f"  …and {len(manifest['files']) - 20} more")


def verify(input_path: Path) -> None:
    """Verify a backup's integrity (re-hashes and compares with manifest)."""
    with tarfile.open(input_path, "r:*") as tar:
        try:
            mf = tar.getmember("manifest.json")
            manifest = json.load(tar.extractfile(mf))
        except KeyError:
            print("[verify] ✗ no manifest in backup", file=sys.stderr)
            sys.exit(1)

        ok = 0
        failed = 0
        skipped = 0
        for entry in manifest.get("files", []):
            expected_sha = entry.get("sha256")
            if not expected_sha:
                skipped += 1
                continue
            try:
                member = tar.getmember(f"files/{entry['path']}")
            except KeyError:
                failed += 1
                continue
            f = tar.extractfile(member)
            if not f:
                failed += 1
                continue
            h = hashlib.sha256()
            for chunk in iter(lambda: f.read(1 << 20), b""):  # noqa: B023
                h.update(chunk)
            if h.hexdigest() == expected_sha:
                ok += 1
            else:
                failed += 1
                print(f"  [verify] ✗ MISMATCH {entry['path']}")

        total = ok + failed + skipped
        print(f"[verify] {ok}/{total} files OK, {failed} failed, {skipped} skipped (>64MB)")
        sys.exit(0 if failed == 0 else 2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Adam Prism backup & restore")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create a backup")
    p_create.add_argument("--output", "-o", type=Path, required=True)
    p_create.add_argument("--no-compress", action="store_true")

    p_restore = sub.add_parser("restore", help="Restore from backup")
    p_restore.add_argument("--input", "-i", type=Path, required=True)
    p_restore.add_argument("--target", type=Path, default=Path("."))
    p_restore.add_argument("--dry-run", action="store_true")

    p_list = sub.add_parser("list", help="List backup contents")
    p_list.add_argument("--input", "-i", type=Path, required=True)

    p_verify = sub.add_parser("verify", help="Verify backup integrity")
    p_verify.add_argument("--input", "-i", type=Path, required=True)

    args = parser.parse_args()
    if args.cmd == "create":
        create(args.output, not args.no_compress)
    elif args.cmd == "restore":
        restore(args.input, args.target, args.dry_run)
    elif args.cmd == "list":
        list_files(args.input)
    elif args.cmd == "verify":
        verify(args.input)


if __name__ == "__main__":
    main()
