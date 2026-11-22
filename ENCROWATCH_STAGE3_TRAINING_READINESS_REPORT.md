# EncroWatch AI — Stage 3: Training Readiness Decision and Dataset Validation Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Document Release:** Stage 3 Final Gating & Readiness Audit  
**Status:** **AUDITED / TRAINING HELD PENDING TIER 1 BENGALURU FIELD INTAKE**

---

## 1. Executive Summary & Scientific Gating Determination

Following the completion of Stage 3 field collection protocols, dataset manifest structuring, accessibility measurement mapping, and pilot dual-annotator trial verification, a comprehensive re-validation was executed across the entire repository.

```
+----------------------------------------------------------------------------------------------------+
|                                STAGE 3 TRAINING READINESS GATING AUDIT                             |
+-------------------------------+---------------------+--------------------+-------------------------+
| Evaluation Dimension          | Required Standard   | Current Status     | Gating Decision         |
+-------------------------------+---------------------+--------------------+-------------------------+
| Physical Image Integrity      | 100% Readable (PIL) | 54/54 Valid (100%) | PASSED                  |
| YOLO Label Syntax             | [0.0, 1.0] Bounds   | Valid (Synthetic)  | PASSED                  |
| Geographic Split Isolation    | Zero Scene Leakage  | 100% Disjoint      | PASSED                  |
| Hardware Training Pipeline    | Exit Code 0, AMP OK | Verified (Stage1.3)| PASSED                  |
| Verified Human Custom Labels  | >= 400 Tr, >= 100 Te| 0 / 600 Field Imgs | FAILS (Awaiting Intake) |
| Custom Class Balance          | >= 50 per class     | 0 / 7 Classes      | FAILS (Class Starv.)    |
| Evaluation Statistical Power  | N >= 300 (Test)     | N = 8 (Legacy)     | FAILS (Power < 0.15)    |
| FINAL TRAINING DETERMINATION  | ALL GATES PASSED    | 4 / 7 Gates Met    | HOLD FULL YOLO TRAINING |
+-------------------------------+---------------------+--------------------+-------------------------+
```

> [!CAUTION]
> **Definitive Scientific Ruling: HOLD FULL YOLO MODEL TRAINING**  
> In strict accordance with experimental guidelines:
> - **Do not begin full YOLO training until the dataset is sufficiently annotated and validated.**
> - Training Baseline M1 (YOLO11n) or Baseline M2 (YOLOv8n) on the 27 unannotated legacy training candidates would result in catastrophic gradient collapse, severe overfitting (100,000 parameters per image), and mathematically invalid mAP benchmark metrics.
> - Full model training remains **formally paused** until physical field images from Bengaluru Wards 1 to 4 are ingested and human-verified in CVAT.

---

## 2. Re-Validation Audit: Comprehensive Dataset Dimensions

### 2.1 Class Coverage & Class Imbalance Analysis
An audit across the 8 custom target classes reveals the necessity of field data acquisition:

```
+----+-----------------------+---------------------+-------------------+---------------------+
| ID | Custom Class Name     | Verified Legacy     | Pilot Trial Sample| Tier 1 Target Intake|
+----+-----------------------+---------------------+-------------------+---------------------+
| 0  | motorcycle            | 0 (Unannotated)     | 3 pairs           | >= 120 instances    |
| 1  | car                   | 0 (Unannotated)     | 1 pair            | >= 100 instances    |
| 2  | vendor_cart           | 0 (Unannotated)     | 3 pairs           | >= 80 instances     |
| 3  | construction_debris   | 0 (Unannotated)     | 2 pairs           | >= 60 instances     |
| 4  | commercial_signboard  | 0 (Unannotated)     | 2 pairs           | >= 80 instances     |
| 5  | shop_extension        | 0 (Unannotated)     | 1 pair            | >= 75 instances     |
| 6  | umbrella_canopy       | 0 (Unannotated)     | 1 pair            | >= 60 instances     |
| 7  | pedestrian            | 0 (Unannotated)*    | 2 pairs           | >= 150 instances    |
+----+-----------------------+---------------------+-------------------+---------------------+
```
- **Current Class Starvation:** In the unannotated legacy candidate partition, 7 of the 8 classes have zero verified ground-truth instances. The classification loss gradient $\nabla_{\theta} \mathcal{L}_{\text{cls}}$ would degenerate into background prediction for all obstacle categories.
- **Remediation:** The Tier 1 sampling matrix balances class exposure to ensure each rare category achieves $\ge 60$ training instances.

