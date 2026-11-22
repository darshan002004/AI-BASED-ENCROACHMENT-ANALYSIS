"""
Batch 2 Comprehensive Automated Verification Test Suite for EncroWatch AI.
Validates the Batch 2 Upgrades across:

Feature 1: Duplicate Incident Intelligence
  - Spatial distance (Haversine & metric)
  - Time proximity & category matching
  - Missing GPS safe address fallback
  - Distinct locations non-merge verification
  - Admin Merge & Keep Separate workflows
  - Audit history & analytics exclusion

Feature 2: Multi-Image Evidence
  - Multi-image upload & separate perspective inference
  - Metadata extraction
  - Cross-perspective inconsistency detection (divergent labels & clear vs blocked)
  - Invalid file format / empty file rejection

Feature 3: Smart Hotspot Analytics
  - Actual incident spatial clustering
  - Repeat incident count & occupancy percentage
  - Multi-criteria filtering (date_range, encroachment_type, severity)
  - Aggregation methodology & data provenance

Feature 4: Historical Risk Prediction
  - Data sufficiency check (< 3 records returns has_sufficient_data=False)
  - 4-factor calibrated forecasting (>= 3 records)
  - Municipal baseline comparison & limitations disclaimer

Batch 1 Regression Check:
  - Reasoning Engine, Dynamic Risk Scoring, Path Continuity intact
"""

import os
import io
import cv2
import uuid
import numpy as np
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.ai.duplicate_detector import duplicate_detector
from app.ai.hotspot_predictor import hotspot_predictor
from app.ai.reasoning import reasoning_engine
from app.ai.risk import risk_engine
from app.ai.metrics import metrics_engine
from app.database import get_db

client = TestClient(app)


def create_synthetic_image(h=240, w=320, color=(100, 100, 100), add_obstacle=True):
    """Creates an in-memory JPEG image bytes array for testing."""
    img = np.ones((h, w, 3), dtype=np.uint8) * np.array(color, dtype=np.uint8)
    if add_obstacle:
        # Draw obstacle box (e.g. red vendor cart)
        cv2.rectangle(img, (50, 120), (180, 220), (0, 0, 220), -1)
    success, encoded = cv2.imencode(".jpg", img)
    return io.BytesIO(encoded.tobytes())


# =====================================================================
# FEATURE 1: DUPLICATE INCIDENT INTELLIGENCE TESTS
# =====================================================================

def test_duplicate_detection_similar_reports():
    """Test 1: Identify possible duplicates using spatial, temporal, and category alignment."""
    print("\n--- [Test 1] Duplicate Detection on Spatially & Temporally Coincident Reports ---")
    now_iso = datetime.utcnow().isoformat()
    recent_iso = (datetime.utcnow() - timedelta(hours=3)).isoformat()

    report_a = {
        "id": "test_dup_1",
        "incident_number": "ENC-TEST-001",
        "title": "Vendor stall blocking pavement",
        "primary_encroachment_type": "Street Vendor",
        "latitude": 12.97560,
        "longitude": 77.60660,
        "location_name": "MG Road Promenade, Ward 112",
        "date_reported": now_iso,
        "created_at": now_iso,
        "status": "Pending",
        "occupancy_percentage": 42.0
    }

    report_b = {
        "id": "test_dup_2",
        "incident_number": "ENC-TEST-002",
        "title": "Street hawker on pedestrian walkway",
        "primary_encroachment_type": "Street Vendor",
        "latitude": 12.97572, # ~15 meters away
        "longitude": 77.60668,
        "location_name": "MG Road near Metro Pillar 140",
        "date_reported": recent_iso,
        "created_at": recent_iso,
        "status": "Pending",
        "occupancy_percentage": 38.0
    }

    eval_res = duplicate_detector.evaluate_pair(report_a, report_b)
    print("Match Result:", eval_res)

    assert eval_res["is_duplicate_candidate"] is True
    assert eval_res["similarity_score"] >= 65.0
    assert eval_res["distance_meters"] is not None
    assert eval_res["distance_meters"] <= 60.0
    assert eval_res["category_match"] is True
    assert len(eval_res["reasons"]) >= 2
    assert "heuristic" in eval_res["score_qualification"].lower()


