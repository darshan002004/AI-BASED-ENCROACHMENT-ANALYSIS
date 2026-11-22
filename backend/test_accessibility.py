import os
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

def run_accessibility_tests():
    with TestClient(app) as client:
        print("=== 1. Testing Uncalibrated Mode (Default) ===")
        veh_path = os.path.join("uploads", "original", "vehicle_indiranagar.jpg")
        with open(veh_path, "rb") as f:
            img_bytes = f.read()

        r_uncal = client.post(
            "/api/ai/analyze",
            files={"file": ("vehicle_indiranagar.jpg", img_bytes, "image/jpeg")}
        )
        assert r_uncal.status_code == 200, f"Error: {r_uncal.text}"
        data_uncal = r_uncal.json()

        # Uncalibrated assertions
        assert data_uncal["is_calibrated_physical_measurement"] is False
        assert data_uncal["real_world_measurements_available"] is False
        assert data_uncal["footpath_area_sqm"] is None
        assert data_uncal["occupied_area_sqm"] is None
        assert data_uncal["free_area_sqm"] is None
        assert data_uncal["footpath_width_m"] is None
        assert data_uncal["obstructed_width_m"] is None
        assert data_uncal["remaining_width_m"] is None

        # Pixel measurements & Bottleneck must be present
        assert data_uncal["footpath_roi_area_px"] > 0
        assert data_uncal["occupied_footpath_px"] > 0
        assert data_uncal["roi_pixel_occupancy_pct"] > 0
        assert data_uncal["bottleneck_y_px"] is not None
        assert data_uncal["corridor_width_at_bottleneck_px"] > 0
        assert data_uncal["obstructed_width_at_bottleneck_px"] > 0
        assert data_uncal["remaining_width_at_bottleneck_px"] >= 0
        assert 0.0 <= data_uncal["bottleneck_blockage_pct"] <= 100.0
        assert 0.0 <= data_uncal["accessibility_score"] <= 100.0
        assert "calibration_requirements" in data_uncal
        assert "scoring_assumptions" in data_uncal
        assert "scoring_formulas" in data_uncal
        assert "engineering_standards" in data_uncal

        print(f"  Uncalibrated Heuristic:")
        print(f"    - Area Occupancy: {data_uncal['roi_pixel_occupancy_pct']}%")
        print(f"    - Bottleneck Y: Row {data_uncal['bottleneck_y_px']} px")
        print(f"    - Corridor Width at Bottleneck: {data_uncal['corridor_width_at_bottleneck_px']} px")
        print(f"    - Obstructed Width: {data_uncal['obstructed_width_at_bottleneck_px']} px")
        print(f"    - Remaining Width: {data_uncal['remaining_width_at_bottleneck_px']} px")
        print(f"    - Bottleneck Blockage: {data_uncal['bottleneck_blockage_pct']}%")
        print(f"    - Accessibility Score: {data_uncal['accessibility_score']}/100")
        print(f"    - Status: {data_uncal['accessibility_status']}")

        print("\n=== 2. Testing Calibrated Mode (Nominal Footpath Width = 2.5m Standard Urban Sidewalk) ===")
        r_cal = client.post(
            "/api/ai/analyze?nominal_footpath_width_m=2.5",
            files={"file": ("vehicle_indiranagar.jpg", img_bytes, "image/jpeg")}
        )
        assert r_cal.status_code == 200, f"Error: {r_cal.text}"
        data_cal = r_cal.json()

        # Calibrated assertions
        assert data_cal["is_calibrated_physical_measurement"] is True
        assert data_cal["real_world_measurements_available"] is True
        assert data_cal["footpath_width_m"] == 2.50
        assert data_cal["obstructed_width_m"] is not None and data_cal["obstructed_width_m"] > 0
        assert data_cal["remaining_width_m"] is not None and data_cal["remaining_width_m"] >= 0
        assert round(data_cal["footpath_width_m"], 2) == round(data_cal["obstructed_width_m"] + data_cal["remaining_width_m"], 2)

        assert data_cal["footpath_area_sqm"] is not None and data_cal["footpath_area_sqm"] > 0
        assert data_cal["occupied_area_sqm"] is not None and data_cal["occupied_area_sqm"] > 0
        assert data_cal["free_area_sqm"] is not None and data_cal["free_area_sqm"] >= 0

        assert 0.0 <= data_cal["accessibility_score"] <= 100.0
        assert "IRC:SP:102" in data_cal["engineering_standards"]["reference_guidelines"][0]

        print(f"  Calibrated Metric Scale (2.5m standard sidewalk):")
        print(f"    - Nominal Footpath Width: {data_cal['footpath_width_m']} m")
        print(f"    - Obstructed Width: {data_cal['obstructed_width_m']} m")
        print(f"    - Remaining Walkable Width: {data_cal['remaining_width_m']} m")
        print(f"    - Footpath Area: {data_cal['footpath_area_sqm']} m²")
        print(f"    - Occupied Area: {data_cal['occupied_area_sqm']} m²")
        print(f"    - Free Walkway Area: {data_cal['free_area_sqm']} m²")
        print(f"    - Accessibility Score: {data_cal['accessibility_score']}/100")
        print(f"    - Status: {data_cal['accessibility_status']}")
        print(f"    - Severity: {data_cal['severity']} ({data_cal['severity_reason']})")
        print(f"    - Warnings: {data_cal['warnings']}")

        print("\n=== 3. Testing Constricted Corridor (1.8m IRC Minimum Footpath) ===")
        r_narrow = client.post(
            "/api/ai/analyze?nominal_footpath_width_m=1.8",
            files={"file": ("vehicle_indiranagar.jpg", img_bytes, "image/jpeg")}
        )
        assert r_narrow.status_code == 200
        data_narrow = r_narrow.json()
        assert data_narrow["footpath_width_m"] == 1.80
        assert data_narrow["remaining_width_m"] < 1.80
        # In a narrow 1.8m footpath with a car encroaching, remaining width will be severely constricted (<1.2m)
        assert data_narrow["severity"] in ["High", "Medium"]
        print(f"  Narrow Walkway Test:")
        print(f"    - Remaining Width: {data_narrow['remaining_width_m']} m")
        print(f"    - Status: {data_narrow['accessibility_status']}")

        print("\n=== 4. Testing Incident Persistence with Calibrated & Bottleneck Metrics ===")
        inc_payload = {
            "title": "Vehicle Blocking 100 Feet Road Footpath",
            "location_name": "100 Feet Road, Indiranagar, Bengaluru",
            "latitude": 12.9716,
            "longitude": 77.6412,
            "image_url": data_cal["original_image_url"],
            "annotated_image_url": data_cal["annotated_image_url"],
            "primary_encroachment_type": data_cal["primary_encroachment_type"],
            "detected_objects": data_cal["detected_objects"],
            "occupied_area_sqm": data_cal["occupied_area_sqm"],
            "footpath_area_sqm": data_cal["footpath_area_sqm"],
            "footpath_width_m": data_cal["footpath_width_m"],
            "obstructed_width_m": data_cal["obstructed_width_m"],
            "remaining_width_m": data_cal["remaining_width_m"],
            "bottleneck_blockage_pct": data_cal["bottleneck_blockage_pct"],
            "is_calibrated": data_cal["is_calibrated_physical_measurement"],
            "calibration_mode": "NOMINAL_STREET_PROFILE",
            "footpath_roi_area_px": data_cal["footpath_roi_area_px"],
            "occupied_footpath_px": data_cal["occupied_footpath_px"],
            "footpath_width_px": data_cal["footpath_width_px"],
            "remaining_width_px": data_cal["remaining_width_px"],
            "bottleneck_y_px": data_cal["bottleneck_y_px"],
            "occupancy_percentage": data_cal["occupancy_percentage"],
            "accessibility_score": data_cal["accessibility_score"],
            "accessibility_status": data_cal["accessibility_status"],
            "severity": data_cal["severity"],
            "severity_reason": data_cal["severity_reason"],
            "warnings": data_cal["warnings"],
            "confidence": data_cal["confidence"]
        }

        # Authenticate with citizen session
        r_auth = client.post("/api/auth/demo-switch/citizen")
        assert r_auth.status_code == 200
        token = r_auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r_create = client.post("/api/incidents", json=inc_payload, headers=headers)
        assert r_create.status_code == 200, f"Error: {r_create.text}"
        inc_created = r_create.json()
        inc_id = inc_created["id"]

        r_get = client.get(f"/api/incidents/{inc_id}", headers=headers)
        assert r_get.status_code == 200
        inc_saved = r_get.json()

        assert inc_saved["is_calibrated"] is True
        assert inc_saved["footpath_width_m"] == 2.50
        assert inc_saved["remaining_width_m"] == data_cal["remaining_width_m"]
        assert inc_saved["bottleneck_y_px"] == data_cal["bottleneck_y_px"]
        assert inc_saved["footpath_roi_area_px"] == data_cal["footpath_roi_area_px"]
        print(f"  Incident {inc_saved['incident_number']} persisted successfully with dual-mode metrics:")
        print(f"    - Calibrated: {inc_saved['is_calibrated']}")
        print(f"    - Remaining Width: {inc_saved['remaining_width_m']} m (Bottleneck row Y={inc_saved['bottleneck_y_px']} px)")
        print(f"    - Footpath Area: {inc_saved['footpath_area_sqm']} m², Occupied: {inc_saved['occupied_area_sqm']} m²")

        print("\nALL FOOTPATH OCCUPANCY & ACCESSIBILITY TESTS PASSED 100%!")

if __name__ == "__main__":
    run_accessibility_tests()
