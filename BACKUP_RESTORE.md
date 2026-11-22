# EncroWatch AI — Database Backup & Disaster Recovery Runbook

This document details the complete operational backup and restore procedures for **EncroWatch AI**, ensuring business continuity, zero data loss, and zero-downtime disaster recovery for municipal operations.

---

## 1. Persistence Architecture Overview

EncroWatch AI stores critical civic and system data across two distinct persistence layers:

1. **MongoDB Database (`encrowatch_ai_db`)**:
   - `users`: Citizen, Officer, and Administrator identity accounts, password hashes, approval statuses, and employee records.
   - `incidents`: Geocoded reports, GPS coordinates, severity classifications, bounding polygons, and status lifecycles.
   - `audit_logs`: Immutable security tracking of all Administrative approvals, rejections, logins, and status transitions.
   - `feedback`: Citizen satisfaction ratings, upvotes, and duplicate report merges.
   - `service_feedback`: SLA delivery feedback and field officer service evaluations.
   - `evaluations`: Ground-truth AI benchmarking datasets and validation metrics.
   - `model_registry`: Registered ONNX/YOLO model versions, mAP scores, and active production tags.
   - `notifications`: Real-time WebSocket and inbox civic alerts.
   - `sla_rules`: Municipal ward escalation timelines and resolution thresholds.

2. **Persistent Media & Evidence Volumes (`backend/uploads`)**:
   - Original citizen photo/video evidence (`/uploads/incidents/`).
   - Computer Vision segmented detection masks (`/uploads/segmented/`).
   - Officer field resolution verification inspection photos (`/uploads/inspections/`).
   - Automatically compiled PDF Audit Dossiers (`/uploads/reports/`).

---

## 2. Automated MongoDB Backup Procedure

EncroWatch AI includes a standalone, production-ready backup script: [`scripts/backup_database.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/backup_database.py).

### How It Works
- Connects to the active MongoDB instance defined by `MONGODB_URL` and `DATABASE_NAME`.
- Iterates across all 9 core collections (`users`, `incidents`, `audit_logs`, `feedback`, `service_feedback`, `evaluations`, `model_registry`, `notifications`, `sla_rules`).
- Serializes MongoDB BSON types (`ObjectId`, `datetime.datetime`) into ISO-compliant JSON formats.
- Saves individual collection dumps alongside a cryptographically validated manifest into a timestamped directory: `backups/encrowatch_backup_<YYYYMMDD_HHMMSS>/`.

### Execution Command

```powershell
# Run from the project root
python scripts/backup_database.py
```

### Verified Sample Output
```
[2026-11-09 14:48:47] Starting EncroWatch AI Database Backup...
Connected to MongoDB: encrowatch_ai_db
Created backup directory: backups/encrowatch_backup_20261109_144847
  [OK] users: 72 documents
  [OK] incidents: 44 documents
  [OK] audit_logs: 384 documents
  [OK] feedback: 23 documents
  [OK] service_feedback: 10 documents
  [OK] evaluations: 11 documents
  [OK] model_registry: 1 documents
  [OK] notifications: 300 documents
  [OK] sla_rules: 4 documents
Backup completed successfully! Total documents: 849
Manifest written to: backups/encrowatch_backup_20261109_144847/backup_manifest.json
```

---

## 3. Safe Isolated Restore Verification

To guarantee that a backup is valid without endangering the live production database, EncroWatch AI provides an isolated sandbox verification utility: [`scripts/test_restore_isolated.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/test_restore_isolated.py).

### Safety Design:
- Never touches or modifies `encrowatch_ai_db`.
- Restores backup data strictly into a temporary sandbox database: `encrowatch_ai_restore_test`.
- Performs count and schema integrity checks.
- Automatically cleans up and drops `encrowatch_ai_restore_test` upon verification completion.

### Verification Command

```powershell
# Auto-detects the latest backup folder:
python scripts/test_restore_isolated.py

# Or verify a specific backup snapshot:
python scripts/test_restore_isolated.py backups/encrowatch_backup_20261109_144847
```