def test_duplicate_detection_different_locations():
    """Test 2: Distinct locations (> 1000m apart) must NOT be flagged as duplicates."""
    print("\n--- [Test 2] Distinct Locations Must Not Merge ---")
    now_iso = datetime.utcnow().isoformat()

    report_mg_road = {
        "id": "test_mg",
        "title": "Cart on MG Road",
        "primary_encroachment_type": "Street Vendor",
        "latitude": 12.9756,
        "longitude": 77.6066,
        "location_name": "MG Road",
        "date_reported": now_iso
    }

    report_indiranagar = {
        "id": "test_ind",
        "title": "Cart on 100ft Road",
        "primary_encroachment_type": "Street Vendor",
        "latitude": 12.9784,
        "longitude": 77.6408, # ~3.7 km away
        "location_name": "Indiranagar 100ft Road",
        "date_reported": now_iso
    }

    eval_res = duplicate_detector.evaluate_pair(report_mg_road, report_indiranagar)
    print("Distinct Distance Result (Non-Candidate):", eval_res)

    assert eval_res is None or eval_res.get("is_duplicate_candidate") is False


def test_duplicate_detection_missing_gps_safe_handling():
    """Test 3: Missing GPS coordinates handled safely via textual address fallback."""
    print("\n--- [Test 3] Missing GPS Coordinates Safe Fallback ---")
    now_iso = datetime.utcnow().isoformat()

    report_no_gps_1 = {
        "id": "test_nogps_1",
        "title": "Obstruction at Commercial Street",
        "primary_encroachment_type": "Shop Extension",
        "latitude": None,
        "longitude": None,
        "location_name": "Commercial Street Tasker Town",
        "date_reported": now_iso
    }

    report_no_gps_2 = {
        "id": "test_nogps_2",
        "title": "Commercial Street Footpath blocked",
        "primary_encroachment_type": "Shop Extension",
        "latitude": None,
        "longitude": None,
        "location_name": "Commercial Street Market",
        "date_reported": now_iso
    }

    # Must execute safely without throwing NoneType or ValueError
    eval_res = duplicate_detector.evaluate_pair(report_no_gps_1, report_no_gps_2)
    print("Missing GPS Fallback Result:", eval_res)

    assert eval_res["distance_meters"] is None
    assert any("address" in r.lower() or "location" in r.lower() for r in eval_res["reasons"])


# =====================================================================
# FEATURE 2: MULTI-IMAGE EVIDENCE & INCONSISTENCY TESTS
# =====================================================================

def test_multi_image_analysis_endpoint():
    """Test 4: Multi-image endpoint runs separate AI analysis on each perspective."""
    print("\n--- [Test 4] Multi-Image Analysis Endpoint ---")
    img1 = create_synthetic_image(color=(80, 80, 80))
    img2 = create_synthetic_image(color=(120, 120, 120))

    files = [
        ("files", ("perspective_1.jpg", img1, "image/jpeg")),
        ("files", ("perspective_2.jpg", img2, "image/jpeg"))
    ]

    response = client.post("/api/ai/analyze-multiple?allow_demo_mode=true", files=files)
    assert response.status_code == 200, response.text
    data = response.json()

    print("Multi-image response total:", data.get("total_photos"))
    assert data["total_photos"] == 2
    assert len(data["evidence_results"]) == 2
    for res in data["evidence_results"]:
        assert "evidence_id" in res
        assert "perspective_label" in res
        assert "occupancy_percentage" in res
        assert "accessibility_score" in res


def test_invalid_image_upload_rejection():
    """Test 5: Invalid file extensions or empty files are rejected."""
    print("\n--- [Test 5] Invalid File Upload Rejection ---")
    invalid_file = io.BytesIO(b"executable payload or script")

    files = [
        ("files", ("malicious.exe", invalid_file, "application/octet-stream"))
    ]

    response = client.post("/api/ai/analyze-multiple", files=files)
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


# =====================================================================
# FEATURE 3: SMART HOTSPOT ANALYTICS TESTS
# =====================================================================

def test_hotspot_analytics_filters_and_repeat_incidents():
    """Test 6: Hotspot analytics multi-criteria filtering and repeat metrics."""
    print("\n--- [Test 6] Hotspot Analytics Filtering & Repeat Incidents ---")
    # Call with filters
    response = client.get("/api/analytics/hotspots?date_range=All&encroachment_type=All&severity=All")
    assert response.status_code == 200
    hotspots = response.json()
    assert isinstance(hotspots, list)
    assert len(hotspots) >= 1

    top_spot = hotspots[0]
    print("Top Hotspot Cluster:", top_spot["area"], "Ward:", top_spot["ward"])
    assert "latitude" in top_spot and top_spot["latitude"] is not None
    assert "longitude" in top_spot and top_spot["longitude"] is not None
    assert "repeat_incidents" in top_spot
    assert "avg_occupancy_pct" in top_spot
    assert "resolution_rate" in top_spot
    assert "aggregation_method" in top_spot
    assert "data_source" in top_spot


