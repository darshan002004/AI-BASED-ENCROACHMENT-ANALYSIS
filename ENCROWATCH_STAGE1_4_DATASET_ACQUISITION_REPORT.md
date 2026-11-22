# EncroWatch AI — Stage 1.4: Tier 1 Bengaluru Dataset Acquisition Report

**Research Initiative:** EncroWatch AI  
**Academic Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Degree:** Master of Computer Applications (MCA) — Final-Year Major Academic Research  
**Document Classification:** Empirical Data Sourcing & Infrastructure Report (Stage 1.4)  
**Hardware Profile:** NVIDIA GeForce RTX 2050 (4 GB VRAM), Windows 11 (AMD64)  
**Source Register:** [`ENCROWATCH_DATASET_SOURCE_REGISTER.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_DATASET_SOURCE_REGISTER.csv)  
**Artifact Path:** [`ENCROWATCH_STAGE1_4_DATASET_ACQUISITION_REPORT.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_STAGE1_4_DATASET_ACQUISITION_REPORT.md)  

---

## 1. Executive Summary & Sourcing Taxonomy

In accordance with Stage 1.4 requirements, a formal **Dataset Source Register** has been established to categorize and quarantine all empirical and software assets. To prevent methodological corruption, four mutually exclusive dataset categories are enforced:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DATASET SOURCE CATEGORIZATION                                    │
├──────────────────────────┬───────────────────┬──────────────┬────────────────────────────────────┤
│ Category                 │ Target Asset      │ Volume       │ Academic Function                  │
├──────────────────────────┼───────────────────┼──────────────┼────────────────────────────────────┤
│ 1. Bengaluru Field       │ Primary Field     │ 1,200 images │ Primary empirical target for       │
│    Survey (Tier 1)       │ Corpus            │ 25 videos    │ validating hypotheses RQ1 to RQ5   │
├──────────────────────────┼───────────────────┼──────────────┼────────────────────────────────────┤
│ 2. Public External       │ IDD, Cityscapes,  │ ~16,242 imgs │ Semantic corridor pre-training and │
│    Datasets              │ FootpathVision    │ audited      │ literature baseline comparisons    │
├──────────────────────────┼───────────────────┼──────────────┼────────────────────────────────────┤
│ 3. Legacy Prototype      │ backend/uploads/  │ 948 files    │ Pilot pipeline inspection, visual  │
│    Uploads               │                   │ (66 unique)  │ contact sheets, & task templates   │
├──────────────────────────┼───────────────────┼──────────────┼────────────────────────────────────┤
│ 4. Synthetic Software    │ dataset/fixtures/ │ 12 synthetic │ GPU training pipeline smoke test;  │
│    Fixtures              │                   │ images       │ zero research accuracy reported    │
└──────────────────────────┴───────────────────┴──────────────┴────────────────────────────────────┘
```

---

## 2. In-Depth Audit of the Dataset Source Register

The full register is preserved in [`ENCROWATCH_DATASET_SOURCE_REGISTER.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_DATASET_SOURCE_REGISTER.csv). Key findings for each source:

