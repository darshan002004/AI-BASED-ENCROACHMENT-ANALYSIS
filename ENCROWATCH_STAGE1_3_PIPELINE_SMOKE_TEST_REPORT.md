# EncroWatch AI — Stage 1.3: GPU Training Pipeline Smoke Test Report

**Research Initiative:** EncroWatch AI  
**Academic Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Degree:** Master of Computer Applications (MCA) — Final-Year Major Academic Research  
**Document Classification:** Software Engineering & Hardware Pipeline Verification (Stage 1.3)  
**Hardware Environment:** NVIDIA GeForce RTX 2050 Laptop GPU (4,095.5 MiB VRAM), Windows 11 (AMD64)  
**Runtime:** Python 3.12.10 (`.venv`), PyTorch 2.6.0+cu124, Ultralytics 8.4.208  
**Artifact Path:** [`ENCROWATCH_STAGE1_3_PIPELINE_SMOKE_TEST_REPORT.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_STAGE1_3_PIPELINE_SMOKE_TEST_REPORT.md)  

---

## 1. Executive Summary & Verification Determination

In accordance with Stage 1.3 requirements, a complete end-to-end training pipeline smoke test was executed on the target **NVIDIA GeForce RTX 2050 Laptop GPU**. 

Because genuine human annotations for the 42 pilot images remain in `TASK_PREPARED_AWAITING_MANUAL_VERIFICATION` status, a separate disposable synthetic dataset fixture (`dataset/fixtures/synthetic_smoke_test/`) was constructed solely to test software execution. **Zero research metrics or accuracy claims are derived from this test.**

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 1.3 PIPELINE VERIFICATION SCORECARD                                │
├──────────────────────────────────────┬──────────────────────┬────────────────────────────────────┤
│ Pipeline Component                   │ Verification Result  │ Operational Assessment             │
├──────────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
│ PyTorch DataLoader                   │ VERIFIED             │ 8 train batches, 4 val batches     │
│ Forward Pass (FP16 AMP)              │ VERIFIED             │ 181 layers, 2.59M parameters       │
│ Multi-Task Loss Calculation          │ VERIFIED             │ Box, Cls, and DFL losses computed  │
│ Autograd Backward Propagation        │ VERIFIED             │ Gradients computed on cuda:0       │
│ Optimizer Weight Update              │ VERIFIED             │ AdamW parameters updated           │
│ Checkpoint Creation                  │ VERIFIED             │ last.pt (5.25 MB), best.pt (5.25MB)│
│ Peak GPU VRAM Occupancy              │ 227.07 MB / 4095.5 MB│ 5.54% of capacity (94.46% buffer)  │
│ Total Execution Duration             │ 60.94 seconds        │ 0 OOM errors; 0 CUDA faults        │
├──────────────────────────────────────┼──────────────────────┼────────────────────────────────────┤
│ FINAL PIPELINE VERDICT               │ PASSED               │ Training pipeline fully functional │
└──────────────────────────────────────┴──────────────────────┴────────────────────────────────────┘
```

---

## 2. Environment & Dependency Status

Programmatic verification confirmed that the computational runtime is fully initialized:
* **Interpreter:** `C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai\.venv\Scripts\python.exe` (Python 3.12.10)
* **PyTorch Core:** `torch==2.6.0+cu124` (Compiled with CUDA 12.4, CUDNN 9.1)
* **Vision Library:** `torchvision==0.21.0+cu124`
* **Detection Engine:** `ultralytics==8.4.208`
* **Host GPU:** `NVIDIA GeForce RTX 2050` (Compute Capability 8.6, 4,095.5 MiB Dedicated VRAM)
* **Global Python Status:** Completely unpolluted; all dependencies locked inside `.venv`.

---

## 3. Disposable Synthetic Test Fixture Specification

Pursuant to research integrity rules, real unverified images were quarantined from model backpropagation. A disposable synthetic fixture was generated via [`scripts/dataset_inspection/run_pipeline_smoke_test.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/dataset_inspection/run_pipeline_smoke_test.py):

* **Designation:** `SYNTHETIC_SOFTWARE_FIXTURE_NOT_RESEARCH_DATA`
* **Storage Location:** [`dataset/fixtures/synthetic_smoke_test/`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/fixtures/synthetic_smoke_test/)
* **Volume:** 12 synthetic $640 \times 640$ RGB street-texture images (8 training, 4 validation).
* **Taxonomy:** All 8 custom classes (`0: motorcycle` to `7: pedestrian`) represented with mathematically valid normalized YOLO coordinates ($[x_c, y_c, w, h] \in [0.0, 1.0]$).
* **Manifest:** [`dataset/fixtures/synthetic_smoke_test/fixture_manifest.json`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/fixtures/synthetic_smoke_test/fixture_manifest.json).

---

## 4. Execution Telemetry & Component Verification

The 1-epoch smoke test was executed using the following conservative settings:
```powershell
model = YOLO("yolo11n.pt")
model.train(
    data="dataset/fixtures/synthetic_smoke_test/synthetic_data.yaml",
    epochs=1,
    imgsz=640,
    batch=1,
    device="cuda:0",
    amp=True,
    workers=0,
    cache=False,
    save=True
)
```

### Measured Pipeline Steps:
1. **Model Adaptation:** Ultralytics successfully remapped the pre-trained COCO-80 detection head to the 8 custom EncroWatch classes (`Overriding model.yaml nc=80 with nc=8`). Transferred 499/499 backbone parameters.
2. **DataLoader Operations:** Loaded 8 training samples and 4 validation samples sequentially without thread deadlocks (`workers=0`).
3. **Automatic Mixed Precision (AMP):** AMP checks passed on `cuda:0`; forward activations executed in FP16.
4. **Loss Calculation & Backward Pass:** Box loss ($1.18$), class cross-entropy loss ($8.20$), and distribution focal loss ($1.31$) were successfully accumulated; autograd gradients propagated through all 181 layers.
5. **Optimizer Step:** AdamW updated 81 weight tensors and 87 bias tensors.
6. **Validation Engine:** Evaluated predictions on the 4 validation samples and computed AP statistics without memory leaks.
7. **Artifact Generation:** Saved model checkpoints [`experiments/smoke_tests/smoke_test_run/weights/last.pt`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/experiments/smoke_tests/smoke_test_run/weights/last.pt) ($5.25\text{ MB}$) and `best.pt` ($5.25\text{ MB}$).

---

## 5. GPU VRAM Consumption Profile (RTX 2050, 4 GB)

Memory telemetry was sampled continuously via PyTorch CUDA memory management:

```
┌────────────────────────────────────────────────────────┬──────────────────────┐
│ Memory Metric                                          │ Measured Value (MB)  │
├────────────────────────────────────────────────────────┼──────────────────────┤
│ Total Dedicated Hardware VRAM                          │ 4,095.50 MB          │
│ Baseline PyTorch CUDA Context Overhead                 │ ~180.00 MB           │
│ Peak Memory During Backpropagation (Batch = 1, 640x640)│ 227.07 MB            │
│ Percentage of Total VRAM Utilized                      │ 5.54%                │
│ Free Safety Buffer Headroom                            │ 3,868.43 MB (94.46%) │
└────────────────────────────────────────────────────────┴──────────────────────┘
```

> [!TIP]
> **Implications for Full Training:**  
> With a peak memory footprint of only **227.07 MB** at batch size 1, the RTX 2050 possesses ample headroom to comfortably scale to batch size **$B = 4$** (estimated peak $\approx 1,400\text{ MB}$) during formal training while remaining well below the 4,096 MB hardware boundary.

---

## 6. Academic Disclaimer & Next Step

* **Synthetic Data Prohibition:** All accuracy values from this run ($mAP50 = 0.0528$) are artifacts of synthetic geometric noise and must **never** be cited as research findings.
* **Milestone Status:** The software and hardware execution layer for Stage 1.3 is **100% COMPLETE**.
* **Transition:** We proceed directly to **Stage 1.4: Tier 1 Bengaluru Dataset Acquisition**.
