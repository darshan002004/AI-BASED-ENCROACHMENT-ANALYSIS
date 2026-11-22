# EncroWatch AI — Stage 3.1: Evidence Audit and Field Intake Gate Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Scope:** Independent Forensic Evidence Verification of all Stage 3 Deliverables  
**Status Classification Standard:** `VERIFIED`, `PREPARED`, `PENDING`, `FAILED`, `NOT VERIFIABLE`

---

## 1. Executive Summary & Audit Mandate

Stage 3.1 executes an exhaustive, forensic evidence audit across all Stage 3 deliverables, manifests, registers, scripts, and image repositories in the EncroWatch AI project. The objective is to rigorously determine which research activities possess **actual physical evidence**, which are **prepared structural specifications**, and which remain **pending field execution**.

> [!CRITICAL]
> **Academic Integrity Ruling:** In strict accordance with experimental ethics:
> - **Zero Fabricated Evidence:** Empty target collection slots are never counted as acquired data.
> - **Zero Fabricated Annotations:** Generated task template skeletons are never treated as completed human annotations.
> - **Zero Fabricated Compliance:** Regulatory compliance under IRC:103-2012 is not claimed as an empirical finding without in-situ field measurement logs and photographic proof.
> - **Full YOLO Model Training:** Remains strictly on **HOLD** until genuine, human-verified field data is ingested.

```
+----------------------------------------------------------------------------------------------------+
|                                STAGE 3 DELIVERABLES EVIDENCE AUDIT MATRIX                          |
+------------------------------------+---------------------+--------------------+--------------------+
| Deliverable Artifact Path          | Record Count        | Verification Method| Evidence Status    |
+------------------------------------+---------------------+--------------------+--------------------+
| ENCROWATCH_STAGE3_FIELD_           | 600 img / 40 vid    | Forensic Directory | PREPARED           |
| COLLECTION_REPORT.md               | target slots        | & File Existence   | (Protocol Ready)   |
+------------------------------------+---------------------+--------------------+--------------------+
| ENCROWATCH_STAGE3_VERIFIED_        | 682 total manifest  | SHA-256 Hash & PIL | PREPARED           |
| DATASET_MANIFEST.csv               | rows (640 tgt, 42 L)| Readability Audit  | (Manifest Ready)   |
+------------------------------------+---------------------+--------------------+--------------------+
| ENCROWATCH_STAGE3_ANNOTATION_      | 42 task templates,  | JSON Syntax & Tag  | PREPARED           |
| COMPLETION_REPORT.md               | 0 verified labels   | Inspection         | (Awaiting CVAT)    |
+------------------------------------+---------------------+--------------------+--------------------+
| ENCROWATCH_STAGE3_INTER_           | 15 trial pairs      | Independent Python | VERIFIED (Trial)   |
| ANNOTATOR_AGREEMENT.md             | (5 pilot images)    | Re-calculation     | PENDING (Field N=60)
+------------------------------------+---------------------+--------------------+--------------------+
| ENCROWATCH_STAGE3_ACCESSIBILITY_   | 50 corridor         | Field Parameter &  | PREPARED           |
| MEASUREMENTS.csv                   | station benchmarks  | Grounding Audit    | (Photo/Log Pending)|
+------------------------------------+---------------------+--------------------+--------------------+
| ENCROWATCH_STAGE3_TRAINING_        | 54 audited images,  | Automated Pipeline | VERIFIED           |
| READINESS_REPORT.md                | 7 Gating Criteria   | & Gating Check     | (Gating Enforced)  |
+------------------------------------+---------------------+--------------------+--------------------+
```

---

## 2. Forensic Audit of Field Data Acquisition

Every entry in [`ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv) and associated physical file directories was evaluated via [`scripts/dataset_inspection/audit_stage3_evidence.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/dataset_inspection/audit_stage3_evidence.py).

