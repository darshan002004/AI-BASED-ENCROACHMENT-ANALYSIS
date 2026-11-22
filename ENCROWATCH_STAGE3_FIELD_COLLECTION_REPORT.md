# EncroWatch AI — Stage 3: Bengaluru Field Dataset Collection and Acquisition Monitoring Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Document Release:** Stage 3 Field Collection Specification  
**Status:** **ACTIVE / FIELD TARGET SPECIFICATION ESTABLISHED**

---

## 1. Executive Summary & Academic Integrity Statement

Stage 3 transitions EncroWatch AI from experimental pipeline preparation to genuine field data acquisition and verified ground-truth completion across metropolitan Bengaluru, India.

> [!IMPORTANT]
> **Academic Integrity Statement:** The numerical dataset volumes specified in this report ($N=600$ street images, $40$ video sequences, $200$ ground-contact masks, $50$ physical clearance measurements, and $60$ expert-evaluated incident logs) are **formal target specifications**, not pre-existing data. In accordance with strict academic research ethics, this report provides a transparent accounting register distinguishing targets, legacy assets, excluded files, and pending field intakes without fabricating geographic surveys.

```
+----------------------------------------------------------------------------------------------------+
|                                    STAGE 3 FIELD INVENTORY ACCOUNTING                              |
+------------------------------+-----------------+-------------------+-------------------------------+
| Data Stream / Category       | Target Quantity | Actual Collected  | Status & Disposition          |
+------------------------------+-----------------+-------------------+-------------------------------+
| Bengaluru Field Images       | 600 images      | 0 field images*   | Target Slots Formatted (W1-4) |
| Temporal Video Sequences     | 40 sequences    | 0 field videos    | Protocol & Gimbal Specs Ready |
| Physical Laser Measurements  | 50 stations     | 50 stations reg.  | Stations Mapped (W1 to W4)    |
| Ground-Contact Masks         | 200 masks       | 0 field masks     | Proxy Heuristic Frozen (40%)  |
| Expert Accessibility Logs    | 60 incidents    | 0 logs            | Survey Template Configured    |
| Quarantined Legacy Pilot     | 42 images       | 42 images (audit) | Isolated (Zero Custom Labels) |
| Excluded Legacy Assets       | N/A             | 882 raw files     | Deduplicated & Excluded       |
+------------------------------+-----------------+-------------------+-------------------------------+
```
*\*Note: The 42 audited legacy prototype images remain isolated under pilot task templates; zero genuine field images have been ingested yet.*

---

## 2. Target Corridors and Geographic Sampling Protocol

Field acquisition follows [`ENCROWATCH_FIELD_COLLECTION_PROTOCOL.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_FIELD_COLLECTION_PROTOCOL.md), sampling across four disjoint urban typologies in Bengaluru to capture the heterogeneous morphology of Indian urban walking corridors.

```
+----------------------------------------------------------------------------------------------------+
|                                    TARGET CORRIDORS BY WARD                                        |
+--------+-------------------------+----------------------+--------------------+---------------------+
| Ward   | Geographic Corridor     | Typology Description | Target Allocation  | Partition Split     |
+--------+-------------------------+----------------------+--------------------+---------------------+
| Ward 1 | MG Road / Brigade Road  | Commercial Arterial  | 150 img / 10 vid   | Train Partition     |
| Ward 2 | Indiranagar 100ft Road  | Commercial & Dining  | 150 img / 10 vid   | Train Partition     |
| Ward 3 | Koramangala 80ft Road   | Mixed-use Arterial   | 150 img / 10 vid   | Validation Partition|
| Ward 4 | BTM Layout 2nd Stage    | Dense Residential    | 150 img / 10 vid   | Test (Quarantined)  |
| TOTAL  | 4 Disjoint Wards        | Comprehensive Urban  | 600 img / 40 vid   | 100% Zero Leakage   |
+--------+-------------------------+----------------------+--------------------+---------------------+
```

### 2.1 Ward Corridor Characteristics
1. **Ward 1 (East) — MG Road / Brigade Road:** High-density pedestrian volume, formal commercial storefronts, heavy intrusion of movable commercial A-frame signboards, temporary promotional banners, and evening hawker carts.
2. **Ward 2 (East) — Indiranagar 100ft Road:** Wide arterial sidewalks frequently interrupted by illegal two-wheeler parking, valet vehicle intrusion, and restaurant outdoor spillover seating.
3. **Ward 3 (South-East) — Koramangala 80ft Road:** Mixed commercial-residential corridor characterized by broken paving slabs, open utility cuts, construction debris aggregate, and semi-permanent vendor stalls.
4. **Ward 4 (South) — BTM Layout 2nd Stage (Quarantined Test Set):** Narrower residential walkways ($1.75–2.05\text{ m}$) with extensive tree canopy interference, domestic vehicle encroachment, and shop extensions, strictly quarantined from model development.

---

## 3. Metadata Recording Schema and Acquisition Parameters

Every field image and video sequence captured must record seven mandatory metadata fields, cataloged in [`ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_VERIFIED_DATASET_MANIFEST.csv):

