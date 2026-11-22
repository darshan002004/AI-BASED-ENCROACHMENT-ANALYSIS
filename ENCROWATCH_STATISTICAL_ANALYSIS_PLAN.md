# EncroWatch AI — Statistical Analysis Plan

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Software Implementation:** [`scripts/evaluation/statistical_hypothesis_tests.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/evaluation/statistical_hypothesis_tests.py)  
**Status Classification Standard:** `VERIFIED (Statistical Plan Formulated and Programmed)`

---

## 1. Research Objectives & Statistical Rationale

The empirical validation of the EncroWatch AI framework must be grounded in formal statistical inference rather than anecdotal performance comparisons. To avoid common pitfalls in computer vision research (such as reporting superficial test accuracy improvements without assessing variance or significance), this plan defines the formal hypotheses, test statistics, error control protocols, and effect size metrics governing the research study.

### 1.1 Non-Parametric Justification
Urban surveillance data and computer vision evaluation metrics (e.g., per-class mAP, IoU overlap ratios, and spatial error residuals) frequently violate the Gaussian normality assumption required by classical Student's $t$-tests and ANOVAs. Consequently:
- Model performance comparisons utilize the **Paired Wilcoxon Signed-Rank Test**.
- Paired categorical discordance is evaluated using **McNemar's Paired Chi-Squared Test with Edwards Continuity Correction**.
- Continuous metric agreement is evaluated via **Bland-Altman Agreement Analysis** accompanied by non-parametric quantile estimation.

---

## 2. Formal Hypotheses & Test Formulations

### 2.1 Hypothesis 1: Edge Object Detection Superiority (M1 vs M2)
- **Null Hypothesis ($H_{1,0}$):** The median difference in test detection accuracy ($\Delta \text{mAP}@0.50$ and $\Delta \text{mAP}@0.50:0.95$) between Baseline Model M1 (YOLO11n) and Baseline Model M2 (YOLOv8n) across geographically isolated test scenes is equal to zero ($\tilde{\mu}_{\Delta} = 0$).
- **Alternative Hypothesis ($H_{1,1}$):** The median difference is non-zero ($\tilde{\mu}_{\Delta} \neq 0$), reflecting systematic performance divergence between C3k2 and C2f backbones.
- **Statistical Test:** Two-tailed Paired Wilcoxon Signed-Rank Test.
- **Test Statistic:**
  $$W = \min(W^+, W^-) \quad \text{where } W^+ = \sum_{d_i > 0} R_i, \quad W^- = \sum_{d_i < 0} R_i$$
- **Effect Size Metric:** Rank-biserial correlation $r = \frac{Z}{\sqrt{N}}$.
- **Decision Rule:** Reject $H_{1,0}$ if $p < 0.05$.

### 2.2 Hypothesis 2: Spatial False-Positive Reduction via Ground-Contact Proxy
- **Null Hypothesis ($H_{2,0}$):** The discordance rate between ground-truth encroachment status and prediction is identical between naive 2D bounding box intersection and the lower 40% ground-contact geometric proxy ($P(b) = P(c)$).
- **Alternative Hypothesis ($H_{2,1}$):** The ground-contact proxy significantly reduces false-positive alarms caused by aerial overhangs ($P(b) > P(c)$).
- **Statistical Test:** McNemar's Paired Chi-Squared Test with Edwards continuity correction:
  $$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}, \quad \text{df} = 1$$
  where $b$ denotes cases correctly resolved by the proxy but falsely flagged by naive bounding box, and $c$ denotes cases correctly resolved by naive box but failed by proxy.
- **Effect Size Metric:** Odds Ratio $\text{OR} = \frac{b}{\max(1, c)}$.
- **Decision Rule:** Reject $H_{2,0}$ if $p < 0.05$.

### 2.3 Hypothesis 3: Measurement Agreement with Physical Laser Ground Truth
- **Null Hypothesis ($H_{3,0}$):** The automated Tier B vision-based clear width estimation exhibits unacceptable systematic error relative to Tier C physical laser survey measurements ($\text{MAE} > 0.15\text{ m}$ or mean bias $|\bar{d}| > 0.05\text{ m}$).
- **Alternative Hypothesis ($H_{3,1}$):** Tier B vision estimation demonstrates clinical/engineering equivalence to physical laser survey ($\text{MAE} \le 0.15\text{ m}$ and $|\bar{d}| \le 0.05\text{ m}$).
- **Statistical Evaluation:** Bland-Altman limits of agreement ($95\% \text{ LoA} = \bar{d} \pm 1.96 s_d$) and Pearson correlation coefficient $r$.
- **Decision Rule:** Fail to reject equivalence if $\text{MAE} \le 0.15\text{ m}$ and $r \ge 0.90$.

---

## 3. Multiple Testing Correction & Data Independence

### 3.1 Family-Wise Error Rate Control
When evaluating eight individual encroachment classes across multiple metrics, the false discovery rate is controlled using the **Benjamini-Hochberg (BH) procedure**:
$$P_{(k)} \le \frac{k}{M} \cdot Q, \quad (Q = 0.05)$$

### 3.2 Geographic Independence Enforcement
Scene leakage creates artificial statistical dependence, severely inflating Type I error rates. To preserve true independent and identically distributed (i.i.d.) assumptions:
- Training scenes originate strictly from **Ward 1 (Kempegowda Ward)** and **Ward 2 (Malleshwaram)**.
- Validation scenes originate strictly from **Ward 3 (Shivajinagar)**.
- Final test evaluation is strictly quarantined to **Ward 4 (Jayanagar)**.
- As confirmed by [`ENCROWATCH_STAGE3_2_LEAKAGE_AUDIT.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_2_LEAKAGE_AUDIT.md), scene intersection across partitions is strictly null ($\emptyset$).
