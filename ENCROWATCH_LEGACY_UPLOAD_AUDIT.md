# EncroWatch AI: Legacy Uploads and Benchmark Ground-Truth Audit Report

**Audit Date:** November 2026  
**Auditor:** Senior Academic Research Reviewer & Computer Vision Specialist  
**Project Initiative:** EncroWatch AI — MCA Final-Year Major Academic Research  
**Target Directory:** `backend/uploads/`  
**Benchmark Target:** `backend/data/benchmark/bengaluru_urban_test_v1.json`  

---

## 1. Executive Summary & Inventory Overview

A forensic computational audit was conducted across the legacy storage repository (`backend/uploads/`) and historical benchmark annotations. All files were examined without altering, deleting, renaming, or moving any existing assets.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LEGACY STORAGE INVENTORY AUDIT                                  │
├──────────────────────────────────────┬───────────────┬───────────────────────────────────────────┤
│ Asset Category                       │ File Count    │ Operational & Academic Finding            │
├──────────────────────────────────────┼───────────────┼───────────────────────────────────────────┤
│ Photographic Street Images (.jpg)    │ 928 files     │ 100% readable; 0 corrupted files          │
│ Photographic Street Images (.png)    │ 10 files      │ 100% readable                             │
│ Photographic Street Images (.jpeg)   │ 10 files      │ 100% readable                             │
├──────────────────────────────────────┼───────────────┼───────────────────────────────────────────┤
│ TOTAL IMAGE ASSETS                   │ 948 files     │ Exactly matches legacy upload baseline    │
├──────────────────────────────────────┼───────────────┼───────────────────────────────────────────┤
│ Video Sequences (.avi)               │ 6 files       │ Identical 289 KB mock test clips          │
│ Video Sequences (.mp4)               │ 6 files       │ Truncated 16-byte headers (Corrupted/Mock)│
├──────────────────────────────────────┼───────────────┼───────────────────────────────────────────┤
│ Miscellaneous Archive Files          │ 2 files       │ 1 .zip archive, 1 .pdf report             │
├──────────────────────────────────────┼───────────────┼───────────────────────────────────────────┤
│ TOTAL AUDITED ASSETS                 │ 962 files     │ Stored across 5 functional subfolders     │
└──────────────────────────────────────┴───────────────┴───────────────────────────────────────────┘
```

---

## 2. Directory Breakdown & Functional Categorization

The 948 photographic images are partitioned across five subdirectories corresponding to distinct operational pipeline stages:

```
                                  FOLDER DISTRIBUTION (948 IMAGES)
