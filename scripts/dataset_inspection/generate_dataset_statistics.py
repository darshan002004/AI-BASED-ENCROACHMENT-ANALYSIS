#!/usr/bin/env python3
"""
EncroWatch AI - Stage 2: Comprehensive Dataset Statistics Generator
Inspects images across raw, pilot, processed, and synthetic fixtures.
Generates ENCROWATCH_DATASET_STATISTICS.csv and detailed metrics.
"""

import os
import sys
import csv
import json
from pathlib import Path
from PIL import Image

def analyze_dataset():
    base_dir = Path(__file__).resolve().parent.parent.parent
    pilot_manifest_path = base_dir / "ENCROWATCH_PILOT_ANNOTATION_MANIFEST.csv"
    synthetic_dir = base_dir / "dataset" / "fixtures" / "synthetic_smoke_test"
    output_csv = base_dir / "ENCROWATCH_DATASET_STATISTICS.csv"
    
    print("=" * 70)
    print("ENCROWATCH AI — STAGE 2 DATASET STATISTICS AUDIT")
    print("=" * 70)
    
    records = []
    
    # 1. Audit Pilot Candidates
    if pilot_manifest_path.exists():
        with open(pilot_manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_path = base_dir / row["relative_path"]
                exists = img_path.exists()
                valid = False
                actual_w, actual_h, mode = 0, 0, "N/A"
                if exists:
                    try:
                        with Image.open(img_path) as im:
                            im.verify()
                        with Image.open(img_path) as im:
                            actual_w, actual_h = im.size
                            mode = im.mode
                            valid = True
                    except Exception as e:
                        valid = False
                
                records.append({
                    "item_id": row["pilot_id"],
                    "dataset_category": "Pilot Legacy Candidate (Awaiting Field/Human Annotation)",
                    "filename": row["filename"],
                    "relative_path": row["relative_path"],
                    "split": row["split"],
                    "assigned_ward": row["assigned_ward"],
                    "file_exists": exists,
                    "is_readable_pil": valid,
                    "width": actual_w if valid else row.get("width", 0),
                    "height": actual_h if valid else row.get("height", 0),
                    "color_channels": mode,
                    "file_size_kb": row.get("size_kb", 0),
                    "overlay_detected": row.get("is_overlay_annotated", "False"),
                    "annotation_status": row.get("annotation_status", "AWAITING"),
                    "provenance": row.get("provenance", "Legacy")
                })
                
    # 2. Audit Synthetic Disposable Fixture (Stage 1.3)
    if synthetic_dir.exists():
        for split in ["train", "val"]:
            img_dir = synthetic_dir / "images" / split
            lbl_dir = synthetic_dir / "labels" / split
            if img_dir.exists():
                for img_file in sorted(img_dir.glob("*.jpg")):
                    lbl_file = lbl_dir / f"{img_file.stem}.txt"
                    lbl_count = 0
                    if lbl_file.exists():
                        with open(lbl_file, "r") as lf:
                            lbl_count = len([l for l in lf.readlines() if l.strip()])
                    
                    with Image.open(img_file) as im:
                        w, h = im.size
                        m = im.mode
                    
                    records.append({
                        "item_id": f"SYNTH_{img_file.stem.upper()}",
                        "dataset_category": "Synthetic Disposable Fixture (Stage 1.3 Smoke Test Only)",
                        "filename": img_file.name,
                        "relative_path": str(img_file.relative_to(base_dir)).replace("\\", "/"),
                        "split": split,
                        "assigned_ward": "Synthetic Quarantined Sandbox",
                        "file_exists": True,
                        "is_readable_pil": True,
                        "width": w,
                        "height": h,
                        "color_channels": m,
                        "file_size_kb": round(img_file.stat().st_size / 1024, 2),
                        "overlay_detected": "False",
                        "annotation_status": f"SYNTHETIC_SMOKE_FIXTURE ({lbl_count} boxes)",
                        "provenance": "Synthetic Automated Generator (Isolated)"
                    })

    # Save to CSV
    fieldnames = [
        "item_id", "dataset_category", "filename", "relative_path", "split",
        "assigned_ward", "file_exists", "is_readable_pil", "width", "height",
        "color_channels", "file_size_kb", "overlay_detected", "annotation_status", "provenance"
    ]
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Dataset statistics generated: {len(records)} items audited.")
    print(f"Saved to: {output_csv}")
    
    # Calculate summary distributions
    pilot_records = [r for r in records if "Pilot" in r["dataset_category"]]
    synth_records = [r for r in records if "Synthetic" in r["dataset_category"]]
    
    print("\nPILOT CANDIDATES BREAKDOWN (N=42):")
    print(f"  Total readable: {sum(1 for r in pilot_records if r['is_readable_pil'])} / {len(pilot_records)}")
    splits = {}
    for r in pilot_records:
        splits[r["split"]] = splits.get(r["split"], 0) + 1
    print(f"  Split counts: {splits}")
    
    print("\nSYNTHETIC FIXTURE BREAKDOWN (N=12):")
    print(f"  Total readable: {sum(1 for r in synth_records if r['is_readable_pil'])} / {len(synth_records)}")
    synth_splits = {}
    for r in synth_records:
        synth_splits[r["split"]] = synth_splits.get(r["split"], 0) + 1
    print(f"  Split counts: {synth_splits}")
    print("=" * 70)

if __name__ == "__main__":
    analyze_dataset()
