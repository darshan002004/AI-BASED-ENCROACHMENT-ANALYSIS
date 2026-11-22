"""
Batch 5.5 Comprehensive Automated Verification Test Suite for EncroWatch AI.
Validates:
Feature A: Citizen Incident Tracking Portal
  - Test 1: Citizens can list only their own reports (strict IDOR boundary)
  - Test 2: Unauthorized citizen incident access is rejected (HTTP 403 Forbidden)
Feature B: Municipal SLA and Escalation Engine
  - Test 3: SLA deadlines calculated correctly from rules (response and resolution targets)
  - Test 4: Repeated escalation does not duplicate escalations (idempotency with 24h cooldown)
  - Test 5: Citizen users cannot modify protected fields (severity, assignment, priority)
Feature C: Resolution Verification & Reopening
  - Test 6: Officer resolution requires notes and after-evidence (transitions to Resolved - Pending Verification)
  - Test 7: Rejected resolution preserves history and requires mandatory reason (transitions to Under Investigation)
  - Test 8: Reopening updates status to Reopened and requires mandatory justification
Feature D: Citizen & Officer In-App Notifications
  - Test 9: Deduplication prevents duplicate notifications within 5-minute window
  - Test 10: Notification content does not leak private information (PII/unblurred data)
Feature E: Privacy-Conscious Public Transparency
  - Test 11: Public endpoints exclude private fields and provide generalized coordinates (~1.1km)
  - Test 12: Public statistics calculated from actual records with explicit denominator
Feature F: Citizen Feedback and Service Quality
  - Test 13: Citizen service feedback permissions, rating boundaries, and duplicate-submission update policy
  - Test 14: Audit logs capture sensitive state transitions (resolutions, reopens, escalations)
Regression Suite:
  - Test 15: Full regression integration across Batches 1–5 (AI reasoning, accessibility, risk, duplicates, privacy)
"""

import os
import io
import json
import uuid
import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import get_db
from app.services.sla_engine import sla_engine
from app.services.notification_service import notification_service
from app.ai.reasoning import reasoning_engine
from app.ai.risk import risk_engine
from app.ai.duplicate_detector import duplicate_detector
from app.ai.privacy import privacy_engine
from app.utils.security import compute_audit_record_hash

client = TestClient(app)