```
+----------------------------------------------------------------------------------------------------+
|                                    FIELD ACQUISITION EVIDENCE DISPOSITION                          |
+------------------------------------+--------------+-------------------+----------------------------+
| Asset Category                     | Count        | Physical Evidence | Audit Classification       |
+------------------------------------+--------------+-------------------+----------------------------+
| Target Field Image Slots (W1 to W4)| 600 slots    | 0 files on disk   | PENDING_PHYSICAL_INTAKE    |
| Target Video Sequence Slots (W1-W4)| 40 slots     | 0 files on disk   | PENDING_PHYSICAL_INTAKE    |
| Legacy Pilot Candidate Images      | 42 images    | 42 files on disk  | VERIFIED_ON_DISK (Isolated)|
| Synthetic Smoke Fixture Images     | 12 images    | 12 files on disk  | VERIFIED_ON_DISK (Sandbox) |
| Excluded Legacy Prototype Uploads  | 882 files    | 882 files on disk | VERIFIED_EXCLUDED          |
| Actual Acquired Bengaluru Field Img| 0 images     | 0 files on disk   | PENDING_FIELD_SURVEY       |
| Actual Acquired Bengaluru Field Vid| 0 videos     | 0 files on disk   | PENDING_FIELD_SURVEY       |
+------------------------------------+--------------+-------------------+----------------------------+
```

### 2.1 Detailed Findings by Category
1. **Target Collection Slots ($N=640$):**
   - 600 static image entries (`BLR_W01_IMG_001` to `BLR_W04_IMG_150`) and 40 video entries (`BLR_W01_VID_01` to `BLR_W04_VID_10`).
   - **Verification:** Inspection of `dataset/raw/images/` and `dataset/raw/videos/` confirms these directories currently contain zero files. They represent pre-formatted target intake slots.
   - **Status:** `PENDING`.
2. **Legacy Pilot Candidate Images ($N=42$):**
   - Located in `backend/uploads/` across `annotated/`, `original/`, and `privacy/` subdirectories.
   - **Verification:** 100% of files physically exist, have verified SHA-256 hashes, and open cleanly in PIL.
   - **Status:** `VERIFIED` as quarantined legacy assets; barred from model training due to lack of ground-truth annotations and presence of 14 burned-in visual overlays.
3. **Synthetic Disposable Fixture ($N=12$):**
   - Located in [`dataset/fixtures/synthetic_smoke_test/images/`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/fixtures/synthetic_smoke_test/images/) (8 train, 4 val, $640 \times 640$).
   - **Verification:** Generated exclusively for Stage 1.3 GPU pipeline smoke testing.
   - **Status:** `VERIFIED` in quarantined sandbox; strictly excluded from research training evidence.
4. **Excluded Legacy Uploads ($N=882$):**
   - **Verification:** Confirmed 840 duplicate uploads, 28 thumbnail files ($< 200\text{ px}$), and 14 corrupted test assets audited and excluded in Stage 1.1.
   - **Status:** `VERIFIED` as excluded.

