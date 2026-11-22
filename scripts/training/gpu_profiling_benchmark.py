#!/usr/bin/env python3
"""
EncroWatch AI - Stage 3.2: GPU Memory Profiling & Training Readiness Benchmark
Executes hardware profiling on the discrete NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM).
Measures:
1. PyTorch Allocated Memory (MB)
2. PyTorch Reserved Memory (MB)
3. Peak Forward/Backward Memory at Batch Sizes B=1, B=2, B=4
4. CUDA Synchronization Timing for FP16 AMP operations
Outputs results to results/evaluation/gpu_profiling_benchmark.json.
"""

import os
import sys
import time
import json
import torch
import torch.nn as nn
from pathlib import Path

def profile_gpu():
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_dir = base_dir / "results" / "evaluation"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_json = results_dir / "gpu_profiling_benchmark.json"
    
    print("=" * 80)
    print("ENCROWATCH AI — STAGE 3.2 GPU MEMORY & LATENCY PROFILER")
    print("=" * 80)
    
    if not torch.cuda.is_available():
        print("ERROR: CUDA is not available. Discrete GPU required.")
        sys.exit(1)
        
    device = torch.device("cuda:0")
    device_name = torch.cuda.get_device_name(0)
    total_vram_mb = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024), 2)
    
    print(f"CUDA Device:           {device_name}")
    print(f"Total Dedicated VRAM:  {total_vram_mb} MB")
    print(f"CUDA Driver Runtime:   {torch.version.cuda}")
    print(f"PyTorch Version:       {torch.__version__}")
    print("-" * 80)
    
    # Simple simulated convolutional block representing YOLO11 / YOLOv8 backbone stages
    class ConvStage(nn.Module):
        def __init__(self, in_c, out_c):
            super().__init__()
            self.conv = nn.Conv2d(in_c, out_c, kernel_size=3, padding=1, bias=False)
            self.bn = nn.BatchNorm2d(out_c)
            self.act = nn.SiLU()
        def forward(self, x):
            return self.act(self.bn(self.conv(x)))

    model = nn.Sequential(
        ConvStage(3, 64),
        ConvStage(64, 128),
        nn.MaxPool2d(2),
        ConvStage(128, 256),
        nn.MaxPool2d(2),
        ConvStage(256, 512),
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
        nn.Linear(512, 8)  # 8 classes
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda")
    
    batch_sizes = [1, 2, 4]
    profiles = {}
    
    for b in batch_sizes:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        
        # Simulated 640x640 input batch
        inputs = torch.randn(b, 3, 640, 640, device=device)
        targets = torch.randint(0, 8, (b,), device=device)
        
        # Warmup
        for _ in range(3):
            with torch.amp.autocast("cuda"):
                out = model(inputs)
                loss = criterion(out, targets)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
        torch.cuda.synchronize()
        
        # Benchmark measurement
        torch.cuda.reset_peak_memory_stats()
        start_time = time.perf_counter()
        
        with torch.amp.autocast("cuda"):
            out = model(inputs)
            loss = criterion(out, targets)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()
        torch.cuda.synchronize()
        
        step_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        peak_allocated_mb = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)
        peak_reserved_mb = round(torch.cuda.max_memory_reserved() / (1024 * 1024), 2)
        vram_headroom_mb = round(total_vram_mb - peak_reserved_mb, 2)
        safety_ratio = round((peak_reserved_mb / total_vram_mb) * 100.0, 2)
        
        profiles[f"batch_{b}"] = {
            "batch_size": b,
            "step_time_ms": step_time_ms,
            "peak_allocated_mb": peak_allocated_mb,
            "peak_reserved_mb": peak_reserved_mb,
            "vram_headroom_mb": vram_headroom_mb,
            "vram_utilization_pct": safety_ratio,
            "safety_verdict": "SAFE (< 75% VRAM)" if safety_ratio < 75.0 else "RISK_OF_OOM"
        }
        
        print(f"Batch B={b}: Step={step_time_ms} ms | Allocated={peak_allocated_mb} MB | Reserved={peak_reserved_mb} MB | Utilization={safety_ratio}% ({profiles[f'batch_{b}']['safety_verdict']})")

    results = {
        "hardware_metadata": {
            "device": device_name,
            "total_vram_mb": total_vram_mb,
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
            "amp_fp16": True
        },
        "profiles": profiles
    }
    
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("-" * 80)
    print(f"Profiling report saved to: {out_json}")
    print("=" * 80)

if __name__ == "__main__":
    profile_gpu()
