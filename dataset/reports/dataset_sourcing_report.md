# EncroWatch AI: Comprehensive Dataset Sourcing & Ingestion Feasibility Report
**Document Version:** 1.0.0 | **Research Level:** MCA Final-Year Major Academic Research  
**Reference Manuscript:** Sections 2.1, 2.3, 6.1, 6.2

---

## 1. Executive Summary & Research Boundaries
Evaluating the multi-stage EncroWatch AI framework requires a robust streetscape dataset capturing Indian urban environments characterized by mixed non-lane-based traffic, ambiguous sidewalk-carriageway transitions, vendor pushcarts, and diverse sidewalk obstructions. 

This report provides a formal academic audit of **six external candidate datasets** alongside the **EncroWatch Primary Bengaluru Corpus**. Each dataset is evaluated against four strict academic criteria:
1. **Pavement/Footpath Boundary Visibility**: Does the dataset image perspective show pedestrian sidewalks with clear ground-contact delineation?
2. **Obstruction vs. Pavement Ground Truth**: Does it distinguish legal traffic on roads from illegal encroachments on footpaths?
3. **Class Compatibility**: How cleanly do its classes map to the 8 EncroWatch classes (`motorcycle`, `car`, `vendor_cart`, `construction_debris`, `commercial_signboard`, `shop_extension`, `umbrella_canopy`, `pedestrian`)?
4. **License & Academic Reproducibility**: Is the dataset legally available for non-commercial academic research?

---

