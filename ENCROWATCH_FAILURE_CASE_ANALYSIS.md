# EncroWatch AI — Failure Case Analysis & Taxonomy Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Focus Domain:** Computer Vision Edge Cases in High-Density Indian Urban Environments  
**Status Classification Standard:** `VERIFIED (Failure Taxonomy & Algorithmic Mitigation Plan Established)`

---

## 1. Problem Context: The Complexity of Indian Urban Sidewalks

Urban sidewalk environments in rapidly growing Global South metropolises—and Bengaluru in particular—present extreme visual, geometric, and semantic challenges rarely encountered in standard Western benchmarks (e.g., Cityscapes or KITTI). Footpaths frequently exhibit irregular geometry, non-standard materials, dynamic informal commerce, and dense visual clutter.

To ensure that the EncroWatch AI framework is robust against deployment failures, this report establishes a formal four-tier failure taxonomy and details corresponding architectural mitigations.

```
+-------------------------------------------------------------------------------+
|                       EncroWatch AI Failure Taxonomy                          |
+-------------------------------------------------------------------------------+
|  [Type 1: High Occlusion & Clustering]                                        |
|  Dense clusters of interlocked motorcycles, pedestrian crowds, overlapping stalls|
|                                                                               |
|  [Type 2: Extreme Illumination & Tropical Cast Shadows]                       |
|  High dynamic range (HDR) noon sun, deep tree canopy shadows, headlight glare |
|                                                                               |
|  [Type 3: Textural Camouflage & Material Ambiguity]                           |
|  Sand/gravel heaps blending with aggregate pavers, faded tarpaulins on walls  |
|                                                                               |
|  [Type 4: Semantic Boundary & Structural Adjudication]                        |
|  Vendor carts tethered to shop awnings, masonry planter boxes vs structures   |
+-------------------------------------------------------------------------------+
```

---

## 2. Four-Tier Failure Mode Taxonomy

### 2.1 Type 1 — High Occlusion & Dense Object Clustering
- **Visual Manifestation:** Outside metro stations and commercial hubs (e.g., Commercial Street, Ward 3), 15–30 two-wheelers park wheel-to-wheel in dense rows. Overlapping handlebars, mirrors, and seats merge into a continuous visual mass.
- **Model Failure Mode:**
  - Non-Maximum Suppression (NMS) over-suppression: When detection bounding boxes have $\text{IoU} > 0.60$, standard greedy NMS suppresses adjacent valid vehicles, resulting in severe false negatives ($\text{FN}$).
  - Grouping error: The network detects a single giant bounding box around 4 motorcycles, miscalculating vehicle count and lateral clearance.
- **Architectural Mitigation:**
  - Deployment of **Soft-NMS** or **Matrix NMS** that decays detection confidence scores as a continuous Gaussian function of IoU rather than hard elimination:
    $$s_i \leftarrow s_i \cdot \exp\left(-\frac{\text{IoU}(\mathbf{b}_M, \mathbf{b}_i)^2}{\sigma_{\text{nms}}}\right)$$
  - Multi-scale feature extraction at P3 ($80 \times 80$) to preserve discrete wheel-hub features.

### 2.2 Type 2 — Extreme Illumination & Tropical Cast Shadows
- **Visual Manifestation:** In Bengaluru's high-irradiance climate (UV index 10+), elevated curbs and roadside trees cast sharp, high-contrast black shadows onto pale concrete paver blocks.
- **Model Failure Mode:**
  - Shadow boundary confusion: High-contrast shadow edges mimic curb boundaries or elongated debris piles, triggering false-positive spatial alarms ($\text{FP}$).
  - Night-time underexposure: Low-lux municipal streetlights ($< 10\text{ lux}$) create sensor noise, causing small objects (`parked_bicycle`, `debris`) to vanish below detection confidence thresholds ($s_i < 0.25$).
- **Architectural Mitigation:**
  - Color-space photometric augmentation during training: Random HSV perturbations ($\Delta H = 0.015, \Delta S = 0.7, \Delta V = 0.4$), Contrast Limited Adaptive Histogram Equalization (CLAHE), and shadow dropout augmentation.
  - Multi-frame temporal accumulation: Stationary shadow boundaries shift with solar angle, whereas genuine stationary obstacles maintain invariant centroid coordinates.

### 2.3 Type 3 — Textural Camouflage & Paver Blending
- **Visual Manifestation:** Dumping of fine construction materials (sand, quarry dust, loose aggregate) directly onto eroded concrete pavers or broken sidewalks creates near-zero color and texture gradient across the boundary.
- **Model Failure Mode:**
  - Boundary vanishing: Standard edge-detection filters fail to identify clear spatial gradients, resulting in fragmented or truncated bounding boxes.
- **Architectural Mitigation:**
  - Cross-Stage Partial attention (C3k2 in YOLO11n): Enhances receptive field context, allowing the network to infer the elevation mound of construction material from context rather than pure edge gradients.
  - Multi-spectral / thermal integration interface: Future expansion pathway for edge municipal vehicles equipped with thermal imaging.

### 2.4 Type 4 — Semantic Boundary & Adjudication Ambiguity
- **Visual Manifestation:** Semi-permanent roadside stalls featuring wheeled wooden bases (`vendor_cart`) physically bolted or tethered to permanent shop canopies (`shop_extension`).
- **Model Failure Mode:**
  - Class flip oscillation: The detector alternately predicts `vendor_cart` and `shop_extension` across successive video frames, resetting tracking persistence timers.
- **Architectural Mitigation:**
  - Binding Adjudication Rules formulated in Stage 3: If an object is electrically wired or physically anchored to a storefront, it is legally designated as `shop_extension`; if free-standing and mobile on wheels, it is classified as `vendor_cart`.
  - Majority-voting track temporal filter: Smooths class predictions across the 10-frame track window:
    $$\hat{c}_k = \operatorname{mode}\Big(\{c_k^{(t-w)}\}_{w=0}^{W-1}\Big)$$

---

## 3. Empirical Failure Analysis Summary Table

| Failure Type | Primary Vulnerable Class | Error Metric Impact | Root Cause Mechanism | EncroWatch AI Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Type 1 (Occlusion)** | `parked_motorcycle` | High False Negatives ($\downarrow$ Recall) | Greedy NMS suppression in dense parking rows | Soft-NMS with Gaussian decay ($\sigma = 0.5$) |
| **Type 2 (Shadows)** | `debris`, `tree_pole` | High False Positives ($\downarrow$ Precision) | High-contrast noon cast shadows mimicking curbs | CLAHE preprocessing + HSV jitter augmentation |
| **Type 3 (Camouflage)** | `construction_material` | Truncated Box / Low IoU | Zero color contrast against broken concrete pavers | C3k2 context aggregation + 40% ground proxy |
| **Type 4 (Ambiguity)** | `vendor_cart` vs `shop_extension`| Track ID fragmentation | Class flip oscillations across video frames | Majority-voting temporal window filter ($W=10$) |