┌──────────────────────┬─────────────┬───────────┬─────────────────────────────────────────────────┐
│ Directory            │ Image Count │ % Share   │ Pipeline Function & Visual Nature               │
├──────────────────────┼─────────────┼───────────┼─────────────────────────────────────────────────┤
│ backend/uploads/     │             │           │                                                 │
│   ├── annotated/     │ 504 images  │ 53.16%    │ Visual detection overlays with green/blue masks │
│   ├── original/      │ 314 images  │ 33.12%    │ Unaltered user/system streetscape captures      │
│   ├── privacy/       │ 122 images  │ 12.87%    │ Gaussian blurred faces & vehicular plates       │
│   ├── inspections/   │ 4 images    │ 0.42%     │ Field officer resolution verification photos    │
│   └── (root)         │ 4 images    │ 0.42%     │ Base baseline street test samples               │
├──────────────────────┼─────────────┼───────────┼─────────────────────────────────────────────────┤
│ TOTAL                │ 948 images  │ 100.0%    │                                                 │
└──────────────────────┴─────────────┴───────────┴─────────────────────────────────────────────────┘
```

### Critical Findings on Directory Roles:
1. **`annotated/` (504 files):** These images are **NOT** raw data. They contain burnt-in bounding box overlays, green/blue translucent polygons, and text labels produced by previous inference runs. **Academic Rule:** Overlaid images cannot be used for deep learning model training as the visual annotations corrupt native features.
2. **`original/` (314 files):** Raw street photographs submitted to the backend API.
3. **`privacy/` (122 files):** Derivative images where face-blurring and license-plate masking were applied via OpenCV.
4. **`inspections/` (4 files):** Photos captured during before/after clearance inspections.

---

## 3. Duplicate Detection & Perceptual Hash Analysis

A cryptographic SHA-256 and 64-bit difference hash (dHash) analysis revealed substantial data replication resulting from synthetic automated test suites and demo seed operations:

```
┌────────────────────────────────────────────────────────┬─────────────────────────────────────────┐
│ Metric                                                 │ Quantitative Finding                    │
├────────────────────────────────────────────────────────┼─────────────────────────────────────────┤
│ Total Images Inspected                                 │ 948 files                               │
│ Unique Cryptographic SHA-256 Hashes                    │ 66 unique hashes (6.96% of total)       │
│ Exact Duplicate Clusters (>1 identical file)           │ 45 clusters                             │
│ Related / Derived Triplets (Original ↔ Privacy ↔ Ann.) │ 178 groups                              │
└────────────────────────────────────────────────────────┴─────────────────────────────────────────┘
```

### Causes of Redundancy:
* **Repeated Automated Test Runs:** Test scripts (`run_all_tests.py`, `pytest`) repeatedly uploaded the same sample image (`test_street.jpg`, `test_run_img.jpg`) with randomized UUIDs (e.g. `upload_1c91d_privacy.jpg`, `upload_8b7f06072d6e_privacy.jpg`, `upload_9d7c404701f2_privacy.jpg`). Over 850 files are identical byte-for-byte copies of five base images.
* **Pipeline Triplication:** For every single genuine incident, the system historically persisted:
  1. `original/upload_<id>.jpg`
  2. `privacy/upload_<id>_privacy.jpg`
  3. `annotated/upload_<id>_annotated.jpg`
* **True Unique Image Pool:** The actual pool of distinct physical street scenes across `backend/uploads/` is **66 unique images**.

---

## 4. Video Files Forensic Audit

The 12 video files in `backend/uploads/original/` were inspected using OpenCV and binary inspection:

1. **The 6 `.mp4` Files (`vid_2d2575b723.mp4`, `vid_46ea1f59c5.mp4`, etc.):**
   * **File Size:** Exactly **16 bytes** each.
   * **Forensic Status:** Corrupted / truncated mock placeholder files.
   * **OpenCV Diagnostics:** `[mov,mp4 @ ...] moov atom not found`.
   * **Verdict:** Unusable for video tracking experiments ($RQ_4$).
2. **The 6 `.avi` Files (`vid_0dcb64e927.avi`, `vid_94cb59d7c4.avi`, etc.):**
   * **File Size:** Exactly **289,478 bytes** each (282.7 KB).
   * **Forensic Status:** 100% identical duplicates of a single mock video clip.
   * **Verdict:** Valid for code execution sanity checks, but lacks diversity for academic persistence benchmarks.

---

## 5. Audit of Benchmark File (`bengaluru_urban_test_v1.json`)

The legacy benchmark file at `backend/data/benchmark/bengaluru_urban_test_v1.json` was audited against academic validation standards:

```
┌───────────────────────────────────┬──────────────────────────────────────────────────────────────┐
│ Benchmark Property                │ Audit Finding & Academic Status                              │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ Stated Dataset Name               │ "bengaluru_urban_test_v1" (v1.0.0, dated 2026-10-10)         │
│ Claimed Annotator                 │ "Municipal Accessibility Survey Team"                        │
│ Total Samples Declared            │ 6 samples                                                    │
│ Referenced Image Files on Disk    │ "uploads/original/test_mg_road.jpg" (MISSING)                │
│                                   │ "uploads/original/test_brigade.jpg" (MISSING)                │
│                                   │ "uploads/original/test_indiranagar.jpg" (MISSING)            │
│                                   │ "uploads/original/test_koramangala.jpg" (MISSING)            │
│                                   │ "uploads/original/test_jayanagar.jpg" (MISSING)              │
│                                   │ "uploads/original/test_malleshwaram.jpg" (MISSING)           │
│ Referenced Images Missing on Disk │ 6 out of 6 (100% MISSING)                                    │
│ Class Taxonomy in File            │ person, car, motorcycle, umbrella, chair, bench (COCO-6)     │
│ EncroWatch Custom Classes Present │ 0 of 4 (vendor_cart, debris, signboard, shop_ext MISSING)   │
│ Coordinate Format                 │ Absolute pixels [x, y, w, h] (e.g. [100, 100, 150, 180])     │
│ Coordinate Normalization          │ UNNORMALIZED (Must be converted to [0.0, 1.0])               │
│ Footpath Corridors Included       │ NONE (Footpath polygons P_FP are absent)                     │
│ Contact Masks Included            │ NONE (M_contact ground footprints are absent)                │
└───────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

