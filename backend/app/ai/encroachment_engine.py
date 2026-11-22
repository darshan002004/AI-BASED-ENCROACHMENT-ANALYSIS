from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from typing import List, Dict, Any, Tuple

class EncroachmentEngine:
    """
    Stage 2: Spatial Overlap & Encroachment Classification Engine.
    Strictly separated from Stage 1 (`ObjectDetector`):
    - Requires geometric evidence of overlap between a detected object and the Prototype
      Footpath or Road Region-of-Interest (ROI).
    - Classifies each detection into one of:
        1. "Potential encroachment"
        2. "Needs human review"
        3. "Not an encroachment"
    - When 0 objects are detected, returns overall status "No obstruction detected".
    - Does NOT invent real-world square metres (m²); reports exact pixel areas (px²) and
      percentage overlap within the 2D Prototype ROI.
    """

    def analyze(
        self,
        detected_objects: List[Dict[str, Any]],
        geometry_data: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        footpath_pts = geometry_data.get("footpath_polygon", [])
        road_pts = geometry_data.get("road_polygon", [])
        footpath_roi_area_px = max(1.0, float(geometry_data.get("footpath_roi_area_px", 1.0)))
        road_roi_area_px = max(1.0, float(geometry_data.get("road_roi_area_px", 1.0)))
        image_area_px = max(1, int(geometry_data.get("image_area_px", 1)))
        is_prototype_seg = geometry_data.get("segmentation_info", {}).get("is_prototype", True)

        footpath_poly = Polygon(footpath_pts) if len(footpath_pts) >= 3 else None
        road_poly = Polygon(road_pts) if len(road_pts) >= 3 else None

        processed_objects: List[Dict[str, Any]] = []
        footpath_obstruction_geoms = []
        overall_explanations: List[str] = []

        # Identify portable street objects (e.g., umbrella/canopy, bench, chair, table) to check proximity
        street_obj_boxes = [
            box(o["bbox"][0], o["bbox"][1], o["bbox"][0] + o["bbox"][2], o["bbox"][1] + o["bbox"][3])
            for o in detected_objects
            if o.get("category") == "Street Object"
        ]

        for obj in detected_objects:
            bx, by, bw, bh = obj["bbox"]
            full_box = box(bx, by, bx + bw, by + bh)
            # Lower 40% of bounding box represents ground contact area; for elevated canopies (umbrella),
            # also evaluate vertical projection onto the ground corridor below it.
            coco_class = obj.get("coco_class") or obj.get("raw_coco_class", "object")
            category = obj.get("category") or obj.get("type", "Object")
            display_label = obj.get("label", coco_class)
            conf = float(obj.get("confidence", 0.0))
            conf_pct = round(conf * 100.0, 1)
            source = obj.get("prediction_source", "YOLOv5n-ONNX")

            ground_box = box(bx, by + (bh * 0.60), bx + bw, by + bh)

            # Calculate exact pixel intersections with Prototype Footpath and Road ROIs
            fp_ground_px = 0.0
            rd_ground_px = 0.0
            fp_full_px = 0.0
            rd_full_px = 0.0

            if footpath_poly and footpath_poly.is_valid:
                if footpath_poly.intersects(ground_box):
                    fp_ground_px = float(footpath_poly.intersection(ground_box).area)
                if footpath_poly.intersects(full_box):
                    fp_full_px = float(footpath_poly.intersection(full_box).area)

            if road_poly and road_poly.is_valid:
                if road_poly.intersects(ground_box):
                    rd_ground_px = float(road_poly.intersection(ground_box).area)
                if road_poly.intersects(full_box):
                    rd_full_px = float(road_poly.intersection(full_box).area)

            fp_ground_ratio = fp_ground_px / max(1.0, float(ground_box.area))
            rd_ground_ratio = rd_ground_px / max(1.0, float(ground_box.area))
            fp_full_ratio = fp_full_px / max(1.0, float(full_box.area))
            rd_full_ratio = rd_full_px / max(1.0, float(full_box.area))

            # For elevated canopies like 'umbrella', use the larger of ground-box or full-box overlap with footpath
            effective_fp_ratio = max(fp_ground_ratio, fp_full_ratio) if coco_class == "umbrella" else fp_ground_ratio
            effective_rd_ratio = max(rd_ground_ratio, rd_full_ratio) if coco_class == "umbrella" else rd_ground_ratio

            footpath_pct = round(effective_fp_ratio * 100.0, 1)
            road_pct = round(effective_rd_ratio * 100.0, 1)

            # Determine primary ROI zone based on overlap evidence
            if footpath_pct >= 15.0 and footpath_pct >= road_pct:
                zone = "footpath"
            elif road_pct >= 15.0:
                zone = "road"
            else:
                zone = "outside_or_boundary"

            classification = "Not an encroachment"
            encroachment_status = "Not an Encroachment"
            is_encroachment = False
            needs_human_review = False
            explanation = ""

            # --- Rule Set 1: Vehicles (car, motorcycle, bus, truck, bicycle) ---
            if category == "Vehicle":
                if footpath_pct >= 35.0 and conf >= 0.40:
                    classification = "Potential encroachment"
                    encroachment_status = "Potential Footpath Encroachment (Needs Human Review)"
                    is_encroachment = True
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) has {footpath_pct}% of its "
                        f"ground footprint inside the Prototype Footpath ROI ({int(round(fp_full_px))} px²). "
                        f"Classified as Potential Encroachment; human review required because region boundaries use a prototype geometric ROI."
                    )
                elif footpath_pct >= 10.0 or (footpath_pct >= 35.0 and conf < 0.40):
                    classification = "Needs human review"
                    encroachment_status = "Needs Human Review (Uncertain Curb/Footpath Overlap)"
                    is_encroachment = False
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) has partial overlap with the "
                        f"Prototype Footpath ROI ({footpath_pct}%) and Road ROI ({road_pct}%). "
                        f"Returned as 'Needs human review' because curb line position and camera angle are uncalibrated."
                    )
                else:
                    classification = "Not an encroachment"
                    encroachment_status = "Not an Encroachment (Normal Road Traffic)"
                    is_encroachment = False
                    needs_human_review = False
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) has {road_pct}% Road ROI overlap "
                        f"and {footpath_pct}% Footpath ROI overlap. Vehicles operating on the roadway without sidewalk "
                        f"overlap are normal traffic, NOT an encroachment."
                    )

            # --- Rule Set 2: Portable / Street Objects, Vendors & Construction Material ---
            elif category in ("Street Object", "Street Vendor", "Construction Material"):
                if footpath_pct >= 35.0 and conf >= 0.40:
                    classification = "Potential encroachment"
                    encroachment_status = "Potential Footpath Encroachment (Needs Human Review)"
                    is_encroachment = True
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) overlaps {footpath_pct}% with the "
                        f"Prototype Footpath ROI ({int(round(fp_full_px))} px²). Stationary canopies/furniture on a walkway "
                        f"indicate a potential vendor setup or obstacle, but require human review because COCO-80 does not "
                        f"natively classify vendor stalls and segmentation is a prototype ROI."
                    )
                elif footpath_pct >= 10.0 or road_pct >= 20.0:
                    classification = "Needs human review"
                    encroachment_status = "Needs Human Review (Uncertain Street Object Overlap)"
                    is_encroachment = False
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) has {footpath_pct}% Footpath ROI "
                        f"and {road_pct}% Road ROI overlap. Flagged as 'Needs human review' to verify whether it obstructs "
                        f"pedestrian or vehicular passage."
                    )
                elif coco_class == "umbrella" and bx < int(geometry_data.get("img_width", 800) * 0.50):
                    classification = "Needs human review"
                    encroachment_status = "Needs Human Review (Elevated Canopy Above Footpath Corridor)"
                    is_encroachment = False
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO 'umbrella', {conf_pct}% confidence) is elevated in the upper frame "
                        f"above the Footpath ROI corridor ({footpath_pct}% direct ground-polygon overlap). "
                        f"Because 2D bounding boxes of overhead canopies do not intersect the ground plane directly, "
                        f"this is flagged as 'Needs human review' to verify if a vendor stall exists beneath it."
                    )
                else:
                    classification = "Not an encroachment"
                    encroachment_status = "Not an Encroachment (No Significant ROI Overlap)"
                    is_encroachment = False
                    needs_human_review = False
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) has negligible overlap with the "
                        f"Footpath ROI ({footpath_pct}%) and Road ROI ({road_pct}%)."
                    )

            # --- Rule Set 3: Pedestrians (person) ---
            elif category == "Pedestrian":
                # Check if this person is standing beneath/adjacent to a detected street object (e.g., umbrella canopy) on the footpath
                expanded_person = box(max(0, bx - 35), max(0, by - 60), bx + bw + 35, by + bh + 20)
                near_street_obj = any(expanded_person.intersects(sb) for sb in street_obj_boxes)

                if near_street_obj and footpath_pct >= 20.0:
                    classification = "Needs human review"
                    encroachment_status = "Needs Human Review (Person Adjacent to Street Object on Footpath)"
                    is_encroachment = False
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO 'person', {conf_pct}% confidence) is located inside the Prototype Footpath ROI "
                        f"({footpath_pct}% overlap) directly adjacent to a detected Street Object (e.g., umbrella/canopy). "
                        f"Because people themselves are not encroachments and COCO-80 cannot directly detect pushcarts, this "
                        f"is marked 'Needs human review' rather than automatically counted as an obstruction."
                    )
                else:
                    classification = "Not an encroachment"
                    encroachment_status = "Not an Encroachment (Pedestrian)"
                    is_encroachment = False
                    needs_human_review = False
                    explanation = (
                        f"{display_label} (COCO 'person', {conf_pct}% confidence) overlaps {footpath_pct}% with the Footpath ROI "
                        f"and {road_pct}% with the Road ROI. Pedestrians are authorized walkway users and are NOT classified as encroachments."
                    )

            # --- Rule Set 4: Other COCO Objects / Fixtures ---
            else:
                if footpath_pct >= 20.0 or road_pct >= 20.0:
                    classification = "Needs human review"
                    encroachment_status = "Needs Human Review (Unverified Object in ROI)"
                    is_encroachment = False
                    needs_human_review = True
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) overlaps {footpath_pct}% with the "
                        f"Footpath ROI and {road_pct}% with the Road ROI. Requires human review."
                    )
                else:
                    classification = "Not an encroachment"
                    encroachment_status = "Not an Encroachment"
                    is_encroachment = False
                    needs_human_review = False
                    explanation = (
                        f"{display_label} (COCO '{coco_class}', {conf_pct}% confidence) does not significantly overlap "
                        f"pedestrian or road regions ({footpath_pct}% footpath / {road_pct}% road)."
                    )

            # Record pixel footprint intersection for non-pedestrian potential encroachments
            if is_encroachment and footpath_poly and footpath_poly.is_valid:
                inter_geom = footpath_poly.intersection(full_box)
                if not inter_geom.is_empty:
                    footpath_obstruction_geoms.append(inter_geom)

            overall_explanations.append(explanation)

            processed_objects.append({
                **obj,
                "classification": classification,
                "is_encroachment": is_encroachment,
                "needs_human_review": needs_human_review,
                "encroachment_status": encroachment_status,
                "zone": zone,
                "encroachment_reason": explanation,
                "explanation": explanation,
                "bbox_area_px": int(bw * bh),
                "footpath_overlap_px": round(fp_full_px, 1),
                "road_overlap_px": round(rd_full_px, 1),
                "footpath_ratio": round(effective_fp_ratio, 3),
                "road_ratio": round(effective_rd_ratio, 3),
                "footpath_overlap_pct": footpath_pct,
                "road_overlap_pct": road_pct,
                "area_sqm": None  # Uncalibrated 2D camera: never invent square metres
            })

        # Exact pixel union area of potential encroachments inside the Prototype Footpath ROI
        if footpath_obstruction_geoms:
            union_geom = unary_union(footpath_obstruction_geoms)
            occupied_footpath_px = round(float(union_geom.area), 1)
        else:
            occupied_footpath_px = 0.0

        occupied_footpath_px = min(footpath_roi_area_px, occupied_footpath_px)
        free_footpath_px = round(max(0.0, footpath_roi_area_px - occupied_footpath_px), 1)
        roi_pixel_occupancy_pct = round((occupied_footpath_px / footpath_roi_area_px) * 100.0, 1)

        encroaching_objs = [o for o in processed_objects if o["classification"] == "Potential encroachment"]
        review_objs = [o for o in processed_objects if o["classification"] == "Needs human review"]
        normal_objs = [o for o in processed_objects if o["classification"] == "Not an encroachment"]

        if len(processed_objects) == 0:
            overall_classification = "No obstruction detected"
            overall_status = "NO OBSTRUCTION DETECTED (0 Objects Predicted by YOLOv5n-ONNX)"
            primary_type = "No Obstruction Detected"
        elif len(encroaching_objs) > 0:
            overall_classification = "Potential encroachment (Needs human review)"
            overall_status = (
                f"POTENTIAL ENCROACHMENT ({len(encroaching_objs)} Potential, {len(review_objs)} Needs Review) "
                f"— Human Review Required (Prototype ROI)"
            )
            # Pick highest-confidence potential encroachment
            top_enc = max(encroaching_objs, key=lambda x: x["confidence"])
            primary_type = f"{top_enc['category']} ({top_enc['coco_class']})"
        elif len(review_objs) > 0:
            overall_classification = "Needs human review"
            overall_status = f"NEEDS HUMAN REVIEW ({len(review_objs)} Object{'s' if len(review_objs) != 1 else ''} with Uncertain Overlap)"
            top_rev = max(review_objs, key=lambda x: x["confidence"])
            primary_type = f"Needs Review: {top_rev['category']} ({top_rev['coco_class']})"
        else:
            overall_classification = "Not an encroachment"
            overall_status = f"NOT AN ENCROACHMENT ({len(normal_objs)} Normal Traffic/Pedestrian Object{'s' if len(normal_objs) != 1 else ''})"
            primary_type = "Not an Encroachment"

        encroachment_summary = {
            "overall_classification": overall_classification,
            "overall_status": overall_status,
            "primary_encroachment_type": primary_type,
            "has_encroachment": len(encroaching_objs) > 0,
            "is_encroachment_present": len(encroaching_objs) > 0,
            "needs_human_review": (len(encroaching_objs) + len(review_objs)) > 0 and is_prototype_seg,
            "total_detected_count": len(processed_objects),
            "encroaching_objects_count": len(encroaching_objs),
            "needs_review_objects_count": len(review_objs),
            "non_encroaching_objects_count": len(normal_objs),
            # Exact 2D Pixel Measurements
            "image_area_px": image_area_px,
            "footpath_roi_area_px": footpath_roi_area_px,
            "road_roi_area_px": road_roi_area_px,
            "occupied_footpath_px": occupied_footpath_px,
            "free_footpath_px": free_footpath_px,
            "roi_pixel_occupancy_pct": roi_pixel_occupancy_pct,
            "occupancy_percentage": roi_pixel_occupancy_pct,
            # Uncalibrated real-world fields explicitly None
            "real_world_measurements_available": False,
            "occupied_area_sqm": None,
            "footpath_area_sqm": None,
            "free_area_sqm": None,
            "explanations": overall_explanations
        }

        return processed_objects, encroachment_summary


encroachment_engine = EncroachmentEngine()
