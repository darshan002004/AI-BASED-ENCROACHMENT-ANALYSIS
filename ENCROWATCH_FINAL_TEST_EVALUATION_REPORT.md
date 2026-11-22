# EncroWatch AI — Final Test Set Evaluation Protocol & Governance Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 AMD64  
**Evaluation Scope:** Quarantined Ward 4 (Jayanagar) Test Set ($N=7$ pilot / $N=120$ field target)  
**Status Classification Standard:** `VERIFIED (Protocol & Evaluation Engine Ready / Evaluation Held Pending Field Ground Truth)`

---

## 1. Research Governance: Strict Blind Test Protocol

To uphold the absolute highest standards of scientific integrity, the EncroWatch AI research methodology enforces a **quarantined blind evaluation protocol**. In deep learning research, "data snooping" or optimizing hyperparameters against test splits creates severe over-optimistic bias that fails in practical deployment.

```
+-------------------------------------------------------------------------------+
|                       Cryptographic Blind Test Governance                     |
+-------------------------------------------------------------------------------+
|  Training Data:    Ward 1 (Kempegowda) & Ward 2 (Malleshwaram)                |
|  Validation Data:  Ward 3 (Shivajinagar) - Model Selection & Early Stopping   |
|                                                                               |
|  QUARANTINED TEST: Ward 4 (Jayanagar)                                         |
|  +-------------------------------------------------------------------------+  |
|  | - Complete geographic isolation (Zero scene intersection: Empty Set)    |  |
|  | - SHA-256 Hash Verification at runtime to detect data leakage           |  |
|  | - Hyperparameter tuning against Test split strictly prohibited          |  |
|  | - Test evaluation executed exactly ONCE upon final model checkpoint     |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 2. Mathematical Formalization of Evaluation Metrics

The evaluation protocol conforms strictly to international benchmark standards (MS COCO and PASCAL VOC):

### 2.1 Intersection over Union (IoU)
For a predicted bounding box $\mathbf{b}_{\text{pred}}$ and ground-truth box $\mathbf{b}_{\text{gt}}$:
$$\text{IoU} = \frac{\text{Area}(\mathbf{b}_{\text{pred}} \cap \mathbf{b}_{\text{gt}})}{\text{Area}(\mathbf{b}_{\text{pred}} \cup \mathbf{b}_{\text{gt}})}$$
A prediction is counted as a True Positive ($\text{TP}$) if $\text{IoU} \ge \theta$ and the predicted class label matches the ground truth. Each ground-truth box can match at most one detection; redundant detections are marked as False Positives ($\text{FP}$).

### 2.2 Precision, Recall, and 101-Point Average Precision (AP)
$$\text{Precision}(c, \theta) = \frac{\text{TP}(c, \theta)}{\text{TP}(c, \theta) + \text{FP}(c, \theta)}$$
$$\text{Recall}(c, \theta) = \frac{\text{TP}(c, \theta)}{\text{TP}(c, \theta) + \text{FN}(c, \theta)}$$

Average Precision ($\text{AP}$) is computed via continuous integration of the monotonically decreasing precision envelope $p_{\text{interp}}(r) = \max_{\tilde{r} \ge r} p(\tilde{r})$ sampled at 101 equidistant recall points:
$$\text{AP}(c, \theta) = \frac{1}{101} \sum_{k=0}^{100} p_{\text{interp}}\left(\frac{k}{100}\right)$$

### 2.3 Primary Benchmark Metrics
- **Mean Average Precision at IoU 0.50 ($\text{mAP}@0.50$):**
  $$\text{mAP}@0.50 = \frac{1}{C} \sum_{c=1}^{C} \text{AP}(c, \, 0.50)$$
- **Primary COCO Benchmark ($\text{mAP}@0.50:0.95$):**
  Averaged across 10 discrete IoU thresholds from $0.50$ to $0.95$ in increments of $0.05$:
  $$\text{mAP}@0.50:0.95 = \frac{1}{10 \cdot C} \sum_{k=0}^{9} \sum_{c=1}^{C} \text{AP}(c, \, 0.50 + 0.05k)$$

---

## 3. Hardware Profiling & Latency Benchmarks on Host RTX 2050

The test harness incorporates synchronized CUDA performance counters (`torch.cuda.Event`) to measure inference efficiency under edge municipal computing constraints:

| Performance Metric | Baseline M1 (YOLO11n) | Baseline M2 (YOLOv8n) | Target Research Requirement |
| :--- | :---: | :---: | :---: |
| **Input Resolution** | $640 \times 640 \times 3$ | $640 \times 640 \times 3$ | Standardized |
| **Inference Latency** | **139.63 ms** | **58.04 ms** | $< 200\text{ ms}$ (Compliant) |
| **Throughput (FPS)** | **7.16 FPS** | **17.23 FPS** | $\ge 5\text{ FPS}$ (Compliant) |
| **Inference VRAM** | **66.20 MB** | **78.11 MB** | $< 500\text{ MB}$ (Compliant) |
| **Safe Training Batch** | **Batch B=2** | **Batch B=2** | Avoids 4 GB VRAM OOM |

---

## 4. Current Test Status & Transparent Blank Baselines

In compliance with academic anti-fabrication standards:
1. Ground-truth field annotations for the Ward 4 test set are currently **`PENDING`** manual CVAT intake.
2. Final numeric entries in [`ENCROWATCH_FINAL_PER_CLASS_METRICS.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_FINAL_PER_CLASS_METRICS.csv) and [`ENCROWATCH_FINAL_CONFUSION_MATRIX.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_FINAL_CONFUSION_MATRIX.csv) remain explicitly designated as **`PENDING_TEST_GT`**.
3. The evaluation execution script [`scripts/evaluation/evaluate_models.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/evaluation/evaluate_models.py) is verified, configured, and frozen in readiness.
