# EncroWatch AI — Stage 1.3: Synthetic Test Fixture Audit Report

**Research Initiative:** EncroWatch AI  
**Academic Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Degree:** Master of Computer Applications (MCA) — Final-Year Major Academic Research  
**Document Classification:** Software Testing & Data Quarantine Audit (Stage 1.3)  
**Storage Directory:** [`dataset/fixtures/synthetic_smoke_test/`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/fixtures/synthetic_smoke_test/)  
**Artifact Path:** [`ENCROWATCH_SYNTHETIC_FIXTURE_AUDIT.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_SYNTHETIC_FIXTURE_AUDIT.md)  

---

## 1. Context & Methodological Necessity

In accordance with academic research integrity standards:
* **The Problem:** The 42 pilot streetscape images identified in Stage 1.2 are awaiting manual human annotation and dual-annotator agreement verification ($\kappa \ge 0.80$). Under research ethics rules, unverified candidate images must **never** be used for model backpropagation to synthesize pseudo-results.
* **The Engineering Requirement:** The software pipeline (PyTorch CUDA autograd, Ultralytics DataLoader, AMP FP16 engine, loss backpropagation, checkpoint creation) must be empirically proven on the physical NVIDIA RTX 2050 GPU before real data is ingested.
* **The Solution:** A dedicated, disposable **synthetic software testing fixture** was constructed. It provides mathematically valid images and labels purely to test code execution and GPU memory dynamics.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         SYNTHETIC TEST FIXTURE ARCHITECTURAL SUMMARY                             │
├──────────────────────────────────────┬──────────────────────┬────────────────────────────────────┤
│ Property                             │ Value / Setting      │ Research Rationale                 │
├──────────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
│ Designation                          │ SYNTHETIC_FIXTURE    │ Explicitly isolated from research  │
│ Total Volume                         │ 12 synthetic images  │ 8 training, 4 validation           │
│ Resolution                           │ 640 x 640 pixels     │ Standard YOLO input geometry       │
│ Color Space                          │ 3-Channel RGB        │ Simulated asphalt & sidewalk paver │
│ Number of Target Classes             │ 8 Classes (0 to 7)   │ Exact taxonomy from classes.json   │
│ Coordinate Format                    │ Normalized YOLO      │ [class_id, x_c, y_c, w, h] in [0,1]│
│ Bounding Box Validity                │ 100% Pass            │ Zero out-of-bounds / zero negative │
│ Training Output Destination          │ experiments/smoke... │ Separate from research experiments │
└──────────────────────────────────────┴──────────────────────┴────────────────────────────────────┘
```

---

## 2. Directory Hierarchy & Storage Layout

The fixture is maintained in an isolated subfolder completely separate from the real dataset directory:

```
dataset/fixtures/synthetic_smoke_test/
├── images/
│   ├── train/                         # 8 synthetic training images (synth_train_00.jpg - 07.jpg)
│   └── val/                           # 4 synthetic validation images (synth_val_00.jpg - 03.jpg)
├── labels/
│   ├── train/                         # 8 normalized YOLO darknet annotation files (.txt)
│   └── val/                           # 4 normalized YOLO darknet annotation files (.txt)
├── synthetic_data.yaml                # Dedicated YOLO dataset manifest pointing strictly here
└── fixture_manifest.json              # Provenance & class occurrence metadata
```

---

## 3. Class Representation & Label Mathematics

The fixture mathematically verified that the model's detection head can bind to all 8 custom classes:

```
┌───────┬─────────────────────────┬──────────────┬───────────────────┬─────────────────────────────┐
│ ID    │ Class Name              │ Category     │ Generated Boxes   │ Coordinate Bounds Checked   │
├───────┼─────────────────────────┼──────────────┼───────────────────┼─────────────────────────────┤
│ 0     │ motorcycle              │ Vehicular    │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 1     │ car                     │ Vehicular    │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 2     │ vendor_cart             │ Commercial   │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 3     │ construction_debris     │ Barrier      │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 4     │ commercial_signboard    │ Commercial   │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 5     │ shop_extension          │ Commercial   │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 6     │ umbrella_canopy         │ Elevated     │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
│ 7     │ pedestrian              │ Authorized   │ 4 boxes           │ [0.0, 1.0] Normalized (OK)  │
├───────┴─────────────────────────┴──────────────┼───────────────────┴─────────────────────────────┤
│ TOTAL SYNTHETIC INSTANCES                      │ 32 bounding boxes (24 train, 8 val)             │
└────────────────────────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 4. Quarantine & Academic Integrity Safeguards

1. **Zero Data Leakage:** This synthetic fixture has **zero intersection** with the real dataset partitions (`dataset/processed/train`, `val`, `test`).
2. **Zero Paper Influence:** All loss metrics, precision, recall, and mAP values generated by running this fixture are strictly classified as **Software Verification Telemetry** and are quarantined from the revised research paper (`EncroWatch_AI_Complete_Research_Paper_Revised.md`).
3. **Disposal Protocol:** Following completion of Stage 1.3, this fixture remains archived in `dataset/fixtures/` as a regression test benchmark for continuous integration, but will never be bundled into the empirical research deliverables.