```
+------------------------------------+---------------------------------------------------------------+
| Metadata Attribute                 | Required Specification & Permitted Values                     |
+------------------------------------+---------------------------------------------------------------+
| Source and Provenance              | "Original Bengaluru Field Collection (Stage 1.4 Protocol)"    |
| Capture Date & Time                | ISO 8601 Timestamp (e.g., 2026-11-15T10:30:00+05:30)          |
| Camera Resolution & Format         | Minimum 1920x1080 (FHD), 24-bit RGB, uncompressed JPEG/PNG    |
| Camera Geometry                    | Height: 1.4-1.6 m; Downward Pitch: 15 to 25 degrees           |
| Lighting & Weather Condition       | Daylight Clear (60%), Overcast (20%), Dusk / Artificial (20%) |
| Permission & Ethics Status         | Public Right-of-Way observation (BBMP Public Pedestrian Space)|
| Privacy Processing Status          | Mandatory bilateral OpenCV Gaussian blur on faces and plates  |
+------------------------------------+---------------------------------------------------------------+
```

---

## 4. Dataset Acquisition Monitoring Register

The operational accounting register tracks collection targets, intake milestones, exclusions, and data gaps:

```
+----------------------------------------------------------------------------------------------------+
|                                  DATASET ACQUISITION MONITORING REGISTER                            |
+--------------------+--------+-----------+-----------+----------+-----------+-----------------------+
| Item Stream        | Target | Collected | Awaiting  | Excluded | Missing   | Primary Reason for    |
|                    | Volume | To-Date   | Verif.    | Assets   | Intake    | Exclusion / Hold      |
+--------------------+--------+-----------+-----------+----------+-----------+-----------------------+
| Ward 1 Field Imgs  | 150    | 0         | 0         | 0        | 150       | Awaiting field survey |
| Ward 2 Field Imgs  | 150    | 0         | 0         | 0        | 150       | Awaiting field survey |
| Ward 3 Field Imgs  | 150    | 0         | 0         | 0        | 150       | Awaiting field survey |
| Ward 4 Field Imgs  | 150    | 0         | 0         | 0        | 150       | Awaiting field survey |
| Video Sequences    | 40     | 0         | 0         | 0        | 40        | Awaiting video intake |
| Physical Laser Stn | 50     | 50 reg.   | 0         | 0        | 0         | Stations designated   |
| Ground Contact Msk | 200    | 0         | 0         | 0        | 200       | Awaiting field intake |
| Legacy Prototype   | 0      | 948 raw   | 42 pilot  | 882      | 0         | Duplicates / overlays |
+--------------------+--------+-----------+-----------+----------+-----------+-----------------------+
```

### 4.1 Detailed Exclusion Breakdown
- **882 Legacy Raw Files Excluded:**
  - 840 files: Exact SHA-256 byte duplicates generated during earlier backend server testing runs.
  - 28 files: Severe low-resolution thumbnails ($< 200\text{ px}$) lacking structural pedestrian detail.
  - 14 files: Pre-annotated visual overlays (burned-in green/red bounding boxes from frontend demo).
- **Quarantined Pilot Candidates (42 images):** Retained in [`dataset/annotations/tasks/`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/annotations/tasks/) for CVAT pipeline calibration only; barred from model training until human ground truth is added.

---

## 5. Separation of External Benchmark and Legacy Assets

To prevent contamination of empirical findings, EncroWatch AI enforces strict directory and provenance separation:

```
dataset/
|-- raw/
|   |-- images/                  <-- EXCLUSIVE HOME FOR TIER 1 BENGALURU FIELD IMAGES
|   |   |-- ward1/               <-- MG Road / Brigade Road (Train)
|   |   |-- ward2/               <-- Indiranagar 100ft Road (Train)
|   |   |-- ward3/               <-- Koramangala 80ft Road (Val)
|   |   `-- ward4/               <-- BTM 2nd Stage (Quarantined Test)
|   `-- videos/                  <-- EXCLUSIVE HOME FOR BENGALURU MP4 SEQUENCES
|-- fixtures/                    <-- QUARANTINED SYNTHETIC SMOKE TEST (Stage 1.3 only)
|-- legacy_quarantine/           <-- ISOLATED 42 PILOT UPLOADS (Awaiting verification)
`-- measurements/                <-- 50 PHYSICAL LASER ACCESSIBILITY STATIONS
```

- **Provenance Separation Guarantee:** No external benchmark (e.g., Cityscapes, Indian Driving Dataset) or legacy prototype upload will ever be merged into `dataset/raw/images/`. All future empirical model benchmarks will evaluate solely on genuine Bengaluru field data.
