"""
Batch 3 Comprehensive Automated Verification Test Suite for EncroWatch AI.
Validates Batch 3 Upgrades across:

Feature 1: Human-in-the-Loop AI Review
  - Review queue for uncertain detections, conflicting evidence, and low confidence
  - Officer confirmation, category modification, and rejection workflows
  - Server-side mandatory reason validation for REJECT and MODIFY (HTTP 400)
  - Strict role-based protection: Unauthorized citizens forbidden from review (HTTP 403)
  - Separation of original AI predictions from human-verified findings
  - Consistent incident status and audit logging

Feature 2: Privacy Protection for Images
  - Real detector-based blurring of faces and vehicle license plates
  - Generation of redacted privacy-protected copy in /uploads/privacy/
  - Accurate metrics tracking: execution time (ms), counts of faces/plates, detector method
  - Corrupt/missing file failure handling (marks is_privacy_protected: False, no false claim)
  - Role-based original evidence access security (citizens receive privacy URL, raw URL protected by HTTP 403)
  - Transparent documentation that automated blurring is not infallible

Feature 3: AI Feedback Dataset & Model Improvement
  - Dedicated MongoDB collection (ai_feedback_dataset) with model_version and approval_status
  - Deduplication prevention on duplicate submissions for same review
  - Admin dataset approval and rejection endpoints
  - Privacy-safe export in JSONL and CSV formats with PII stripped
  - Structured retraining workflow specification (70/15/15 split, mAP@0.5 benchmark, municipal sign-off)

Regression Suite:
  - Batch 1 and Batch 2 capabilities intact
"""

import os
import io
import cv2
import json
import uuid
import numpy as np
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.ai.privacy import privacy_engine
from app.ai.reasoning import reasoning_engine
from app.ai.risk import risk_engine
from app.ai.duplicate_detector import duplicate_detector
from app.ai.hotspot_predictor import hotspot_predictor
from app.config import settings

client = TestClient(app)


