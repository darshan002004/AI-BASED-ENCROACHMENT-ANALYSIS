"""
Database Restore Utility for EncroWatch AI.
Restores collections from a timestamped backup directory into MongoDB (or local fallback).
Includes pre-flight checks and requires explicit user confirmation.
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import db_manager
from app.config import settings

async def restore_database(source_dir: str, force: bool = False):
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Backup directory not found: {source_dir}")

    manifest_file = os.path.join(source_dir, "backup_manifest.json")
    if not os.path.exists(manifest_file):
        raise FileNotFoundError(f"Missing backup_manifest.json in {source_dir}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("=" * 60)
    print("ENCROWATCH AI — DATABASE RESTORE PROCEDURE")
    print(f"Source Directory: {source_dir}")
    print(f"Backup Created At: {manifest.get('timestamp')}")
    print(f"Original Database: {manifest.get('database_name')}")
    print("=" * 60)

    if not force:
        confirm = input("CAUTION: This will overwrite/restore collections. Type 'YES' to proceed: ")
        if confirm != "YES":
            print("Restore aborted by operator.")
            return

    await db_manager.connect()
    print(f"Connected to database (Mode: {db_manager.mode})")

    for col_name, meta in manifest.get("collections", {}).items():
        json_file = os.path.join(source_dir, meta["file"])
        if not os.path.exists(json_file):
            print(f"  [WARN] File {json_file} missing, skipping collection '{col_name}'")
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            docs = json.load(f)

        col = db_manager.get_collection(col_name)
        # Drop or clear existing collection before restoring
        await col.delete_many({})
        if docs:
            await col.insert_many(docs)
        print(f"  [RESTORE] Restored {len(docs)} documents into collection '{col_name}'")

    await db_manager.close()
    print("=" * 60)
    print("SUCCESS: Database restore completed.")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_database.py <backup_directory_path> [--force]")
        sys.exit(1)
    src = sys.argv[1]
    is_force = "--force" in sys.argv
    asyncio.run(restore_database(src, force=is_force))
