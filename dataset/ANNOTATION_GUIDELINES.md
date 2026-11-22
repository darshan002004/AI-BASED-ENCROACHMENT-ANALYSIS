# EncroWatch AI: Urban Footpath Encroachment Dataset Annotation Protocol
**Document Version:** 1.0.0 | **Research Level:** MCA Final-Year Major Academic Research  
**Reference Manuscript:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"* (Sections 3.1, 5.3, 6.2, 6.3)

---

## 1. Introduction & Academic Objectives
This protocol establishes standardized, reproducible annotation specifications for training and evaluating deep learning models for urban pedestrian walkway encroachment detection, accessibility auditing, and civic risk prioritization.

Annotation targets consist of:
1. **8 Custom Object Classes** (bounding boxes and contact masks).
2. **3 Geometric Surface Classes** (semantic polygonal boundaries).
3. **Contact-Footprint Masks ($\mathcal{M}_{\text{contact}}$)** on $N = 200$ benchmark evaluation images.

---

## 2. Taxonomy of the Eight Custom Object Classes

All object annotations must conform strictly to the following 8 class IDs ($0$ through $7$):

| Class ID | Class Name | Category | Risk Weight ($W_c$) | Primary Inclusion Criteria | Visual Boundary / Edge Cases |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **0** | `motorcycle` | Vehicular | 22.0 | Two-wheelers (scooters, motorcycles, mopeds) parked or moving on the sidewalk or curb. | Include mirrors and rear storage boxes. Exclude riders when dismounted (rider is annotated as `pedestrian`). |
| **1** | `car` | Vehicular | 26.0 | Passenger cars, auto-rickshaws, vans, and light commercial vehicles encroaching onto the sidewalk. | Annotate full vehicle chassis. Overhanging bumpers/mirrors included in full box; tires capture ground contact. |
| **2** | `vendor_cart` | Commercial | 20.0 | Wheeled pushcarts, fruit/vegetable carts, tea stalls, and mobile food trolleys on pedestrian corridors. | Encompasses the entire physical cart body, side trays, and display surfaces. Exclude vendor person. |
| **3** | `construction_debris` | Physical Barrier | 24.0 | Loose sand mounds, gravel, concrete rubble, loose brick stacks, and excavated paving materials. | Draw a tight bounding box/polygon around the contiguous heap. Ignore dispersed dust or single stray pebbles. |
| **4** | `commercial_signboard` | Commercial | 14.0 | Portable retail standees, A-frame chalkboard signs, promotional flex banners, and display tripods. | Frame the entire board structure including ground support legs. Exclude permanent municipal signs ($>2.2\text{ m}$). |
| **5** | `shop_extension` | Commercial | 20.0 | Commercial storefront spillover, clothing display racks, beverage crates, mannequins, and merchandise tables. | Encompasses goods displayed on public walkway outside the formal commercial shopfront shutter. |
| **6** | `umbrella_canopy` | Elevated Structure | 12.0 | Large fabric/polythene vendor umbrellas, tarpaulins, and temporary weather awnings overhanging the walkway. | Annotate the overhead fabric canopy. Vertical support pole ground-contact must be distinguished. |
| **7** | `pedestrian` | Authorized User | 0.0 | Walking, standing, or wheelchair-bound humans; authorized walkway occupants (baseline class). | Full body box from head crown to lowest foot contact. Wheelchair users annotated as a combined entity. |

---

## 3. Bounding-Box Annotation Protocol (YOLO Darknet Format)

### 3.1 File & Coordinate Specifications
* Annotation files must be plaintext files (`.txt`) bearing the exact identical basename as the image (e.g., `ward1_img_0012.jpg` $\leftrightarrow$ `ward1_img_0012.txt`).
* One line per object detection:
  $$\text{<class\_id>} \quad x_{\text{center}} \quad y_{\text{center}} \quad \text{width} \quad \text{height}$$
* All coordinates must be normalized floating-point numbers in the closed interval $[0.0, 1.0]$:
  $$x_{\text{center}} = \frac{x_{\text{min}} + x_{\text{max}}}{2 \cdot W_{\text{img}}}, \quad y_{\text{center}} = \frac{y_{\text{min}} + y_{\text{max}}}{2 \cdot H_{\text{img}}}$$
  $$\text{width} = \frac{x_{\text{max}} - x_{\text{min}}}{W_{\text{img}}}, \quad \text{height} = \frac{y_{\text{max}} - y_{\text{min}}}{H_{\text{img}}}$$

### 3.2 Occlusion and Boundary Guidelines
1. **Tight Boundary Rule:** Bounding boxes must fit tightly around the visible exterior boundaries of the target entity with no more than $5\text{ px}$ of surrounding background padding.
2. **Partial Occlusion ($>30\%$ Visible):** If an object is partially occluded by a pole, pedestrian, or tree, annotate the entire estimated physical envelope of the object provided at least $30\%$ is visible. Objects with $>70\%$ occlusion are omitted.
3. **Truncation at Image Margins:** If an object is cut off at the edge of the photographic frame, annotate only the visible portion inside the frame boundaries ($[0.0, 1.0]$).

