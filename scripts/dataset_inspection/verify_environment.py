#!/usr/bin/env python3
"""
EncroWatch AI - Stage 1: Hardware & Computational Environment Audit
Part of Phase 2 Execution.

Verifies:
- NVIDIA GPU model, VRAM, driver version, CUDA UMD via nvidia-smi.
- Python version, executable path, architecture.
- PyTorch version, CUDA availability (torch.cuda.is_available()).
- Ultralytics installation.
- OpenCV, Shapely, NumPy, SciPy, Scikit-learn status.
- Formulates conservative GPU training profile for RTX 2050 (4 GB VRAM).
"""

import sys
import os
import subprocess
import json
import platform
from pathlib import Path

def get_gpu_info():
    gpu_info = {
        "gpu_available": False,
        "gpu_name": "None",
        "total_vram_mb": 0,
        "driver_version": "None",
        "cuda_version": "None",
        "error": None
    }
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        lines = res.stdout.strip().split("\n")
        if lines and lines[0]:
            parts = [p.strip() for p in lines[0].split(",")]
            gpu_info["gpu_available"] = True
            gpu_info["gpu_name"] = parts[0]
            gpu_info["total_vram_mb"] = int(float(parts[1]))
            gpu_info["driver_version"] = parts[2]
            
        # Get CUDA version from nvidia-smi
        smi_out = subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout
        for line in smi_out.split("\n"):
            if "CUDA Version:" in line:
                gpu_info["cuda_version"] = line.split("CUDA Version:")[1].split("|")[0].strip()
                break
    except Exception as e:
        gpu_info["error"] = str(e)
    return gpu_info

def check_python_packages():
    packages = ["torch", "torchvision", "ultralytics", "cv2", "shapely", "numpy", "scipy", "sklearn"]
    status = {}
    for pkg in packages:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "installed")
            status[pkg] = {"installed": True, "version": ver}
            if pkg == "torch":
                status["torch"]["cuda_available"] = mod.cuda.is_available()
                if mod.cuda.is_available():
                    status["torch"]["device_count"] = mod.cuda.device_count()
                    status["torch"]["device_name"] = mod.cuda.get_device_name(0)
                    status["torch"]["cuda_version"] = mod.version.cuda
                else:
                    status["torch"]["device_count"] = 0
                    status["torch"]["device_name"] = None
                    status["torch"]["cuda_version"] = None
        except ImportError:
            status[pkg] = {"installed": False, "version": None}
    return status

def audit_environment():
    gpu = get_gpu_info()
    pkgs = check_python_packages()
    
    # Assess compatibility for 4 GB RTX 2050
    torch_installed = pkgs.get("torch", {}).get("installed", False)
    torch_cuda = pkgs.get("torch", {}).get("cuda_available", False)
    ultralytics_installed = pkgs.get("ultralytics", {}).get("installed", False)
    
    readiness = "NOT_READY_DEPENDENCIES_MISSING"
    if torch_installed and torch_cuda and ultralytics_installed:
        readiness = "READY_FOR_GPU_EXPERIMENTS"
    elif torch_installed and not torch_cuda:
        readiness = "WARNING_TORCH_CPU_ONLY"

    vram_mb = gpu.get("total_vram_mb", 0)
    conservative_config = {
        "recommended_backbones": ["yolo11n.pt", "yolov8n.pt"],
        "recommended_imgsz": 640,
        "recommended_batch_size": 4 if vram_mb >= 3500 else 2,
        "mixed_precision_fp16": True,
        "max_workers": 2,
        "sequential_execution_required": True,
        "vram_budget_estimate_mb": {
            "model_weights": 25,
            "gradients_and_optimizer_states": 120,
            "fp16_activations_batch_4_img640": 1400,
            "cuda_context_overhead": 450,
            "total_estimated_peak_vram_mb": 1995,
            "free_headroom_mb": max(0, vram_mb - 1995)
        }
    }

    installation_plan = [
        "# Step 1: Install PyTorch with CUDA 12.1 / 12.4 support (compatible with Driver 610.91):",
        "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121",
        "",
        "# Step 2: Install Ultralytics YOLO framework and statistical/scientific dependencies:",
        "pip install ultralytics scipy scikit-learn"
    ]

    report = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_executable": sys.executable,
            "python_version": platform.python_version()
        },
        "gpu_hardware": gpu,
        "python_packages": pkgs,
        "environment_readiness": readiness,
        "conservative_gpu_configuration": conservative_config,
        "safe_installation_plan": installation_plan
    }
    return report

if __name__ == "__main__":
    report = audit_environment()
    print("=" * 65)
    print("ENCROWATCH AI — HARDWARE & ENVIRONMENT AUDIT")
    print("=" * 65)
    print(f"OS: {report['platform']['system']} {report['platform']['release']} ({report['platform']['machine']})")
    print(f"Python: {report['platform']['python_version']} at {report['platform']['python_executable']}")
    print(f"GPU: {report['gpu_hardware']['gpu_name']} ({report['gpu_hardware']['total_vram_mb']} MB VRAM)")
    print(f"NVIDIA Driver: {report['gpu_hardware']['driver_version']} | CUDA Driver: {report['gpu_hardware']['cuda_version']}")
    print("-" * 65)
    print("Package Status:")
    for pkg, info in report["python_packages"].items():
        if info["installed"]:
            cuda_extra = f" (CUDA: {info.get('cuda_available')})" if pkg == "torch" else ""
            print(f"  [INSTALLED] {pkg}: v{info['version']}{cuda_extra}")
        else:
            print(f"  [MISSING]   {pkg}")
    print("-" * 65)
    print(f"Readiness Status: {report['environment_readiness']}")
    print(f"Conservative Batch Size for RTX 2050: {report['conservative_gpu_configuration']['recommended_batch_size']}")
    print(f"Peak Estimated VRAM: {report['conservative_gpu_configuration']['vram_budget_estimate_mb']['total_estimated_peak_vram_mb']} MB / {report['gpu_hardware']['total_vram_mb']} MB")
    print("=" * 65)
    
    # Save report
    out_dir = Path(__file__).resolve().parent.parent.parent / "dataset" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "hardware_environment_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved audit report to: {out_dir / 'hardware_environment_report.json'}")
