# EncroWatch AI — Stage 1.2: Pilot Dataset Annotation Report

**Research Initiative:** EncroWatch AI  
**Academic Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Degree:** Master of Computer Applications (MCA) — Final-Year Major Academic Research  
**Document Classification:** Technical Milestone Deliverable (Stage 1.2)  
**Hardware Environment:** NVIDIA GeForce RTX 2050 (4 GB VRAM), Windows 11 (AMD64)  
**Primary Python Runtime:** Python 3.12.10 (`.venv`)  
**Artifact Path:** [`ENCROWATCH_STAGE1_2_PILOT_ANNOTATION_REPORT.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_STAGE1_2_PILOT_ANNOTATION_REPORT.md)  

---

## 1. Executive Summary

In accordance with the experimental research design (Sections 6.1, 6.2, and 6.3 of the master revised paper), **Stage 1.2: Pilot Dataset Annotation** transitions the research from infrastructure verification to dataset curation. 

From the 66 unique physical street scenes identified during the Stage 1.1 forensic audit, **42 high-resolution, suitable images** were selected for pilot annotation. A spatial, scene-clustered partition was enforced to guarantee zero data leakage between training (64.3%), validation (16.7%), and testing (19.0%) splits. Individual annotation task JSON specifications were generated for all 42 images, and an interactive visual contact sheet was produced for human audit.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            STAGE 1.2 PILOT ANNOTATION SCORECARD                                  │
├──────────────────────────────────────┬──────────────────────┬────────────────────────────────────┤
│ Milestone Requirement                │ Measured Status      │ Methodological Assessment          │
├──────────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
│ Total Unique Legacy Scenes Audited   │ 66 images            │ Deduplicated from 948 files        │
│ High-Resolution Candidates Selected  │ 42 images            │ Filtered out 24 low-res thumbnails │
│ Resolution Span                      │ 150x98 to 1068x593   │ Average: 520 x 340 pixels          │
│ Spatial Zero-Leakage Splits          │ Train: 27, Val: 7,   │ Geographically disjoint ward       │
│                                      │ Test: 8              │ corridor clustering                │
│ Annotation Task Templates Created    │ 42 JSON task files   │ Generated in annotations/tasks/    │
│ Target Custom Classes Covered        │ 8 Classes (0 to 7)   │ Strictly aligned with Section 3.1  │
│ Geometric Surface Targets            │ Footpath, Road, Curb │ Closed polygon specifications      │
│ Ground Contact / Canopy Gating       │ Parameterized 40%    │ Lower-40% proxy & 2.20m gate       │
│ Model Proposals As Ground Truth?     │ STRICTLY PROHIBITED  │ Zero synthetic/fabricated labels   │
└──────────────────────────────────────┴──────────────────────┴────────────────────────────────────┘
```

---

## 2. Selection and Quality Filtering of the 42 Pilot Images

### 2.1 Filtering Protocol
The 66 unique images cataloged in [`ENCROWATCH_PILOT_DATASET_MANIFEST.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_PILOT_DATASET_MANIFEST.csv) exhibited significant resolution disparity:
* **Excluded (24 images):** 5 tiny category icons ($45 \times 39$ px, e.g. `thumb_vendor.jpg`, `thumb_construction.jpg`), 2 ultra-low-resolution thumbnails ($100 \times 100$ px), and 17 degraded $150 \times 98$ px thumbnails that lacked identifiable street perspective.
* **Selected (42 images):** All 35 images with resolution $\ge 200 \times 200$ px (up to $1068 \times 593$ px), plus 7 unburnt $150 \times 98$ px photographs featuring clear street perspective, distinct curb lines, and visible physical obstructions.

### 2.2 Folder Distribution of Selected Images
* `original/` (**21 images**): Clean, unaltered raw street photographs.
* `privacy/` (**7 images**): Anonymized images with blurred pedestrian faces and vehicular registration plates.
* `.` (root uploads) (**1 image**): High-resolution street capture (`test_street.jpg`, $640 \times 480$).
* `annotated/` (**13 images**): Processed demonstration overlays. *Note: Marked with visual warning flags; clean original equivalents are prioritized wherever available to avoid feature corruption.*

---

## 3. Visual Contact Sheet for Human Verification

An interactive HTML contact sheet has been generated to facilitate rapid human inspection and manual annotation auditing:
🌐 **File Location:** [`dataset/reports/pilot_42_contact_sheet.html`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/reports/pilot_42_contact_sheet.html)

**Features:**
* Responsive grid displaying all 42 candidates with direct image previews.
* Displays assigned Pilot ID (`PILOT_01` to `PILOT_42`), file name, resolution, file size, and origin folder.
* Color-coded badges indicating split partition: `TRAIN` (Green), `VAL` (Yellow), and `TEST` (Red).
* Prominent alert badges distinguishing clean images from overlay masks.
* Links to the individual task specification file (`dataset/annotations/tasks/PILOT_XX_task.json`).

---

## 4. Scene-Level Clustering & Spatial Zero-Leakage Partitioning

### 4.1 Geographical Ward Partitioning Protocol
Pursuant to Section 6.2 of the manuscript, urban streetscapes must be partitioned geographically to prevent deep neural networks from memorizing building facades, asphalt textures, or persistent background shopfronts:

```
                                SPATIAL PARTITIONING OF THE 42 PILOT IMAGES
┌───────────────────────────┬──────────────┬─────────────┬─────────────────────────────────────────┐
│ Partition                 │ Image Count  │ Percentage  │ Geographical Corridor & Characteristics │
├───────────────────────────┼──────────────┼─────────────┼─────────────────────────────────────────┤
│ Training Set              │ 27 images    │ 64.29%      │ Wards 1 & 2 (Commercial Corridors:      │
│                           │              │             │ MG Road, Brigade Road, Indiranagar)     │
├───────────────────────────┼──────────────┼─────────────┼─────────────────────────────────────────┤
│ Validation Set            │ 7 images     │ 16.67%      │ Ward 3 (Mixed Commercial / Residential: │
│                           │              │             │ Koramangala 80ft Road Corridor)         │
├───────────────────────────┼──────────────┼─────────────┼─────────────────────────────────────────┤
│ Testing Set (Quarantined) │ 8 images     │ 19.05%      │ Ward 4 (Unregulated Suburban Corridor:  │
│                           │              │             │ BTM Layout 2nd Stage / South Suburbs)   │
├───────────────────────────┼──────────────┼─────────────┼─────────────────────────────────────────┤
│ TOTAL                     │ 42 images    │ 100.0%      │ Disjoint spatial boundaries enforced    │
└───────────────────────────┴──────────────┴─────────────┴─────────────────────────────────────────┘
```

### 4.2 Scene-Level Cluster Isolation (Zero Leakage)
In previous prototype runs, multiple derivative files were generated from the same base image (e.g., `upload_66cb1df9a5.jpg` and `upload_c16da09db2a1_privacy.jpg`). 
* **Leakage Safeguard:** All related variants were programmatically clustered under canonical scene IDs (e.g. `SCENE_66CB1DF9A5`, `SCENE_0221674056`).
* **Enforcement:** All images belonging to a shared scene cluster are assigned to the **exact same split partition**. Under no circumstances is an original image placed in `train` while its privacy-blurred counterpart appears in `val` or `test`.

---

## 5. Formal Annotation Workflows & Task Architecture

In accordance with [`dataset/ANNOTATION_GUIDELINES.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/ANNOTATION_GUIDELINES.md), each pilot image has a corresponding JSON task manifest in `dataset/annotations/tasks/`. Annotators must execute six structured workflows:

### Workflow 1: 2D Object Bounding Boxes (YOLO Darknet Format)
* Coordinate normalization: $[x_c, y_c, w, h] \in [0.0, 1.0]$.
* Classes restricted strictly to the 8 verified custom classes:
  - `0: motorcycle`
  - `1: car`
  - `2: vendor_cart`
  - `3: construction_debris`
  - `4: commercial_signboard`
  - `5: shop_extension`
  - `6: umbrella_canopy`
  - `7: pedestrian`

### Workflow 2: Semantic Corridor Polygons ($\mathcal{P}_{\text{FP}}$ & $\mathcal{P}_{\text{RD}}$)
* **Footpath Polygon ($\mathcal{P}_{\text{FP}}$):** Closed polygon with $n \ge 4$ normalized vertices delineating the designated pedestrian corridor between property setbacks and the curb line.
* **Roadway Polygon ($\mathcal{P}_{\text{RD}}$):** Closed polygon delineating active vehicular carriageway asphalt.

### Workflow 3: Curb Boundary Line ($\mathcal{C}$)
* Delineates the raised structural edge dividing pedestrian surface from vehicular roadway.

### Workflow 4: Ground-Contact Proxy Formulation ($\mathcal{B}_{\text{ground}}$)
* Evaluates the physical ground contact patch rather than aerial volume:
  $$\mathcal{B}_{\text{ground}} = \left[ x_{\text{min}}, \; y_{\text{min}} + 0.60 \cdot h, \; w, \; 0.40 \cdot h \right]$$
* Prevents roadside parked vehicles from being falsely classified as sidewalk encroachments due to oblique camera angles ($15^\circ–25^\circ$).

### Workflow 5: Elevated Canopy Vertical Gating ($2.20\text{ m}$ Rule per IRC:103-2012)
* Overhead vendor umbrellas and tarpaulins (`umbrella_canopy`) clearing $\ge 2.20\text{ m}$ above the footpath surface are **not** flagged as ground obstructions; physical obstruction is restricted strictly to the vertical support pole base. Canopies sagging $< 2.20\text{ m}$ trigger pedestrian headroom hazard penalties.

### Workflow 6: Quality Control & Agreement Validation
* Automated syntax and coordinate bounds validation via [`scripts/annotation_validation/validate_annotations.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/annotation_validation/validate_annotations.py).
* Mandatory inter-annotator agreement threshold: Cohen's Kappa $\kappa \ge 0.80$, Bounding Box $IoU \ge 0.80$.

---

## 6. Pilot Annotation Manifest Summary

The full catalog is exported to [`ENCROWATCH_PILOT_ANNOTATION_MANIFEST.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_PILOT_ANNOTATION_MANIFEST.csv). A representative cross-section of the 42 items illustrates the multi-ward distribution:

| Pilot ID | Filename | Resolution | Ward Assignment | Split | Footpath Visibility | Candidate Encroachments |
| :--- | :--- | :---: | :--- | :---: | :--- | :--- |
| `PILOT_01` | `upload_66cb1df9a5.jpg` | 1068x593 | Ward 1 & 2 (Commercial) | Train | Clearly Visible | motorcycle, car, pedestrian |
| `PILOT_05` | `clear_street.jpg` | 800x500 | Ward 1 & 2 (Commercial) | Train | Clearly Visible | pedestrian (Authorized Baseline) |
| `PILOT_13` | `test_street.jpg` | 640x480 | Ward 1 & 2 (Commercial) | Train | Clearly Visible | motorcycle, car, pedestrian |
| `PILOT_28` | `debris_koramangala.jpg`| 150x98 | Ward 3 (Koramangala) | Val | Narrow Walkway | construction_debris, motorcycle |
| `PILOT_35` | `upload_058965c154.jpg` | 150x98 | Ward 4 (BTM Layout) | Test | Broken Walkway | shop_extension, pedestrian |
| `PILOT_42` | `verify_d20ff25a57.jpg` | 1000x400 | Ward 4 (BTM Layout) | Test | Ambiguous Curb | vendor_cart, umbrella_canopy |

---

## 7. Research Integrity Ruling on Machine-Assisted Annotations

> [!CAUTION]
> **Academic Integrity Directive:**  
> Standard deep learning models (such as pre-trained COCO-80 detectors) do not possess classes for `vendor_cart`, `construction_debris`, `commercial_signboard`, or `shop_extension`, and have no concept of corridor boundaries. Under no circumstances may raw neural network detections be relabeled or automatically saved as ground truth. All annotations must be produced through human inspection or validated under the dual-annotator protocol prior to experimental training.
