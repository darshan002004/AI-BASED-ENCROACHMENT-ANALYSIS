#!/usr/bin/env python3
"""
EncroWatch AI - Stage 1.1: GPU Environment Verification & Inference Smoke Test
Part of Task A & Task D Execution.

Verifies:
- torch & torchvision versions
- torch.cuda.is_available(), device name, VRAM
- CUDA tensor allocation & matrix multiplication computation
- YOLO nano model GPU inference at imgsz=640, batch=1, FP16
- Peak VRAM tracking and latency measurement
- Exports results to dataset/reports/gpu_smoke_test_report.json
"""

import sys
import os
import time
import json
from pathlib import Path

def test_cuda_tensor():
    import torch
    print("--- CUDA Tensor Allocation & Math Test ---")
    if not torch.cuda.is_available():
        return {"cuda_available": False, "error": "torch.cuda.is_available() is False"}

    device = torch.device("cuda:0")
    device_name = torch.cuda.get_device_name(0)
    total_mem_bytes = torch.cuda.get_device_properties(0).total_memory
    total_mem_mb = round(total_mem_bytes / (1024 ** 2), 2)
    
    # 1. Allocate FP32 tensor
    mem_before = torch.cuda.memory_allocated(0)
    a = torch.randn(1024, 1024, device=device, dtype=torch.float32)
    b = torch.randn(1024, 1024, device=device, dtype=torch.float32)
    c = torch.matmul(a, b)
    torch.cuda.synchronize()
    
    # 2. Allocate FP16 tensor
    a_fp16 = torch.randn(2048, 2048, device=device, dtype=torch.float16)
    b_fp16 = torch.randn(2048, 2048, device=device, dtype=torch.float16)
    c_fp16 = torch.matmul(a_fp16, b_fp16)
    torch.cuda.synchronize()
    
    mem_peak = torch.cuda.max_memory_allocated(0)
    peak_mb = round(mem_peak / (1024 ** 2), 2)
    
    # Cleanup
    del a, b, c, a_fp16, b_fp16, c_fp16
    torch.cuda.empty_cache()

    print(f"Device: {device_name}")
    print(f"Total VRAM: {total_mem_mb} MB")
    print(f"CUDA Computation: SUCCESS (FP32 & FP16 GEMM passed)")
    print(f"Peak VRAM during matrix math: {peak_mb} MB")

    return {
        "cuda_available": True,
        "device_name": device_name,
        "total_vram_mb": total_mem_mb,
        "cuda_version_torch": torch.version.cuda,
        "tensor_computation_success": True,
        "peak_tensor_vram_mb": peak_mb
    }

def run_yolo_smoke_test(image_path: Path):
    import torch
    from ultralytics import YOLO

    print("\n--- YOLO Nano GPU Inference Smoke Test (Task D) ---")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Target Device: {device}")
    print(f"Test Image: {image_path}")

    # Load YOLO11n or YOLOv8n
    model_name = "yolo11n.pt"
    print(f"Loading {model_name}...")
    t0 = time.time()
    model = YOLO(model_name)
    load_time_sec = round(time.time() - t0, 3)

    torch.cuda.reset_peak_memory_stats(0)
    mem_start = torch.cuda.memory_allocated(0)

    # Warmup pass
    _ = model.predict(source=str(image_path), imgsz=640, device=device, half=True, verbose=False)
    torch.cuda.synchronize()

    # Timed inference pass (imgsz 640, batch 1, FP16 half precision)
    t_inf_start = time.time()
    results = model.predict(
        source=str(image_path),
        imgsz=640,
        batch=1,
        device=device,
        half=True,
        verbose=False
    )
    torch.cuda.synchronize()
    inf_latency_ms = round((time.time() - t_inf_start) * 1000, 2)

    peak_vram_bytes = torch.cuda.max_memory_allocated(0)
    peak_vram_mb = round(peak_vram_bytes / (1024 ** 2), 2)

    res = results[0]
    boxes = res.boxes
    det_count = len(boxes) if boxes is not None else 0
    detected_classes = [res.names[int(cls)] for cls in boxes.cls.tolist()] if boxes is not None else []

    print(f"Inference Latency: {inf_latency_ms} ms")
    print(f"Peak VRAM Occupancy: {peak_vram_mb} MB / 4096 MB")
    print(f"Detections Found ({det_count}): {detected_classes}")
    print(f"Smoke Test Result: PASSED")

    return {
        "model": model_name,
        "device": device,
        "half_precision_fp16": True,
        "imgsz": 640,
        "batch_size": 1,
        "inference_latency_ms": inf_latency_ms,
        "peak_vram_mb": peak_vram_mb,
        "detections_count": det_count,
        "detected_classes": detected_classes,
        "status": "PASSED"
    }

def main():
    import torch
    import torchvision
    import ultralytics
    import scipy
    import sklearn

    base_dir = Path(__file__).resolve().parent.parent.parent
    reports_dir = base_dir / "dataset" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("ENCROWATCH AI — STAGE 1.1 GPU ENVIRONMENT & SMOKE TEST")
    print("=" * 65)
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"TorchVision Version: {torchvision.__version__}")
    print(f"Ultralytics Version: {ultralytics.__version__}")
    print(f"SciPy Version: {scipy.__version__}")
    print(f"Scikit-Learn Version: {sklearn.__version__}")
    print(f"CUDA Available in PyTorch: {torch.cuda.is_available()}")
    print("-" * 65)

    tensor_res = test_cuda_tensor()
    
    # Pick a sample image from backend/uploads
    sample_img = base_dir / "backend" / "uploads" / "clear_street.jpg"
    if not sample_img.exists():
        sample_img = base_dir / "backend" / "uploads" / "test_street.jpg"

    smoke_res = run_yolo_smoke_test(sample_img)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "torch_version": torch.__version__,
            "torchvision_version": torchvision.__version__,
            "ultralytics_version": ultralytics.__version__,
            "scipy_version": scipy.__version__,
            "sklearn_version": sklearn.__version__,
            "torch_cuda_available": torch.cuda.is_available()
        },
        "cuda_hardware_test": tensor_res,
        "gpu_inference_smoke_test": smoke_res
    }

    out_file = reports_dir / "gpu_smoke_test_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("-" * 65)
    print(f"Full Report exported to: {out_file}")
    print("=" * 65)

if __name__ == "__main__":
    main()
