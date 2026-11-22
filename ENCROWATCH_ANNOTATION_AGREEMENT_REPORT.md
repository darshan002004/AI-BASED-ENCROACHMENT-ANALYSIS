# EncroWatch AI — Inter-Annotator Agreement and Verification Protocol

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Document Release:** Stage 1.5 Quality Verification Specification  
**Status:** **ACTIVE / FROZEN FOR DUAL-ANNOTATOR BATCHES**

---

## 1. Scientific Necessity of Inter-Annotator Reliability

In complex, heterogeneous urban environments such as Indian metropolitan sidewalks, human annotation subjectivity introduces significant label noise. Visual ambiguities frequently arise regarding:
- Whether a stationary two-wheeler is legally parked or an active sidewalk obstacle.
- The precise boundary between an authorized storefront entrance and an illegal sidewalk shop extension.
- Distinguishing loosely packed construction debris from deteriorated pavement rubble.
- Identifying true ground-contact footprints in heavily shadowed or occluded scenes.

To prevent label noise from corrupting deep learning model training and to ensure scientific rigor, EncroWatch AI enforces a formal **Inter-Annotator Agreement Protocol** based on multi-metric statistical verification.

---

## 2. Mathematical Formulations

Reliability is quantified across three complementary dimensions: **Categorical Consistency**, **Bounding Box Spatial Precision**, and **Corridor Polygon Contour Precision**.

### 2.1 Categorical Agreement: Cohen's Kappa ($\kappa$)

For the 8 custom encroachment classes, classification consistency between two independent human annotators ($A$ and $B$) is measured using Cohen's Kappa:

$$\kappa = \frac{P_o - P_e}{1 - P_e}$$

Where:
- $P_o$ is the observed proportional agreement across all matched annotations:
  $$P_o = \frac{1}{N} \sum_{k=1}^{K} C_{kk}$$
  with $C$ representing the $K \times K$ confusion matrix ($K=8$ custom classes) and $N = \sum_{i=1}^K \sum_{j=1}^K C_{ij}$ total matched object pairs.
- $P_e$ is the expected agreement by chance under independent marginal distributions:
  $$P_e = \frac{1}{N^2} \sum_{k=1}^{K} \left( \sum_{j=1}^K C_{kj} \cdot \sum_{i=1}^K C_{ik} \right)$$

#### Interpretation Scale (Landis & Koch, 1977)
- $\kappa < 0.20$: Slight agreement
- $0.21 \le \kappa \le 0.40$: Fair agreement
- $0.41 \le \kappa \le 0.60$: Moderate agreement
- $0.61 \le \kappa \le 0.80$: Substantial agreement
- $\mathbf{\kappa \ge 0.80}$: **Almost Perfect / Certified Scientific Standard (EncroWatch Requirement)**

### 2.2 Spatial Bounding Box Precision: Greedy IoU Matching

For two bounding boxes $\mathcal{B}_A$ and $\mathcal{B}_B$ defined by normalized coordinates $[x_c, y_c, w, h]$:

$$\text{IoU}(\mathcal{B}_A, \mathcal{B}_B) = \frac{\text{Area}(\mathcal{B}_A \cap \mathcal{B}_B)}{\text{Area}(\mathcal{B}_A \cup \mathcal{B}_B)}$$

Pairs are matched using a greedy maximum-overlap algorithm with a minimum overlap threshold $\tau = 0.50$:
1. For each box $i$ in Annotator $A$'s annotation set, find box $j$ in Annotator $B$'s set that maximizes $\text{IoU}(\mathcal{B}_{A,i}, \mathcal{B}_{B,j})$.
2. If $\max_j \text{IoU} \ge 0.50$, mark the pair as matched and record the spatial IoU.
3. Compute the batch mean spatial precision:
   $$\overline{\text{IoU}}_{\text{box}} = \frac{1}{M} \sum_{m=1}^{M} \text{IoU}_m \quad \ge \mathbf{0.80}$$

### 2.3 Contour Polygon Precision: Boundary F1-Score (BF1)

For corridor polygons (footpath and roadway boundaries), standard pixel IoU can be misleadingly high for large areas even when the boundary edge is substantially misaligned. EncroWatch AI utilizes the **Boundary F1-Score (BF1)**:

$$\text{BF1} = \frac{2 \cdot \text{Precision}_{\text{boundary}} \cdot \text{Recall}_{\text{boundary}}}{\text{Precision}_{\text{boundary}} + \text{Recall}_{\text{boundary}}}$$

