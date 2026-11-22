"""
Database Backup Utility for EncroWatch AI.
Safely exports all collections from MongoDB (or local fallback) into a timestamped backup directory.
Preserves user accounts, incident history, audit trails, and model configurations.
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

BACKUP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backups"))

async def backup_database(destination_dir: str = None) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    target_dir = destination_dir or os.path.join(BACKUP_ROOT, f"encrowatch_backup_{timestamp}")
    os.makedirs(target_dir, exist_ok=True)

    await db_manager.connect()
    print("=" * 60)
    print("ENCROWATCH AI — DATABASE BACKUP PROCEDURE")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Database Mode: {db_manager.mode}")
    print(f"Target Directory: {target_dir}")
    print("=" * 60)

    collections = [
        "users",
        "incidents",
        "audit_logs",
        "ai_feedback_dataset",
        "service_feedback",
        "model_evaluations",
        "model_registry",
        "notifications",
        "sla_rules"
    ]

    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database_name": settings.DATABASE_NAME,
        "database_mode": db_manager.mode,
        "collections": {}
    }

    for col_name in collections:
        col = db_manager.get_collection(col_name)
        docs = await col.find({}).to_list(100000)
        
        # Strip internal MongoDB ObjectID into string representation for clean serialization
        clean_docs = []
        for d in docs:
            d_copy = dict(d)
            if "_id" in d_copy:
                d_copy["_id"] = str(d_copy["_id"])
            clean_docs.append(d_copy)

        output_file = os.path.join(target_dir, f"{col_name}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(clean_docs, f, indent=2, default=str)

        manifest["collections"][col_name] = {
            "document_count": len(clean_docs),
            "file": f"{col_name}.json"
        }
        print(f"  [BACKUP] Collection '{col_name}': {len(clean_docs)} records saved to {col_name}.json")

    manifest_file = os.path.join(target_dir, "backup_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    await db_manager.close()
    print("=" * 60)
    print(f"SUCCESS: Database backup completed successfully at:\n{target_dir}")
    print("=" * 60)
    return target_dir

if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(backup_database(dest))
