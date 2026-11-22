"""
Source Code Backup Utility for EncroWatch AI.
Creates an archive of the application codebase, excluding node_modules, caches, and build artifacts.
"""

import os
import sys
import zipfile
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_ROOT = os.path.join(PROJECT_ROOT, "backups")

EXCLUDE_DIRS = {
    "node_modules",
    ".pytest_cache",
    "__pycache__",
    "dist",
    ".git",
    "backups"
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo"
}

def backup_source() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    zip_path = os.path.join(BACKUP_ROOT, f"encrowatch_source_backup_{timestamp}.zip")

    print("=" * 60)
    print("ENCROWATCH AI — SOURCE CODE ARCHIVE BACKUP")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Target Archive: {zip_path}")
    print("=" * 60)

    total_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in EXCLUDE_EXTENSIONS:
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                zf.write(full_path, arcname=rel_path)
                total_files += 1

    file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"SUCCESS: Archived {total_files} files into {zip_path} ({file_size_mb:.2f} MB)")
    print("=" * 60)
    return zip_path

if __name__ == "__main__":
    backup_source()