### Source 1: EncroWatch Primary Field Survey (Bengaluru Wards 1–4)
* **Status:** Primary Research Target.
* **Geographical Scope:** Ward 1 (MG Road / Brigade Road), Ward 2 (Indiranagar 100ft Road), Ward 3 (Koramangala 80ft Road), Ward 4 (BTM Layout 2nd Stage).
* **Target Volume:** $N = 1,200$ images, $N = 25$ video clips, $N = 200$ contact masks, $N = 50$ physical laser measurements, $N = 60$ expert-reviewed incidents.
* **Governing Document:** [`ENCROWATCH_FIELD_COLLECTION_PROTOCOL.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_FIELD_COLLECTION_PROTOCOL.md).

### Source 2: Indian Driving Dataset (IDD)
* **Origin:** IIIT Hyderabad & Intel India (IEEE WACV 2019).
* **Volume:** 10,004 fine annotations across 182 drive sequences in Bengaluru and Hyderabad.
* **Suitability:** High value for fine-tuning semantic segmentation backbones on Indian curb and asphalt transitions.
* **Limitation:** Captured strictly from a $1.2\text{ m}$ vehicular dashboard perspective. It lacks pedestrian walkability annotations and does not classify roadside parked vehicles as civic encroachments.

### Source 3: Cityscapes Dataset
* **Origin:** European cities (IEEE CVPR 2016).
* **Volume:** 5,000 fine annotations, 20,000 coarse annotations.
* **Suitability:** Gold standard for pre-training general urban feature extractors.
* **Limitation:** Severe domain collapse when tested on Indian streetscapes (dropping from $>80\%$ to $\approx 55\%$ mIoU). Completely lacks informal commercial pushcarts, rubble heaps, and unpaved sidewalk geometry.

### Source 4: FootpathVision Dataset
* **Origin:** Dhaka, Bangladesh (SSRN Preprint 2025).
* **Volume:** 1,238 photographic images.
* **Suitability:** Comparable urban context for isolated 2D detection comparisons ($RQ_1$).
* **Limitation:** Contains 2D bounding boxes only. It lacks ground-contact footprint masks ($\mathcal{M}_{\text{contact}}$) and semantic corridor polygons ($\mathcal{P}_{\text{FP}}$).

### Source 5: Project Sidewalk & Sidewalk Accessibility Deep Learning
* **Origin:** University of Washington (ACM ASSETS 2019).
* **Volume:** 205,385 crowd labels across 2,941 audited street miles.
* **Suitability:** Excellent methodological literature baseline for wheelchair accessibility auditing.
* **Limitation:** Evaluates fixed physical infrastructure defects (missing curb ramps, surface cracks) from Google Street View crops; does not evaluate dynamic urban encroachments.

### Source 6: CitySurfaces Dataset
* **Origin:** ISPRS Journal of Photogrammetry and Remote Sensing (2022).
* **Volume:** ~14,000 sidewalk patch crops.
* **Suitability:** Surface material texture reference (concrete, asphalt, pavers).
* **Limitation:** No object bounding boxes or obstacle coordinates.

### Source 7: Legacy Prototype Uploads
* **Origin:** Local repository (`backend/uploads/`).
* **Volume:** 948 files (66 unique physical scenes).
* **Suitability:** Serves as the candidate pool for the Stage 1.2 pilot dataset.
* **Limitation:** Lack signed civic consent forms and survey metadata; 882 files are duplicate test copies or burned-in visualization overlays.

### Source 8: Disposable Synthetic Software Fixture
* **Origin:** Local generator (`dataset/fixtures/synthetic_smoke_test/`).
* **Volume:** 12 synthetic images (8 train, 4 val).
* **Suitability:** Verified the complete PyTorch CUDA training pipeline in Stage 1.3 (peak VRAM: 227 MB).
* **Limitation:** Artificial geometric textures; zero research accuracy may be claimed.

---

## 3. Disjoint Spatial Splitting Architecture

To guarantee zero data leakage between training, validation, and testing sets:

```
┌────────────────────────────────────────────────────────┬─────────────────────────────────────────┐
│ Dataset Split Partition                                │ Geographic Corridor Assignment          │
├────────────────────────────────────────────────────────┼─────────────────────────────────────────┤
│ Training Set (60%)                                     │ Ward 1 (MG Road) & Ward 2 (Indiranagar) │
│ Validation Set (20%)                                   │ Ward 3 (Koramangala 80ft Road)          │
│ Testing Set (20% - QUARANTINED)                        │ Ward 4 (BTM Layout 2nd Stage)           │
└────────────────────────────────────────────────────────┴─────────────────────────────────────────┘
```

* **Spatial Quarantine:** Data from Ward 4 is quarantined permanently for model evaluation. It must never participate in gradient updates, learning rate tuning, or model selection.
* **Video Isolation:** Video sequences are partitioned at the whole-clip level, never by frame interleaving.

---

## 4. Current Status & Required Human Actions

```
┌────────────────────────────────────────────────────────┬─────────────────────────────────────────┐
│ Milestone Task                                         │ Current Completion Status               │
├────────────────────────────────────────────────────────┼─────────────────────────────────────────┤
│ Dataset Source Register Formulated                     │ COMPLETED (ENCROWATCH_DATASET_SOURCE...)│
│ Field Collection Protocol Authored                     │ COMPLETED (ENCROWATCH_FIELD_COLLECT...) │
│ Public Datasets Audited & Mapped                       │ COMPLETED (6 Datasets Audited)          │
│ Physical On-Site Field Survey                          │ PENDING (Requires on-site survey team)  │
│ Optical Laser Distance Meter Cross-Sections            │ PENDING (Requires on-site laser survey) │
│ Dual-Annotator Verification (κ >= 0.80)                │ PENDING (Requires human annotation pass)│
└────────────────────────────────────────────────────────┴─────────────────────────────────────────┘
```
