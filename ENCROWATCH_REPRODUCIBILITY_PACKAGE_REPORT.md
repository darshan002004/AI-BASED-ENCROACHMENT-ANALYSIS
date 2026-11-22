# EncroWatch AI — Reproducibility Package Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Operating System:** Windows 11 AMD64 (OS Build 26100)  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM)  
**Software Runtime:** Python 3.12.10 | PyTorch 2.6.0+cu124 | Ultralytics 8.4.208  
**Status Classification Standard:** `VERIFIED (Reproducibility Archive Complete)`

---

## 1. Reproducibility Architecture & Directory Hierarchy

The EncroWatch AI research repository is structured into isolated, deterministic functional modules ensuring complete decoupling between experimental data, model weights, evaluation scripts, and academic documentation.

```text
encrowatch-ai/
├── .venv/                              # Isolated Python 3.12.10 virtual environment
├── dataset/
│   ├── metadata/
│   │   └── classes.json                # 8 target class definitions and IDs
│   ├── raw/
│   │   ├── images/ward1..4/            # Genuine Bengaluru field intake directories
│   │   └── videos/ward1..4/            # Continuous urban surveillance sequences
│   ├── splits/
│   │   ├── train/                      # Geographically isolated (Wards 1 & 2)
│   │   ├── val/                        # Geographically isolated (Ward 3)
│   │   ├── test/                       # Quarantined blind test split (Ward 4)
│   │   └── dataset.yaml                # Standard Ultralytics YOLO dataset configuration
│   ├── staging/                        # Unverified intake buffer
│   ├── privacy_processed/              # Bilateral Gaussian blurred images (PII redacted)
│   ├── rejected/                       # Decodability or resolution failure quarantine
│   └── legacy_quarantine/              # 948 legacy web scrapes forensically isolated
├── experiments/
│   ├── baseline_yolo11n/               # Model M1 training checkpoints and run logs
│   ├── baseline_yolov8n/               # Model M2 comparative baseline checkpoints
│   └── smoke_tests/                    # Verified GPU autograd smoke test checkpoints
├── results/
│   └── evaluation/
│       ├── gpu_profiling_benchmark.json# Empirical VRAM and step time benchmarks
│       ├── multistage_framework_simulation_output.json # 50-frame framework simulation
│       └── statistical_hypothesis_results.json        # SciPy hypothesis test payloads
├── scripts/
│   ├── accessibility/
│   │   └── accessibility_calculator.py # 3-tier IRC:103-2012 clearance calculation engine
│   ├── annotation_validation/
│   │   ├── calculate_classwise_agreement.py # Cohen's kappa and classwise IoU
│   │   └── cvat_pipeline_manager.py    # Multi-task annotation ingest & validation
│   ├── dataset_inspection/
│   │   ├── dataset_certification.py    # Leakage and statistical certification engine
│   │   ├── field_data_intake_manager.py# Ingestion, deduplication, and privacy blurring
│   │   ├── gpu_smoke_test.py           # Autograd & DataLoader GPU verification
│   │   └── verify_environment.py       # PyTorch CUDA environment audit
│   ├── evaluation/
│   │   ├── evaluate_models.py          # Standalone inference latency & VRAM evaluator
│   │   ├── generate_baseline_comparison.py # Comparative baseline table generator
│   │   └── statistical_hypothesis_tests.py # Wilcoxon, McNemar, Bland-Altman, Power
│   ├── framework/
│   │   └── multistage_framework.py     # End-to-end 7-stage analytical pipeline
│   ├── orchestrator/
│   │   └── master_research_orchestrator.py # Dependency-aware master research controller
│   └── training/
│       ├── gpu_profiling_benchmark.py  # Discrete VRAM allocation profiler (B=1,2,4)
│       ├── train_baseline_yolo11n.py   # Model M1 training script (safe batch B=2)
│       └── train_baseline_yolov8n.py   # Model M2 training script (safe batch B=2)
└── backups/
    └── stage3_2_pre_execution_backup/  # 29 pre-execution snapshot files preserved
```

---

## 2. Environment Reconstruction & Verification Walkthrough

To recreate the experimental research environment from scratch on an identical or compatible Windows/Linux machine:

### Step 1: Create Dedicated Virtual Environment
```powershell
# From project root directory:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Compatible PyTorch CUDA Wheels & Dependencies
```powershell
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ultralytics==8.4.208 scipy==1.18.1 scikit-learn==1.9.1 shapely==2.0.7 opencv-python==4.11.0.86
```

### Step 3: Verify Hardware & GPU Acceleration
```powershell
& ".\.venv\Scripts\python.exe" "scripts\dataset_inspection\verify_environment.py"
# Expected Output: torch.cuda.is_available() == True, Device: NVIDIA GeForce RTX 2050
```

---

## 3. Cryptographic Verification & Data Integrity

All experimental registers, image manifests, and survey records are accompanied by cryptographic SHA-256 hashes:
- Image Deduplication: Enforced via `scripts/dataset_inspection/field_data_intake_manager.py` computing byte-level SHA-256 checksums to guarantee zero identical images in the training/testing partitions.
- Geographic Isolation: Verified by `scripts/dataset_inspection/dataset_certification.py`, certifying zero scene cluster overlap ($\emptyset$) between Wards 1 & 2 (Train), Ward 3 (Val), and Ward 4 (Test).
- Pre-Execution Preservation: A complete snapshot of 29 existing project files was archived to `backups/stage3_2_pre_execution_backup/` before running any destructive operations.