def create_test_image_with_objects(filename="test_b3_sample.jpg"):
    """Creates a synthetic image with a pedestrian and vehicle for privacy test."""
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "original"), exist_ok=True)
    img_path = os.path.join(settings.UPLOAD_DIR, "original", filename)
    img = np.ones((300, 400, 3), dtype=np.uint8) * 160
    # Draw pedestrian (head + body)
    cv2.circle(img, (100, 70), 20, (120, 160, 220), -1)
    cv2.rectangle(img, (80, 90), (120, 220), (80, 80, 180), -1)
    # Draw vehicle (body + plate zone)
    cv2.rectangle(img, (220, 140), (360, 260), (40, 120, 60), -1)
    cv2.rectangle(img, (260, 225), (320, 245), (240, 240, 240), -1)
    cv2.putText(img, "KA01AB1234", (262, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
    cv2.imwrite(img_path, img)
    return img_path


def get_auth_headers(role="admin"):
    """Helper to authenticate as specified demo role."""
    res = client.post(f"/api/auth/demo-switch/{role}")
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# FEATURE 1: HUMAN-IN-THE-LOOP AI REVIEW TESTS
# =====================================================================

def test_hitl_officer_confirm_and_audit():
    """Test 1: Authorized officer confirms AI finding and updates incident status consistently."""
    print("\n--- [Test 1] HITL Officer Confirmation ---")
    officer_headers = get_auth_headers("officer")

    # 1. Create a pending incident
    inc_payload = {
        "title": "Commercial St Hawkers Obstruction",
        "location_name": "Commercial Street, Ward 92",
        "latitude": 12.9810,
        "longitude": 77.6080,
        "primary_encroachment_type": "Street Vendor",
        "severity": "Medium",
        "confidence": 0.88,
        "image_url": "/uploads/original/test_b3_sample.jpg"
    }
    create_res = client.post("/api/incidents", json=inc_payload, headers=officer_headers)
    assert create_res.status_code in (200, 201), create_res.text
    inc_data = create_res.json()
    inc_id = inc_data["id"]

    # 2. Officer submits CONFIRM
    verify_payload = {
        "incident_id": inc_id,
        "action": "CONFIRM",
        "original_ai_category": "Street Vendor",
        "original_ai_confidence": 0.88,
        "notes": "Verified fruit stall physically occupying walkway."
    }
    verify_res = client.post("/api/feedback/verify", json=verify_payload, headers=officer_headers)
    assert verify_res.status_code == 200, verify_res.text
    res_data = verify_res.json()
    assert res_data["success"] is True
    assert res_data["human_verification_status"] == "CONFIRM"

    # 3. Verify incident document status updated
    get_res = client.get(f"/api/incidents/{inc_id}", headers=officer_headers)
    assert get_res.status_code == 200
    updated = get_res.json()
    assert updated["human_verification_status"] == "CONFIRM"
    assert updated["status"] in ("Verified", "In Progress", "Assigned")
    assert updated["original_ai_category"] == "Street Vendor"


def test_hitl_mandatory_reason_validation():
    """Test 2: Reject and Modify strictly require non-empty notes (HTTP 400)."""
    print("\n--- [Test 2] Mandatory Reason Validation for Reject/Modify ---")
    officer_headers = get_auth_headers("officer")

    inc_payload = {
        "title": "Suspected False Positive Object",
        "location_name": "Brigade Road Footpath",
        "latitude": 12.9730,
        "longitude": 77.6070,
        "primary_encroachment_type": "Street Object",
        "severity": "Low",
        "confidence": 0.52,
        "image_url": "/uploads/original/test_b3_sample.jpg"
    }
    create_res = client.post("/api/incidents", json=inc_payload, headers=officer_headers)
    inc_id = create_res.json()["id"]

    # 1. Attempt REJECT with empty reason -> must fail with HTTP 400
    reject_fail = client.post("/api/feedback/verify", json={
        "incident_id": inc_id,
        "action": "REJECT",
        "original_ai_category": "Street Object",
        "notes": "   "
    }, headers=officer_headers)
    assert reject_fail.status_code == 400
    assert "A valid reason is required" in reject_fail.json()["detail"]

    # 2. Attempt MODIFY without reason -> must fail with HTTP 400
    modify_fail = client.post("/api/feedback/verify", json={
        "incident_id": inc_id,
        "action": "MODIFY",
        "original_ai_category": "Street Object",
        "corrected_category": "Construction Material",
        "notes": ""
    }, headers=officer_headers)
    assert modify_fail.status_code == 400
    assert "A valid reason is required" in modify_fail.json()["detail"]

    # 3. Submit REJECT with valid reason -> succeeds
    reject_success = client.post("/api/feedback/verify", json={
        "incident_id": inc_id,
        "action": "REJECT",
        "original_ai_category": "Street Object",
        "notes": "Authorized municipal telecom feeder box; not an unlawful encroachment."
    }, headers=officer_headers)
    assert reject_success.status_code == 200
    assert reject_success.json()["human_verification_status"] == "REJECT"

    # Verify incident status marked as Rejected
    inc_check = client.get(f"/api/incidents/{inc_id}", headers=officer_headers).json()
    assert inc_check["status"] == "Rejected"
    assert inc_check["human_verification_status"] == "REJECT"
    assert "Authorized municipal telecom" in inc_check["human_review_reason"]


def test_hitl_unauthorized_citizen_forbidden():
    """Test 3: Citizens cannot modify official review decisions (HTTP 403 Forbidden)."""
    print("\n--- [Test 3] Citizen Review Attempt Forbidden (HTTP 403) ---")
    citizen_headers = get_auth_headers("citizen")

    verify_attempt = client.post("/api/feedback/verify", json={
        "incident_id": "inc_001",
        "action": "REJECT",
        "original_ai_category": "Street Vendor",
        "notes": "Citizen trying to dismiss municipal ticket"
    }, headers=citizen_headers)

    assert verify_attempt.status_code == 403
    assert "Only authorized officers and admins" in verify_attempt.json()["detail"]


def test_officer_review_queue_endpoint():
    """Test 4: Review queue surfaces low confidence or uncertain items to officers."""
    print("\n--- [Test 4] Officer Review Queue Endpoint ---")
    officer_headers = get_auth_headers("officer")
    citizen_headers = get_auth_headers("citizen")

    # 1. Citizen cannot access review queue
    citizen_req = client.get("/api/incidents/review-queue", headers=citizen_headers)
    assert citizen_req.status_code == 403

    # 2. Officer accesses review queue
    officer_req = client.get("/api/incidents/review-queue", headers=officer_headers)
    assert officer_req.status_code == 200
    data = officer_req.json()
    assert "total_queued" in data
    assert "conflicting_evidence_count" in data
    assert "low_confidence_count" in data
    assert "items" in data

    if data["items"]:
        first = data["items"][0]
        assert "incident" in first
        assert "review_reasons" in first
        assert isinstance(first["review_reasons"], list)


# =====================================================================
# FEATURE 2: PRIVACY PROTECTION TESTS
# =====================================================================

def test_privacy_redaction_engine_success():
    """Test 5: Privacy engine redacts faces and plates, saves privacy copy, and outputs metrics."""
    print("\n--- [Test 5] Privacy Redaction Engine Success ---")
    sample_path = create_test_image_with_objects("privacy_test_real.jpg")

    detected_objects = [
        {"bbox": [80, 50, 50, 160], "coco_class": "person", "category": "pedestrian"},
        {"bbox": [220, 140, 140, 120], "coco_class": "car", "category": "vehicle"}
    ]

    result = privacy_engine.redact_image(sample_path, detected_objects=detected_objects)
    assert result["is_privacy_protected"] is True
    assert result["faces_detected"] >= 1
    assert result["plates_detected"] >= 1
    assert result["processing_time_ms"] > 0
    assert result["privacy_image_url"].startswith("/uploads/privacy/")
    assert os.path.exists(result["privacy_image_path"])
    assert "Automated privacy blurring" in result["limitations_notice"]
    assert result["preserves_raw_evidence"] is True


def test_privacy_redaction_corrupt_file_handling():
    """Test 6: Missing or invalid file marks is_privacy_protected: False without false claims."""
    print("\n--- [Test 6] Privacy Redaction Failure Handling ---")
    bad_result = privacy_engine.redact_image("non_existent_corrupted_file.xyz")
    assert bad_result["is_privacy_protected"] is False
    assert bad_result["faces_detected"] == 0
    assert bad_result["plates_detected"] == 0
    assert bad_result["privacy_image_url"] is None
    assert "not found" in bad_result["error"].lower()


def test_role_based_raw_evidence_security():
    """Test 7: Unredacted raw evidence is protected from unauthorized citizens."""
    print("\n--- [Test 7] Role-Based Raw Evidence Access Security ---")
    admin_headers = get_auth_headers("admin")
    officer_headers = get_auth_headers("officer")
    citizen_headers = get_auth_headers("citizen")

    # 1. Create an incident with privacy image
    inc_payload = {
        "title": "Privacy Protected Encroachment Dossier",
        "location_name": "Koramangala 80 Feet Road",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "primary_encroachment_type": "Vehicle on Footpath",
        "severity": "High",
        "image_url": "/uploads/original/test_b3_sample.jpg",
        "privacy_image_url": "/uploads/privacy/test_b3_sample_privacy.jpg",
        "privacy_protected": True
    }
    create_res = client.post("/api/incidents", json=inc_payload, headers=admin_headers)
    inc_id = create_res.json()["id"]

    # 2. Citizen viewing incident gets privacy-protected URL masked
    cit_view = client.get(f"/api/incidents/{inc_id}", headers=citizen_headers).json()
    assert cit_view["image_url"] == "/uploads/privacy/test_b3_sample_privacy.jpg"

    # 3. Citizen accessing raw-evidence endpoint directly is blocked with HTTP 403
    cit_raw_req = client.get(f"/api/incidents/{inc_id}/raw-evidence", headers=citizen_headers)
    assert cit_raw_req.status_code == 403
    assert "restricted to authorized municipal officers" in cit_raw_req.json()["detail"]

    # 4. Officer accessing raw-evidence endpoint succeeds (HTTP 200)
    off_raw_req = client.get(f"/api/incidents/{inc_id}/raw-evidence", headers=officer_headers)
    assert off_raw_req.status_code == 200
    off_data = off_raw_req.json()
    assert off_data["raw_image_url"] == "/uploads/original/test_b3_sample.jpg"


# =====================================================================
# FEATURE 3: AI FEEDBACK DATASET & MODEL IMPROVEMENT TESTS
# =====================================================================

def test_ai_feedback_dataset_deduplication():
    """Test 8: Duplicate feedback records for the same incident/reviewer update instead of duplicating."""
    print("\n--- [Test 8] AI Feedback Dataset Deduplication ---")
    officer_headers = get_auth_headers("officer")

    # Create incident first so target exists
    inc_payload = {
        "title": "Deduplication Test Incident",
        "location_name": "MG Road Footpath",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "primary_encroachment_type": "Street Vendor",
        "severity": "Medium",
        "confidence": 0.82,
        "image_url": "/uploads/original/test_b3_sample.jpg"
    }
    create_res = client.post("/api/incidents", json=inc_payload, headers=officer_headers)
    assert create_res.status_code == 200
    target_inc_id = create_res.json()["id"]

    # Submit review twice for same incident
    payload = {
        "incident_id": target_inc_id,
        "action": "CONFIRM",
        "original_ai_category": "Street Vendor",
        "original_ai_confidence": 0.82,
        "notes": "First submission notes"
    }
    res1 = client.post("/api/feedback/verify", json=payload, headers=officer_headers)
    assert res1.status_code == 200, res1.text
    fb_id_1 = res1.json()["feedback_id"]

    # Second submission with updated notes
    payload["notes"] = "Updated second submission notes"
    res2 = client.post("/api/feedback/verify", json=payload, headers=officer_headers)
    assert res2.status_code == 200, res2.text
    fb_id_2 = res2.json()["feedback_id"]

    # Must reuse the same feedback ID without creating duplicates
    assert fb_id_1 == fb_id_2

    # Query dataset
    dataset_res = client.get("/api/feedback/dataset", headers=officer_headers).json()
    matching = [item for item in dataset_res["items"] if item["id"] == fb_id_1]
    assert len(matching) == 1
    assert matching[0]["model_version"] == "YOLOv5n-ONNX-v1.0"
    assert matching[0]["notes"] == "Updated second submission notes"


def test_admin_dataset_approval_and_pii_export():
    """Test 9: Admin approval workflow, PII-sanitized export (JSONL/CSV), and training protocol."""
    print("\n--- [Test 9] Admin Dataset Management & PII-Sanitized Export ---")
    admin_headers = get_auth_headers("admin")

    # 1. Fetch dataset items
    dataset_res = client.get("/api/feedback/dataset", headers=admin_headers).json()
    assert "items" in dataset_res
    assert len(dataset_res["items"]) >= 1
    sample_id = dataset_res["items"][0]["id"]

    # 2. Admin approves sample
    appr_res = client.post(f"/api/feedback/{sample_id}/approve", headers=admin_headers)
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "APPROVED"

    # 3. Export JSONL with PII stripped
    jsonl_res = client.get("/api/feedback/export?format=jsonl", headers=admin_headers)
    assert jsonl_res.status_code == 200
    assert "application/x-ndjson" in jsonl_res.headers.get("content-type", "")

    lines = [line for line in jsonl_res.text.strip().split("\n") if line.strip()]
    assert len(lines) >= 1
    first_record = json.loads(lines[0])
    # Verify PII is stripped: no reviewer_name or reporter info
    assert "reviewer_name" not in first_record
    assert "reporter_name" not in first_record
    assert "original_ai_category" in first_record
    assert "model_version" in first_record

    # 4. Export CSV format
    csv_res = client.get("/api/feedback/export?format=csv", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "incident_id,action,original_ai_category" in csv_res.text

    # 5. Training workflow guidelines
    workflow_res = client.get("/api/feedback/training-workflow", headers=admin_headers)
    assert workflow_res.status_code == 200
    wf_data = workflow_res.json()
    assert wf_data["policy"]["automated_retraining"] is False
    assert wf_data["dataset_split"]["training_pct"] == 70
    assert wf_data["dataset_split"]["validation_pct"] == 15
    assert wf_data["dataset_split"]["testing_pct"] == 15
    assert "mAP@0.5" in wf_data["evaluation_criteria"]["primary_metric"]


# =====================================================================
# FEATURE 4: BATCH 1 & BATCH 2 REGRESSION TESTS
# =====================================================================

def test_batch1_batch2_regression_suite():
    """Test 10: Regression testing ensuring Batch 1 and Batch 2 capabilities remain intact."""
    print("\n--- [Test 10] Batch 1 & 2 Regression Suite ---")

    # 1. Batch 1 Reasoning Engine
    mock_detection = {
        "box": [50, 100, 150, 200],
        "category": "Street Vendor",
        "confidence": 0.85,
        "region": "footpath"
    }
    reasoning = reasoning_engine.evaluate_detection(
        detection=mock_detection,
        footpath_overlap_pct=60.0,
        road_overlap_pct=0.0,
        remaining_width_m=0.8,
        occupancy_pct=60.0,
        persistence_sec=None,
        is_calibrated=True
    )
    assert reasoning["potential_encroachment"] == "YES"

    # 2. Batch 1 Dynamic Risk Score
    risk = risk_engine.compute_risk_score(
        category="Vehicle",
        coco_class="car",
        footpath_overlap_pct=60.0,
        accessibility_score=40.0,
        persistence_sec=None,
        is_video=False
    )
    assert risk["score"] >= 60

    # 3. Batch 2 Duplicate Detector
    inc_a = {
        "id": "inc_a",
        "incident_number": "ENC-REG-01",
        "latitude": 12.9756,
        "longitude": 77.6066,
        "primary_encroachment_type": "Street Vendor",
        "date_reported": datetime.utcnow().isoformat()
    }
    dup_res = duplicate_detector.find_duplicate_incident(
        new_lat=12.97565,
        new_lng=77.60665,
        new_type="Street Vendor",
        active_incidents=[inc_a]
    )
    assert dup_res is not None
    assert dup_res["is_duplicate_candidate"] is True

    # 4. Batch 2 Hotspot Prediction Data Sufficiency
    sparse_pred = hotspot_predictor.predict_risk([inc_a])
    assert sparse_pred["has_sufficient_data"] is False


if __name__ == "__main__":
    print("=====================================================================")
    print("RUNNING BATCH 3 AUTOMATED UPGRADES VERIFICATION SUITE")
    print("=====================================================================")

    test_hitl_officer_confirm_and_audit()
    test_hitl_mandatory_reason_validation()
    test_hitl_unauthorized_citizen_forbidden()
    test_officer_review_queue_endpoint()
    test_privacy_redaction_engine_success()
    test_privacy_redaction_corrupt_file_handling()
    test_role_based_raw_evidence_security()
    test_ai_feedback_dataset_deduplication()
    test_admin_dataset_approval_and_pii_export()
    test_batch1_batch2_regression_suite()

    print("\n=====================================================================")
    print("ALL BATCH 3 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=====================================================================")
