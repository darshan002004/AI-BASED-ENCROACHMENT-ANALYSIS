# EncroWatch AI — Stage 1.4: Tier 1 Bengaluru Field Collection Protocol

**Research Initiative:** EncroWatch AI  
**Academic Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Degree:** Master of Computer Applications (MCA) — Final-Year Major Academic Research  
**Document Classification:** Empirical Field Methodology & Ethical Data Governance Manual  
**Target Geographical Scope:** Bengaluru Urban District, Karnataka, India  
**Artifact Path:** [`ENCROWATCH_FIELD_COLLECTION_PROTOCOL.md`](file:///C:/Users/Darshan%20B/.gemini/antigravity/brain/cb519cdb-5935-42b4-88b0-d7dba4b5e06e/ENCROWATCH_FIELD_COLLECTION_PROTOCOL.md)  

---

## 1. Research Objectives & Empirical Sampling Targets

To provide statistically defensible validation for Research Questions $RQ_1$ through $RQ_5$ (as formulated in Section IV and Section VI of the master paper), field data collection targets a **Tier 1 Guaranteed Feasible Corpus**:

```
┌────────────────────────────────────────────────────────┬──────────────────────┬──────────────────┐
│ Empirical Research Asset                               │ Tier 1 Target Volume │ Research Role    │
├────────────────────────────────────────────────────────┼──────────────────────┼──────────────────┤
│ High-Resolution Streetscape Photographs               │ N = 1,200 images     │ RQ1, RQ2, RQ5    │
│ Continuous Urban Video Sequences (60–120s @ 30 FPS)    │ N = 25 video clips   │ RQ4 Persistence  │
│ Manually Traced Ground-Contact Polygon Footprints      │ N = 200 masks        │ RQ2 Evaluation   │
│ Physical Bottleneck Width Surveys (Laser Meter)        │ N = 50 cross-sections│ RQ3 IRC:103 Test │
│ Independent Expert Municipal Enforcement Reviews       │ N = 60 incidents     │ RQ5 Validation   │
└────────────────────────────────────────────────────────┴──────────────────────┴──────────────────┘
```

---

## 2. Geographical Ward Corridors & Sampling Stratification

Collection is strictly stratified across four representative municipal zones in Bengaluru to capture diverse urban typology:

```
                                SAMPLING CORRIDOR SPECIFICATIONS
┌────────┬──────────────────────┬──────────────────────┬───────────────────────────────────────────┐
│ Ward   │ Corridor Name        │ Target Allocation    │ Dominant Urban Characteristics & Obstacles│
├────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────┤
│ Ward 1 │ MG Road /            │ 300 images           │ Commercial retail corridor, high footfall,│
│        │ Brigade Road         │ 6 video clips        │ A-frame signboards, shopfront merchandise │
├────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────┤
│ Ward 2 │ Indiranagar          │ 300 images           │ Food & beverage corridor, vendor carts,   │
│        │ (100ft Road)         │ 6 video clips        │ sun canopies/tarps, valet vehicular spill │
├────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────┤
│ Ward 3 │ Koramangala          │ 300 images           │ Mixed commercial/residential, two-wheeler │
│        │ (80ft Road)          │ 6 video clips        │ footpath parking, shared mobility cycles  │
├────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────┤
│ Ward 4 │ BTM Layout           │ 300 images           │ Suburban arterial, unpaved shoulders,     │
│        │ (2nd Stage)          │ 7 video clips        │ open utility excavations, rubble heaps    │
├────────┴──────────────────────┼──────────────────────┼───────────────────────────────────────────┤
│ TOTAL PLANNED CORPUS          │ 1,200 images, 25 vids│ Stratified representative sampling        │
└───────────────────────────────┴──────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Optical Equipment, Capture Geometry & Physical Calibration

### 3.1 Photographic Capture Specifications
* **Sensor Resolution:** Minimum $1920 \times 1080$ pixels (Full HD) at native uncompressed or high-quality JPEG compression ($Q \ge 95$).
* **Mounting Height:** $1.40\text{ m} \pm 0.10\text{ m}$ above the pavement surface (representing standard eye-level perspective of an adult pedestrian or civic field inspector).
* **Pitch Angle:** $15^\circ$ to $25^\circ$ downward tilt relative to the horizon, ensuring both the footpath surface and pedestrian headroom ($> 2.20\text{ m}$) are simultaneously visible in the frame.
* **Aspect Ratio:** Standard 16:9 landscape orientation.

### 3.2 Video Sequence Specifications
* **Frame Rate:** $30.0\text{ FPS}$ progressive scan.
* **Duration:** $60$ to $120\text{ seconds}$ per clip.
* **Capture Modality:**
  - *Stationary Tripod Mode (15 clips):* Mounted at fixed curb locations to evaluate temporal dwell time ($T_{\text{dwell}}$) without camera motion.
  - *Walking Handheld Gimbal Mode (10 clips):* Mobile pedestrian corridor sweeping to validate Global Motion Compensation (GMC via ORB feature tracking) under camera translation.

### 3.3 Physical Ground-Truth Width Measurement Protocol (For $RQ_3$)
* **Survey Instrument:** Digital optical laser distance meter (Class II, measuring accuracy $\pm 1.5\text{ mm}$, range $0.05–50.0\text{ m}$).
* **Execution:**
  1. Identify the narrowest physical pedestrian clearance bottleneck ($W_{\text{bottleneck}}$) within the designated camera field of view.
  2. Measure horizontal distance from the outer edge of the obstruction (e.g. parked motorcycle handlebar or vendor cart tray) to the opposite corridor boundary (curbstone or property wall).
  3. Record physical laser measurement in metric metres ($m$) to two decimal places in the field log sheet.
  4. Compare directly against statutory **IRC:103-2012** thresholds: Standard comfortable passage ($\ge 1.80\text{ m}$), minimum permissible ($1.50\text{ m}$), single wheelchair accessible ($1.20\text{ m}$), and impassable barrier ($< 0.60\text{ m}$).

---

## 4. Privacy Protection, Civic Ethics & Data Anonymization

Pursuant to Section 7.2 of the manuscript, field collection enforces strict privacy governance:

1. **Automated PII Blurring:** Every photographic and video asset must pass through an automated OpenCV anonymization pipeline prior to permanent dataset indexing:
   - Facial features blurred using an automated Haar/RetinaFace cascade with Gaussian kernel ($\sigma = 15$).
   - Vehicular registration license plates blurred via automated text-box masking.
2. **Public Thoroughfare Boundary:** Capture is strictly restricted to designated public sidewalks, municipal pedestrian plazas, and public road right-of-ways. Photography into private residences, commercial interior back-offices, or behind property setback fences is strictly prohibited.
3. **Safety First:** Field survey personnel must maintain active situational awareness, wear high-visibility safety waistcoats, and avoid obstructing active pedestrian traffic or vehicular lanes.

---

## 5. Spatial Split Segregation & Zero-Leakage Guarantee

To eliminate spatial memorization and temporal frame correlation:

```
┌────────────────────────────────────────────────────────┬─────────────────────────────────────────┐
│ Dataset Split Partition                                │ Strict Geographical Allocation          │
├────────────────────────────────────────────────────────┼─────────────────────────────────────────┤
│ Training Set (60%)                                     │ Ward 1 (MG Road) & Ward 2 (Indiranagar) │
│ Validation Set (20%)                                   │ Ward 3 (Koramangala 80ft Road)          │
│ Testing Set (20% - QUARANTINED)                        │ Ward 4 (BTM Layout 2nd Stage)           │
└────────────────────────────────────────────────────────┴─────────────────────────────────────────┘
```

* **Zero Geographical Leakage:** Ward 4 data is permanently quarantined for testing. Under no circumstances may images or videos from Ward 4 be utilized for model training, tuning, or hyperparameter selection.
* **Video Clip Splitting:** All video clips are partitioned at the whole-clip level. Alternating or consecutive frames from the same video sequence must never be interleaved between training and testing sets.