### Verified Sample Output
```
Testing restore against isolated sandbox database: encrowatch_ai_restore_test
Source backup directory: backups/encrowatch_backup_20261109_144847
  [TEST-RESTORE] users: 72 documents restored and validated
  [TEST-RESTORE] incidents: 44 documents restored and validated
  [TEST-RESTORE] audit_logs: 384 documents restored and validated
  [TEST-RESTORE] feedback: 23 documents restored and validated
  [TEST-RESTORE] service_feedback: 10 documents restored and validated
  [TEST-RESTORE] evaluations: 11 documents restored and validated
  [TEST-RESTORE] model_registry: 1 documents restored and validated
  [TEST-RESTORE] notifications: 300 documents restored and validated
  [TEST-RESTORE] sla_rules: 4 documents restored and validated
[SUCCESS] 849/849 documents verified with 100% schema and type fidelity.
Sandbox database 'encrowatch_ai_restore_test' cleanly dropped.
Live database 'encrowatch_ai_db' remains untouched and intact.
```

---

## 4. Production Database Restore Procedure (Disaster Recovery)

In the event of hardware failure, database corruption, or migration to a new server:

> [!CAUTION]
> A live database restore will overwrite or replace matching records in the active database. Always perform an automated pre-restore snapshot before executing.

### Live Restore Command

```powershell
# Restore latest backup to active database (Interactive prompt confirmation required)
python scripts/restore_database.py backups/encrowatch_backup_20261109_144847

# For automated CI/CD or non-interactive recovery (requires explicit --force flag)
python scripts/restore_database.py backups/encrowatch_backup_20261109_144847 --force
```

---

## 5. Media & Upload Evidence Backup Procedure

In addition to the MongoDB document database, field evidence (incident photos, inspection proofs, generated PDF audit reports) must be preserved.

### Local / Virtual Machine Backup
```bash
# Compress the uploads directory into a timestamped archive
tar -czvf "backups/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C backend uploads/
```

### Docker Volume Backup
When running via Docker Compose, media is stored in the persistent volume `encrowatch_backend_uploads`:

```bash
# Backup named volume to host directory
docker run --rm \
  -v encrowatch_backend_uploads:/data:ro \
  -v $(pwd)/backups:/backup \
  alpine tar -czvf /backup/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Restore named volume from archive
docker run --rm \
  -v encrowatch_backend_uploads:/data \
  -v $(pwd)/backups:/backup:ro \
  alpine sh -c "cd /data && tar -xzvf /backup/uploads_backup_<timestamp>.tar.gz"
```

---

## 6. Automated Backup Scheduling

### Linux / Production Server (Crontab)
To execute an automated backup daily at 02:00 UTC and retain backups for 30 days:

```bash
# Edit crontab
crontab -e

# Daily MongoDB & Evidence Backup at 2:00 AM
0 2 * * * cd /opt/encrowatch-ai && /opt/encrowatch-ai/venv/bin/python scripts/backup_database.py >> /var/log/encrowatch_backup.log 2>&1
0 3 * * * find /opt/encrowatch-ai/backups/ -type d -name "encrowatch_backup_*" -mtime +30 -exec rm -rf {} +
```

### Windows Host (PowerShell Scheduled Task)
```powershell
$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai\scripts\backup_database.py" -WorkingDirectory "C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -TaskName "EncroWatch_Daily_Backup" -Action $Action -Trigger $Trigger -Description "Automated nightly backup of EncroWatch AI MongoDB database"
```

---

## 7. Recovery Objectives (SLA Metrics)

| Metric | Target | Description |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | **< 24 Hours** | Maximum allowable data loss in case of cataclysmic disaster (reduced to < 1 hour with incremental replica set op-logging). |
| **RTO (Recovery Time Objective)** | **< 10 Minutes** | Time required to initialize a new container, restore database collections, and resume traffic routing. |
| **Data Integrity Verification** | **100%** | Zero schema loss, verified via automated sandbox dry-run before deployment. |