Full itemized audit records are published in [`ENCROWATCH_STAGE3_1_FIELD_INTAKE_STATUS.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_1_FIELD_INTAKE_STATUS.csv).

---

## 3. Forensic Audit of Annotation Evidence

An inspection of all annotation directories was conducted across `dataset/annotations/tasks/`, `dataset/annotations/detection/`, `dataset/annotations/segmentation/`, and `dataset/processed/`.

```
+----------------------------------------------------------------------------------------------------+
|                                     ANNOTATION EVIDENCE BREAKDOWN                                  |
+------------------------------------+--------------+-------------------+----------------------------+
| Annotation Stream                  | Target Count | Verified Human    | Evidence Classification    |
+------------------------------------+--------------+-------------------+----------------------------+
| Target Field Bounding Boxes        | ~4,800 boxes | 0 boxes           | PENDING_FIELD_INTAKE       |
| Target Footpath Polygons           | 600 polygons | 0 polygons        | PENDING_FIELD_INTAKE       |
| Target Roadway Polygons            | 600 polygons | 0 polygons        | PENDING_FIELD_INTAKE       |
| Target Curb Polylines              | 600 polylines| 0 polylines       | PENDING_FIELD_INTAKE       |
| Target Ground-Contact Masks        | 200 masks    | 0 masks           | PENDING_FIELD_INTAKE       |
| Pilot Legacy Task Templates        | 42 templates | 0 verified labels | PREPARED (Task Skeletons)  |
| Pilot Calibration Trial Annotations| 15 box pairs | 15 trial pairs    | VERIFIED (Pilot Trial Only)|
| Processed Training Labels          | N/A          | 0 label files     | VERIFIED (Clean / Empty)   |
| Orphan Labels / Orphan Images      | 0            | 0                 | VERIFIED (Zero Desync)     |
+------------------------------------+--------------+-------------------+----------------------------+
```

### 3.1 Task Templates vs. Completed Annotations
- The 42 files in [`dataset/annotations/tasks/`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/annotations/tasks/) (`PILOT_01_task.json` to `PILOT_42_task.json`) were inspected.
- **Finding:** Every file has `annotation_status: "TASK_PREPARED_AWAITING_MANUAL_VERIFICATION"`. These are structured metadata task definitions prepared for CVAT ingestion, not completed human annotations.
- **Status:** `PREPARED`.

### 3.2 Directory Integrity Check
- `dataset/processed/train/labels/` and `dataset/processed/val/labels/` were inspected and confirmed to contain zero `.txt` files.
- **Finding:** No unverified legacy predictions were prematurely converted into YOLO training labels. Image-label synchronization is 100% clean with zero orphan files.
- **Status:** `VERIFIED`.

Full itemized annotation audit records are published in [`ENCROWATCH_STAGE3_1_ANNOTATION_STATUS.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_1_ANNOTATION_STATUS.csv).

---

## 4. Independent Verification of Inter-Annotator Agreement Calculations

The pilot agreement trial recorded in [`results/evaluation/stage3_pilot_agreement_trial.json`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/results/evaluation/stage3_pilot_agreement_trial.json) was independently audited and re-executed.

```
+----------------------------------------------------------------------------------------------------+
|                                 INTER-ANNOTATOR TRIAL RE-VERIFICATION                              |
+-------------------------------+---------------------+--------------------+-------------------------+
| Metric                        | Reported Value      | Re-Computed Value  | Audit Verification      |
+-------------------------------+---------------------+--------------------+-------------------------+
| Cohen's Kappa (kappa)         | 0.8438              | 0.8438             | VERIFIED EXACT MATCH    |
| Mean Bounding Box IoU         | 0.8398              | 0.8398             | VERIFIED EXACT MATCH    |
| Mean Boundary F1 (BF1)        | 0.9784              | 0.9784             | VERIFIED EXACT MATCH    |
| Sample Size                   | 15 paired objects   | 15 paired objects  | VERIFIED (5 Images)     |
| Statistical Unit              | Paired 2D Box / Poly| Paired 2D Box / Poly| VERIFIED                |
| Matching Method               | Greedy Box IoU      | Greedy Box IoU     | VERIFIED (tau >= 0.50)  |
| Documented Disagreements      | 2 pairs (P02, P12)  | 2 pairs (P02, P12) | VERIFIED                |
| Senior Adjudication Rulings   | 2 formal rulings    | 2 formal rulings   | VERIFIED                |
+-------------------------------+---------------------+--------------------+-------------------------+
```

### 4.1 Statistical Scope and Limitations
- **Confirmed Pilot Scope:** The values $\kappa = 0.8438$, $\text{IoU} = 0.8398$, and $\text{BF1} = 0.9784$ were computed on a calibration sample of 15 objects across 5 images (`PILOT_09`, `PILOT_12`, `PILOT_21`, `PILOT_34`, `PILOT_35`).
- **Extrapolation Restriction:** This trial verifies the mathematical execution of the agreement engine. It **must not be extrapolated** to represent the inter-annotator agreement of the full 600-image field collection, which remains `PENDING`.

---

## 5. Forensic Audit of Physical Accessibility Measurements

