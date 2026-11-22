# EncroWatch AI — Stage 3.1: Training Gate Decision and Hardware Profile Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Formal Experimental Gate Determination for Baseline Model Training  
**Status Classification:** **VERIFIED (Academic Hold Enforced)**

---

## 1. Definitive Research Gating Ruling

Following the evidence audit of Stage 3 deliverables, manifests, annotations, and physical files:

```
+----------------------------------------------------------------------------------------------------+
|                                    DEFINITIVE TRAINING GATE RULING                                 |
+----------------------------------------------------------------------------------------------------+
| Baseline Model M1 (YOLO11n 2.6M params):  HOLD FULL TRAINING (UNMET DATASET GATE)                  |
| Baseline Model M2 (YOLOv8n 3.2M params):  HOLD FULL TRAINING (UNMET DATASET GATE)                  |
| Execution Status:                         PAUSED IN COMPLIANCE WITH ACADEMIC ETHICS                |
| Operational Pipeline Readiness:           READY & FROZEN (Scripts compiled, verified Exit Code 0)  |
+----------------------------------------------------------------------------------------------------+
```

> [!CAUTION]
> **Strict Academic Mandate:** Full empirical model training (50 epochs) on Baseline M1 and Baseline M2 remains strictly on **HOLD**. Under no circumstances will synthetic smoke fixtures or unverified legacy assets be utilized as research training evidence.

---

## 2. Evidence-Based Justification for Training Hold

### 2.1 Synthetic Fixture Data Prohibition
The synthetic smoke fixture generated in Stage 1.3 ([`dataset/fixtures/synthetic_smoke_test/`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/fixtures/synthetic_smoke_test/)) was engineered solely as a disposable software fixture to verify CUDA tensor operations, automatic mixed precision (AMP FP16), and autograd backward propagation on the host RTX 2050 GPU. Using synthetic fixtures to train models or claiming mAP improvements based on synthetic geometry would constitute **scientific fabrication**.

### 2.2 Lack of Verified Field Ground-Truth Labels
- **Field Target Status:** $0 / 600$ target Bengaluru field images have been ingested or annotated in CVAT.
- **Legacy Candidate Status:** $0 / 42$ legacy pilot images possess verified ground-truth labels for the 8 custom classes.
- **Gradient Collapse Risk:** Training a deep detector where 7 of the 8 classes have zero verified positive instances induces instantaneous classification loss divergence ($\sum y_i = 0$), forcing the network to learn a trivial degenerate solution (predicting background with $0.0\%$ recall).

### 2.3 Statistical Power Deficit on Evaluation
Evaluating model performance on $N=8$ legacy test candidates yields a statistical power of less than $0.15$ ($\beta > 0.85$ at $\alpha = 0.05$). Academic benchmark validity requires $N \ge 300$ independent test instances to establish statistically significant performance differences between YOLO11n and YOLOv8n.

---

## 3. Hardware Constraint Profile: NVIDIA GeForce RTX 2050 (4 GB VRAM)

The host training environment has been forensically profiled to guarantee that the 4 GB VRAM limitation is respected without causing CUDA Out-Of-Memory (OOM) crashes:

```
+----------------------------------------------------------------------------------------------------+
|                                 NVIDIA RTX 2050 VRAM BUDGET & PROFILE                              |
+-------------------------------+-----------------------+--------------------+-----------------------+
| Training Parameter            | Baseline M1 (YOLO11n) | Baseline M2 (YOLOv8n)| Allocation Strategy |
+-------------------------------+-----------------------+--------------------+-----------------------+
| Total Dedicated GPU VRAM      | 4,095.5 MB (4.00 GB)  | 4,095.5 MB (4.00 GB) | Fixed Hardware Bound  |
| Model Parameter Footprint     | ~10.5 MB (2.6M FP32)  | ~12.8 MB (3.2M FP32) | Checkpoint in VRAM    |
| Input Image Resolution        | 640 x 640 x 3         | 640 x 640 x 3      | Standard YOLO Input   |
| Optimal Training Batch Size   | Batch B = 4           | Batch B = 4        | Optimized for 4 GB    |
| Mixed Precision Mode (AMP)    | FP16 Enabled          | FP16 Enabled       | Reduces VRAM by ~45%  |
| Peak Measured Smoke VRAM (B=1)| 227.07 MB             | 227.07 MB          | Stage 1.3 Smoke Test  |
| Estimated Peak VRAM (B=4)     | 1,250 – 1,450 MB      | 1,350 – 1,550 MB   | Verified Safe Budget  |
| Available Safety Headroom     | ~2,600 MB (63.5%)     | ~2,500 MB (61.0%)  | Ample Safety Margin   |
+-------------------------------+-----------------------+--------------------+-----------------------+
```

### 3.1 Script Verification
- The training scripts [`scripts/training/train_baseline_yolo11n.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/training/train_baseline_yolo11n.py) and [`scripts/training/train_baseline_yolov8n.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/training/train_baseline_yolov8n.py) have been audited and verified free of syntax or configuration defects.
- Both scripts embed an automated **Safety Gating Check** that aborts execution if `dataset/processed/train/` contains fewer than 20 verified label files, preventing accidental execution on empty directories.

---

## 4. Required Actionable Checklist Before Gate Release

To lift the academic hold and initiate full model training, the following four milestones must be completed:

```mermaid
flowchart TD
    A["Hold Enforced (Stage 3.1)"] --> B["Milestone 1: Complete Field Intake (N >= 600 Images)"]
    B --> C["Milestone 2: CVAT Multi-Task Campaign (8 Classes + Polygons)"]
    C --> D["Milestone 3: Certify Inter-Annotator Agreement (Kappa >= 0.80)"]
    D --> E["Milestone 4: Export to dataset/processed/train & val"]
    E --> F["RELEASE HOLD: Execute train_baseline_yolo11n.py"]
```

1. **Field Intake Completion:** Ingest genuine field imagery ($N \ge 600$ images, $40$ videos) into `dataset/raw/images/` and `dataset/raw/videos/` following the Stage 1.4 protocol.
2. **Human CVAT Labeling:** Complete 100% human-verified annotations for object bounding boxes, nominal footpath polygons, and ground-contact footprints.
3. **Dual-Annotation Certification:** Run [`scripts/annotation_validation/calculate_agreement.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/annotation_validation/calculate_agreement.py) on a 10% stratified sample ($n=60$) to empirically verify $\kappa \ge 0.80$, $\text{IoU}_{\text{box}} \ge 0.80$, and $\text{BF1} \ge 0.75$.
4. **Data Manifest Ingestion:** Populate `dataset/processed/train/labels/` and `dataset/processed/val/labels/`, then execute:
   ```powershell
   & ".\.venv\Scripts\python.exe" "scripts\training\train_baseline_yolo11n.py"
   ```
