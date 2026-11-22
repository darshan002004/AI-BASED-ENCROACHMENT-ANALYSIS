#!/usr/bin/env python3
"""
EncroWatch AI - Stage 2.2: Baseline M2 (YOLOv8n) Training Engine
Executes training of the secondary benchmark baseline detector on NVIDIA RTX 2050 GPU.

Hyperparameter Profile:
- Architecture: YOLOv8n (3.2M parameters)
- Image Resolution: 640x640
- Batch Size: 4 (Optimized for 4 GB VRAM)
- Mixed Precision (AMP): FP16 enabled
- Hardware Acceleration: cuda:0
- Epochs: 50
- Optimizer: AdamW (lr0=0.001, lrf=0.01, weight_decay=0.0005)
"""

import os
import sys
import argparse
import torch
from pathlib import Path

def train_m2(override_check: bool = False):
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_yaml = base_dir / "dataset" / "processed" / "data.yaml"
    train_img_dir = base_dir / "dataset" / "processed" / "train" / "images"
    train_lbl_dir = base_dir / "dataset" / "processed" / "train" / "labels"
    output_dir = base_dir / "experiments" / "models" / "m2_yolov8n"
    
    print("=" * 75)
    print("ENCROWATCH AI — STAGE 2.2: BASELINE M2 (YOLOv8n) TRAINING PIPELINE")
    print("=" * 75)
    print(f"CUDA Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU (WARNING)'}")
    print(f"Dataset Manifest: {data_yaml}")
    print(f"Output Directory: {output_dir}")
    print("-" * 75)

    # 1. Dataset Readiness Validation Gate
    train_images = list(train_img_dir.glob("*.*")) if train_img_dir.exists() else []
    train_labels = list(train_lbl_dir.glob("*.txt")) if train_lbl_dir.exists() else []
    
    print(f"Dataset Status Check:")
    print(f"  Training Images Found: {len(train_images)}")
    print(f"  Training Labels Found: {len(train_labels)}")

    if (len(train_images) < 20 or len(train_labels) < 20) and not override_check:
        print("\n[ACADEMIC TRAINING HOLD ENFORCED]")
        print("  Scientific Justification: Training a deep 8-class detector on an empty or")
        print("  insufficient dataset (<20 images) will cause gradient collapse and model divergence.")
        print("  Status: Awaiting human annotations from CVAT (Stage 1.5).")
        print("  To bypass this check for testing, pass: --override_check")
        print("=" * 75)
        sys.exit(2)

    # 2. Launch Ultralytics YOLOv8n Training
    from ultralytics import YOLO
    
    print("\nInitializing YOLOv8n architecture...")
    model = YOLO("yolov8n.pt")
    
    print("Launching GPU Training on RTX 2050 (cuda:0)...")
    results = model.train(
        data=str(data_yaml),
        epochs=50,
        imgsz=640,
        batch=2,  # Empirically profiled safe bound for RTX 2050 4GB (54.25% VRAM vs 111.24% at B=4)
        device=0 if torch.cuda.is_available() else "cpu",
        amp=True,
        workers=2,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        project=str(output_dir.parent),
        name=output_dir.name,
        exist_ok=True,
        verbose=True
    )
    
    print("\n" + "=" * 75)
    print(f"TRAINING COMPLETE. Checkpoints saved to: {output_dir / 'weights'}")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EncroWatch AI M2 YOLOv8n Training")
    parser.add_argument("--override_check", action="store_true", help="Override dataset validation gate for debugging")
    args = parser.parse_args()
    train_m2(override_check=args.override_check)
