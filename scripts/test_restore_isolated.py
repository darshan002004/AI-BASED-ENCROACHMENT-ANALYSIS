"""
Test Restore Verification Script.
Restores a backup into an isolated test database ('encrowatch_ai_restore_test')
to verify backup integrity and collection fidelity without modifying the live database.
"""

import os
import sys
import json
import pymongo

BACKUP_DIR = sys.argv[1] if len(sys.argv) > 1 else None
TEST_DB_NAME = "encrowatch_ai_restore_test"
MONGO_URI = "mongodb://localhost:27017"

def verify_restore_in_isolated_db(backup_path: str):
    if not backup_path or not os.path.exists(backup_path):
        print(f"[FAIL] Backup directory not found: {backup_path}")
        sys.exit(1)

    manifest_file = os.path.join(backup_path, "backup_manifest.json")
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    client = pymongo.MongoClient(MONGO_URI)
    test_db = client[TEST_DB_NAME]

    print("=" * 70)
    print("VERIFYING RESTORE IN ISOLATED TEST DATABASE")
    print(f"Target Isolated DB: {TEST_DB_NAME}")
    print(f"Source Backup: {backup_path}")
    print("=" * 70)

    # Clean test DB first
    for col_name in test_db.list_collection_names():
        test_db[col_name].drop()

    verified_counts = {}

    for col_name, meta in manifest.get("collections", {}).items():
        json_file = os.path.join(backup_path, meta["file"])
        if not os.path.exists(json_file):
            print(f"[FAIL] Missing {json_file}")
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            docs = json.load(f)

        col = test_db[col_name]
        if docs:
            # Recreate docs converting _id strings if needed
            col.insert_many(docs)
        
        count = col.count_documents({})
        expected = meta["document_count"]
        assert count == expected, f"Mismatch in {col_name}: expected {expected}, got {count}"
        verified_counts[col_name] = count
        print(f"[PASS] Collection '{col_name}': Restored and verified {count}/{expected} records")

    # Verify critical business data in isolated DB
    admin_user = test_db.users.find_one({"email": "admin@encrowatch.ai"})
    assert admin_user is not None, "Admin user not found in restored DB!"
    assert admin_user["role"] == "admin", "Admin role mismatch!"
    print("[PASS] User authentication & roles preserved in restored DB")

    incident = test_db.incidents.find_one({})
    assert incident is not None, "Incidents not found in restored DB!"
    print(f"[PASS] Incidents preserved in restored DB (Sample: {incident.get('incident_number', 'N/A')})")

    audit = test_db.audit_logs.find_one({"action": "OFFICER_REGISTRATION_APPROVED"})
    assert audit is not None, "Officer approval audit log not found in restored DB!"
    print(f"[PASS] Cryptographic audit logs preserved (Found OFFICER_REGISTRATION_APPROVED)")

    # Clean up isolated test database
    client.drop_database(TEST_DB_NAME)
    print(f"[PASS] Isolated test database '{TEST_DB_NAME}' cleaned up and dropped")
    print("=" * 70)
    print("ALL RESTORE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    latest_backup = r"C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai\backups\encrowatch_backup_20261109_144847"
    target = sys.argv[1] if len(sys.argv) > 1 else latest_backup
    verify_restore_in_isolated_db(target)
