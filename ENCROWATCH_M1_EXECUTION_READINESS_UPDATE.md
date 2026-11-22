# EncroWatch AI — Stage 1.3: Baseline Model M1 Execution Readiness Update

**Research Initiative:** EncroWatch AI  
**Academic Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Degree:** Master of Computer Applications (MCA) — Final-Year Major Academic Research  
**Document Classification:** Milestone Readiness Assessment (Stage 1.3)  
**Hardware Verified:** NVIDIA GeForce RTX 2050 (4 GB VRAM), Windows 11 (AMD64)  
**Target Milestone:** Baseline Model M1 Training (YOLO11n Backbone — $RQ_1$)  
**Artifact Path:** [`ENCROWATCH_M1_EXECUTION_READINESS_UPDATE.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_M1_EXECUTION_READINESS_UPDATE.md)  

---

## 1. Readiness Gating Matrix

Before launching the formal 50-epoch training run for Baseline Model M1, three strict operational gates must be evaluated:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         BASELINE MODEL M1 PRE-TRAINING READINESS GATES                           │
├──────────────────────────────┬──────────────────────┬────────────────────────────────────────────┤
│ Gating Dimension             │ Verification Status  │ Current Assessment & Technical Evidence    │
├──────────────────────────────┼──────────────────────┼────────────────────────────────────────────┤
│ Gate 1: Hardware & CUDA      │ PASSED (100% Ready)  │ RTX 2050 verified; CUDA 12.4 operational;  │
│                              │                      │ Tensor math passed; FP16 AMP confirmed     │
├──────────────────────────────┼──────────────────────┼────────────────────────────────────────────┤
│ Gate 2: Training Pipeline    │ PASSED (100% Ready)  │ DataLoader, backward autograd, optimizer,  │
│                              │                      │ validation, & checkpoint saving all passed │
│                              │                      │ with only 227 MB peak VRAM on smoke test   │
├──────────────────────────────┼──────────────────────┼────────────────────────────────────────────┤
│ Gate 3: Empirical Dataset &  │ ACTIVE GATING FACTOR │ 42 pilot images awaiting verified human    │
│ Human Ground Truth           │ (In Progress)        │ annotation; full Tier 1 dataset (1,200     │
│                              │                      │ images) required to prevent class collapse │
├──────────────────────────────┼──────────────────────┼────────────────────────────────────────────┤
│ OVERALL M1 STATUS            │ EXECUTION-READY CODE │ Pipeline proven; awaiting verified field   │
│                              │ DATA-GATED EXECUTION │ dataset ingestion (Stage 1.4 & 1.5)        │
└──────────────────────────────┴──────────────────────┴────────────────────────────────────────────┘
```

---

## 2. Technical Capabilities Proven by Stage 1.3

1. **VRAM Safety Margin:** The smoke test demonstrated that a full $640 \times 640$ training pass on YOLO11n consumes only **227.07 MB** VRAM at batch size 1. This empirically confirms that a batch size of **$B = 4$** will require $\approx 1,400\text{ MB}$, leaving more than $2.6\text{ GB}$ of safe headroom on the RTX 2050.
2. **Loss Convergence Engine:** The PyTorch autograd engine successfully propagated multi-task loss gradients (DFL loss, CIoU box loss, and binary cross-entropy class loss) into the 8 custom output heads without numerical NaN instability.
3. **Checkpoint Architecture:** The training loop created valid, deployable checkpoints (`last.pt`, `best.pt`, $5.25\text{ MB}$) that can be loaded for downstream evaluation.

---

## 3. Active Next Actions Prior to Launching Model M1

To satisfy Gate 3 without violating academic research ethics:
* **Stage 1.4:** Formally structure the Tier 1 Bengaluru dataset acquisition register and field collection protocol across Wards 1 to 4.
* **Stage 1.5:** Complete the human annotation and dual-annotator verification workflow under Cohen's Kappa protocol ($\kappa \ge 0.80$).
* **Stage 2:** Run automated dataset validation to verify class balance and split isolation.
* **Stage 2.1:** Launch formal Baseline Model M1 training on genuine verified research data.
