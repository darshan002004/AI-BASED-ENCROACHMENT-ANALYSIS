# EncroWatch AI — Stage 3.2: Physical Accessibility Assessment Architecture

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Multi-Tier Clear Walking Width Assessment and Statutory Compliance  
**Status Classification Standard:** `PREPARED (Computational Engine Verified / In-Situ Surveys Pending)`

---

## 1. Three-Tier Measurement Architecture

A fundamental contribution of EncroWatch AI is distinguishing between uncalibrated image-space metrics and physical metric-space reality:

```
+----------------------------------------------------------------------------------------------------+
|                                  THREE-TIER ACCESSIBILITY FRAMEWORK                                |
+------+-----------------------+---------------------+--------------------+--------------------------+
| Tier | Assessment Level      | Data Modality       | Units of Measure   | Operational Role         |
+------+-----------------------+---------------------+--------------------+--------------------------+
| A    | Pixel-Space Occupancy | Monocular Image Mask| Dimensionless [0-1]| Coarse Encroachment Ratio|
| B    | Calibrated Metric Est.| Homography Scanlines| Metres (W_clear)   | Algorithm Bottleneck Est.|
| C    | Physical Ground Truth | Optical Laser Sensor| Metres (+/- 1.5 mm)| Empirical Field Standard |
+------+-----------------------+---------------------+--------------------+--------------------------+
```

### 1.1 Strict Separation Rule
- Under no circumstances may 2D pixel area be directly converted to physical square metres without a calibrated camera homography matrix or an optical laser benchmark.
- Pixel-space ratios serve as scale-invariant visual descriptors, whereas municipal accessibility compliance mandates metric dimensions ($W_{\text{clear}}$ in metres).

---

## 2. Mathematical Clear-Width Formulation

For a footpath cross-section with nominal physical width $W_{\text{nom}}$ and lateral obstacle obstructions:

### 2.1 Multi-Obstacle Non-Double-Counting Formulation
When multiple obstacles occupy a single transverse cross-section (e.g., a parked motorcycle on the curb side and an advertising A-frame sign on the shopfront side):

$$W_{\text{clear}} = W_{\text{nom}} - \bigcup_{i=1}^{M} \left[ x_{\min}^{(i)}, x_{\max}^{(i)} \right]$$

Where:
- $\left[ x_{\min}^{(i)}, x_{\max}^{(i)} \right]$ represents the 1D transverse interval occupied by obstacle $i$.
- Overlapping intervals are merged to avoid penalizing the walkway twice for stacked obstacles.

---

## 3. Statutory Compliance Standards (IRC:103-2012)

Evaluated against the **Indian Roads Congress Guidelines for Pedestrian Facilities**:
- **Commercial Corridors (Wards 1, 2, 3):** Standard minimum clear walking width is **$1.80\text{ metres}$**.
- **Residential Corridors (Ward 4):** Standard minimum clear walking width is **$1.50\text{ metres}$**.
- **Universal Wheelchair Accessibility:** Absolute bottleneck clear width is **$1.20\text{ metres}$** (National Building Code & ADA equivalent).

```
+------------------------------------+------------------+---------------------+----------------------+
| Corridor Category                  | Minimum Standard | Threshold Formula   | Regulatory Verdict   |
+------------------------------------+------------------+---------------------+----------------------+
| Commercial Arterial (Wards 1, 2, 3)| 1.80 m           | W_clear >= 1.80 m   | IRC COMPLIANT        |
| Residential Arterial (Ward 4)      | 1.50 m           | W_clear >= 1.50 m   | IRC COMPLIANT        |
| Wheelchair Passage Threshold       | 1.20 m           | W_clear >= 1.20 m   | WHEELCHAIR ACCESSIBLE|
| Severe Obstruction Deficit         | < 1.20 m         | W_clear < 1.20 m    | CRITICAL BARRIER     |
+------------------------------------+------------------+---------------------+----------------------+
```
