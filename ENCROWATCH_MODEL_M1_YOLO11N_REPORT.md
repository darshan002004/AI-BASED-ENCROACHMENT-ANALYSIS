# EncroWatch AI — Baseline Model M1 (YOLO11n) Technical Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Environment:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB dedicated GDDR6 VRAM) | Windows 11 AMD64  
**Software Stack:** Python 3.12.10 | PyTorch 2.6.0+cu124 | TorchVision 0.21.0+cu124 | Ultralytics 8.4.208  
**Model Designation:** Baseline M1 — Ultralytics YOLO11n (`yolo11n.pt`)  
**Status Classification Standard:** `VERIFIED (Architecture & Benchmarks Verified / Full Training Held)`

---

## 1. Architectural Specification

Baseline Model M1 represents the primary lightweight single-stage object detector evaluated within the EncroWatch AI framework. YOLO11n incorporates recent advancements in convolutional backbones and multi-scale feature pyramids designed for resource-constrained edge perception.

```
+-------------------------------------------------------------------------------+
|                       YOLO11n Architectural Flow                             |
+-------------------------------------------------------------------------------+
| Input Image (640x640x3)                                                       |
|       |                                                                       |
|       v                                                                       |
| [Backbone: Conv + C3k2 Blocks + Spatial Pyramid Pooling Fast (SPPF)]          |
|       |                                                                       |
|       +--> P3 (80x80x64)   -- Small Encroachments (Bollards, Debris)          |
|       +--> P4 (40x40x128)  -- Medium Encroachments (Bicycles, Trees, Poles)   |
|       +--> P5 (20x20x256)  -- Large Encroachments (Vehicles, Carts, Stalls)   |
|       |                                                                       |
|       v                                                                       |
| [Neck: PANet Path Aggregation with C3k2 Cross-Stage Feature Fusion]           |
|       |                                                                       |
|       v                                                                       |
| [Head: Decoupled Classification & Regression Heads (Anchor-Free)]             |
|       |                                                                       |
|       v                                                                       |
| Detections: {Bounding Box [x, y, w, h], Class ID (0-7), Confidence (0-1)}     |
+-------------------------------------------------------------------------------+
```

### 1.1 Structural Parameters
- **Backbone Family:** YOLO11 (Ultralytics architecture generation 2024–2025)
- **Model Variant:** Nano (`yolo11n`)
- **Parameter Count:** **2,610,000 parameters (2.61 M)**
- **Computational Complexity:** **6.5 GFLOPs** (at $640 \times 640 \times 3$ input)
- **Primary Modules:** C3k2 (Cross-Stage Partial with kernel-size 2 adaptations), SPPF (Spatial Pyramid Pooling Fast), decoupled anchor-free distribution focal loss (DFL) heads.
- **Target Target Classes:** 8 urban encroachment classes defined in `dataset/metadata/classes.json`:
  1. `construction_material`
  2. `debris`
  3. `parked_bicycle`
  4. `parked_motorcycle`
  5. `permanent_structure`
  6. `shop_extension`
  7. `tree_pole`
  8. `vendor_cart`

---

## 2. Empirical GPU Benchmarks on NVIDIA GeForce RTX 2050

The computational profile of YOLO11n was empirically measured on the dedicated host GPU (`NVIDIA GeForce RTX 2050 Laptop GPU`, 4,095.5 MB dedicated GDDR6 VRAM, 2,048 CUDA cores, Ampere GA107 architecture).

### 2.1 Inference Speed and Memory Footprint
Benchmarks were conducted using `scripts/evaluation/evaluate_models.py` with 50 synchronized CUDA warm-up and evaluation iterations at $640 \times 640$ resolution:

| Metric | Measured Value | Unit | Research Significance |
| :--- | :--- | :--- | :--- |
| **Mean Inference Latency** | **139.63** | ms / frame | Edge municipal camera streaming latency |
| **Inference Throughput** | **7.16** | FPS | Real-time survey video processing capability |
| **Peak Inference VRAM** | **66.20** | MB | Extremely low footprint, enables co-residence with segmentation |
| **VRAM Utilization (Inference)** | **1.62%** | % of 4,096 MB | Leaves 98.38% headroom for temporal buffers |
| **CUDA Stream Synchronization** | Verified | Boolean | Zero GPU synchronization stalls observed |

### 2.2 Discrete Training Memory Profiling & Safe Batch Sizing
Empirical training step simulation was conducted via `scripts/training/gpu_profiling_benchmark.py` under PyTorch 2.6.0+cu124 with Automatic Mixed Precision (AMP FP16) and AdamW backward passes:

```
Batch Size B=1: [███████                      ] 32.57% (Allocated: 933.3 MB, Reserved: 1,334.0 MB) -> STABLE
Batch Size B=2: [███████████                  ] 54.25% (Allocated: 1,826.8 MB, Reserved: 2,222.0 MB) -> OPTIMAL
Batch Size B=4: [███████████████████████!     ] 111.24% (Allocated: 3,615.9 MB, Reserved: 4,556.0 MB) -> OOM SPILLOVER
```

- **Scientific Conclusion:** Training YOLO11n at $B=4$ on a 4 GB GPU triggers PyTorch CUDA caching allocator oversubscription (4,556 MB reserved vs 4,095.5 MB physical), forcing Windows driver paging to shared host system RAM and increasing step latency by **$707\%$** (from 214.96 ms to 1,520.71 ms).
- **Approved Hyperparameter:** Default training batch size is strictly bounded to **`batch=2`** with gradient accumulation steps (`accumulate=2`), simulating an effective mini-batch of 4 while capping GPU memory at 2,222 MB ($54.25\%$).

---

## 3. Training Configuration & Hyperparameter Registry

The complete training script is implemented in [`scripts/training/train_baseline_yolo11n.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/training/train_baseline_yolo11n.py).

```python
# Verified Production Training Parameters
training_args = {
    "model": "yolo11n.pt",
    "data": "dataset/splits/dataset.yaml",
    "epochs": 50,
    "batch": 2,                # Empirically verified safe batch for 4 GB VRAM
    "imgsz": 640,
    "device": 0,               # NVIDIA GeForce RTX 2050
    "workers": 0,              # Windows multiprocess dead-lock prevention
    "optimizer": "AdamW",
    "lr0": 0.001,
    "lrf": 0.01,
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3.0,
    "warmup_momentum": 0.8,
    "box": 7.5,
    "cls": 0.5,
    "dfl": 1.5,
    "amp": True,               # Automatic Mixed Precision FP16
    "plots": True,
    "save": True,
}
```

---

## 4. Academic Governance & Training Hold Status

> [!IMPORTANT]
> **TRAINING HOLD ENFORCED BY ACADEMIC RESEARCH ETHICS GATE**
> - **Empirical Pipeline Status:** `FROZEN_READY`
> - **Field Ground Truth Status:** `PENDING_TIER1_ANNOTATION`
> - **Hold Rationale:** As mandated by the EncroWatch AI research charter, full 50-epoch training cannot be executed against synthetic fixtures or unverified pilot candidates. Training will be initiated immediately upon ingestion of CVAT-adjudicated field annotations ($N=600$ target images).

### 4.1 Evaluation Protocol (Planned)
Upon unfreezing, Model M1 performance will be evaluated against the quarantined Ward 4 test set ($N=7$ pilot / $N=120$ field target) across:
1. Primary Metric: Mean Average Precision ($\text{mAP}@0.50$ and $\text{mAP}@0.50:0.95$).
2. Class-wise Breakdown: PR-curves across small vs large objects.
3. Edge Inference Stability: Standard deviation of frame latency under continuous thermal load.
