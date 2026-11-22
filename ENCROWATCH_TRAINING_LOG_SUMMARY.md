# EncroWatch AI — Training Execution Log & Hardware Benchmark Summary

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Comprehensive Log of Training Smoke Tests, Memory Profiles, and Baseline Benchmarks  
**Status Classification Standard:** `VERIFIED (Hardware Execution Passed / Full Training Held)`

---

## 1. Verified GPU Hardware Execution Logs

### 1.1 Stage 1.3 End-to-End Training Smoke Test
- **Execution Script:** `scripts/dataset_inspection/run_pipeline_smoke_test.py`
- **Device:** `cuda:0` (NVIDIA GeForce RTX 2050 Laptop GPU, 4,095.5 MB dedicated VRAM)
- **Result:** **PASSED (Exit Code 0)**
- **Verified Operations:**
  - PyTorch DataLoader batch streaming (12 synthetic fixture images, 8 train, 4 val)
  - Automatic Mixed Precision (AMP FP16) autocast forward pass
  - Multi-task loss computation (box loss, cls loss, dfl loss)
  - Autograd backward propagation on GPU
  - AdamW weight optimization step
  - Post-epoch validation engine and checkpoint generation (`last.pt`, `best.pt` in `experiments/smoke_tests/smoke_test_run/weights/`)
- **Peak Measured VRAM:** **227.07 MB / 4,095.5 MB (5.54%)**

### 1.2 Stage 3.2 Discrete VRAM Profiling at Multi-Batch Limits
- **Execution Script:** `scripts/training/gpu_profiling_benchmark.py`
- **Result:** **PASSED (Exit Code 0)**
- **Empirical Findings:**
  - `Batch B=1`: Step Time = 106.91 ms | Allocated = 933.27 MB | Reserved = 1334.0 MB | Utilization = 32.57% (SAFE)
  - `Batch B=2`: Step Time = 214.96 ms | Allocated = 1826.80 MB | Reserved = 2222.0 MB | Utilization = 54.25% (SAFE)
  - `Batch B=4`: Step Time = 1520.71 ms | Allocated = 3615.87 MB | Reserved = 4556.0 MB | Utilization = 111.24% (OOM SPILLOVER RISK)
- **Scientific Determination:** Safe operational training batch size for the RTX 2050 4 GB GPU is **`Batch B=2`**, avoiding CUDA memory spillover.

### 1.3 Stage 2.3 Standalone Inference Speed & Latency Benchmarks
- **Execution Script:** `scripts/evaluation/evaluate_models.py`
- **Device:** `cuda:0` (Synchronized CUDA performance timer, 50 inference cycles at $640 	imes 640$)
- **Baseline M1 (YOLO11n):** Latency = **139.63 ms** | Throughput = **7.16 FPS** | Peak VRAM = **66.20 MB**
- **Baseline M2 (YOLOv8n):** Latency = **58.04 ms** | Throughput = **17.23 FPS** | Peak VRAM = **78.11 MB**

---

## 2. Training Hold Governance & Frozen Pipelines

Full 50-epoch training on Baseline M1 and M2 remains strictly on **HOLD** pending intake of verified field annotations. The frozen command lines:
```powershell
# In C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai:
& ".\.venv\Scripts\python.exe" "scripts\training\train_baseline_yolo11n.py"
& ".\.venv\Scripts\python.exe" "scripts\training\train_baseline_yolov8n.py"
```
