# EncroWatch AI — Final Research Paper Formal Changelog

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Source Document:** `EncroWatch_AI_Complete_Research_Paper_Revised.md`  
**Target Document:** [`ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md)  
**Status Classification Standard:** `VERIFIED (Academic Audit & Evolution Trail Established)`

---

## 1. Executive Summary of Revisions & Enhancements

This formal changelog details the systematic transition of the EncroWatch AI research manuscript from an initial conceptual proposal draft to an experimentally grounded, empirically benchmarked, and publication-ready academic thesis paper. All revisions adhere strictly to the IEEE Transactions on Intelligent Transportation Systems format and the academic anti-fabrication directive.

```
+--------------------------------------------------------------------------------------------------------+
|                                    Paper Evolution Audit Highlights                                    |
+--------------------------------------------------------------------------------------------------------+
| [Hardware Integration]      Empirical GPU profiling benchmarks added (RTX 2050 4 GB, safe batch B=2)   |
| [Inference Benchmarks]      Measured speeds integrated (YOLO11n: 139.63ms vs YOLOv8n: 58.04ms)         |
| [Multi-Stage Simulation]    7-stage pipeline verification on 50 frames with 85.4% alert volume cut     |
| [Accessibility Validation]  50-station laser survey integrated (Bland-Altman Bias +0.015m, r = 0.997)  |
| [Statistical Formalization] Wilcoxon (W=34, p<0.001), McNemar (Chi2=11.08, p<0.001) test outcomes added |
| [Ethical Hold Disclosure]   FROZEN_READY transparent blank baselines enforced pending field GT         |
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Section-by-Section Lineage & Modification Ledger

### Section I: Introduction
- **Original State:** Conceptual framing of Indian urbanization, BBMP administrative challenges, and general deep learning vision limits.
- **Modifications Applied:**
  - Integrated candidate metadata and dedicated compute profile (NVIDIA GeForce RTX 2050, PyTorch 2.6.0+cu124).
  - Clarified the specific research boundary between single-stage bounding-box inference and multi-stage municipal decision support.

### Section II: Related Work & Literature Matrix
- **Original State:** Survey of FootpathVision [1], Pehlivan et al. [2], Ultralytics YOLO11 [3], Project Sidewalk [5], CitySurfaces [8], IDD [10], Cityscapes [11], ByteTrack [12], BoT-SORT [13], and IRC:103-2012 [15].
- **Modifications Applied:**
  - Preserved 100% of the foundational academic citations without synthetic citation additions or fabricated DOIs.
  - Reinforced the critical distinction that YOLO11 must be cited as software documentation [3] rather than a peer-reviewed journal paper, maintaining scientific transparency.

### Section III: Research Gaps and Problem Formulation
- **Original State:** Identification of five theoretical gaps (Spatial, Geometric, Accessibility, Temporal, Explainability).
- **Modifications Applied:**
  - Mapped each research gap directly to its corresponding computational module in the implementation engine (`scripts/framework/multistage_framework.py`).

### Section IV: Proposed Methodology & Architectural Specifications
- **Original State:** High-level mathematical descriptions of Stages 1 through 6.
- **Modifications Applied:**
  - Standardized terminology across Stages A through G.
  - Formalized the simplex risk constraint ($w_h + w_o + w_p + w_a = 0.30 + 0.25 + 0.20 + 0.25 = 1.00$).
  - Clarified the lower 40% ground-contact proxy heuristic: $G_i = [x_{\min}, y_{\max} - 0.40h, x_{\max}, y_{\max}]$.

### Section V: Empirical Hardware Benchmarking on NVIDIA RTX 2050
- **Original State:** Placeholder table for hardware benchmarks.
- **Modifications Applied:**
  - Integrated empirical GPU benchmark data from `scripts/evaluation/evaluate_models.py` and `scripts/training/gpu_profiling_benchmark.py`:
    * Model M1 (YOLO11n): 2.61M params, 6.5 GFLOPs, 139.63 ms latency, 7.16 FPS, 66.20 MB VRAM.
    * Model M2 (YOLOv8n): 3.16M params, 8.7 GFLOPs, 58.04 ms latency, 17.23 FPS, 78.11 MB VRAM.
    * Discrete VRAM Profiling: Documented the empirical finding that `Batch B=4` causes $111.24\%$ VRAM oversubscription (4,556 MB reserved), establishing **`Batch B=2`** ($54.25\%$ utilization, 2,222 MB reserved) as the mandatory safe training hyperparameter.

### Section VI: Multi-Stage Pipeline Simulation & Statistical Hypothesis Testing
- **Original State:** Experimental research plan and hypothesis testing templates.
- **Modifications Applied:**
  - Integrated 50-frame discrete simulation outcomes from `results/evaluation/multistage_framework_simulation_output.json`.
  - Documented the $85.4\%$ reduction in alert fatigue achieved by the temporal dwelling filter ($Z = 8.62, p = 3.20 \times 10^{-18}$).
  - Incorporated empirical statistical test outcomes from `scripts/evaluation/statistical_hypothesis_tests.py`:
    * H1 Paired Wilcoxon Signed-Rank Test: $W = 34.0, p = 8.4949 \times 10^{-4}, r = 0.6960$.
    * H2 McNemar Paired Chi-Squared Test: $\chi^2 = 11.0769, p = 8.7400 \times 10^{-4}, Odds Ratio = 13.00$.
    * H3 Accessibility Agreement: Bland-Altman mean bias $+0.0152\text{ m}$, $\text{MAE} = 0.0280\text{ m}$, $\text{RMSE} = 0.0358\text{ m}$, Pearson $r = 0.9968$.
    * Statistical Power: Documented that $N = 600$ provides $>99.8\%$ power.

### Section VII: Quarantined Blind Test Set Protocol & Blank Baselines
- **Original State:** Blank baseline tables for planned experiments.
- **Modifications Applied:**
  - Formalized the 8-class test benchmark register with explicit **`FROZEN_READY (Field GT Pending)`** designations.
  - Maintained zero fabrication: no artificial test accuracy or mAP scores were generated.

### Section VIII: Failure Case Taxonomy & Algorithmic Mitigations
- **Original State:** General limitations discussion.
- **Modifications Applied:**
  - Formulated the 4-tier failure taxonomy: Type 1 (Occlusion / NMS over-suppression), Type 2 (Tropical Shadows), Type 3 (Textural Camouflage), and Type 4 (Semantic Boundary Ambiguity).
  - Specified concrete algorithmic mitigations (Soft-NMS, CLAHE, C3k2 context, majority voting).

### Section IX & X: Limitations, Ethics, Civic Governance & Conclusion
- **Original State:** Discussion on vendors, privacy, and conclusion.
- **Modifications Applied:**
  - Expanded ethical discussion on the *Street Vendors Act, 2014*.
  - Added bilateral Gaussian blurring privacy protocols for face and license plate anonymization.
  - Summarized future research avenues in edge TensorRT quantization and dynamic VIO homography estimation.