All 50 entries in [`ENCROWATCH_STAGE3_ACCESSIBILITY_MEASUREMENTS.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_ACCESSIBILITY_MEASUREMENTS.csv) were audited for physical evidentiary support.

```
+----------------------------------------------------------------------------------------------------+
|                                  ACCESSIBILITY EVIDENCE AUDIT BREAKDOWN                            |
+------------------------------------+--------------+-------------------+----------------------------+
| Measurement Attribute              | Status       | Evidentiary Basis | Audit Classification       |
+------------------------------------+--------------+-------------------+----------------------------+
| Measurement Stations Defined       | 50 stations  | Mapped W1 to W4   | PREPARED (Station Network) |
| GPS Coordinates (Lat/Lon)          | 50 pairs     | Corridor Waypoints| PREPARED (Anchor Waypoints)|
| Instrument & Calibration Spec      | 50 entries   | Bosch GLM 50-27 CG| PREPARED (Instrument Spec) |
| Nominal & Clear Width Values       | 50 values    | Corridor Models   | PREPARED (Baseline Models) |
| In-Situ Field Survey Timestamps    | 0 entries    | Pending Survey    | PENDING_FIELD_EXECUTION    |
| In-Situ Photographic Proof Logs    | 0 entries    | Pending Survey    | PENDING_SURVEY_PHOTOS      |
| In-Situ Surveyor Sign-off Logs     | 0 entries    | Pending Survey    | PENDING_SURVEYOR_SIGNOFF   |
| Regulatory Compliance Claims       | 50 flags     | Model Projections | NOT_VERIFIABLE_EMPIRICALLY |
+------------------------------------+--------------+-------------------+----------------------------+
```

### 5.1 Critical Audit Findings
1. **Corridor Waypoints vs. Surveyed GPS:** The coordinates in the register (e.g., $12.9732^\circ\text{ N}, 77.6205^\circ\text{ E}$) represent designated corridor anchor waypoints along the survey routes, not RTK-GPS surveyor-pinned benchmarks.
2. **Clearance Widths:** The clear-width values (e.g., $1.65\text{ m}$) represent planned cross-sectional measurement targets. In-situ field logs with surveyor signatures and timestamped calibration checks remain pending physical survey deployment.
3. **Regulatory Compliance Ruling:** Claiming formal compliance or non-compliance under **IRC:103-2012** is **NOT EMPIRICALLY VERIFIABLE** until physical laser survey logs and photographic verification proofs are collected in the field.

Full itemized accessibility audit records are published in [`ENCROWATCH_STAGE3_1_ACCESSIBILITY_EVIDENCE_AUDIT.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_1_ACCESSIBILITY_EVIDENCE_AUDIT.csv).

---

## 6. Audit Summary by Deliverable Status

```
+----------------------------------------------------------------------------------------------------+
|                                     OVERALL EVIDENCE STATUS MATRIX                                 |
+-----------------------+--------------------+-------------------------------------------------------+
| Project Deliverable   | Evidence Status    | Audit Summary & Evidentiary Grounding                 |
+-----------------------+--------------------+-------------------------------------------------------+
| Field Collection Plan | PREPARED           | Protocol, routes, and targets fully defined; intake   |
|                       |                    | of genuine Bengaluru images pending field survey.     |
| Dataset Manifest      | PREPARED           | 640 target slots structured; 42 legacy images verified |
|                       |                    | on disk; 882 duplicates excluded.                     |
| CVAT Annotation Plan  | PREPARED           | Multi-task guidelines frozen; 42 task templates ready;|
|                       |                    | full field human annotation pending intake.           |
| Agreement Trial       | VERIFIED (Pilot)   | Kappa = 0.8438, IoU = 0.8398, BF1 = 0.9784 re-verified|
|                       | PENDING (Field)    | on 15 trial pairs; full field agreement pending.      |
| Accessibility Register| PREPARED           | 50 stations mapped with laser specs; in-situ field    |
|                       |                    | logs, photos, and compliance claims pending survey.   |
| Training Readiness    | VERIFIED           | Gating criteria audited; full model training correctly|
|                       |                    | held on discrete NVIDIA RTX 2050 hardware.            |
+-----------------------+--------------------+-------------------------------------------------------+
```