## 2. Comparative Audit of Evaluated Datasets

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   EXTERNAL DATASET AUDIT & SUITABILITY MATRIX                                    │
├────────────────────┬───────────┬──────────────────────┬──────────────────────┬─────────────┬─────────────────────┤
│ Dataset Name       │ Year      │ Volume & Origin      │ Annotation Format    │ License     │ Direct Suitability  │
├────────────────────┼───────────┼──────────────────────┼──────────────────────┼─────────────┼─────────────────────┤
│ IDD (Indian        │ 2019      │ 10,004 images        │ Fine polygonal       │ CC BY-NC 4.0│ ⚠️ Partial (Road    │
│ Driving Dataset)   │ (Varma)   │ Bengaluru/Hyderabad  │ semantic segmentation│ (Academic)  │ Segmentation only)  │
├────────────────────┼───────────┼──────────────────────┼──────────────────────┼─────────────┼─────────────────────┤
│ Cityscapes         │ 2016      │ 5,000 fine +         │ Instance & semantic  │ Non-commer- │ ⚠️ Very Limited     │
│                    │ (Cordts)  │ 20,000 coarse (EU)   │ polygonal masks      │ cial terms  │ (No Indian classes) │
├────────────────────┼───────────┼──────────────────────┼──────────────────────┼─────────────┼─────────────────────┤
│ FootpathVision     │ 2025      │ 1,238 images         │ Bounding boxes       │ SSRN Open   │ ⚠️ Methodological   │
│                    │ (Saha)    │ Dhaka, Bangladesh    │ (YOLO format)        │ Preprint    │ Overlap (Pedestrian)│
├────────────────────┼───────────┼──────────────────────┼──────────────────────┼─────────────┼─────────────────────┤
│ Project Sidewalk / │ 2019      │ 205,385 crowd labels │ Point/box labels     │ Academic    │ ⚠️ Defect Audit     │
│ Sidewalk DL        │ (Weld)    │ US cities            │ on Street View crops │ Research    │ (Not Encroachment)  │
├────────────────────┼───────────┼──────────────────────┼──────────────────────┼─────────────┼─────────────────────┤
│ CitySurfaces       │ 2022      │ ~14,000 patches      │ Classification /     │ Open        │ ❌ Texture Only     │
│                    │ (Hosseini)│ Global cities        │ Patch segmentation   │ Academic    │ (No Obstruction)    │
├────────────────────┼───────────┼──────────────────────┼──────────────────────┼─────────────┼─────────────────────┤
│ EncroWatch Primary │ 2026      │ Tier 1: 1,200 imgs   │ 8-class YOLO bboxes, │ Custom Open │ ✅ Direct Fit       │
│ Bengaluru Corpus   │ (Proposed)│ 25 videos (4 Wards)  │ Footpath, Road, Curb │ Academic    │ (Built for RQ1-RQ5) │
└────────────────────┴───────────┴──────────────────────┴──────────────────────┴─────────────┴─────────────────────┘
```

---

## 3. In-Depth External Dataset Profiles

### 3.1 Indian Driving Dataset (IDD)
* **Lead Citation:** G. Varma et al., *"IDD: A Dataset for Exploring Problems of Autonomous Navigation in Unconstrained Environments,"* in *IEEE Winter Conference on Applications of Computer Vision (WACV)*, 2019, pp. 1743–1751.
* **Source Repository:** [http://idd.insaan.iiit.ac.in/](http://idd.insaan.iiit.ac.in/)
* **Volume:** 10,004 finely annotated images and 50,000 coarsely annotated frames across 182 drive sequences in Bengaluru and Hyderabad.
* **Available Classes (34 Classes):** Includes `curb`, `sidewalk`, `parking`, `motorcycle`, `rider`, `car`, `truck`, `bus`, `autorickshaw`, `person`, `vegetation`, `wall`, `fence`, `pole`, `traffic sign`, `billboard`.
* **Licensing:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). Freely accessible for university research following academic registration.
* **Suitability Analysis for EncroWatch AI:**
  - **Strengths:** Captures genuine Bengaluru urban street conditions (MG Road, Hosur Road, unpaved shoulders, non-uniform curb edges). Exceptional resource for pre-training the semantic segmentation backbone (DeepLabV3+) on Indian curbs and sidewalks.
  - **Critical Limitations:** IDD was recorded strictly from vehicular dashboard cameras ($1.2\text{ m}$ forward-facing height). Footpaths appear at extreme lateral margins with oblique perspective compression. It **does NOT** annotate sidewalk encroachment status: vehicles parked on sidewalks are simply labeled `car` without spatial interaction flags. Pushcarts (`vendor_cart`) and `construction_debris` mounds are absorbed into generic `billboard` or `obstacle` categories.
* **Permitted Academic Role in EncroWatch AI:** Pre-training and fine-tuning the semantic corridor segmentor ($\mathcal{P}_{\text{FP}}$ and $\mathcal{P}_{\text{RD}}$).

---

### 3.2 Cityscapes Dataset
* **Lead Citation:** M. Cordts et al., *"The Cityscapes Dataset for Semantic Urban Scene Understanding,"* in *IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 3213–3223.
* **Source Repository:** [https://www.cityscapes-dataset.com/](https://www.cityscapes-dataset.com/)
* **Volume:** 5,000 finely annotated street images across 50 European cities (2,975 train, 500 val, 1,525 test), plus 20,000 coarsely annotated images.
* **Available Classes (30 Classes):** Includes `sidewalk`, `road`, `curb`, `person`, `rider`, `car`, `truck`, `bus`, `motorcycle`, `bicycle`, `pole`, `traffic sign`.
* **Licensing:** Free for non-commercial academic research.
* **Suitability Analysis for EncroWatch AI:**
  - **Strengths:** Gold-standard benchmark for urban autonomous driving segmentation ($>80\%$ mIoU).
  - **Critical Limitations (Domain Shift):** Cityscapes exhibits structured European urban geometry with uniform granite curbstones, wide asphalt carriageways, and standard lane markings. It completely lacks characteristic Global South urban features: vendor pushcarts, informal tarpaulin shades, rubble mounds, and chaotic mixed traffic. Models trained on Cityscapes suffer severe domain collapse when tested on Indian streetscapes (dropping to $\approx 55\%$ mIoU as documented by Varma et al.).
* **Permitted Academic Role in EncroWatch AI:** General feature backbone pre-training only; cannot serve as custom encroachment training data.

---

### 3.3 FootpathVision Dataset
* **Lead Citation:** S. Saha, M. S. Lubaina, et al., *"FootpathVision: AI-Powered Footpath Encroachment and Obstruction Detection in South Asian Mega-Cities,"* SSRN Electronic Journal Preprint, 2025.
* **Source Repository:** Open academic preprint repository (SSRN / ResearchGate).
* **Volume:** 1,238 manually labeled photographic images captured in Dhaka, Bangladesh.
* **Available Classes:** Includes `pedestrian`, `motorcycle`, `rickshaw`, `vendor`, `signboard`, `trash`.
* **Licensing:** Open academic research distribution.
* **Suitability Analysis for EncroWatch AI:**
  - **Strengths:** Geographically and urbanistically comparable to high-density Indian cities (chaotic sidewalks, street vendors, two-wheelers parked on curbs).
  - **Critical Limitations:** Annotations are 2D bounding boxes without ground-contact footprint masks ($\mathcal{M}_{\text{contact}}$) and without semantic footpath corridor polygons ($\mathcal{P}_{\text{FP}}$). Bounding boxes cannot determine whether an object actually encroaches without ground surface context.
* **Permitted Academic Role in EncroWatch AI:** Comparative benchmarking dataset for evaluating isolated 2D detection accuracy vs. spatially aware encroachment classification.

---

### 3.4 Project Sidewalk & Sidewalk Accessibility Deep Learning
* **Lead Citation:** G. Weld, E. Jang, A. Li, A. Zeng, K. Heimerl, and J. Froehlich, *"Deep Learning for Automatically Detecting Sidewalk Accessibility Problems: An Approach That Integrates Multimodal Street-Level Imagery with Surface-Level Sensor Data,"* in *ACM ASSETS*, 2019, pp. 196–209.
* **Source Repository:** [https://makeabilitylab.cs.washington.edu/project/sidewalk/](https://makeabilitylab.cs.washington.edu/project/sidewalk/)
* **Volume:** 205,385 crowd-audited accessibility labels across 2,941 audited street miles in Seattle, Washington DC, and New parameter cities.
* **Available Classes:** `Curb Ramp`, `Missing Curb Ramp`, `Obstacle in Path`, `Surface Problem` (cracked pavement).
* **Licensing:** Open Source Academic License (MIT / CC BY).
* **Suitability Analysis for EncroWatch AI:**
  - **Strengths:** Outstanding methodological validation of civic accessibility auditing and wheelchair barrier detection.
  - **Critical Limitations:** Focuses almost exclusively on physical ADA infrastructure defects (e.g., missing curb ramps, cracked concrete) captured from Google Street View crops. It does **not** evaluate dynamic encroachments (motorcycles, pushcarts, shopfront spillover) common to Indian arterial roads.
* **Permitted Academic Role in EncroWatch AI:** Methodological literature foundation for accessibility classification and curb ramp compliance.

---

### 3.5 CitySurfaces Dataset
* **Lead Citation:** M. Hosseini et al., *"CitySurfaces: A High-Resolution Dataset for Pedestrian Infrastructure Surface Texture and Material Classification,"* *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 79, pp. 88–101, 2022.
* **Volume:** ~14,000 photographic crops of sidewalk surface textures.
* **Available Classes:** Material classification (`asphalt`, `concrete`, `paving stone`, `gravel`, `dirt`). Reported classification mIoU: 90.5%.
* **Licensing:** Open Academic Use.
* **Suitability Analysis for EncroWatch AI:** Evaluates pavement materials and surface textures only. Does not contain bounding boxes for vehicles, vendors, or dynamic obstacles.
* **Permitted Academic Role in EncroWatch AI:** Texture reference baseline; not suitable for object detection.

---

## 4. Class Label Cross-Mapping Matrix

The following matrix documents the exact mapping from external dataset labels to the 8 custom EncroWatch AI classes:

```
┌──────────────────────────┬──────────────────────┬──────────────────────┬─────────────────────────┐
│ EncroWatch AI Class      │ IDD Class Mapping    │ Cityscapes Mapping   │ FootpathVision Mapping  │
├──────────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────┤
│ 0: motorcycle            │ motorcycle, rider    │ motorcycle, rider    │ motorcycle, 2-wheeler   │
│ 1: car                   │ car, autorickshaw    │ car, truck, bus      │ car, rickshaw, cng      │
│ 2: vendor_cart           │ obstacle (filtered)  │ [None - unmapped]    │ vendor, tea-stall       │
│ 3: construction_debris   │ [None - unmapped]    │ [None - unmapped]    │ trash, debris (partial) │
│ 4: commercial_signboard  │ billboard, sign      │ traffic sign (part.) │ signboard, banner       │
│ 5: shop_extension        │ [None - unmapped]    │ [None - unmapped]    │ stall-spillover         │
│ 6: umbrella_canopy       │ [None - unmapped]    │ [None - unmapped]    │ umbrella (partial)      │
│ 7: pedestrian            │ person               │ person, pedestrian   │ person, pedestrian      │
└──────────────────────────┴──────────────────────┴──────────────────────┴─────────────────────────┘
```

> [!IMPORTANT]
> **Academic Integrity Rule on Label Merging:** Road-scene datasets (IDD, Cityscapes) cannot be converted into footpath encroachment datasets by simply renaming classes. External datasets must be utilized strictly for pre-training feature representations. The fine-grained 8-class custom detection evaluation requires primary streetscape data collected and annotated under the EncroWatch protocol.

---

## 5. Primary Field Collection Strategy (Wards 1–4, Bengaluru)

To meet the statistical power requirements established in Section IV ($RQ_1$ to $RQ_5$):

* **Tier 1 (Guaranteed Feasible Target):**
  - **Total Images:** $N = 1,200$ high-resolution images ($300$ per ward).
  - **Total Videos:** $N = 25$ video clips ($60$–$120\text{ s}$ each at $1080\text{p}$, $30\text{ FPS}$).
  - **Contact Masks:** $N = 200$ finely annotated ground-contact polygon masks.
  - **Physical Cross-Sections:** $N = 50$ physical corridor width measurements using a laser distance meter.
  - **Expert Incidents:** $N = 60$ real incidents evaluated by civil/municipal experts.

* **Tier 2 (Target Scalability Target):**
  - $N = 2,500$ images, $N = 40$ videos, $N = 100$ physical cross-sections, $N = 100$ expert evaluations.

* **Privacy & Ethical Safeguards:**
  - Automated facial blurring and license plate anonymization applied before storage.
  - Collection restricted to public pedestrian thoroughfares; zero private property intrusions.
