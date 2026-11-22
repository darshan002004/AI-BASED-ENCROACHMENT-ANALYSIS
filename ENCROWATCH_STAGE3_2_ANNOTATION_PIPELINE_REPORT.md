# EncroWatch AI — Stage 3.2: Human Annotation Pipeline and Ground-Truth Architecture

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Standardized Ground-Truth Creation, Geometric Validation, and CVAT Tooling  
**Status Classification Standard:** `PREPARED (Ready for Field Imagery Ingestion)`

---

## 1. Multi-Task Annotation Architecture

To support the multi-stage EncroWatch AI framework, annotation encompasses four distinct geometric modalities:

```
+----------------------------------------------------------------------------------------------------+
|                                    MULTI-TASK ANNOTATION MODALITIES                                |
+----+--------------------------+-----------------------+--------------------+-----------------------+
| Mod| Geometric Primitive      | Target Semantic Entity| Output Format      | Downstream Research   |
+----+--------------------------+-----------------------+--------------------+-----------------------+
| 1  | 2D Bounding Box          | 8 Encroachment Classes| YOLO Darknet [x,y,w,h] Detection Baseline (M1)|
| 2  | Dense Closed Polygon     | Walkable Footpath Area| COCO / Polygon Text| Corridor Segment. (M3)|
| 3  | Roadway Polygon          | Active Vehicular Lane | COCO / Polygon Text| Roadway Delineation   |
| 4  | Linear Polyline (2-3 px) | Footpath-Roadway Curb | Linear Vertex Array| Curb Step Extraction  |
| 5  | Ground-Contact Footprint | Base Physical Contact | Binary Mask / 40%  | Spatial Overlap (M4)  |
+----+--------------------------+-----------------------+--------------------+-----------------------+
```

---

## 2. Eight-Class Ontological Ontology

All annotations must adhere strictly to the ontology defined in [`dataset/metadata/classes.json`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/dataset/metadata/classes.json):

```
+----+-----------------------+---------------------+--------------------+----------------------------+
| ID | Class Name            | YOLO Color Code     | Ground Contact Rule| Primary Visual Identifier  |
+----+-----------------------+---------------------+--------------------+----------------------------+
| 0  | motorcycle            | Magenta (#FF00FF)   | Dual tire footprint| Parked two-wheelers        |
| 1  | car                   | Orange  (#FFA500)   | 4 tire footprints  | Parked four-wheelers/autos |
| 2  | vendor_cart           | Cyan    (#00FFFF)   | Wheel / leg chassis| Mobile hawker pushcarts    |
| 3  | construction_debris   | Brown   (#8B4513)   | Surface polygon    | Sand, brick heaps, rubble  |
| 4  | commercial_signboard  | Blue    (#0000FF)   | Base stand contact | A-frame sandwich boards    |
| 5  | shop_extension        | Yellow  (#FFFF00)   | Facade base contact| Fixed storefront displays  |
| 6  | umbrella_canopy       | Purple  (#800080)   | 2.20 m Head Clear. | Cantilevered tarpaulins    |
| 7  | pedestrian            | Green   (#00FF00)   | Shoe contact       | Walking non-obstacle human |
+----+-----------------------+---------------------+--------------------+----------------------------+
```

---

## 3. Ground-Contact Lower 40% Proxy Heuristic Formulation

Obtaining dense pixel masks for every obstacle footprint in large-scale datasets is labor-intensive. EncroWatch AI incorporates a mathematically formulated **Lower 40% Bounding Box Proxy Heuristic**:

$$\mathcal{B}_{\text{proxy}} = \left[ x_c, \; y_{\max} - 0.20 \cdot h, \; w, \; 0.40 \cdot h \right]$$

Where:
- $[x_c, y_c, w, h]$ is the 2D bounding box normalized coordinates.
- $y_{\max} = y_c + h / 2.0$ represents the bottom edge contacting the pavement plane.
- The vertical slice captures the support base, wheels, and ground intersection while discarding empty overhead space, windshields, and elevated canopies.
- Integrated into [`scripts/annotation_validation/cvat_pipeline_manager.py`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/scripts/annotation_validation/cvat_pipeline_manager.py).

---

## 4. Multi-Annotator Quality Control Ladder

To enforce inter-rater reliability:
1. **Primary Pass:** Annotator 1 annotates 100% of the ingested ward images in CVAT.
2. **Dual-Blind Sample:** Annotator 2 independently annotates a 10% stratified random sample ($n=60$ images).
3. **Automated Verification:** `calculate_agreement.py` computes Cohen's Kappa, Box IoU, and Boundary F1.
4. **Senior Adjudication:** All categorical disagreements are logged in [`ENCROWATCH_STAGE3_2_ADJUDICATION_REGISTER.csv`](file:///C:/Users/Darshan%20B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_STAGE3_2_ADJUDICATION_REGISTER.csv) and resolved by the Senior Academic Reviewer.
