# EncroWatch AI — Multi-Stage Framework Implementation Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Software Implementation:** [`scripts/framework/multistage_framework.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/framework/multistage_framework.py)  
**Execution Environment:** Python 3.12.10 | PyTorch 2.6.0+cu124 | Shapely 2.0.7 | NumPy 2.2.3  
**Status Classification Standard:** `VERIFIED (Mathematical Engine Executed and Empirically Validated)`

---

## 1. Executive Summary & Architectural Overview

The core scientific innovation of the EncroWatch AI research framework is its transition from conventional, static single-stage object detection to an end-to-end, multi-stage urban analytical pipeline. Conventional computer vision models merely locate bounding boxes in isolation; they fail to determine whether an object physically rests upon a pedestrian walkway, whether the object is transient or stationary, the extent to which it degrades pedestrian and wheelchair accessibility, and how municipal authorities should prioritize enforcement.

To resolve these challenges, the EncroWatch AI framework implements a seven-stage decoupled architecture:

```
+---------------------------------------------------------------------------------------------------+
|                           EncroWatch AI Multi-Stage Pipeline                                     |
+---------------------------------------------------------------------------------------------------+
|  [Stage A: Object Detection]        YOLO11n / YOLOv8n (8 Target Urban Encroachment Classes)       |
|            |                                                                                      |
|            v                                                                                      |
|  [Stage B: Spatial Segmentation]    Footpath Surface & Roadway Boundary Polygons                  |
|            |                                                                                      |
|            v                                                                                      |
|  [Stage C: Ground-Contact Geometry] Lower 40% Bounding Box Proxy / Semantic Footprint ($G_i \cap F$)|
|            |                                                                                      |
|            v                                                                                      |
|  [Stage D: Temporal Tracking]       Kalman-Assisted IoU Data Association (Persistent Track ID)     |
|            |                                                                                      |
|            v                                                                                      |
|  [Stage E: Temporal Persistence]    Dwelling Time Accumulation ($\tau_i$: Transient vs Persistent)|
|            |                                                                                      |
|            v                                                                                      |
|  [Stage F: Accessibility Assessment]IRC:103-2012 Clearance Deficit & Level of Service (LOS A–E)   |
|            |                                                                                      |
|            v                                                                                      |
|  [Stage G: Explainable Risk Scoring]Decomposable Index ($0–100$): Hazard, Overlap, Persist, Deficit|
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Mathematical Formalization of Pipeline Stages

### 2.1 Stage A — Single-Stage Object Detection
Given an RGB surveillance frame $I_t \in \mathbb{R}^{H \times W \times 3}$, Stage A predicts an ensemble of bounding boxes:
$$\mathcal{D}_t = \{(\mathbf{b}_i, c_i, s_i)\}_{i=1}^{N_t}$$
where $\mathbf{b}_i = [x_{\min}, y_{\min}, x_{\max}, y_{\max}]$, $c_i \in \{0, \dots, 7\}$ denotes the urban obstacle class, and $s_i \in [0, 1]$ represents the detection confidence score.

### 2.2 Stage B — Spatial Footpath Surface Segmentation
The walkable pedestrian domain is represented by a planar polygon $F \subset \mathbb{R}^2$ delineated by its vertex sequence:
$$F = \text{Polygon}\Big(\{(x_k, y_k)\}_{k=1}^{K}\Big)$$
accompanied by a nominal surveyed corridor width $W_{\text{nominal}}$ (in meters) and a camera spatial calibration scale factor $\sigma$ (in pixels per meter).

### 2.3 Stage C — Ground-Contact Footprint Intersection
To prevent false-positive alarms from aerial overhangs (awnings, banners, cantilevered shop signs, or bicycle handlebars), the ground-contact zone $G_i$ is extracted via the lower 40% vertical proxy slice:
$$G_i = \Big[x_{\min}, \, y_{\max} - 0.40 \cdot (y_{\max} - y_{\min}), \, x_{\max}, \, y_{\max}\Big]$$
The spatial encroachment overlap ratio $O_i$ is computed using planar computational geometry (Shapely):
$$O_i = \frac{\text{Area}(G_i \cap F)}{\text{Area}(G_i)} \in [0.0, 1.0]$$
Detections where $O_i < 0.05$ (less than 5% ground intersection) are pruned as non-encroaching objects.

### 2.4 Stage D & E — Temporal Tracking and Persistence Modeling
Each detected object is assigned a persistent track identity $k$ across sequential video frames using Kalman-assisted bounding box IoU assignment:
$$\text{IoU}(\mathbf{b}_i^{(t)}, \mathbf{b}_j^{(t-1)}) = \frac{\text{Area}(\mathbf{b}_i^{(t)} \cap \mathbf{b}_j^{(t-1)})}{\text{Area}(\mathbf{b}_i^{(t)} \cup \mathbf{b}_j^{(t-1)})}$$
The cumulative stationary dwelling time $\tau_k$ is computed as:
$$\tau_k = \frac{\sum_{t} \mathbb{I}(\text{track } k \text{ active at } t)}{\text{FPS}}$$
Obstacles are classified into three persistence regimes:
- **Transient ($\tau_k < 3.0\text{ s}$):** Passing pedestrians, turning carts, momentary stops.
- **Short-Term ($3.0\text{ s} \le \tau_k < 10.0\text{ s}$):** Active vendor transactions, temporary passenger drop-offs.
- **Persistent ($\tau_k \ge 10.0\text{ s}$):** Stationary vehicular parking, dumped construction debris, unauthorized stalls.

### 2.5 Stage F — Physical Accessibility Assessment
Under the Indian Road Congress (IRC:103-2012) Guidelines for Pedestrian Facilities, footpaths must maintain an unobstructed walking clear zone. The effective clear width $W_{\text{clear}}$ is modeled as:
$$W_{\text{clear}} = \max\left(0.0, \, W_{\text{nominal}} - \frac{\text{width}(G_i)}{\sigma}\right)$$
The clearance deficit $D_i$ relative to standard wheelchair navigation requirements ($W_{\text{IRC}} = 1.80\text{ m}$) is:
$$D_i = \max(0.0, \, 1.80 - W_{\text{clear}})$$
The corridor accessibility is graded into five discrete Levels of Service (LOS):
- **LOS A:** $W_{\text{clear}} \ge 1.80\text{ m}$ (Unrestricted wheelchair passing)
- **LOS B:** $1.50\text{ m} \le W_{\text{clear}} < 1.80\text{ m}$ (Single wheelchair + pedestrian)
- **LOS C:** $1.20\text{ m} \le W_{\text{clear}} < 1.50\text{ m}$ (Minimum wheelchair standard, no passing)
- **LOS D:** $0.90\text{ m} \le W_{\text{clear}} < 1.20\text{ m}$ (Severely constricted)
- **LOS E:** $W_{\text{clear}} < 0.90\text{ m}$ (Complete wheelchair blockage)

### 2.6 Stage G — Explainable Risk Index Formulation
The multi-criteria Risk Index $R_i \in [0, 100]$ is computed via a linear combination of normalized orthogonal factors:
$$R_i = w_h \cdot H_i + w_o \cdot O_i + w_p \cdot P_i + w_a \cdot A_i$$
Subject to:
$$\sum \{w_h, w_o, w_p, w_a\} = 0.30 + 0.25 + 0.20 + 0.25 = 1.00$$
Where:
- $H_i \in [0, 100]$: Class hazard severity (permanent structure = 100, cart = 75, motorcycle = 70, bicycle = 50).
- $O_i \in [0, 100]$: Ground-contact overlap percentage ($100 \times O_i$).
- $P_i \in [0, 100]$: Normalized persistence: $\min\left(100.0, \, 100.0 \times \frac{\tau_i}{10.0}\right)$.
- $A_i \in [0, 100]$: Normalized accessibility deficit: $\min\left(100.0, \, 100.0 \times \frac{D_i}{W_{\text{nominal}}}\right)$.

---

## 3. Empirical Verification Test Harness Results

The pipeline script was validated via `scripts/framework/multistage_framework.py` running a 50-frame discrete simulation. Output results are archived in [`results/evaluation/multistage_framework_simulation_output.json`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/results/evaluation/multistage_framework_simulation_output.json).

### 3.1 Simulated Incident Behavior
- **Motorcycle Encroachment (Track 1):** Bounding box width 60px ($0.60\text{ m}$), nominal width $1.80\text{ m}$. Result: $W_{\text{clear}} = 1.20\text{ m}$, assigned **LOS C** (bare wheelchair accessible). At $3.0\text{ s}$, Risk Index $= 60.33$ (**HIGH**).
- **Vendor Cart Encroachment (Track 2):** Bounding box width 120px ($1.20\text{ m}$), nominal width $1.80\text{ m}$. Result: $W_{\text{clear}} = 0.60\text{ m}$, assigned **LOS E** (wheelchair completely blocked). At $5.0\text{ s}$, Risk Index $= 74.17$ (**HIGH/CRITICAL**).
- **Momentary Bicycle (Track 3):** Active for only 6 frames ($0.6\text{ s}$). Classified as **TRANSIENT**, mitigating alert fatigue.

All verification assertions exited with code 0.