---

## 4. Semantic Corridor Segmentation Protocol

Polygonal annotations define the spatial surfaces required for geometric overlap calculation:

### 4.1 Surface Classes & Polygon Formatting
1. **Footpath Polygon ($\mathcal{P}_{\text{FP}}$):**
   * Delineates the entire paved or unpaved walking surface designated for pedestrians, bounded by building property lines/fences on one side and the curb line on the other.
   * Continuous closed polygon with vertices normalized:
     $$\text{class\_id} \quad u_1 \quad v_1 \quad u_2 \quad v_2 \quad \dots \quad u_n \quad v_n$$
   * Vertex count $n \ge 4$ to accurately trace curvature and driveway cuts.
2. **Roadway Polygon ($\mathcal{P}_{\text{RD}}$):**
   * Delineates the asphalt or concrete vehicular carriageway surface, bounded by the curb line.
3. **Curb Line ($\mathcal{C}$):**
   * The structural granite or concrete raised edge separating the footpath from the carriageway.

---

## 5. Ground-Contact Geometric Analysis Protocol & Vertical Headroom Gating

Oblique monocular street photography introduces severe perspective distortion. Annotators and validation scripts must enforce two critical geometric rules:

### 5.1 Lower-40% Ground Contact Proxy ($\mathcal{B}_{\text{ground}}$)
* For grounded volumetric objects (`motorcycle`, `car`, `vendor_cart`, `shop_extension`), the true obstruction occurs strictly where the object makes physical contact with the pavement surface.
* The system computes the parameterized ground proxy box:
  $$\mathcal{B}_{\text{ground}} = \left[ x_{\text{min}}, \; y_{\text{min}} + 0.60 \cdot h, \; w, \; 0.40 \cdot h \right]$$
* **Ground-Truth Contact Mask ($\mathcal{M}_{\text{contact}}$):** For the $N = 200$ benchmark evaluation subset, annotators must manually draw a precise closed polygon over the actual tire/wheel/base footprint on the pavement to validate $RQ_2$.

### 5.2 Elevated Canopy Vertical Gating Protocol (For `umbrella_canopy`)
* Elevated vendor tarps, cloth awnings, and large sun umbrellas project large 2D aerial bounding boxes that float above the pavement.
* **Vertical Headroom Gating Rule (IRC:103-2012 Standard [15]):**
  - Statutory minimum pedestrian headroom clearance is **$2.20\text{ m}$**.
  - If the bottom edge of an overhanging canopy is measured or estimated to clear $>2.20\text{ m}$ above the footpath surface, the canopy volume itself does **NOT** constitute a physical ground obstruction.
  - The obstruction is restricted strictly to the **ground support pole or tripod base** ($\le 0.10\text{ m}$ footprint).
  - If the canopy sags below $2.20\text{ m}$ (headroom hazard), the overhead polygon is flagged as a pedestrian hazard and factored into the accessibility penalty.

---

## 6. Spatial Ward Disjoint Data Splitting Protocol

To prevent geographical background correlation and urban streetscape leakage across splits:

| Partition | Allocation | Geographic Corridor | Dominant Urban Characteristics |
| :--- | :---: | :--- | :--- |
| **Training** | **60%** | **Ward 1 (MG Road / Brigade Road)** &<br>**Ward 2 (Indiranagar 100ft Road)** | Commercial pedestrian corridors, high retail density, wide paved sidewalks, portable signboards, vendor carts. |
| **Validation** | **20%** | **Ward 3 (Koramangala 80ft Road)** | Mixed commercial/residential corridor, tree grates, frequent unauthorized two-wheeler parking. |
| **Testing** | **20%** | **Ward 4 (BTM Layout 2nd Stage)** | Unregulated sidewalk sections, broken paving, open utility excavations, construction debris heaps. |

* **Zero-Leakage Enforcement:** Images and videos from Ward 4 are strictly quarantined for final testing and model generalization evaluation. Under no circumstances may images from Ward 4 appear in training or validation splits.
* **Video Clip Splitting:** Temporal video sequences must be partitioned at the whole-clip level, never by interleaving alternating frames between train and test sets.

---

## 7. Quality Assurance & Inter-Annotator Agreement Protocol

1. **Dual-Annotation Pilot Batch:** Prior to full dataset annotation, a random sample of $N = 100$ streetscape images is independently annotated by two trained annotators.
2. **Reliability Metrics:**
   * **Categorical Agreement:** Cohen's Kappa ($\kappa$) must exceed $0.80$:
     $$\kappa = \frac{p_o - p_e}{1 - p_e} \ge 0.80$$
   * **Boundary Precision:** Bounding box Intersection-over-Union ($IoU \ge 0.80$) and Boundary F1-score ($BF1 \ge 0.75$) for semantic polygons.
3. **Discrepancy Adjudication:** Any annotation discrepancies failing the threshold are reviewed and adjudicated by the project principal supervisor.