Where the boundary is dilated by a tolerance radius $\theta = 0.02$ (corresponding to $2\%$ of image dimension, or $\sim 12.8\text{ pixels}$ at $640 \times 640$ resolution):
- $\text{Precision}_{\text{boundary}}$: Fraction of points on Annotator $A$'s boundary within distance $\theta$ of Annotator $B$'s boundary.
- $\text{Recall}_{\text{boundary}}$: Fraction of points on Annotator $B$'s boundary within distance $\theta$ of Annotator $A$'s boundary.
- Target Requirement: $\mathbf{\text{BF1} \ge 0.75}$.

---

## 3. Dual-Annotator Sampling Protocol

To maximize quality control while managing human labeling costs, a stratified dual-annotation protocol is deployed:

```
+----------------------------------------------------------------------------------------------------+
|                                  STRATIFIED SAMPLING SPECIFICATION                                 |
+----------------------------------------------------------------------------------------------------+
| Target Batch Size:           N = 600 field images (Bengaluru Tier 1)                              |
| Dual-Annotated Validation:   10% random stratified sample (n = 60 images)                          |
| Stratification Dimensions:   1. Geographic Ward (15 images per Ward across Wards 1 to 4)          |
|                              2. Lighting Condition (45 daylight, 15 dusk/artificial)              |
|                              3. Encroachment Complexity (Low: 1-2 objs, Med: 3-5 objs, High: >5)   |
+----------------------------------------------------------------------------------------------------+
```

### 3.1 Blind Dual-Annotation Mechanics
1. **Annotator Independence:** Annotator 1 and Annotator 2 work on identical image sets without access to each other's annotations, comments, or class selections.
2. **Task Lock:** Annotations are locked upon submission in CVAT to prevent retrospective tampering.
3. **Execution Pipeline:**
   ```bash
   python scripts/annotation_validation/calculate_agreement.py \
       --batch_a dataset/annotations/cvat_export_annotator_1/ \
       --batch_b dataset/annotations/cvat_export_annotator_2/ \
       --out_report dataset/reports/agreement_batch_01.json
   ```

---

## 4. Formal Quality Thresholds & Pass/Fail Criteria

A field annotation batch is certified for inclusion in training and benchmark evaluation only if it simultaneously satisfies all three quality criteria:

```
+-----------------------------------------+--------------------+---------------------+
| Reliability Metric                      | Minimum Threshold  | Academic Standard   |
+-----------------------------------------+--------------------+---------------------+
| Cohen's Kappa (kappa)                   | >= 0.80            | Landis & Koch (1977)|
| Mean Bounding Box IoU (IoU_box)         | >= 0.80            | Everingham et al.   |
| Mean Polygon Boundary F1 (BF1)          | >= 0.75            | Csurka et al.       |
| Unmatched False Positive / Negative Rate| <= 5.0%            | EncroWatch Protocol |
+-----------------------------------------+--------------------+---------------------+
```

---

## 5. Discrepancy Arbitration and Adjudication Workflow

When a dual-annotated validation batch fails any of the three thresholds, the following formal escalation ladder is executed:

```
+----------------------------------------------------------------------------------------------------+
|                                    ADJUDICATION ESCALATION LADDER                                   |
+----+-----------------------+-----------------------------------------------------------------------+
|Step| Stage                 | Actions & Protocols                                                   |
+----+-----------------------+-----------------------------------------------------------------------+
| 1  | Automated Failure Flag| Engine outputs JSON discrepancy report detailing mismatched pairs,    |
|    |                       | confusing class tuples (e.g., vendor_cart vs. shop_extension).        |
| 2  | Visual Side-by-Side   | Senior Reviewer inspects overlaid bounding boxes and polygons in      |
|    | Inspection            | CVAT diff view.                                                       |
| 3  | Guideline Alignment   | If discrepancy stems from ambiguous edge cases (e.g., fruit crates on |
|    | Meeting               | sidewalk), guidelines are refined with explicit visual exemplars.     |
| 4  | Ground-Truth Resolution| Senior Reviewer issues definitive ruling; image annotation updated    |
|    |                       | with tag "ADJUDICATED_EXPERT_CONSENSUS".                              |
| 5  | Remediation Re-check  | If error rate across non-dual batch is suspected > 5%, the entire     |
|    |                       | ward batch is returned to annotators for systematic re-verification. |
+----+-----------------------+-----------------------------------------------------------------------+
```

---

> [!NOTE]
> The complete mathematical engine is operational at [`scripts/annotation_validation/calculate_agreement.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/annotation_validation/calculate_agreement.py), equipped with Shapely geometric validation, Hungarian/greedy spatial matching, and Cohen's Kappa matrix computation.
