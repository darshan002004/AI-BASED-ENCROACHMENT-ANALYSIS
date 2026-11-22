# EncroWatch AI — Explainable Decomposable Risk Model Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Module:** Stage G (Explainable Multi-Criteria Risk Assessment & Enforcement Prioritization)  
**Implementation:** [`scripts/framework/multistage_framework.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/framework/multistage_framework.py)  
**Status Classification Standard:** `VERIFIED (Mathematical Engine Executed & Validated)`

---

## 1. Problem Formulation: The Necessity of Explainable AI in Municipal Governance

In municipal administrative law and urban policy, automated enforcement actions (such as towing a vehicle, seizing a vendor cart, or issuing statutory demolition notices) are subject to judicial and administrative review. "Black-box" deep learning classifiers that output an opaque scalar risk score cannot be audited, cannot be justified to affected citizens, and expose municipal bodies to legal challenges under arbitrary action doctrines.

To satisfy the dual requirements of scientific rigor and administrative auditability, EncroWatch AI implements a **strictly decomposable, white-box Multi-Criteria Decision Model (MCDM)**. Every risk score emitted by the framework can be disassembled into its underlying physical, temporal, and legal components.

```
+---------------------------------------------------------------------------------------+
|                    Explainable Risk Index Decomposition ($0 - 100$)                   |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +--------------------------+  Weight w_h = 0.30                                     |
|   |  Class Hazard Score (H)  | --------------------+                                  |
|   +--------------------------+                     |                                  |
|   +--------------------------+  Weight w_o = 0.25  |                                  |
|   |  Ground Overlap Ratio (O)| --------------------+---> [ SUM ] ---> TOTAL RISK      |
|   +--------------------------+                     |                  SCORE (0 - 100) |
|   +--------------------------+  Weight w_p = 0.20  |                  [LOW / MOD /    |
|   |  Temporal Persistence (P)| --------------------+                  HIGH / CRIT]    |
|   +--------------------------+                     |                                  |
|   +--------------------------+  Weight w_a = 0.25  |                                  |
|   |  Accessibility Deficit(A)| --------------------+                                  |
|   +--------------------------+                                                        |
+---------------------------------------------------------------------------------------+
```

---

## 2. Mathematical Formalization of Risk Score

The total composite risk index $R_i \in [0, 100]$ for an detected obstacle $i$ is formulated as:
$$R_i = w_h \cdot H(c_i) + w_o \cdot O(i) + w_p \cdot P(\tau_i) + w_a \cdot A(D_i)$$
Subject to the simplex constraint:
$$w_h + w_o + w_p + w_a = 0.30 + 0.25 + 0.20 + 0.25 = 1.00$$

### 2.1 Factor 1: Class Hazard Severity ($H_i \in [0, 100]$, $w_h = 0.30$)
The class hazard score reflects the intrinsic difficulty of obstacle removal, rigidity, and acute safety threat:

| Class Name | Hazard Weight ($H_i$) | Legal / Physical Rationale |
| :--- | :---: | :--- |
| `permanent_structure` | **100.0** | Concrete/brick masonry; irreversible structural alienation of public right-of-way |
| `construction_material`| **90.0** | Piles of gravel/sand/cement; severe slip/fall hazard, airborne particulate pollution |
| `shop_extension` | **80.0** | Commercial display racks/iron grilles; chronic commercial encroachment |
| `vendor_cart` | **75.0** | Large physical envelope (often $1.5\text{ m} \times 1.0\text{ m}$); blocks pedestrian flow |
| `parked_motorcycle` | **70.0** | Heavy metallic obstacle; sharp footpegs/hot exhaust pipes present burn hazards |
| `debris` | **65.0** | Garbage mounds, broken tiles; sanitary hazard and tripping danger |
| `parked_bicycle` | **50.0** | Lighter physical mass; easily relocated, moderate pedestrian disruption |
| `tree_pole` | **40.0** | Static utility infrastructure; baseline obstacle, non-punitive |

### 2.2 Factor 2: Ground-Contact Overlap Ratio ($O_i \in [0, 100]$, $w_o = 0.25$)
$$O_i = 100.0 \times \frac{\text{Area}(G_i \cap F)}{\text{Area}(G_i)}$$
Directly quantifies the proportion of the object's base that intrudes into the pedestrian walking surface.

### 2.3 Factor 3: Temporal Persistence Factor ($P_i \in [0, 100]$, $w_p = 0.20$)
$$P_i = \min\left(100.0, \, 100.0 \times \frac{\tau_i}{\tau_{\text{threshold}}}\right) \quad (\tau_{\text{threshold}} = 10.0\text{ seconds})$$
Saturates linearly at 10 seconds. Transient moving objects ($\tau < 3.0\text{ s}$) have minimal persistence contributions, suppressing false alarms.

### 2.4 Factor 4: Accessibility Clearance Deficit ($A_i \in [0, 100]$, $w_a = 0.25$)
$$A_i = \min\left(100.0, \, 100.0 \times \frac{D_i}{W_{\text{nominal}}}\right)$$
Where $D_i = \max(0.0, \, 1.80 - W_{\text{clear}}^{(i)})$. When the remaining clear width drops to zero, $A_i$ reaches maximum penalty.

---

## 3. Administrative Risk Tiers and Municipal Action Protocols

| Risk Score ($R_i$) | Risk Tier | Urban Impact Description | Prescribed Municipal Action Protocol |
| :---: | :---: | :--- | :--- |
| **$0.00 - 24.99$** | **LOW** | Minor obstruction; transient activity or slight curb overhang | Informational logging only; no field dispatch |
| **$25.00 - 49.99$** | **MODERATE** | Partial obstruction; reduced walking comfort, wheelchair passable | Flagged for routine beat-patrol inspection |
| **$50.00 - 74.99$** | **HIGH** | Significant constriction; wheelchair navigation blocked (LOS D/E) | Automated notification to ward traffic / health inspector |
| **$75.00 - 100.00$** | **CRITICAL** | Severe total blockage; pedestrians forced into active traffic flow | Immediate towing dispatch / emergency clearance notice |

---

## 4. Decomposable Output Schema for Legal Auditability

Every alert generated by EncroWatch AI is serialized into an auditable JSON record:

```json
{
  "incident_id": "INC_00050_TRK_002",
  "frame_id": 50,
  "track_id": 2,
  "class_name": "vendor_cart",
  "total_risk_score": 74.17,
  "risk_tier": "HIGH",
  "decomposition": {
    "class_hazard_component": 22.50,
    "ground_overlap_component": 25.00,
    "persistence_component": 10.00,
    "accessibility_component": 16.67
  },
  "rationale": "Class 'vendor_cart' (75 pts) contributes 22.5 pts; Ground overlap (100.0%) contributes 25.0 pts; Persistence (5.0s, sat 50.0%) contributes 10.0 pts; Accessibility deficit (1.20m) contributes 16.7 pts. Assigned Tier: HIGH (74.17/100)."
}
```

This guarantees complete transparency: municipal officers, ombudsmen, and courts can independently verify exactly how each numerical point was derived.
