# EncroWatch AI — Stage 3.1: Geographic Data Leakage Audit Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Dimension:** Spatial Data Leakage, Scene Disjointness, and Hash Partition Integrity  
**Status Classification:** **VERIFIED (Pilot Legacy Partition) / PREPARED (Target Field Partition)**

---

## 1. Executive Summary & Zero-Leakage Mandate

In computer vision models deployed for urban infrastructure analysis, **geographic data leakage** represents a critical failure mode. If consecutive frames, identical street corners, or near-duplicate storefronts appear across both training and evaluation splits, convolutional neural networks memorize specific background textures rather than learning generalized obstacle features, producing artificially inflated benchmark metrics.

EncroWatch AI enforces strict **Zero-Data-Leakage Geographic Partitioning** across four distinct administrative wards in Bengaluru:

```
+----------------------------------------------------------------------------------------------------+
|                                    GEOGRAPHIC SPLIT ARCHITECTURE                                   |
+------------+-----------------------+-----------------------------+-------------------+-------------+
| Split Role | Assigned Ward         | Primary Street Corridor     | Spatial Buffer    | Target Vol. |
+------------+-----------------------+-----------------------------+-------------------+-------------+
| Train      | Ward 1 (East)         | MG Road / Brigade Road      | Baseline Corridor | 150 img/10v |
| Train      | Ward 2 (East)         | Indiranagar 100ft Road      | > 3.8 km from W1  | 150 img/10v |
| Validation | Ward 3 (South-East)   | Koramangala 80ft Road       | > 4.2 km from W2  | 150 img/10v |
| Test       | Ward 4 (South)        | BTM Layout 2nd Stage        | > 3.5 km from W3  | 150 img/10v |
+------------+-----------------------+-----------------------------+-------------------+-------------+
```

---

## 2. Forensic Audit of Pilot Legacy Dataset Splits

The 42 selected pilot candidate images were forensically evaluated for scene-level and hash-level overlap using [`scripts/dataset_inspection/audit_stage3_evidence.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/dataset_inspection/audit_stage3_evidence.py).

```
+----------------------------------------------------------------------------------------------------+
|                                  PILOT DATASET LEAKAGE AUDIT METRICS                               |
+--------------------------+-----------------------+---------------------+---------------------------+
| Leakage Metric           | Observed Overlap      | Tolerance Threshold | Audit Verification        |
+--------------------------+-----------------------+---------------------+---------------------------+
| Train-Val Scene Overlap  | 0 scenes (0 / 30)     | 0 scenes (Strict)   | VERIFIED ZERO LEAKAGE     |
| Train-Test Scene Overlap | 0 scenes (0 / 30)     | 0 scenes (Strict)   | VERIFIED ZERO LEAKAGE     |
| Val-Test Scene Overlap   | 0 scenes (0 / 14)     | 0 scenes (Strict)   | VERIFIED ZERO LEAKAGE     |
| Train-Val Hash Overlap   | 0 hashes (0 / 34)     | 0 hashes (Strict)   | VERIFIED ZERO LEAKAGE     |
| Train-Test Hash Overlap  | 0 hashes (0 / 35)     | 0 hashes (Strict)   | VERIFIED ZERO LEAKAGE     |
| Val-Test Hash Overlap    | 0 hashes (0 / 15)     | 0 hashes (Strict)   | VERIFIED ZERO LEAKAGE     |
+--------------------------+-----------------------+---------------------+---------------------------+
```

### 2.1 Scene Cluster Disjointness Evidence
- **Train Split (27 images):** Spans 23 distinct scene cluster IDs (`SCENE_01C7665651`, `SCENE_0221674056`, `SCENE_0226F9EF90`, etc.).
- **Validation Split (7 images):** Spans 7 distinct scene cluster IDs (`SCENE_052F0A6F7D`, `SCENE_098FAA67AA`, `SCENE_2DBD00371F`, etc.).
- **Test Split (8 images):** Spans 7 distinct scene cluster IDs (`SCENE_053CBC202E`, `SCENE_1D3D63_6B4DA`, `SCENE_6B4DA95BD5`, `SCENE_PRIVACY_TEST`, etc.).
- **Verdict:** Mathematical intersection across all three sets is $\emptyset$. No physical scene or background building facade crosses partition boundaries.

---

## 3. Video-Level and Temporal Sequence Leakage Safeguards

For the 40 target video sequences ($10$ per ward) specified in [`ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv):

```mermaid
flowchart TD
    A["Raw Gimbal Video Sequence (30 fps)"] --> B["Temporal Sub-sampling: Max 1 frame/sec"]
    B --> C["Consecutive Frame Redundancy Filter"]
    C --> D{"Ward Origin Check"}
    D -- Ward 1 or 2 --> E["Assigned Exclusively to TRAIN Split"]
    D -- Ward 3 --> F["Assigned Exclusively to VAL Split"]
    D -- Ward 4 --> G["Assigned Exclusively to TEST (Quarantined)"]
```

### 3.1 Temporal Redundancy Protocols
1. **Sub-sampling Bound:** Continuous video frames extracted for 2D object detection must be sub-sampled at $\le 1.0\text{ frame per second}$ ($\Delta t \ge 1.0\text{ s}$). Extracting consecutive $30\text{ fps}$ frames produces virtually identical feature maps that inflate validation mAP.
2. **Video-Level Split Atomicity:** Individual video sequences are never split across train and validation. If `BLR_W01_VID_01` is assigned to Ward 1, 100% of its extracted frames belong exclusively to the training split.
3. **Quarantine Governance:** Ward 4 (`BLR_W04_VID_01` to `BLR_W04_VID_10`) is permanently quarantined. Test sequences will be processed once, after model hyperparameter optimization is completely frozen.

---

## 4. Unknown Provenance and Geographic Attribution Rules

In adherence to the instruction: *"Do not assign unknown images to wards without evidence"*:

```
+------------------------------------+---------------------------------------------------------------+
| Provenance Category                | Attribution Rule & Storage Governance                         |
+------------------------------------+---------------------------------------------------------------+
| Genuine Field Data (Tier 1)        | Certified GPS coordinate and surveyor timestamp required.     |
| Legacy Pilot Images (N=42)         | Marked as "Provisional Ward Assignment" in metadata;          |
|                                    | barred from formal geographic generalization claims.          |
| Legacy Uploads without GPS         | Assigned to "UNVERIFIED_LEGACY_ARCHIVE" partition;            |
|                                    | never assigned to Bengaluru Wards 1 to 4.                     |
+------------------------------------+---------------------------------------------------------------+
```

- **Zero False Attribution Guarantee:** No image without verified field provenance will be attributed to Bengaluru field corridors in final MCA research publications.