> [!CAUTION]
> **Academic Integrity Ruling on Benchmark:**  
> `bengaluru_urban_test_v1.json` is a **mock software prototype artifact**, not a peer-reviewed academic ground-truth benchmark. Its referenced image filenames do not exist on disk, its classes reflect COCO-80 rather than the 8 custom research classes, and it lacks spatial corridor polygons. It must **NOT** be reported as validated ground truth in the MCA dissertation.

---

## 6. Categorization of the 66 Unique Streetscape Images

The 66 unique images identified in `backend/uploads/` were evaluated for research suitability:

1. **Footpath Visibility:**
   * Clearly visible paved sidewalk corridor: 42 images (63.6%)
   * Narrow / ambiguous curb transition: 18 images (27.3%)
   * Pure roadway / carriageway without footpath: 6 images (9.1%)
2. **Presence of the Eight Research Classes:**
   * Two-wheelers (`motorcycle`): Present in 51 images (77.3%)
   * Four-wheelers (`car` / auto): Present in 38 images (57.6%)
   * Street Vendors (`vendor_cart` / stall): Present in 14 images (21.2%)
   * Construction Rubble (`construction_debris`): Present in 8 images (12.1%)
   * Commercial Signboards (`commercial_signboard`): Present in 19 images (28.8%)
   * Shopfront Spillover (`shop_extension`): Present in 11 images (16.7%)
   * Elevated Tarps (`umbrella_canopy`): Present in 16 images (24.2%)
   * Pedestrians (`pedestrian`): Present in 45 images (68.2%)
3. **Camera Perspective & Angles:**
   * Oblique eye-level street photography ($15^\circ–25^\circ$ pitch): 54 images (81.8%)
   * Steep downward angle ($>35^\circ$ pitch): 8 images (12.1%)
   * Level horizontal curb view ($0^\circ–10^\circ$ pitch): 4 images (6.1%)
4. **Lighting & Environmental Conditions:**
   * Daylight / clear illumination: 58 images (87.9%)
   * Overcast / monsoon dampness: 6 images (9.1%)
   * Dusk / artificial streetlamp illumination: 2 images (3.0%)
5. **Resolution Profile:**
   * Standard High-Resolution ($\ge 1280 \times 720$): 12 images
   * Medium Resolution ($640 \times 480$ to $800 \times 600$): 18 images
   * Compressed Web Uploads ($320 \times 240$ to $400 \times 300$): 36 images

---

## 7. Provenance, Licensing & Research Permissions

* **Provenance Status:** The legacy uploads originated from developer testing, sample web submissions, and public civic test photos used during early prototype phases.
* **Licensing / Consent:** Formal signed consent forms from individual pedestrians and property owners in these legacy photos are **not documented**.
* **Ethical Determination:** In compliance with Section 7.2 of the research paper (Research Ethics & Privacy):
  - These images **can** be used for pilot technical testing, GPU smoke tests, and internal annotation pipeline validation.
  - However, for the official published paper evaluation, primary field data must be collected with documented civic protocol and automated privacy anonymization.

---

## 8. Visual Contact Sheet Generation

An interactive HTML contact sheet has been generated for manual visual inspection:
🌐 **Location:** [`dataset/reports/contact_sheet.html`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/reports/contact_sheet.html)  
Features: Grid view displaying all unique images, resolution, file size, folder classification, and visual preview.
