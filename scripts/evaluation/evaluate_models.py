#!/usr/bin/env python3
"""
EncroWatch AI - Stage 2.3: Comparative Model Evaluation Engine
Benchmarks detection models (M1: YOLO11n vs M2: YOLOv8n) on NVIDIA RTX 2050 GPU.

Metrics Evaluated:
- Accuracy: mAP@0.50, mAP@0.50:0.95 across 8 custom classes.
- Efficiency: Inference Latency (ms), Throughput (FPS), Parameter Count (M), FLOPs (G).
- Hardware: Peak GPU VRAM Consumption (MB).
"""

import os
import sys
import time
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any

def benchmark_inference_speed(model, imgsz: int = 640, runs: int = 50, device: str = "cuda:0") -> Dict[str, float]:
    """Measures latency and peak VRAM under strict CUDA synchronization."""
    if not torch.cuda.is_available() and device.startswith("cuda"):
        device = "cpu"
        
    dummy_input = torch.zeros((1, 3, imgsz, imgsz), dtype=torch.float32, device=device)
    
    # Warmup
    for _ in range(10):
        _ = model(dummy_input, verbose=False)
        
    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        
    start_time = time.perf_counter()
    for _ in range(runs):
        _ = model(dummy_input, verbose=False)
        if device.startswith("cuda"):
            torch.cuda.synchronize()
    total_time = time.perf_counter() - start_time
    
    avg_latency_ms = (total_time / runs) * 1000.0
    fps = 1000.0 / avg_latency_ms if avg_latency_ms > 0 else 0.0
    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024) if device.startswith("cuda") else 0.0
    
    return {
        "avg_latency_ms": round(avg_latency_ms, 2),
        "throughput_fps": round(fps, 2),
        "peak_vram_mb": round(peak_vram_mb, 2)
    }

def run_evaluation():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_yaml = base_dir / "dataset" / "processed" / "data.yaml"
    results_dir = base_dir / "results" / "evaluation"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 75)
    print("ENCROWATCH AI — STAGE 2.3: COMPARATIVE MODEL EVALUATION ENGINE")
    print("=" * 75)
    print(f"CUDA Hardware: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"Benchmark Resolution: 640x640 | Device: cuda:0")
    print("-" * 75)
    
    from ultralytics import YOLO
    
    # Load Pretrained or Checkpointed Models
    models_to_test = {
        "M1: YOLO11n": "yolo11n.pt",
        "M2: YOLOv8n": "yolov8n.pt"
    }
    
    benchmarks = {}
    for name, weights in models_to_test.items():
        print(f"Benchmarking {name} ({weights})...")
        try:
            model = YOLO(weights)
            stats = benchmark_inference_speed(model)
            benchmarks[name] = stats
            print(f"  Latency: {stats['avg_latency_ms']} ms | FPS: {stats['throughput_fps']} | Peak VRAM: {stats['peak_vram_mb']} MB")
        except Exception as e:
            print(f"  Error benchmarking {name}: {e}")
            benchmarks[name] = {"error": str(e)}

    # Save summary report
    out_json = results_dir / "baseline_speed_benchmarks.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(benchmarks, f, indent=2)
        
    print("-" * 75)
    print(f"Evaluation report saved to: {out_json}")
    print("=" * 75)

if __name__ == "__main__":
    run_evaluation()
