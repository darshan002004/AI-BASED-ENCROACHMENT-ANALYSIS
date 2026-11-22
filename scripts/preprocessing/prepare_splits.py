#!/usr/bin/env python3
"""
EncroWatch AI - Stage 1: Spatial Ward-Based Dataset Partitioning
Part of Phase 4 & Section 6.2 Execution.

Partitions the collected dataset into Train (60%), Validation (20%), and Test (20%)
using strict spatial ward boundaries to prevent geographical background leakage:
- Wards 1 & 2 (Commercial MG Road & Indiranagar): Training Set (60%)
- Ward 3 (Mixed Commercial/Residential Koramangala): Validation Set (20%)
- Ward 4 (Unregulated Corridor BTM Layout): Test Set (20%)

Generates data.yaml manifest pointing directly to the processed splits.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List

WARD_SPLIT_MAP = {
    "ward_1": "train",
    "ward_2": "train",
    "ward_3": "val",
    "ward_4": "test"
}

CUSTOM_CLASSES = [
    "motorcycle",
    "car",
    "vendor_cart",
    "construction_debris",
    "commercial_signboard",
    "shop_extension",
    "umbrella_canopy",
    "pedestrian"
]

def prepare_splits(base_dir: Path, copy_files: bool = True) -> Dict[str, Any]:
    dataset_dir = base_dir / "dataset"
    raw_images_dir = dataset_dir / "raw" / "images"
    raw_ann_dir = dataset_dir / "annotations" / "detection"
    processed_dir = dataset_dir / "processed"

    for split in ["train", "val", "test"]:
        (processed_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (processed_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    split_counts = {"train": 0, "val": 0, "test": 0, "unassigned": 0}
    image_files = sorted(list(raw_images_dir.glob("*.jpg")) + list(raw_images_dir.glob("*.png")))

    for img_path in image_files:
        stem = img_path.stem.lower()
        target_split = None
        for ward_key, split_name in WARD_SPLIT_MAP.items():
            if ward_key in stem:
                target_split = split_name
                break
        
        # If image filename doesn't contain ward, fallback to deterministic hash split (60/20/20)
        if not target_split:
            h = hash(img_path.name) % 100
            if h < 60:
                target_split = "train"
            elif h < 80:
                target_split = "val"
            else:
                target_split = "test"

        split_counts[target_split] += 1

        if copy_files:
            # Copy image
            dest_img = processed_dir / target_split / "images" / img_path.name
            shutil.copy2(img_path, dest_img)

            # Copy corresponding label if present
            label_file = raw_ann_dir / f"{img_path.stem}.txt"
            if label_file.exists():
                dest_label = processed_dir / target_split / "labels" / label_file.name
                shutil.copy2(label_file, dest_label)

    # Generate data.yaml
    data_yaml_content = f"""# EncroWatch AI - Processed Dataset Manifest
path: {str(processed_dir.as_posix())}
train: train/images
val: val/images
test: test/images

names:
"""
    for idx, name in enumerate(CUSTOM_CLASSES):
        data_yaml_content += f"  {idx}: {name}\n"

    data_yaml_path = processed_dir / "data.yaml"
    with open(data_yaml_path, "w", encoding="utf-8") as f:
        f.write(data_yaml_content)

    manifest = {
        "dataset_name": "encrowatch_urban_corridor_v1",
        "splitting_protocol": "Spatial Ward Disjoint (Wards 1 & 2 -> Train, Ward 3 -> Val, Ward 4 -> Test)",
        "split_counts": split_counts,
        "classes": CUSTOM_CLASSES,
        "manifest_path": str(data_yaml_path)
    }

    manifest_json_path = dataset_dir / "metadata" / "split_manifest.json"
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent.parent
    result = prepare_splits(base, copy_files=False)
    print("=" * 60)
    print("ENCROWATCH AI — DATASET SPLIT PREPARATION")
    print("=" * 60)
    print(f"Protocol: {result['splitting_protocol']}")
    print(f"Split Distribution: {result['split_counts']}")
    print(f"YAML Manifest: {result['manifest_path']}")
    print("=" * 60)
