# EncroWatch AI — Stage 3.2: Formal Dataset Readiness Decision

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Formal Certification Gate Determination for Baseline Model Training  
**Status Classification Standard:** `VERIFIED (Academic Training Hold Enforced)`

---

## 1. Definitive Research Ruling

Following the automated certification audit of dataset quality, image decodability, class distributions, and geographic isolation:

```
+----------------------------------------------------------------------------------------------------+
|                                    DEFINITIVE TRAINING READINESS VERDICT                           |
+----------------------------------------------------------------------------------------------------+
| Baseline Model M1 (YOLO11n):  HOLD FULL MODEL TRAINING (UNMET ANNOTATION GATE)                     |
| Baseline Model M2 (YOLOv8n):  HOLD FULL MODEL TRAINING (UNMET ANNOTATION GATE)                     |
| Pipeline Computational State: VERIFIED FUNCTIONAL ON RTX 2050 (Exit Code 0)                        |
| Scientific Integrity Status:  PRESERVED (Zero Fabricated Training Results)                         |
+----------------------------------------------------------------------------------------------------+
```

> [!CAUTION]
> **Academic Integrity Ruling: Full Model Training is Paused.**  
> Launching 50-epoch training on 27 unannotated legacy training images would cause catastrophic gradient collapse ($0.0\%$ recall on rare classes), extreme overfitting (100,000 parameters per image), and invalid mAP metrics. In strict accordance with academic ethics, full model training is held until genuine field data and CVAT annotations are ingested.

---

## 2. Gate Criteria Evaluation Matrix

```
+-----------------------------------+--------------------+--------------------+----------------------+
| Readiness Gate Criterion          | Required Standard  | Observed Status    | Gate Status          |
+-----------------------------------+--------------------+--------------------+----------------------+
| 1. Image Readability & Format     | 100% Valid (PIL)   | 54/54 Valid (100%) | PASSED               |
| 2. Zero Geographic Data Leakage   | 0 Cross-Split Scene| 0 Overlapping Scene| PASSED               |
| 3. Quarantined Test Split         | Ward 4 Isolated    | Ward 4 Quarantined | PASSED               |
| 4. Hardware Pipeline Stability    | Exit Code 0, AMP OK| Verified on RTX2050| PASSED               |
| 5. Human-Verified Field Labels    | >= 400 Tr / 100 Te | 0 Field Labels     | FAILS (Awaiting Data)|
| 6. Custom Class Balance Ratio     | < 10:1 Ratio       | Severe Starvation  | FAILS (Class Starv.) |
| 7. Evaluation Statistical Power   | N >= 300 (Test)    | N = 8 (Legacy)     | FAILS (Power < 0.15) |
+-----------------------------------+--------------------+--------------------+----------------------+
```

---

## 3. Clear Prerequisites for Gate Release

To lift the training hold and initiate official model training:
1. Ingest genuine field imagery ($N \ge 600$ images, $40$ videos) into `dataset/raw/images/` and `dataset/raw/videos/`.
2. Complete 100% human-verified CVAT annotations across the 8 custom classes and corridor polygons.
3. Certify inter-annotator reliability on a 10% validation sample ($\kappa \ge 0.80$, $\text{IoU} \ge 0.80$, $\text{BF1} \ge 0.75$).
4. Export verified Darknet labels to `dataset/processed/train/labels/` and `dataset/processed/val/labels/`.
5. Execute `python scripts/training/train_baseline_yolo11n.py`.