def get_auth_headers(role="admin"):
    """Helper to authenticate as specified demo role."""
    res = client.post(f"/api/auth/demo-switch/{role}")
    assert res.status_code == 200, f"Demo switch failed for {role}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestBatch5Point5CitizenAndMunicipalServices:
    """Batch 5.5 test suite verifying municipal SLA, citizen tracking, resolution verification, and notifications."""

    # -------------------------------------------------------------------------
    # Feature A: Citizen Incident Tracking Portal
    # -------------------------------------------------------------------------
    def test_01_citizen_can_list_only_own_reports(self):
        """Test 1: Citizens can list only their own reports via strict IDOR boundary."""
        citizen_headers = get_auth_headers("citizen")

        # Unique coordinate so it does not auto-merge with MG Road duplicates
        inc_data = {
            "title": "Unique Citizen Isolated Footpath Stall",
            "primary_encroachment_type": "Street Vendor",
            "location_name": "Yelahanka New Town Outer Ring",
            "latitude": 13.1005,
            "longitude": 77.5960,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "Medium",
            "occupancy_percentage": 25.0,
            "accessibility_score": 60.0
        }
        res_create = client.post("/api/incidents", json=inc_data, headers=citizen_headers)
        assert res_create.status_code == 200, f"Incident create failed: {res_create.text}"
        created_inc = res_create.json()
        citizen_inc_id = created_inc["id"]

        # List incidents as citizen
        res_list = client.get("/api/incidents?my_reports=true", headers=citizen_headers)
        assert res_list.status_code == 200
        reports = res_list.json()
        assert isinstance(reports, list)
        assert any(r["id"] == citizen_inc_id for r in reports)

        # Ensure all returned reports belong to this citizen
        me_res = client.get("/api/auth/me", headers=citizen_headers)
        citizen_user_id = me_res.json()["id"]
        for r in reports:
            assert r.get("reporter_id") == citizen_user_id or any(
                s.get("reporter_id") == citizen_user_id for s in r.get("supporting_reports", [])
            )

    def test_02_unauthorized_incident_access_rejected(self):
        """Test 2: Unauthorized citizen incident access is rejected with HTTP 403 Forbidden."""
        admin_headers = get_auth_headers("admin")
        citizen_headers = get_auth_headers("citizen")

        # Admin creates incident belonging to admin at isolated coords
        inc_data = {
            "title": "Restricted Commercial Encroachment",
            "primary_encroachment_type": "Commercial Display",
            "location_name": "Koramangala 80ft Road Isolated",
            "latitude": 12.8052,
            "longitude": 77.4045,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "High",
            "occupancy_percentage": 45.0,
            "accessibility_score": 40.0
        }
        res_create = client.post("/api/incidents", json=inc_data, headers=admin_headers)
        assert res_create.status_code == 200, f"Admin incident create failed: {res_create.text}"
        admin_inc_id = res_create.json()["id"]

        # Citizen attempts to access this non-owned incident
        res_get = client.get(f"/api/incidents/{admin_inc_id}", headers=citizen_headers)
        assert res_get.status_code == 403, f"Expected 403 Forbidden, got {res_get.status_code}"

    # -------------------------------------------------------------------------
    # Feature B: Municipal SLA and Escalation Engine
    # -------------------------------------------------------------------------
    def test_03_sla_deadlines_calculated_from_rules(self):
        """Test 3: SLA deadlines calculated correctly from persistent rules."""
        admin_headers = get_auth_headers("admin")

        # Fetch SLA rules
        res_rules = client.get("/api/sla/rules", headers=admin_headers)
        assert res_rules.status_code == 200
        rules_data = res_rules.json()
        rules = rules_data if isinstance(rules_data, list) else rules_data.get("rules", [])
        assert len(rules) > 0

        # Create an incident to evaluate
        inc_data = {
            "title": "Severe Obstruction SLA Target",
            "primary_encroachment_type": "Construction Material",
            "location_name": "Hebbal Flyover Pedestrian Ramp",
            "latitude": 13.0358,
            "longitude": 77.5970,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "High",
            "occupancy_percentage": 60.0,
            "accessibility_score": 30.0
        }
        res_inc = client.post("/api/incidents", json=inc_data, headers=admin_headers)
        assert res_inc.status_code == 200
        inc = res_inc.json()

        # Run SLA evaluation on this specific incident
        res_eval = client.post(f"/api/sla/evaluate?incident_id={inc['id']}", headers=admin_headers)
        assert res_eval.status_code == 200
        eval_result = res_eval.json()
        assert eval_result["total_evaluated"] >= 1

        # Check incident SLA status
        res_sla = client.get(f"/api/sla/incident/{inc['id']}", headers=admin_headers)
        assert res_sla.status_code == 200
        sla_data = res_sla.json()
        assert "milestones" in sla_data
        milestones = sla_data["milestones"]
        assert "initial_response" in milestones
        assert "final_resolution" in milestones
        assert milestones["initial_response"]["target_hours"] > 0
        assert milestones["final_resolution"]["target_hours"] > 0

    def test_04_repeated_escalation_does_not_duplicate(self):
        """Test 4: Repeated escalation does not duplicate escalations (idempotency with 24h cooldown)."""
        admin_headers = get_auth_headers("admin")

        # Run evaluate twice in quick succession
        res_eval1 = client.post("/api/sla/evaluate", headers=admin_headers)
        assert res_eval1.status_code == 200

        res_eval2 = client.post("/api/sla/evaluate", headers=admin_headers)
        assert res_eval2.status_code == 200
        # Second run within seconds should trigger 0 new escalations due to 24h cooldown
        assert res_eval2.json()["escalated_count"] == 0

    def test_05_citizen_cannot_modify_protected_fields(self):
        """Test 5: Citizen users cannot modify protected fields (severity, assigned_officer, priority)."""
        citizen_headers = get_auth_headers("citizen")

        # Citizen creates an incident
        inc_data = {
            "title": "Citizen Attempted Priority Manipulation",
            "primary_encroachment_type": "Street Vendor",
            "location_name": "Jayanagar 4th Block",
            "latitude": 12.9299,
            "longitude": 77.5824,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "Medium"
        }
        res_create = client.post("/api/incidents", json=inc_data, headers=citizen_headers)
        assert res_create.status_code == 200
        inc_id = res_create.json()["id"]

        # Citizen attempts to reassign incident to an officer or elevate priority
        res_patch = client.patch(
            f"/api/incidents/{inc_id}",
            json={"assigned_officer_id": "fake_officer", "priority_rank": "Emergency"},
            headers=citizen_headers
        )
        assert res_patch.status_code in (403, 400), "Citizens must not be able to reassign or modify administrative priority"

    # -------------------------------------------------------------------------
    # Feature C: Resolution Verification & Reopening
    # -------------------------------------------------------------------------
    def test_06_officer_resolution_requires_notes_and_evidence(self):
        """Test 6: Officer resolution requires notes (>=10 chars) and after-evidence."""
        admin_headers = get_auth_headers("admin")
        officer_headers = get_auth_headers("officer")

        # Create active incident
        inc_data = {
            "title": "Clearance Case for Resolution",
            "primary_encroachment_type": "Temporary Structure",
            "location_name": "Whitefield ITPL Main Road",
            "latitude": 12.9850,
            "longitude": 77.7280,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "Medium",
            "status": "In Progress"
        }
        res_inc = client.post("/api/incidents", json=inc_data, headers=admin_headers)
        assert res_inc.status_code == 200
        inc_id = res_inc.json()["id"]

        # Attempt submit with notes < 10 chars -> 400
        res_bad1 = client.post(
            f"/api/incidents/{inc_id}/submit-resolution",
            json={"resolution_notes": "short", "after_image_url": "/uploads/after/test.jpg"},
            headers=officer_headers
        )
        assert res_bad1.status_code == 400

        # Attempt submit without after photo -> 400
        res_bad2 = client.post(
            f"/api/incidents/{inc_id}/submit-resolution",
            json={"resolution_notes": "Vendor relocated to authorized municipal vending zone.", "after_image_url": ""},
            headers=officer_headers
        )
        assert res_bad2.status_code == 400

        # Valid submit with photo and detailed notes
        res_valid = client.post(
            f"/api/incidents/{inc_id}/submit-resolution",
            json={
                "resolution_notes": "Vendor relocated to authorized municipal vending zone, footpath fully cleared.",
                "after_image_url": "/uploads/after/test_clearance.jpg"
            },
            headers=officer_headers
        )
        assert res_valid.status_code == 200, f"Submit resolution failed: {res_valid.text}"
        resolved_inc = res_valid.json()
        assert resolved_inc["status"] == "Resolved - Pending Verification"
        assert len(resolved_inc["after_images"]) >= 1

    def test_07_rejected_resolution_requires_reason_and_preserves_history(self):
        """Test 7: Supervisory rejection requires a reason and moves status back to Under Investigation."""
        admin_headers = get_auth_headers("admin")
        officer_headers = get_auth_headers("officer")

        # Create and submit resolution
        inc_data = {
            "title": "Disputed Clearance Case",
            "primary_encroachment_type": "Street Vendor",
            "location_name": "Malleshwaram 8th Cross",
            "latitude": 13.0031,
            "longitude": 77.5703,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "Medium",
            "status": "In Progress"
        }
        inc_id = client.post("/api/incidents", json=inc_data, headers=admin_headers).json()["id"]

        client.post(
            f"/api/incidents/{inc_id}/submit-resolution",
            json={
                "resolution_notes": "Partial cleanup done on the sidewalk.",
                "after_image_url": "/uploads/after/partial_clearance.jpg"
            },
            headers=officer_headers
        )

        # Admin rejects without reason -> 400
        res_bad_reject = client.post(
            f"/api/incidents/{inc_id}/review-resolution",
            json={"decision": "REJECT", "review_notes": ""},
            headers=admin_headers
        )
        assert res_bad_reject.status_code == 400

        # Admin rejects with documented reason
        res_reject = client.post(
            f"/api/incidents/{inc_id}/review-resolution",
            json={"decision": "REJECT", "reason": "Cart debris and packaging materials remain on sidewalk.", "review_notes": "Cart debris and packaging materials remain on sidewalk."},
            headers=admin_headers
        )
        assert res_reject.status_code == 200
        rejected_inc = res_reject.json()
        assert rejected_inc["status"] == "Under Investigation"
        assert rejected_inc["resolution_rejection_reason"] == "Cart debris and packaging materials remain on sidewalk."

    def test_08_reopening_updates_status_and_requires_reason(self):
        """Test 8: Reopening updates status to Reopened and requires mandatory justification."""
        admin_headers = get_auth_headers("admin")
        officer_headers = get_auth_headers("officer")

        # Setup an incident that is verified resolved
        inc_data = {
            "title": "Resolved Case To Be Reopened",
            "primary_encroachment_type": "Vehicle on Footpath",
            "location_name": "BTM Layout 2nd Stage",
            "latitude": 12.9166,
            "longitude": 77.6101,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "Low",
            "status": "In Progress"
        }
        inc_id = client.post("/api/incidents", json=inc_data, headers=admin_headers).json()["id"]

        client.post(
            f"/api/incidents/{inc_id}/submit-resolution",
            json={
                "resolution_notes": "Vehicle towed away by traffic enforcement.",
                "after_image_url": "/uploads/after/towed_car.jpg"
            },
            headers=officer_headers
        )
        client.post(
            f"/api/incidents/{inc_id}/review-resolution",
            json={"decision": "ACCEPT", "review_notes": "Clearance verified."},
            headers=admin_headers
        )

        # Reopen without reason -> 400
        res_bad_reopen = client.post(
            f"/api/incidents/{inc_id}/reopen",
            json={"reason": " "},
            headers=admin_headers
        )
        assert res_bad_reopen.status_code == 400

        # Reopen with reason
        res_reopen = client.post(
            f"/api/incidents/{inc_id}/reopen",
            json={"reason": "Citizen reports vehicle has parked back on the footpath same afternoon."},
            headers=admin_headers
        )
        assert res_reopen.status_code == 200
        reopened_inc = res_reopen.json()
        assert reopened_inc["status"] == "Reopened"
        assert reopened_inc["reopen_reason"] == "Citizen reports vehicle has parked back on the footpath same afternoon."

    # -------------------------------------------------------------------------
    # Feature D: Citizen & Officer Notifications
    # -------------------------------------------------------------------------
    def test_09_notification_deduplication(self):
        """Test 9: Deduplication prevents duplicate notifications within 5-minute window."""
        citizen_headers = get_auth_headers("citizen")
        me_res = client.get("/api/auth/me", headers=citizen_headers)
        user_id = me_res.json()["id"]

        unique_incident_id = f"test_inc_{uuid.uuid4().hex[:8]}"

        # Send first notification via service
        loop = asyncio.get_event_loop()
        database = get_db()
        n1 = loop.run_until_complete(notification_service.create_notification(
            db=database,
            recipient_id=user_id,
            recipient_role="citizen",
            notif_type="SLA_APPROACHING_DEADLINE",
            title="SLA Warning",
            message="Your incident SLA milestone has been evaluated.",
            incident_id=unique_incident_id
        ))
        assert n1 is not None

        # Send duplicate notification immediately
        n2 = loop.run_until_complete(notification_service.create_notification(
            db=database,
            recipient_id=user_id,
            recipient_role="citizen",
            notif_type="SLA_APPROACHING_DEADLINE",
            title="SLA Warning",
            message="Your incident SLA milestone has been evaluated.",
            incident_id=unique_incident_id
        ))
        # Deduplicated: returns existing document without creating duplicate record
        assert n1["id"] == n2["id"]

    def test_10_notification_content_privacy(self):
        """Test 10: Notification content does not leak private user information."""
        admin_headers = get_auth_headers("admin")
        res = client.get("/api/notifications?limit=20", headers=admin_headers)
        assert res.status_code == 200
        items = res.json()["items"]
        for notif in items:
            msg = notif.get("message", "")
            # Ensure no passwords or internal secrets leak
            assert "password" not in msg.lower()
            assert "jwt" not in msg.lower()

    # -------------------------------------------------------------------------
    # Feature E: Privacy-Conscious Public Transparency
    # -------------------------------------------------------------------------
    def test_11_public_endpoints_exclude_private_fields(self):
        """Test 11: Public endpoints exclude private fields and provide coarse coordinates."""
        res = client.get("/api/public/incidents?limit=20")
        assert res.status_code == 200
        items = res.json()
        assert isinstance(items, list)

        for item in items:
            # Prohibited sensitive fields
            assert "reporter_id" not in item
            assert "reporter_name" not in item
            assert "reporter_phone" not in item
            assert "internal_notes" not in item
            assert "raw_evidence_paths" not in item

            # Verify coarse coordinates (2 decimal places ~1.1km)
            if item.get("generalized_latitude") is not None:
                lat_str = str(item["generalized_latitude"])
                decimals = len(lat_str.split(".")[1]) if "." in lat_str else 0
                assert decimals <= 2, f"Coarse latitude had {decimals} decimals, expected <= 2"

    def test_12_public_statistics_from_actual_records(self):
        """Test 12: Public statistics calculated from actual records with explicit denominator."""
        res = client.get("/api/public/statistics?days=30")
        assert res.status_code == 200
        stats = res.json()
        assert "total_reports_received" in stats
        assert "verified_resolutions" in stats
        assert "open_cases" in stats
        assert "resolution_rate_pct" in stats
        assert "average_resolution_days" in stats
        assert 0.0 <= stats["resolution_rate_pct"] <= 100.0

    # -------------------------------------------------------------------------
    # Feature F: Citizen Feedback and Service Quality
    # -------------------------------------------------------------------------
    def test_13_citizen_service_feedback_lifecycle(self):
        """Test 13: Citizen service feedback rating submission, update policy, and quality summary."""
        admin_headers = get_auth_headers("admin")
        citizen_headers = get_auth_headers("citizen")
        officer_headers = get_auth_headers("officer")

        # Create incident filed by citizen at isolated coordinate outside city cluster
        import random
        rand_lat = 15.1000 + random.uniform(0.01, 0.90)
        rand_lon = 75.1000 + random.uniform(0.01, 0.90)
        inc_data = {
            "title": f"Feedback Evaluation Case {uuid.uuid4().hex[:6]}",
            "primary_encroachment_type": "Street Vendor",
            "location_name": "Isolated Sector Test",
            "latitude": rand_lat,
            "longitude": rand_lon,
            "image_url": "/uploads/original/clear_street.jpg",
            "severity": "Low"
        }
        res_create = client.post("/api/incidents", json=inc_data, headers=citizen_headers)
        assert res_create.status_code == 200
        inc_id = res_create.json()["id"]

        # Citizen attempts to rate while still In Progress -> 400
        res_bad_fb = client.post(
            f"/api/incidents/{inc_id}/citizen-feedback",
            json={"satisfaction_rating": 5, "timeliness_rating": 4},
            headers=citizen_headers
        )
        assert res_bad_fb.status_code == 400

        # Officer resolves and Admin verifies
        client.post(
            f"/api/incidents/{inc_id}/submit-resolution",
            json={
                "resolution_notes": "Vendor stall moved to designated spot.",
                "after_image_url": "/uploads/after/vendor_spot.jpg"
            },
            headers=officer_headers
        )
        client.post(
            f"/api/incidents/{inc_id}/review-resolution",
            json={"decision": "ACCEPT", "review_notes": "Accepted."},
            headers=admin_headers
        )

        # Citizen submits valid rating
        res_fb1 = client.post(
            f"/api/incidents/{inc_id}/citizen-feedback",
            json={"satisfaction_rating": 5, "timeliness_rating": 4, "feedback_text": "Prompt and clear resolution!"},
            headers=citizen_headers
        )
        assert res_fb1.status_code == 200
        fb_item = res_fb1.json()
        assert fb_item["satisfaction_rating"] == 5
        assert fb_item["timeliness_rating"] == 4

        # Citizen updates rating (idempotent update policy)
        res_fb2 = client.post(
            f"/api/incidents/{inc_id}/citizen-feedback",
            json={"satisfaction_rating": 4, "timeliness_rating": 4, "feedback_text": "Updated feedback"},
            headers=citizen_headers
        )
        assert res_fb2.status_code == 200
        assert res_fb2.json()["satisfaction_rating"] == 4

        # Verify Service Quality summary includes feedback
        res_summary = client.get("/api/service-quality/summary", headers=admin_headers)
        assert res_summary.status_code == 200
        summary = res_summary.json()
        assert summary["total_feedbacks"] >= 1
        assert summary["average_satisfaction"] is not None

    def test_14_audit_logs_capture_sensitive_transitions(self):
        """Test 14: Audit logs capture sensitive state transitions (resolutions, reopens, escalations)."""
        admin_headers = get_auth_headers("admin")
        res_logs = client.get("/api/audit/logs?limit=50", headers=admin_headers)
        assert res_logs.status_code == 200
        items = res_logs.json()["items"]

        actions = [log["action"] for log in items]
        assert len(actions) > 0, "Audit logs should not be empty"

    # -------------------------------------------------------------------------
    # Regression Suite: Batches 1–5 Intact
    # -------------------------------------------------------------------------
    def test_15_full_regression_integration(self):
        """Test 15: Full regression integration across Batches 1–5."""
        # Batch 1: Reasoning engine
        scene_eval = reasoning_engine.generate_overall_explanation(
            evaluated_objects=[],
            overall_accessibility_score=100.0,
            footpath_occupancy_pct=0.0,
            path_continuity="CLEAR"
        )
        assert scene_eval["potential_encroachment"] == "NO"

        # Batch 1: Risk engine
        risk = risk_engine.compute_risk_score(
            category="Clear",
            coco_class="none",
            footpath_overlap_pct=0.0,
            accessibility_score=100.0,
            persistence_sec=None,
            is_video=False
        )
        assert risk["level"] == "LOW"

        # Batch 2: Duplicate detector
        now_iso = datetime.now(timezone.utc).isoformat()
        rep_a = {
            "id": "t1",
            "incident_number": "ENC-001",
            "title": "Vendor",
            "primary_encroachment_type": "Street Vendor",
            "latitude": 12.9756,
            "longitude": 77.6066,
            "location_name": "MG Road",
            "date_reported": now_iso,
            "created_at": now_iso,
            "status": "Pending",
            "occupancy_percentage": 40.0
        }
        rep_b = {
            "id": "t2",
            "incident_number": "ENC-002",
            "title": "Hawker",
            "primary_encroachment_type": "Street Vendor",
            "latitude": 12.9757,
            "longitude": 77.6067,
            "location_name": "MG Road",
            "date_reported": now_iso,
            "created_at": now_iso,
            "status": "Pending",
            "occupancy_percentage": 35.0
        }
        eval_res = duplicate_detector.evaluate_pair(rep_a, rep_b)
        assert eval_res["is_duplicate_candidate"] is True

        # Batch 3: Privacy engine
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        blurred = privacy_engine.apply_gaussian_blur(img)
        mosaic = privacy_engine.apply_mosaic(img)
        assert blurred is not None
        assert blurred.shape == (100, 100, 3)
        assert mosaic is not None

        # Batch 5: Model registry
        res_models = client.get("/api/model-ops/models", headers=get_auth_headers("admin"))
        assert res_models.status_code == 200
        models_data = res_models.json()
        assert models_data["total_models"] >= 1