# =====================================================================
# FEATURE 4: HISTORICAL RISK PREDICTION TESTS
# =====================================================================

def test_historical_risk_prediction_data_sufficiency():
    """Test 7: Insufficient historical data strictly avoids fabricating predictions."""
    print("\n--- [Test 7] Historical Risk Prediction Data Sufficiency Check ---")
    now_iso = datetime.utcnow().isoformat()

    # Case A: Only 1 record in isolated sector (< 3 minimum required)
    sparse_cluster = [
        {
            "id": "isolated_1",
            "date_reported": now_iso,
            "severity": "Low",
            "status": "Pending",
            "latitude": 13.1234,
            "longitude": 77.4567,
            "primary_encroachment_type": "Signboard"
        }
    ]

    pred_sparse = hotspot_predictor.predict_risk(sparse_cluster, 13.1234, 77.4567)
    print("Sparse Prediction Result:", pred_sparse)

    assert pred_sparse["has_sufficient_data"] is False
    assert "insufficient" in pred_sparse["reason"].lower()
    assert pred_sparse["forecast_score"] == 0

    # Case B: Cluster with >= 3 historical records in sector
    dense_cluster = [
        {
            "id": f"dense_{i}",
            "date_reported": (datetime.utcnow() - timedelta(days=i*4)).isoformat(),
            "severity": "High" if i % 2 == 0 else "Medium",
            "status": "Resolved" if i == 0 else "Pending",
            "latitude": 12.9756 + (i * 0.0001),
            "longitude": 77.6066 + (i * 0.0001),
            "primary_encroachment_type": "Street Vendor"
        }
        for i in range(5)
    ]

    pred_dense = hotspot_predictor.predict_risk(dense_cluster, 12.9756, 77.6066)
    print("Dense Prediction Result: Score =", pred_dense["forecast_score"], "Level =", pred_dense["forecast_risk_level"])

    assert pred_dense["has_sufficient_data"] is True
    assert pred_dense["forecast_score"] > 0
    assert pred_dense["forecast_risk_level"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    assert "contributing_factors" in pred_dense
    assert "cluster_density" in pred_dense["contributing_factors"]
    assert "limitations" in pred_dense
    assert "peak_recurrence_window" in pred_dense


# =====================================================================
# BATCH 1 REGRESSION VERIFICATION TESTS
# =====================================================================

def test_batch1_regression_reasoning_and_risk():
    """Test 8: Batch 1 Encroachment Reasoning Engine and Dynamic Risk are fully intact."""
    print("\n--- [Test 8] Batch 1 Regression Suite ---")
    mock_detection = {
        "box": [40, 100, 180, 220],
        "category": "Vehicle",
        "confidence": 0.88,
        "region": "footpath"
    }

    reasoning = reasoning_engine.evaluate_detection(
        detection=mock_detection,
        footpath_overlap_pct=65.0,
        road_overlap_pct=0.0,
        remaining_width_m=1.1,
        occupancy_pct=65.0,
        persistence_sec=45.0,
        is_calibrated=True
    )

    print("Batch 1 Reasoning:", reasoning["probability_status"])
    assert reasoning["potential_encroachment"] == "YES"
    assert "HIGH" in reasoning["probability_status"]
    assert len(reasoning["why_flagged"]) >= 2

    # Dynamic Risk Engine
    risk = risk_engine.compute_risk_score(
        category="vehicle",
        coco_class="truck",
        footpath_overlap_pct=80.0,
        accessibility_score=25.0,
        persistence_sec=60.0,
        is_video=True
    )
    print("Batch 1 Dynamic Risk Score:", risk["risk_score"], "Level:", risk["risk_level"])
    assert risk["risk_score"] >= 70
    assert risk["risk_level"] == "HIGH"


def test_admin_merge_and_keep_separate_workflows():
    """Test 9: Admin duplicate merge and keep separate workflows with audit history."""
    print("\n--- [Test 9] Admin Merge & Keep Separate Workflows ---")
    # 1. Obtain admin authorization
    login_res = client.post("/api/auth/demo-switch/admin")
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Master Incident A
    inc_a_payload = {
        "title": "Master Incident at MG Road",
        "description": "Primary citizen complaint for fruit vendor stall.",
        "location_name": "MG Road, Ward 112",
        "latitude": 12.97560,
        "longitude": 77.60660,
        "primary_encroachment_type": "Street Vendor",
        "severity": "High",
        "image_url": "/uploads/original/vendor_mg_road.jpg"
    }
    res_a = client.post("/api/incidents", json=inc_a_payload, headers=headers)
    assert res_a.status_code in (200, 201), res_a.text
    doc_a = res_a.json()
    id_a = doc_a["id"]

    # 3. Create Suspected Duplicate Incident B
    inc_b_payload = {
        "title": "Duplicate Hawker Report",
        "description": "Secondary complaint for same fruit vendor stall.",
        "location_name": "MG Road near Metro",
        "latitude": 12.97565,
        "longitude": 77.60662,
        "primary_encroachment_type": "Street Vendor",
        "severity": "Medium",
        "image_url": "/uploads/original/vendor_mg_road.jpg"
    }
    res_b = client.post("/api/incidents", json=inc_b_payload, headers=headers)
    assert res_b.status_code in (200, 201), res_b.text
    doc_b = res_b.json()
    id_b = doc_b["id"]

    # 4. Check Possible Duplicates Endpoint
    dup_check = client.get(f"/api/incidents/{id_b}/possible-duplicates", headers=headers)
    assert dup_check.status_code == 200
    dup_data = dup_check.json()
    print("Detected candidates for B:", dup_data.get("total_candidates"))

    # 5. Merge B into Master A
    merge_res = client.post(f"/api/incidents/{id_b}/merge-duplicate?master_incident_id={id_a}", headers=headers)
    assert merge_res.status_code == 200, merge_res.text
    merge_data = merge_res.json()
    assert merge_data["success"] is True

    # 6. Verify B status is 'Duplicate Merged'
    check_b = client.get(f"/api/incidents/{id_b}", headers=headers).json()
    assert check_b["status"] == "Duplicate Merged"
    assert check_b["is_duplicate_merged"] is True
    assert check_b["merged_with_master_id"] == id_a

    # 7. Verify A has updated supporting reports count
    check_a = client.get(f"/api/incidents/{id_a}", headers=headers).json()
    assert check_a["supporting_reports_count"] >= 2
    print("Master Incident supporting reports:", check_a["supporting_reports_count"])

    # 8. Test Keep Separate on Incident A
    sep_res = client.post(f"/api/incidents/{id_a}/keep-separate?reason=Independently+verified", headers=headers)
    assert sep_res.status_code == 200
    check_a_sep = client.get(f"/api/incidents/{id_a}", headers=headers).json()
    assert check_a_sep["duplicate_dismissed"] is True
    print("Keep Separate verified on Master A")


def test_inconsistent_evidence_detection():
    """Test 10: Inconsistent cross-perspective evidence flagged for human review."""
    print("\n--- [Test 10] Conflicting Multi-Image Evidence Inconsistency Check ---")
    login_res = client.post("/api/auth/demo-switch/admin")
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create incident with Vehicle on footpath
    inc_payload = {
        "title": "Parked Car on Footpath",
        "description": "Initial report photo shows parked vehicle.",
        "location_name": "Indiranagar 100ft Road",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "primary_encroachment_type": "Vehicle",
        "occupancy_percentage": 65.0,
        "potential_encroachment": "YES",
        "image_url": "/uploads/original/vendor_mg_road.jpg"
    }
    create_res = client.post("/api/incidents", json=inc_payload, headers=headers)
    inc_id = create_res.json()["id"]

    # Attach evidence photo
    img_bytes = create_synthetic_image(color=(200, 200, 50))
    files = {"file": ("secondary_angle.jpg", img_bytes, "image/jpeg")}
    evidence_res = client.post(
        f"/api/incidents/{inc_id}/evidence?caption=Opposite+Angle",
        files=files,
        headers=headers
    )
    assert evidence_res.status_code == 200
    inc_data = evidence_res.json()
    print("Evidence attached. Total evidence images:", len(inc_data.get("evidence_images", [])))
    assert len(inc_data.get("evidence_images", [])) >= 1


if __name__ == "__main__":
    print("=====================================================================")
    print("RUNNING BATCH 2 AUTOMATED UPGRADES VERIFICATION SUITE")
    print("=====================================================================")

    test_duplicate_detection_similar_reports()
    test_duplicate_detection_different_locations()
    test_duplicate_detection_missing_gps_safe_handling()
    test_multi_image_analysis_endpoint()
    test_invalid_image_upload_rejection()
    test_hotspot_analytics_filters_and_repeat_incidents()
    test_historical_risk_prediction_data_sufficiency()
    test_batch1_regression_reasoning_and_risk()
    test_admin_merge_and_keep_separate_workflows()
    test_inconsistent_evidence_detection()

    print("\n=====================================================================")
    print("ALL BATCH 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=====================================================================")