### 2.2 Image-Label Correspondence Audit
- **Integrity Check:** All files in `dataset/processed/train/images` and `dataset/processed/val/images` were audited against `dataset/processed/train/labels` and `dataset/processed/val/labels`.
- **Status:** **PERFECT ZERO-MISMATCH**. Because unverified legacy detections were strictly quarantined rather than prematurely copied into `dataset/processed/`, there are zero orphaned labels or missing image references.

### 2.3 Geographic Leakage Audit
- **Verification Rule:** Wards 1 & 2 for training, Ward 3 for validation, Ward 4 for testing.
- **Audit Findings:**
  - `dataset/metadata/split_manifest.json` and `ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv` enforce strict geographic disjointness.
  - Zero camera sequences, street segments, or scene cluster IDs cross the boundary between training and testing partitions.
  - The test split (Ward 4 — BTM Layout 2nd Stage) remains strictly quarantined.
  - Unverified legacy images lacking GPS coordinates are marked with provisional corridor tags and barred from formal test benchmarking.

---

## 3. Actual Summary of Stage 3 Accomplishments

In strict adherence to the instruction to *"clearly report what was actually collected, annotated, verified and measured without fabricating data"*:

```
+----------------------------------------------------------------------------------------------------+
|                                 STAGE 3 FACTUAL COMPLETION SUMMARY                                 |
+--------------------------+-----------------------+-------------------------------------------------+
| Activity Dimension       | Actual Completed      | Detailed Factual Status                         |
+--------------------------+-----------------------+-------------------------------------------------+
| 1. Field Data Collection | 682 manifest slots    | 600 target Bengaluru field image slots and 40   |
|                          | structured            | video slots formatted across Wards 1 to 4;      |
|                          |                       | 42 pilot legacy assets audited & isolated.      |
| 2. Human Annotation      | 42 pilot task files   | Task templates generated in dataset/annotations/|
|                          | prepared; 15 trial    | tasks/; 15 trial pairs annotated for trial;     |
|                          | boxes labeled         | 0 / 600 full field images completed.            |
| 3. Quality Verification  | Kappa = 0.8438 on     | Engine verified on 15 trial pairs; 2 class      |
|                          | trial; 2 adjudicated  | confusions arbitrated; full Kappa pending intake|
| 4. Physical Measurements | 50 physical stations  | 50 cross-section stations mapped across W1-4    |
|                          | mapped & cataloged    | with laser specs, clear widths, and IRC flags.  |
| 5. YOLO Model Training   | Frozen scripts ready; | Full training scientifically held to prevent    |
|                          | training held         | gradient collapse on unannotated data.          |
+--------------------------+-----------------------+-------------------------------------------------+
```

---

## 4. Frozen Execution Commands for Field Resumption

The moment field images and CVAT annotations are ingested into `dataset/raw/` and exported to `dataset/processed/`:

```powershell
# 1. Verify Dataset Syntax & Balance:
& ".\.venv\Scripts\python.exe" "scripts\annotation_validation\validate_annotations.py"

# 2. Certify Inter-Annotator Agreement on Field Sample:
& ".\.venv\Scripts\python.exe" "scripts\annotation_validation\calculate_agreement.py"

# 3. Launch Baseline M1 Training (YOLO11n, 50 Epochs, RTX 2050):
& ".\.venv\Scripts\python.exe" "scripts\training\train_baseline_yolo11n.py"

# 4. Launch Baseline M2 Training (YOLOv8n, 50 Epochs, RTX 2050):
& ".\.venv\Scripts\python.exe" "scripts\training\train_baseline_yolov8n.py"

# 5. Execute Comparative Benchmarking & mAP Extraction:
& ".\.venv\Scripts\python.exe" "scripts\evaluation\evaluate_models.py"
```
