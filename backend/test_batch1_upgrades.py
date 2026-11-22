"""
Batch 1 Comprehensive Verification Test Suite for EncroWatch AI.
Validates the 5 Core Upgrades across the 10 Required Test Scenarios:

1. Clear footpath
2. Vehicle on road
3. Vehicle on footpath
4. Street vendor on footpath
5. Multiple obstructions
6. Video with persistent object
7. Video with moving object
8. Poor-quality image
9. Image without visible footpath
10. Insufficient evidence case
"""

import os
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.reasoning import reasoning_engine
from app.ai.metrics import metrics_engine
from app.ai.risk import risk_engine
from app.ai.encroachment_engine import encroachment_engine
from app.ai.segmentor import segmentor
from app.ai.tracker import tracker
from app.ai.pipeline import run_ai_pipeline


def create_dummy_video(filename: str, num_frames: int = 25, fps: float = 5.0, move_box: bool = False):
    """Creates a temporary MP4 video with a synthetic stationary or moving rectangle."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    w, h = 320, 240
    out = cv2.VideoWriter(filename, fourcc, fps, (w, h))
    for i in range(num_frames):
        frame = np.ones((h, w, 3), dtype=np.uint8) * 128
        # Left side footpath corridor
        cv2.rectangle(frame, (0, 100), (120, 240), (94, 197, 34), -1)
        # Road corridor
        cv2.rectangle(frame, (120, 100), (320, 240), (246, 130, 59), -1)
        
        # Object
        x_offset = int(i * 8) if move_box else 20
        cv2.rectangle(frame, (x_offset, 140), (x_offset + 50, 210), (0, 0, 220), -1)
        out.write(frame)
    out.release()


def test_scenario_1_clear_footpath():
    """Scenario 1: Clear Footpath (No Obstructions Detected)"""
    print("\n--- [Scenario 1] Clear Footpath ---")
    h, w = 480, 640
    dummy_img = np.ones((h, w, 3), dtype=np.uint8) * 120
    _, geom = segmentor.segment(dummy_img)

    # Empty detections
    raw_objects = []
    processed_objects, enc_summary = encroachment_engine.analyze(raw_objects, geom)
    acc_metrics = metrics_engine.calculate_accessibility(geom, enc_summary, processed_objects)
    scene_eval = reasoning_engine.generate_overall_explanation(
        processed_objects,
        acc_metrics["accessibility_score"],
        acc_metrics["roi_pixel_occupancy_pct"],
        acc_metrics["path_continuity"]
    )
    dynamic_risk = risk_engine.compute_risk_score(
        category="Clear",
        coco_class="none",
        footpath_overlap_pct=0.0,
        accessibility_score=acc_metrics["accessibility_score"],
        persistence_sec=None,
        is_video=False
    )

    print(f"  Decision: {scene_eval['potential_encroachment']}")
    print(f"  Reason: {scene_eval['reason']}")
    print(f"  Continuity: {acc_metrics['path_continuity']}")
    print(f"  Accessibility Score: {acc_metrics['accessibility_score']} ({acc_metrics['accessibility_category']})")
    print(f"  Risk Level: {dynamic_risk['level']} ({dynamic_risk['score']}/100)")

    assert scene_eval["potential_encroachment"] == "NO"
    assert acc_metrics["path_continuity"] == "CLEAR"
    assert acc_metrics["accessibility_score"] == 100.0
    assert acc_metrics["accessibility_category"] == "Good"
    assert acc_metrics["obstruction_impact"] == "LOW"
    assert dynamic_risk["level"] == "LOW"
    print("  => PASSED: Clear footpath correctly marked NO encroachment and 100% accessible.")


def test_scenario_2_vehicle_on_road():
    """Scenario 2: Vehicle on Road (Not on Footpath)"""
    print("\n--- [Scenario 2] Vehicle on Road ---")
    h, w = 480, 640
    dummy_img = np.ones((h, w, 3), dtype=np.uint8) * 120
    _, geom = segmentor.segment(dummy_img)

    # Vehicle in the right-center portion (road region: x=400 to 520, y=280 to 400)
    raw_objects = [{
        "bbox": [400, 280, 120, 120],
        "coco_class": "car",
        "category": "Vehicle",
        "confidence": 0.89,
        "label": "Car"
    }]

    processed_objects, enc_summary = encroachment_engine.analyze(raw_objects, geom)
    assert len(processed_objects) == 1
    car_obj = processed_objects[0]

    # Evaluate with reasoning engine
    reasoning_eval = reasoning_engine.evaluate_detection(
        car_obj,
        footpath_overlap_pct=car_obj["footpath_overlap_pct"],
        road_overlap_pct=car_obj["road_overlap_pct"]
    )

    print(f"  Classification: {car_obj['classification']}")
    print(f"  Footpath Overlap: {car_obj['footpath_overlap_pct']}%")
    print(f"  Road Overlap: {car_obj['road_overlap_pct']}%")
    print(f"  Reasoning Decision: {reasoning_eval['potential_encroachment']}")
    print(f"  Reason: {reasoning_eval['reason']}")

    assert car_obj["classification"] == "Not an encroachment"
    assert car_obj["footpath_overlap_pct"] < 10.0
    assert reasoning_eval["potential_encroachment"] == "NO"
    assert "outside the pedestrian footpath" in reasoning_eval["reason"]
    print("  => PASSED: Road vehicle recognized as legitimate road occupant, not flagged.")


def test_scenario_3_vehicle_on_footpath():
    """Scenario 3: Vehicle on Footpath (Substantial Encroachment)"""
    print("\n--- [Scenario 3] Vehicle on Footpath ---")
    h, w = 480, 640
    dummy_img = np.ones((h, w, 3), dtype=np.uint8) * 120
    _, geom = segmentor.segment(dummy_img)

    # Vehicle placed heavily inside the prototype footpath ROI (x=10, y=280, w=150, h=160)
    raw_objects = [{
        "bbox": [10, 280, 150, 160],
        "coco_class": "car",
        "category": "Vehicle",
        "confidence": 0.88,
        "label": "Parked Car"
    }]

    processed_objects, enc_summary = encroachment_engine.analyze(raw_objects, geom)
    car_obj = processed_objects[0]

    acc_metrics = metrics_engine.calculate_accessibility(geom, enc_summary, processed_objects)
    reasoning_eval = reasoning_engine.evaluate_detection(
        car_obj,
        footpath_overlap_pct=car_obj["footpath_overlap_pct"],
        road_overlap_pct=car_obj["road_overlap_pct"],
        occupancy_pct=acc_metrics["roi_pixel_occupancy_pct"]
    )
    dynamic_risk = risk_engine.compute_risk_score(
        category="Vehicle",
        coco_class="car",
        footpath_overlap_pct=car_obj["footpath_overlap_pct"],
        accessibility_score=acc_metrics["accessibility_score"],
        persistence_sec=None,
        is_video=False
    )

    print(f"  Classification: {car_obj['classification']}")
    print(f"  Footpath Overlap: {car_obj['footpath_overlap_pct']}%")
    print(f"  Potential Encroachment: {reasoning_eval['potential_encroachment']}")
    print(f"  Reason: {reasoning_eval['reason']}")
    print(f"  Dynamic Risk: {dynamic_risk['score']} ({dynamic_risk['level']})")
    print(f"  Why Flagged Evidence Items: {len(reasoning_eval['evidence_breakdown'])}")

    assert car_obj["classification"] == "Potential encroachment"
    assert car_obj["footpath_overlap_pct"] >= 35.0
    assert reasoning_eval["potential_encroachment"] == "YES"
    assert dynamic_risk["score"] >= 40.0
    assert any(e["flagged"] for e in reasoning_eval["evidence_breakdown"])
    print("  => PASSED: Vehicle on footpath successfully flagged YES with explainable evidence.")


def test_scenario_4_street_vendor_on_footpath():
    """Scenario 4: Street Vendor / Cart on Footpath"""
    print("\n--- [Scenario 4] Street Vendor on Footpath ---")
    h, w = 480, 640
    dummy_img = np.ones((h, w, 3), dtype=np.uint8) * 120
    _, geom = segmentor.segment(dummy_img)

    # Street vendor / cart situated in footpath
    raw_objects = [{
        "bbox": [20, 260, 140, 140],
        "coco_class": "cart",
        "category": "Street Vendor",
        "confidence": 0.82,
        "label": "Vendor Cart"
    }]

    processed_objects, enc_summary = encroachment_engine.analyze(raw_objects, geom)
    vendor_obj = processed_objects[0]
    acc_metrics = metrics_engine.calculate_accessibility(geom, enc_summary, processed_objects)

    reasoning_eval = reasoning_engine.evaluate_detection(
        vendor_obj,
        footpath_overlap_pct=vendor_obj["footpath_overlap_pct"],
        road_overlap_pct=vendor_obj["road_overlap_pct"],
        occupancy_pct=acc_metrics["roi_pixel_occupancy_pct"]
    )

    print(f"  Footpath Overlap: {vendor_obj['footpath_overlap_pct']}%")
    print(f"  Potential Encroachment: {reasoning_eval['potential_encroachment']}")
    print(f"  Continuity: {acc_metrics['path_continuity']}")
    print(f"  Remaining Pedestrian Region: {acc_metrics['remaining_pedestrian_region_pct']}%")

    assert reasoning_eval["potential_encroachment"] == "YES"
    assert acc_metrics["remaining_pedestrian_region_pct"] < 100.0
    print("  => PASSED: Vendor cart identified as potential encroachment with corridor reduction.")


def test_scenario_5_multiple_obstructions():
    """Scenario 5: Multiple Obstructions Constricting Footpath"""
    print("\n--- [Scenario 5] Multiple Obstructions ---")
    h, w = 480, 640
    dummy_img = np.ones((h, w, 3), dtype=np.uint8) * 120
    _, geom = segmentor.segment(dummy_img)

    # 3 distinct objects obstructing different portions of footpath
    raw_objects = [
        {"bbox": [10, 220, 90, 90], "coco_class": "motorcycle", "category": "Vehicle", "confidence": 0.85, "label": "Motorbike"},
        {"bbox": [60, 270, 100, 100], "coco_class": "cart", "category": "Street Vendor", "confidence": 0.80, "label": "Vendor Cart"},
        {"bbox": [10, 340, 110, 100], "coco_class": "chair", "category": "Street Object", "confidence": 0.75, "label": "Stall Seating"}
    ]

    processed_objects, enc_summary = encroachment_engine.analyze(raw_objects, geom)
    acc_metrics = metrics_engine.calculate_accessibility(geom, enc_summary, processed_objects)
    scene_eval = reasoning_engine.generate_overall_explanation(
        processed_objects,
        acc_metrics["accessibility_score"],
        acc_metrics["roi_pixel_occupancy_pct"],
        acc_metrics["path_continuity"]
    )

    print(f"  Detected Objects: {len(processed_objects)}")
    print(f"  Footpath Occupancy: {acc_metrics['roi_pixel_occupancy_pct']}%")
    print(f"  Corridor Bottleneck Blockage: {acc_metrics['bottleneck_blockage_pct']}%")
    print(f"  Path Continuity: {acc_metrics['path_continuity']}")
    print(f"  Overall Decision: {scene_eval['overall_decision']}")

    assert len(processed_objects) == 3
    assert acc_metrics["path_continuity"] in ("PARTIALLY BLOCKED", "SEVERELY BLOCKED")
    assert scene_eval["potential_encroachment"] == "YES"
    assert acc_metrics["accessibility_score"] < 80.0
    print("  => PASSED: Cumulative bottleneck blockage triggers compromised continuity.")


def test_scenario_6_video_persistent_object():
    """Scenario 6: Video with Persistent Object (>= 3.0s Stationary)"""
    print("\n--- [Scenario 6] Video with Persistent Object ---")
    test_vid_path = "test_persistent_clip.mp4"
    # 5.0 seconds at 5 FPS = 25 frames
    create_dummy_video(test_vid_path, num_frames=25, fps=5.0, move_box=False)

    try:
        from unittest.mock import patch
        # Mock detector.detect to return a persistent vehicle parked on the footpath for all frames
        stationary_det = [{
            "bbox": [20, 140, 60, 70],
            "coco_class": "car",
            "category": "Vehicle",
            "confidence": 0.88,
            "label": "Parked Car",
            "prediction_source": "YOLOv5n-ONNX",
            "is_mock": False
        }]
        with patch.object(tracker, 'detect', return_value=(stationary_det, {}), create=True), \
             patch('app.ai.tracker.detector.detect', return_value=(stationary_det, {})):
            vid_results = tracker.process_video(test_vid_path)

        print(f"  Video Status: {vid_results['processing_status']}")
        print(f"  Total Duration: {vid_results['total_duration_sec']}s")
        print(f"  Frames Analyzed: {vid_results['frames_analyzed']}")
        print(f"  Persistent Obstructions: {len(vid_results['persistent_obstructions'])}")
        print(f"  Incident Triggered: {vid_results['incident_triggered']}")

        assert vid_results["processing_status"] in ("COMPLETED", "COMPLETED_CLIP_SHORTER_THAN_THRESHOLD")
        assert vid_results["total_duration_sec"] >= tracker.PERSISTENCE_THRESHOLD_SEC
        assert len(vid_results["persistent_obstructions"]) >= 1
        assert vid_results["persistent_obstructions"][0]["is_persistent"] is True
        assert vid_results["incident_triggered"] is True

        # Evaluate risk score with temporal persistence points
        risk_with_persistence = risk_engine.compute_risk_score(
            category="Vehicle",
            coco_class="car",
            footpath_overlap_pct=60.0,
            accessibility_score=40.0,
            persistence_sec=58.0,
            is_video=True
        )
        print(f"  Risk with 58s persistence: {risk_with_persistence['score']} (Factor 3: {risk_with_persistence['factors']['persistence']['points']}/20 pts)")
        assert risk_with_persistence["factors"]["persistence"]["points"] == 15.0

        # Peak persistence test (>= 60s)
        risk_peak = risk_engine.compute_risk_score(
            category="Vehicle",
            coco_class="car",
            footpath_overlap_pct=60.0,
            accessibility_score=40.0,
            persistence_sec=65.0,
            is_video=True
        )
        assert risk_peak["factors"]["persistence"]["points"] == 20.0
        print("  => PASSED: Stationary temporal persistence recognized and factored into risk.")
    finally:
        if os.path.exists(test_vid_path):
            os.remove(test_vid_path)


def test_scenario_7_video_moving_object():
    """Scenario 7: Video with Moving / Transient Object"""
    print("\n--- [Scenario 7] Video with Moving Object ---")
    test_vid_path = "test_moving_clip.mp4"
    # Moving object with high displacement
    create_dummy_video(test_vid_path, num_frames=25, fps=5.0, move_box=True)

    try:
        from unittest.mock import patch
        # Generate moving bounding boxes where object displaces significantly across frames
        frame_counter = {"count": 0}
        def moving_detect(frame):
            c = frame_counter["count"]
            frame_counter["count"] += 1
            # Shifts by 35px each sampled frame -> high displacement
            bx = 10 + (c * 35)
            det = [{
                "bbox": [bx, 140, 60, 70],
                "coco_class": "car",
                "category": "Vehicle",
                "confidence": 0.88,
                "label": "Moving Car",
                "prediction_source": "YOLOv5n-ONNX",
                "is_mock": False
            }]
            return det, {}

        with patch('app.ai.tracker.detector.detect', side_effect=moving_detect):
            vid_results = tracker.process_video(test_vid_path)

        print(f"  Video Status: {vid_results['processing_status']}")
        print(f"  Temporary Movements: {vid_results['temporary_movements_count']}")
        print(f"  Persistent Count: {len(vid_results['persistent_obstructions'])}")
        print(f"  Incident Triggered: {vid_results['incident_triggered']}")

        # Moving objects should NOT be flagged as persistent
        assert len(vid_results["persistent_obstructions"]) == 0
        assert vid_results["temporary_movements_count"] >= 1
        assert vid_results["incident_triggered"] is False
        print("  => PASSED: Transient/moving object is NOT classified as persistent obstruction.")
    finally:
        if os.path.exists(test_vid_path):
            os.remove(test_vid_path)


def test_scenario_8_poor_quality_image():
    """Scenario 8: Poor-Quality / Invalid Image Handling"""
    print("\n--- [Scenario 8] Poor-Quality Image Handling ---")
    with TestClient(app) as client:
        # 1. Invalid empty image
        r_empty = client.post("/api/ai/analyze", files={"file": ("empty.jpg", b"", "image/jpeg")})
        print(f"  Empty file status: {r_empty.status_code}")
        assert r_empty.status_code == 400

        # 2. Corrupted file bytes
        r_corrupt = client.post("/api/ai/analyze", files={"file": ("corrupt.jpg", b"NOT_A_VALID_JPEG_HEADER", "image/jpeg")})
        print(f"  Corrupted file status: {r_corrupt.status_code}")
        assert r_corrupt.status_code == 400

        # 3. Microscopic image (< 16x16)
        tiny_img = np.zeros((8, 8, 3), dtype=np.uint8)
        tiny_path = "tiny_test.jpg"
        cv2.imwrite(tiny_path, tiny_img)
        try:
            with open(tiny_path, "rb") as f:
                r_tiny = client.post("/api/ai/analyze", files={"file": (tiny_path, f, "image/jpeg")})
            print(f"  Tiny 8x8 image status: {r_tiny.status_code}")
            assert r_tiny.status_code == 400
            assert "too small" in r_tiny.json()["detail"]
        finally:
            if os.path.exists(tiny_path):
                os.remove(tiny_path)

        print("  => PASSED: Poor-quality and corrupt files safely rejected with clear HTTP 400.")


def test_scenario_9_image_without_visible_footpath():
    """Scenario 9: Image Without Visible Footpath (Fallback Coordinates)"""
    print("\n--- [Scenario 9] Image Without Visible Footpath ---")
    # Empty or zero footpath polygon
    geom_no_fp = {
        "footpath_polygon": [],
        "road_polygon": [[0, 0], [400, 0], [400, 300], [0, 300]],
        "footpath_roi_area_px": 0.0,
        "road_roi_area_px": 120000.0,
        "footpath_width_px": 0,
        "image_area_px": 120000,
        "segmentation_info": {"is_prototype": True}
    }
    enc_summary_no_fp = {
        "roi_pixel_occupancy_pct": 0.0,
        "occupied_footpath_px": 0.0,
        "free_footpath_px": 0.0,
        "needs_review_objects_count": 0,
        "overall_classification": "No obstruction detected"
    }

    acc = metrics_engine.calculate_accessibility(
        geometry_data=geom_no_fp,
        enc_summary=enc_summary_no_fp,
        detected_objects=[]
    )

    print(f"  Path Continuity: {acc['path_continuity']}")
    print(f"  Path Continuity Reason: {acc['path_continuity_reason']}")
    print(f"  Accessibility Score: {acc['accessibility_score']}")

    assert acc["path_continuity"] == "UNKNOWN"
    assert "Insufficient footpath region coordinates" in acc["path_continuity_reason"]
    print("  => PASSED: Absence of visible footpath geometry reports UNKNOWN without crashing.")


def test_scenario_10_insufficient_evidence():
    """Scenario 10: Insufficient Evidence / Ambiguous Overlap -> Needs Human Review"""
    print("\n--- [Scenario 10] Insufficient Evidence Case ---")
    h, w = 480, 640
    dummy_img = np.ones((h, w, 3), dtype=np.uint8) * 120
    _, geom = segmentor.segment(dummy_img)

    # Object with ambiguous boundary overlap (12% overlap) or low confidence (0.35)
    raw_objects = [{
        "bbox": [280, 350, 80, 80],
        "coco_class": "car",
        "category": "Vehicle",
        "confidence": 0.35,
        "label": "Ambiguous Object"
    }]

    processed_objects, enc_summary = encroachment_engine.analyze(raw_objects, geom)
    ambiguous_obj = processed_objects[0]

    reasoning_eval = reasoning_engine.evaluate_detection(
        ambiguous_obj,
        footpath_overlap_pct=12.0,  # borderline overlap
        road_overlap_pct=80.0
    )

    print(f"  Classification: {ambiguous_obj['classification']}")
    print(f"  Potential Encroachment: {reasoning_eval['potential_encroachment']}")
    print(f"  Needs Human Review: {reasoning_eval['needs_human_review']}")
    print(f"  Primary Reason: {reasoning_eval['reason']}")

    assert reasoning_eval["potential_encroachment"] == "NEEDS REVIEW"
    assert reasoning_eval["needs_human_review"] is True
    assert "Automatic decision withheld" in reasoning_eval["reason"] or "human review" in reasoning_eval["reason"].lower()
    print("  => PASSED: Ambiguous/insufficient evidence triggers NEEDS REVIEW without inventing facts.")


if __name__ == "__main__":
    print("==================================================================")
    print("RUNNING BATCH 1 TEN-SCENARIO AUTOMATED VERIFICATION SUITE")
    print("==================================================================")
    test_scenario_1_clear_footpath()
    test_scenario_2_vehicle_on_road()
    test_scenario_3_vehicle_on_footpath()
    test_scenario_4_street_vendor_on_footpath()
    test_scenario_5_multiple_obstructions()
    test_scenario_6_video_persistent_object()
    test_scenario_7_video_moving_object()
    test_scenario_8_poor_quality_image()
    test_scenario_9_image_without_visible_footpath()
    test_scenario_10_insufficient_evidence()
    print("\n==================================================================")
    print("ALL 10 BATCH 1 TEST SCENARIOS PASSED WITH ZERO FAILURES!")
    print("==================================================================")
