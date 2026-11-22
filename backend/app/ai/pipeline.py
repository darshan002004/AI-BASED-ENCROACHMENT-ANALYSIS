import cv2
import numpy as np
import os
import time
import uuid
from typing import Dict, Any, Optional
from app.ai.segmentor import segmentor
from app.ai.detector import detector
from app.ai.encroachment_engine import encroachment_engine
from app.ai.metrics import metrics_engine, SCORING_ASSUMPTIONS
from app.ai.reasoning import reasoning_engine
from app.ai.risk import risk_engine
from app.ai.privacy import privacy_engine
from app.config import settings


def run_ai_pipeline(
    image_path: str,
    output_prefix: str = "annotated",
    allow_demo_mode: bool = False,
    nominal_footpath_width_m: Optional[float] = None,
    calibration_px_per_m: Optional[float] = None
) -> Dict[str, Any]:
    """
    Executes the EncroWatch AI Pipeline with strict separation and transparency:
      1. Image Validation & Decoding
      2. Prototype Road & Footpath Region-of-Interest (ROI) Module (Explicitly labeled Non-AI Prototype unless ONNX segmentation weights are present)
      3. Stage 1 — Pure Object Detection (Pretrained YOLOv5n-ONNX COCO-80 predictions only; zero fabricated boxes or guessed classes)
      4. Stage 2 — Spatial Overlap & Encroachment Classification ('Potential encroachment', 'Needs human review', 'Not an encroachment', or 'No obstruction detected')
      5. Slice-by-Slice Horizontal Bottleneck & Occupancy Calculations (Dual Mode: Calibrated Metric Scale or Transparent Uncalibrated 2D Pixel Metrics)
      6. Saves Prototype ROI Overlay Map and Annotated Detection Output
    """
    start_time = time.time()

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Invalid or corrupted image file at path: {image_path}")

    h, w = img.shape[:2]
    if h < 16 or w < 16:
        raise ValueError(f"Image dimensions ({w}x{h}) are too small for computer vision analysis.")

    # 1. Road and Footpath Region Module (Prototype Geometric ROI)
    segmented_overlay, geometry_data = segmentor.segment(img)

    # 2. Stage 1: Pure YOLOv5n-ONNX Object Detection (raises RuntimeError if weights fail to load and allow_demo_mode=False)
    raw_detected_objects, detection_metadata = detector.detect(img, allow_demo_mode=allow_demo_mode)

    # 3. Stage 2: Spatial Overlap & Encroachment Classification
    processed_objects, enc_summary = encroachment_engine.analyze(raw_detected_objects, geometry_data)

    # Apply object footprint shading to prototype ROI map
    seg_with_obstructions = segmentor.apply_obstruction_overlays(segmented_overlay, processed_objects)

    # 4. Slice-by-Slice Walkability & Corridor Bottleneck Analysis (Calibrated or Uncalibrated)
    acc_metrics = metrics_engine.calculate_accessibility(
        geometry_data=geometry_data,
        enc_summary=enc_summary,
        detected_objects=processed_objects,
        nominal_footpath_width_m=nominal_footpath_width_m,
        calibration_px_per_m=calibration_px_per_m
    )

    # 5. Severity Estimation considering Area and Bottleneck Width Blockage
    severity, severity_reason = metrics_engine.compute_severity(
        overall_classification=enc_summary["overall_classification"],
        roi_pixel_occupancy_pct=enc_summary["roi_pixel_occupancy_pct"],
        bottleneck_blockage_pct=acc_metrics["bottleneck_blockage_pct"],
        remaining_width_m=acc_metrics.get("remaining_width_m"),
        needs_review_count=enc_summary["needs_review_objects_count"]
    )


    # 6. Render Bounding Boxes, Exact COCO Labels, Confidence & Classification on Annotated Canvas
    annotated_canvas = seg_with_obstructions.copy()
    font_scale = max(0.36, min(0.58, w / 700.0))
    thickness = 1 if w < 300 else 2

    for obj in processed_objects:
        bx, by, bw, bh = obj["bbox"]
        coco_cls = obj["coco_class"]
        conf = obj["confidence"]
        classification = obj["classification"]

        # Color coding by classification:
        # Red (BGR: 50, 50, 235) = Potential encroachment
        # Amber (BGR: 15, 158, 245) = Needs human review
        # Teal/Blue (BGR: 210, 140, 35) = Not an encroachment
        if classification == "Potential encroachment":
            box_color = (50, 50, 235)
            status_tag = "POTENTIAL ENCROACHMENT"
        elif classification == "Needs human review":
            box_color = (15, 158, 245)
            status_tag = "NEEDS REVIEW"
        else:
            box_color = (210, 140, 35)
            status_tag = "NOT ENCROACHMENT"

        cv2.rectangle(annotated_canvas, (bx, by), (bx + bw, by + bh), box_color, thickness)

        tag_text = f"{coco_cls} {conf * 100:.1f}% [{status_tag}]" if w >= 320 else f"{coco_cls} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        banner_top = max(0, by - th - 8)
        banner_btm = banner_top + th + 8
        cv2.rectangle(
            annotated_canvas,
            (bx, banner_top),
            (min(w - 1, bx + tw + 8), banner_btm),
            box_color,
            -1
        )
        cv2.putText(
            annotated_canvas,
            tag_text,
            (bx + 4, banner_btm - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )

    os.makedirs(os.path.join(settings.UPLOAD_DIR, "annotated"), exist_ok=True)
    uid = uuid.uuid4().hex[:10]
    annotated_filename = f"{output_prefix}_{uid}.jpg"
    seg_only_filename = f"segmap_{uid}.jpg"

    annotated_dest = os.path.join(settings.UPLOAD_DIR, "annotated", annotated_filename)
    seg_only_dest = os.path.join(settings.UPLOAD_DIR, "annotated", seg_only_filename)

    cv2.imwrite(annotated_dest, annotated_canvas)
    cv2.imwrite(seg_only_dest, seg_with_obstructions)

    elapsed_sec = round(max(0.01, time.time() - start_time), 3)

    # Confidence is NEVER invented: None when 0 objects are detected
    enc_objs = [o for o in processed_objects if o["classification"] == "Potential encroachment"]
    rev_objs = [o for o in processed_objects if o["classification"] == "Needs human review"]
    if enc_objs:
        overall_conf = round(float(max(o["confidence"] for o in enc_objs)), 4)
    elif rev_objs:
        overall_conf = round(float(max(o["confidence"] for o in rev_objs)), 4)
    elif processed_objects:
        overall_conf = round(float(max(o["confidence"] for o in processed_objects)), 4)
    else:
        overall_conf = None

    overall_explanation = (
        " ".join(enc_summary.get("explanations", []))
        if enc_summary.get("explanations")
        else (
            "No objects were detected by the pretrained YOLOv5n-ONNX model above the confidence threshold "
            f"({detector.confidence_threshold}). 0% of the Prototype Footpath ROI is obstructed."
        )
    )

    proc_status = (
        "DEMO_MODE_WEIGHTS_UNAVAILABLE"
        if detection_metadata.get("is_demo_mode")
        else "COMPLETED"
    )

    is_calibrated = acc_metrics["is_calibrated_physical_measurement"]

    # Evaluate each object with EncroachmentReasoningEngine (Upgrade 1)
    for obj in processed_objects:
        obj_eval = reasoning_engine.evaluate_detection(
            detection=obj,
            footpath_overlap_pct=obj.get("footpath_overlap_pct", 0.0),
            road_overlap_pct=obj.get("road_overlap_pct", 0.0),
            remaining_width_m=acc_metrics.get("remaining_width_m"),
            remaining_width_px=acc_metrics.get("remaining_width_at_bottleneck_px"),
            occupancy_pct=acc_metrics.get("roi_pixel_occupancy_pct", 0.0),
            persistence_sec=obj.get("duration_sec"),
            location_history_count=0,
            is_calibrated=is_calibrated
        )
        obj["reasoning"] = obj_eval

    # Overall Scene Reasoning & Explainable Checklist (Upgrade 1 & 13)
    scene_explanation = reasoning_engine.generate_overall_explanation(
        evaluated_objects=processed_objects,
        overall_accessibility_score=acc_metrics["accessibility_score"],
        footpath_occupancy_pct=acc_metrics["roi_pixel_occupancy_pct"],
        path_continuity=acc_metrics.get("path_continuity", "UNKNOWN"),
        is_calibrated=is_calibrated,
        remaining_width_m=acc_metrics.get("remaining_width_m")
    )

    # Dynamic Encroachment Risk Score (Upgrade 5)
    primary_category = enc_summary.get("primary_encroachment_type", "Street Object")
    dominant_overlap = enc_summary.get("roi_pixel_occupancy_pct", 0.0)
    primary_coco = enc_objs[0]["coco_class"] if enc_objs else (processed_objects[0]["coco_class"] if processed_objects else "object")

    dynamic_risk = risk_engine.compute_risk_score(
        category=primary_category,
        coco_class=primary_coco,
        footpath_overlap_pct=dominant_overlap,
        accessibility_score=acc_metrics["accessibility_score"],
        persistence_sec=None,
        is_video=False
    )

    # Privacy Protection Redaction (Upgrade 14)
    privacy_result = privacy_engine.redact_image(
        image_path=image_path,
        detected_objects=processed_objects,
        output_prefix="privacy"
    )

    return {
        "processing_status": proc_status,
        "image_dimensions": {"width": w, "height": h, "image_area_px": w * h},
        "raw_detections": raw_detected_objects,
        "detected_objects": processed_objects,
        "detection_metadata": detection_metadata,
        "segmentation_info": {
            **geometry_data.get("segmentation_info", {}),
            "footpath_roi_area_px": geometry_data["footpath_roi_area_px"],
            "road_roi_area_px": geometry_data["road_roi_area_px"],
            "footpath_width_px": geometry_data["footpath_width_px"],
            "camera_calibrated": is_calibrated,
            "footpath_area_sqm": acc_metrics["footpath_area_sqm"],
            "road_area_sqm": None,
            "segmentation_image_url": f"/uploads/annotated/{seg_only_filename}"
        },
        "encroachment_summary": enc_summary,
        "overall_classification": enc_summary["overall_classification"],
        "primary_encroachment_type": enc_summary["primary_encroachment_type"],
        "has_encroachment": enc_summary["has_encroachment"],
        "needs_human_review": enc_summary["needs_human_review"],
        "confidence": overall_conf,
        # Honest 2D Pixel Measurements
        "footpath_roi_area_px": enc_summary["footpath_roi_area_px"],
        "occupied_footpath_px": enc_summary["occupied_footpath_px"],
        "free_footpath_px": enc_summary["free_footpath_px"],
        "roi_pixel_occupancy_pct": enc_summary["roi_pixel_occupancy_pct"],
        "occupancy_percentage": enc_summary["roi_pixel_occupancy_pct"],
        "footpath_width_px": acc_metrics["corridor_width_at_bottleneck_px"],
        "obstructed_width_px": acc_metrics["obstructed_width_at_bottleneck_px"],
        "remaining_width_px": acc_metrics["remaining_width_at_bottleneck_px"],
        "horizontal_blockage_pct": acc_metrics["bottleneck_blockage_pct"],
        "remaining_width_pct": acc_metrics["bottleneck_clearance_pct"],
        # Slice-by-Slice Horizontal Bottleneck Analysis
        "bottleneck_y_px": acc_metrics["bottleneck_y_px"],
        "corridor_width_at_bottleneck_px": acc_metrics["corridor_width_at_bottleneck_px"],
        "obstructed_width_at_bottleneck_px": acc_metrics["obstructed_width_at_bottleneck_px"],
        "remaining_width_at_bottleneck_px": acc_metrics["remaining_width_at_bottleneck_px"],
        "bottleneck_blockage_pct": acc_metrics["bottleneck_blockage_pct"],
        "bottleneck_clearance_pct": acc_metrics["bottleneck_clearance_pct"],
        # Real-World Metric Scale (populated if calibrated, None if uncalibrated)
        "is_calibrated_physical_measurement": is_calibrated,
        "real_world_measurements_available": is_calibrated,
        "measurement_unit": acc_metrics["measurement_unit"],
        "calibration_metadata": acc_metrics["calibration_metadata"],
        "engineering_standards": acc_metrics["engineering_standards"],
        "scoring_formulas": acc_metrics["scoring_formulas"],
        "occupied_area_sqm": acc_metrics["occupied_area_sqm"],
        "footpath_area_sqm": acc_metrics["footpath_area_sqm"],
        "free_area_sqm": acc_metrics["free_area_sqm"],
        "footpath_width_m": acc_metrics["footpath_width_m"],
        "obstructed_width_m": acc_metrics["obstructed_width_m"],
        "remaining_width_m": acc_metrics["remaining_width_m"],
        # Accessibility Score, Category & Path Continuity (Upgrades 3 & 4)
        # Accessibility Score, Category, Continuity & Obstruction Impact (Upgrades 3 & 4)
        "accessibility_score": acc_metrics["accessibility_score"],
        "accessibility_category": acc_metrics.get("accessibility_category", "Good"),
        "obstruction_impact": acc_metrics.get("obstruction_impact", "LOW"),
        "remaining_pedestrian_region_pct": acc_metrics.get("remaining_pedestrian_region_pct", round(max(0.0, 100.0 - enc_summary["roi_pixel_occupancy_pct"]), 1)),
        "pixel_clearance_estimate_pct": acc_metrics["pixel_clearance_estimate_pct"],
        "accessibility_status": acc_metrics["accessibility_status"],
        "path_continuity": acc_metrics.get("path_continuity", "UNKNOWN"),
        "path_continuity_reason": acc_metrics.get("path_continuity_reason", ""),
        "calibration_requirements": acc_metrics["calibration_metadata"]["calibration_details"],
        "scoring_assumptions": SCORING_ASSUMPTIONS,
        "severity": severity,
        "severity_reason": severity_reason,
        "explanation": overall_explanation,
        "ai_explanation": overall_explanation,
        "warnings": acc_metrics["warnings"],
        # Explainable Reasoning & "WHY WAS THIS FLAGGED?" (Upgrades 1 & 13)
        "potential_encroachment": scene_explanation["potential_encroachment"],
        "reasoning_summary": scene_explanation,
        "reason": scene_explanation["reason"],
        "why_flagged": scene_explanation["checklist"],
        "probability_status": scene_explanation["overall_decision"],
        # Dynamic Risk Scoring (Upgrade 5)
        "risk_score": dynamic_risk["score"],
        "risk_level": dynamic_risk["level"],
        "risk_factors": dynamic_risk["factors"],
        "risk_formula": dynamic_risk["formula"],
        "persistence_sec": None,
        "is_persistent": False,
        "review_status": "NEEDS_REVIEW" if scene_explanation["potential_encroachment"] == "NEEDS REVIEW" else "PENDING",
        # Privacy Protection (Upgrade 14)
        "privacy_protected": True,
        "privacy_image_url": privacy_result["privacy_image_url"],
        "privacy_badge": privacy_result["badge"],
        "faces_redacted_count": privacy_result["faces_redacted_count"],
        "plates_redacted_count": privacy_result["plates_redacted_count"],
        # Visual Assets
        "annotated_image_url": f"/uploads/annotated/{annotated_filename}",
        "segmentation_image_url": f"/uploads/annotated/{seg_only_filename}",
        "processing_time_sec": elapsed_sec,
        "engine": detection_metadata["engine_summary"]
    }
