# EncroWatch AI — Baseline Model M2 (YOLOv8n) Technical Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Environment:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB dedicated GDDR6 VRAM) | Windows 11 AMD64  
**Software Stack:** Python 3.12.10 | PyTorch 2.6.0+cu124 | TorchVision 0.21.0+cu124 | Ultralytics 8.4.208  
**Model Designation:** Baseline M2 — Ultralytics YOLOv8n (`yolov8n.pt`)  
**Status Classification Standard:** `VERIFIED (Architecture & Benchmarks Verified / Full Training Held)`

---

## 1. Architectural Specification

Baseline Model M2 serves as the primary comparative baseline against Model M1 (YOLO11n). As the established industry standard in lightweight convolutional detection, YOLOv8n provides an essential empirical benchmark to isolate the performance benefits of YOLO11's newer C3k2 blocks and architectural refinements.

```
+-------------------------------------------------------------------------------+
|                        YOLOv8n Architectural Flow                             |
+-------------------------------------------------------------------------------+
| Input Image (640x640x3)                                                       |
|       |                                                                       |
|       v                                                                       |
| [Backbone: Conv + C2f Blocks + Spatial Pyramid Pooling Fast (SPPF)]           |
|       |                                                                       |
|       +--> P3 (80x80x64)   -- Fine-Grained Features                           |
|       +--> P4 (40x40x128)  -- Intermediate Spatial Features                   |
|       +--> P5 (20x20x256)  -- Coarse Semantic Features                        |
|       |                                                                       |
|       v                                                                       |
| [Neck: Modified PANet with C2f Feature Aggregation]                           |
|       |                                                                       |
|       v                                                                       |
| [Head: Decoupled Classification & Regression Heads (Anchor-Free DFL)]         |
|       |                                                                       |
|       v                                                                       |
| Detections: {Bounding Box [x, y, w, h], Class ID (0-7), Confidence (0-1)}     |
+-------------------------------------------------------------------------------+
```

### 1.1 Structural Parameters
- **Backbone Family:** YOLOv8 (Ultralytics architecture generation 2023)
- **Model Variant:** Nano (`yolov8n`)
- **Parameter Count:** **3,157,200 parameters (3.16 M)**
- **Computational Complexity:** **8.7 GFLOPs** (at $640 \times 640 \times 3$ input)
- **Primary Modules:** C2f (Cross-Stage Partial with 2 convolutions), SPPF, decoupled anchor-free distribution focal loss heads.
- **Target Classes:** 8 urban encroachment classes identical to M1.

---

## 2. Empirical GPU Benchmarks on NVIDIA GeForce RTX 2050

Empirical profiling was conducted identically to Model M1 under `scripts/evaluation/evaluate_models.py` (50 synchronized iterations at $640 \times 640$):

| Metric | Measured Value | Unit | Research Significance |
| :--- | :--- | :--- | :--- |
| **Mean Inference Latency** | **58.04** | ms / frame | Superior throughput on GA107 Ampere tensor cores |
| **Inference Throughput** | **17.23** | FPS | Exceeds 15 FPS threshold for live dashcam feeds |
| **Peak Inference VRAM** | **78.11** | MB | Compact memory residency |
| **VRAM Utilization (Inference)** | **1.91%** | % of 4,096 MB | 98.09% headroom available |
| **CUDA Stream Synchronization** | Verified | Boolean | Zero GPU pipeline stalls observed |

---

## 3. Comparative Architectural Analysis: M1 (YOLO11n) vs M2 (YOLOv8n)

| Architectural Attribute | Baseline M1 (YOLO11n) | Baseline M2 (YOLOv8n) | Delta ($\Delta$) | Research Implication |
| :--- | :--- | :--- | :--- | :--- |
| **Parameters** | **2.61 M** | 3.16 M | -17.4% (-0.55 M) | M1 has smaller edge storage footprint |
| **Theoretical FLOPs** | **6.5 G** | 8.7 G | -25.3% (-2.2 G) | M1 requires fewer theoretical operations |
| **Empirical GPU Latency** | 139.63 ms | **58.04 ms** | +81.59 ms (+140%) | M2 kernel operations execute faster on GA107 |
| **Throughput (FPS)** | 7.16 FPS | **17.23 FPS** | +10.07 FPS (+140%) | M2 is faster for high-rate video ingestion |
| **Inference VRAM** | **66.20 MB** | 78.11 MB | -11.91 MB (-15.2%) | M1 has lower steady-state inference VRAM |
| **Backbone Module** | C3k2 Blocks | C2f Blocks | Structural | C3k2 provides enhanced multi-scale features |
| **Safe Training Batch** | **Batch B=2** | **Batch B=2** | Identical | 4 GB VRAM ceiling enforces $B=2$ for both |

### 3.1 Computational Trade-off Analysis
While YOLO11n achieves lower parameter and FLOP counts through refined channel allocation and C3k2 grouping, YOLOv8n exhibits lower wall-clock latency on the GA107 Ampere GPU. This discrepancy stems from PyTorch/CUDA kernel optimization: the standard $3 \times 3$ convolutions in C2f map with near-optimal efficiency to NVIDIA cuDNN GEMM kernels, whereas C3k2 incorporates smaller grouped splits that incur minor PyTorch dispatch overhead on consumer mobile GPUs. Both models remain viable baselines for urban footpath inspection.

---

## 4. Training Configuration & Hyperparameter Registry

The complete training script is implemented in [`scripts/training/train_baseline_yolov8n.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/training/train_baseline_yolov8n.py).

```python
# Verified Production Training Parameters (Matched to M1)
training_args = {
    "model": "yolov8n.pt",
    "data": "dataset/splits/dataset.yaml",
    "epochs": 50,
    "batch": 2,                # Safe batch size for 4 GB RTX 2050
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

## 5. Academic Governance & Training Hold Status

> [!IMPORTANT]
> **TRAINING HOLD ENFORCED BY ACADEMIC RESEARCH ETHICS GATE**
> - **Empirical Pipeline Status:** `FROZEN_READY`
> - **Field Ground Truth Status:** `PENDING_TIER1_ANNOTATION`
> - **Hold Rationale:** In accordance with the EncroWatch AI research charter, Baseline Model M2 training is held in strict synchronization with Model M1. Both models will undergo identical paired 50-epoch training upon release of CVAT-certified field annotations.
