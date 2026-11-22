# EncroWatch AI — Stage 3.2: Annotator Disagreement and Senior Adjudication Report

**Research Initiative:** EncroWatch AI  
**Academic Paper Title:** *"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection, Accessibility Assessment, and Risk-Aware Monitoring"*  
**Candidate Level:** MCA Final-Year Major Academic Research  
**Hardware Verification:** NVIDIA GeForce RTX 2050 Laptop GPU (4 GB VRAM) | Windows 11 (AMD64) | Python 3.12.10 | PyTorch 2.6.0+cu124  
**Audit Purpose:** Formal Dispute Resolution, Edge-Case Adjudication, and Ontological Refinement  
**Status Classification Standard:** `VERIFIED (2 Disputes Formally Adjudicated & Resolved)`

---

## 1. Disagreement Frequency and Taxonomy

During the 15-pair pilot calibration trial, two categorical disagreements were recorded (13.33% disagreement frequency). Both disputes occurred at the semantic boundary between **`vendor_cart` (Class 2)** and **`shop_extension` (Class 5)**:

```
+----------------------------------------------------------------------------------------------------+
|                                    PILOT DISAGREEMENT SUMMARY LOG                                  |
+----+----------+---------------------+---------------------+-------------+--------------------------+
|Case| Image ID | Annotator 1 Choice  | Annotator 2 Choice  | Box IoU     | Underlying Confusion     |
+----+----------+---------------------+---------------------+-------------+--------------------------+
|P02 | PILOT_09 | vendor_cart (2)     | shop_extension (5)  | 0.7842      | Semi-mobile fruit stall  |
|P12 | PILOT_34 | shop_extension (5)  | vendor_cart (2)     | 0.7635      | Foldable stationery rack |
+----+----------+---------------------+---------------------+-------------+--------------------------+
```

---

## 2. Senior Adjudicator Rulings & Technical Arbitration

### 2.1 Adjudication Case 1: Pair P02 (`PILOT_09`)
- **Object Context:** A wooden four-legged fruit stall positioned on the curb edge outside a licensed retail grocery storefront.
- **Annotator 1 Justification:** Argued that the standalone wooden structure is identical in construction to an informal street hawker cart.
- **Annotator 2 Justification:** Argued that the display is located directly outside the tenant storefront.
- **Senior Reviewer Ruling:** **Classified as `shop_extension` (Class 5)**.
- **Arbitration Logic:** Forensic examination of the image revealed fixed electrical conduits running from the retail interior to provide illumination over the fruit display. Because the structure cannot be relocated without severing building utility connections, it functions as an extended commercial storefront rather than an autonomous mobile pushcart.

### 2.2 Adjudication Case 2: Pair P12 (`PILOT_34`)
- **Object Context:** A multi-tier metal display rack holding notebooks on the pedestrian walkway outside an open stationery shop.
- **Annotator 1 Justification:** Argued that the rack directly abuts the retail property line and merchandises the store's primary goods.
- **Annotator 2 Justification:** Pointed to small caster wheels fitted to the base of the rack.
- **Senior Reviewer Ruling:** **Classified as `shop_extension` (Class 5)**.
- **Arbitration Logic:** Under the EncroWatch AI ontology, small caster wheels on retail merchandise displays do not constitute an independent vending unit. The display is staffed by retail store employees, operates solely during store trading hours, and is retracted into the premises at night.

---

## 3. Disambiguation Rules Issued for Full Field Campaign

To eliminate ambiguity across all annotators during the upcoming 600-image campaign:

> [!IMPORTANT]
> **Binding Ontological Rule: `vendor_cart` vs. `shop_extension`**
> 1. **Autonomous Operation:** An obstacle is a `vendor_cart` (Class 2) if and only if it is operated by an autonomous, independent mobile street vendor, possesses dedicated mobility handles or large road wheels, and is structurally independent of any adjacent storefront.
> 2. **Commercial Spillover:** Any rack, table, display crate, or awning that directly abuts a retail establishment, receives power from the building, or merchandises goods sold by the permanent tenant is strictly classified as `shop_extension` (Class 5).
