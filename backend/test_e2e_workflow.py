import os
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

def run_e2e_workflow_tests():
    print("======================================================================")
    print("=== STARTING ENCROWATCH AI END-TO-END WORKFLOW INTEGRATION TEST SUITE ===")
    print("======================================================================")

    with TestClient(app) as client:
        # ------------------------------------------------------------------
        # PHASE 1: CITIZEN AUTHENTICATION & INITIAL REPORT SUBMISSION
        # ------------------------------------------------------------------
        print("\n--- [PHASE 1] Citizen Authentication & Encroachment Submission ---")
        r_citizen1 = client.post("/api/auth/demo-switch/citizen")
        assert r_citizen1.status_code == 200, f"Citizen 1 login failed: {r_citizen1.text}"
        c1_token = r_citizen1.json()["access_token"]
        c1_user = r_citizen1.json()["user"]
        c1_headers = {"Authorization": f"Bearer {c1_token}"}
        print(f"  [+] Citizen 1 Authenticated: {c1_user['full_name']} ({c1_user['email']})")

        # Create or verify sample image exists for testing
        test_img_path = os.path.join("uploads", "original", "vendor_mg_road.jpg")
        assert os.path.exists(test_img_path), f"Test image missing: {test_img_path}"

        # Citizen 1 analyzes the image with AI pipeline first
        with open(test_img_path, "rb") as f:
            r_ai = client.post(
                "/api/ai/analyze?nominal_footpath_width_m=2.5",
                files={"file": ("vendor_mg_road.jpg", f.read(), "image/jpeg")}
            )
        assert r_ai.status_code == 200, f"AI analysis failed: {r_ai.text}"
        ai_result = r_ai.json()
        print(f"  [+] Real YOLOv5n-ONNX Detection Executed:")
        print(f"    - Model: {ai_result.get('model_used')}")
        print(f"    - Detected Objects: {len(ai_result.get('detections', []))}")
        print(f"    - Footpath Area: {ai_result.get('footpath_area_sqm')} sqm")
        print(f"    - Occupied Area: {ai_result.get('occupied_area_sqm')} sqm ({ai_result.get('occupancy_percentage')}%)")
        print(f"    - Remaining Clear Width: {ai_result.get('remaining_width_m')} m (Nominal: {ai_result.get('footpath_width_m')} m)")
        print(f"    - Accessibility Score: {ai_result.get('accessibility_score')}% ({ai_result.get('accessibility_status')})")
        print(f"    - Severity: {ai_result.get('severity')} ({ai_result.get('severity_reason')})")

        # Citizen 1 submits formal Incident report
        import time
        t_seed = (int(time.time() * 1000) % 10000) / 10000.0  # 0.0000 to 0.9999
        base_lat = 13.0500 + (t_seed * 0.1)
        base_lng = 77.6500 + (t_seed * 0.1)
        report_payload = {
            "title": "Vendor stall blocking pedestrian sidewalk near Metro Pillar 42",
            "location_name": "MG Road Promenade, Ward 112",
            "latitude": base_lat,
            "longitude": base_lng,
            "image_url": ai_result.get("annotated_image_url") or "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": ai_result.get("occupancy_percentage", 32.0),
            "accessibility_score": ai_result.get("accessibility_score", 48.0),
            "severity": ai_result.get("severity", "Medium"),
            "footpath_width_m": ai_result.get("footpath_width_m"),
            "obstructed_width_m": ai_result.get("obstructed_width_m"),
            "remaining_width_m": ai_result.get("remaining_width_m"),
            "bottleneck_blockage_pct": ai_result.get("bottleneck_blockage_pct"),
            "is_calibrated": ai_result.get("is_calibrated", True),
            "calibration_mode": ai_result.get("calibration_mode", "calibrated"),
            "warnings": ai_result.get("warnings", [])
        }
        r_inc1 = client.post("/api/incidents", json=report_payload, headers=c1_headers)
        assert r_inc1.status_code == 200, f"Incident creation failed: {r_inc1.text}"
        inc1_data = r_inc1.json()
        master_id = inc1_data["id"]
        master_num = inc1_data["incident_number"]
        print(f"  [+] Master Incident Created: {master_num} (ID: {master_id})")
        print(f"    - Initial Status: {inc1_data['status']}")
        print(f"    - Initial Supporting Reports: {inc1_data['supporting_reports_count']}")

        # ------------------------------------------------------------------
        # PHASE 2: SECOND CITIZEN REPORTS DUPLICATE (MERGE & ENDORSEMENT)
        # ------------------------------------------------------------------
        print("\n--- [PHASE 2] Second Citizen Duplicate Detection & Merging ---")
        # Second citizen reports same obstruction 22m away with same category
        dup_lat = base_lat + 0.00020  # ~22 meters
        dup_lng = base_lng + 0.00005
        dup_payload = {
            "title": "Stall occupying sidewalk space",
            "description": "Footpath completely blocked by vendor cart, pedestrians forced to walk on main road.",
            "location_name": "MG Road sidewalk near Metro Pillar 42",
            "latitude": dup_lat,
            "longitude": dup_lng,
            "image_url": "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": 30.0,
            "accessibility_score": 50.0,
            "severity": "Low"
        }
        r_inc2 = client.post("/api/incidents", json=dup_payload, headers=c1_headers)
        assert r_inc2.status_code == 200, f"Duplicate report failed: {r_inc2.text}"
        inc2_data = r_inc2.json()

        assert inc2_data.get("is_duplicate_merged") is True, "Second report should be flagged as merged duplicate"
        assert inc2_data.get("merged_with_master_id") == master_id, "Should merge with master incident"
        print(f"  [+] Multi-factor Duplicate Engine Triggered:")
        print(f"    - Merged into Master Incident: {inc2_data.get('incident_number')}")
        print(f"    - Endorsement Count: {inc2_data.get('supporting_reports_count')}")

        # Verify Master Incident in database now reflects merged report
        r_master_get = client.get(f"/api/incidents/{master_id}", headers=c1_headers)
        assert r_master_get.status_code == 200
        master_updated = r_master_get.json()
        assert master_updated["supporting_reports_count"] == 2
        assert len(master_updated["supporting_reports"]) == 1
        merged_item = master_updated["supporting_reports"][0]
        print(f"    - Verified Supporting Report record: distance={merged_item['distance_meters']}m, reporter={merged_item['reporter_name']}")

        # ------------------------------------------------------------------
        # PHASE 3: MUNICIPAL ADMIN VERIFICATION & OFFICER ASSIGNMENT
        # ------------------------------------------------------------------
        print("\n--- [PHASE 3] Admin Review, AI Verification & Officer Assignment ---")
        r_admin = client.post("/api/auth/demo-switch/admin")
        assert r_admin.status_code == 200, f"Admin login failed: {r_admin.text}"
        admin_token = r_admin.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("  [+] Admin Authenticated (Municipal Control Center)")

        # Admin fetches officers
        r_officers = client.get("/api/auth/officers", headers=admin_headers)
        assert r_officers.status_code == 200
        officers_list = r_officers.json()
        assert len(officers_list) > 0, "At least one officer required"
        target_officer = officers_list[0]
        target_officer_id = target_officer["id"]
        target_officer_name = target_officer["full_name"]
        print(f"  [+] Available Field Officer: {target_officer_name} (ID: {target_officer_id})")

        # Admin changes status to "Verified"
        r_verify_status = client.patch(
            f"/api/incidents/{master_id}",
            json={"status": "Verified"},
            headers=admin_headers
        )
        assert r_verify_status.status_code == 200
        assert r_verify_status.json()["status"] == "Verified"
        print(f"  [+] Admin verified AI detection -> Status: Verified")

        # Admin assigns incident to Field Officer
        r_assign = client.patch(
            f"/api/incidents/{master_id}",
            json={
                "assigned_officer_id": target_officer_id,
                "assigned_officer_name": target_officer_name
            },
            headers=admin_headers
        )
        assert r_assign.status_code == 200
        assigned_inc = r_assign.json()
        assert assigned_inc["status"] == "Assigned"
        assert assigned_inc["assigned_officer_id"] == target_officer_id
        print(f"  [+] Assigned to {target_officer_name} -> Status: Assigned")

        # ------------------------------------------------------------------
        # PHASE 4: FIELD OFFICER INSPECTION & EVIDENCE SUBMISSION
        # ------------------------------------------------------------------
        print("\n--- [PHASE 4] Field Officer Site Visit & Inspection ---")
        r_officer_login = client.post("/api/auth/demo-switch/officer")
        assert r_officer_login.status_code == 200
        officer_token = r_officer_login.json()["access_token"]
        officer_headers = {"Authorization": f"Bearer {officer_token}"}
        print(f"  [+] Field Officer Authenticated: {r_officer_login.json()['user']['full_name']}")

        # Officer views assigned tasks
        r_assigned_tasks = client.get("/api/incidents?assigned_to_me=true", headers=officer_headers)
        assert r_assigned_tasks.status_code == 200
        assigned_tasks = r_assigned_tasks.json()
        matching_task = next((t for t in assigned_tasks if t["id"] == master_id), None)
        assert matching_task is not None, "Master incident must appear in Officer's assigned queue"
        print(f"  [+] Officer found incident {master_num} in assigned queue")

        # Officer marks status "In Progress" and uploads clearance inspection photo
        clear_img_path = os.path.join("uploads", "original", "clear_street.jpg")
        assert os.path.exists(clear_img_path), f"Clear street image missing: {clear_img_path}"

        inspect_payload = {
            "inspection_image_url": "/uploads/original/clear_street.jpg",
            "inspection_notes": "Encroachment cleared. Vendor moved behind building line. Footpath clear width restored to 2.5m."
        }
        r_inspect = client.post(f"/api/incidents/{master_id}/inspect", json=inspect_payload, headers=officer_headers)
        assert r_inspect.status_code == 200
        inspected_inc = r_inspect.json()
        assert inspected_inc["status"] == "In Progress"
        assert inspected_inc["inspection_image_url"] == "/uploads/original/clear_street.jpg"
        print(f"  [+] Inspection Submitted -> Status: In Progress, Evidence: {inspected_inc['inspection_image_url']}")

        # ------------------------------------------------------------------
        # PHASE 5: BEFORE/AFTER AI RESOLUTION VERIFICATION
        # ------------------------------------------------------------------
        print("\n--- [PHASE 5] AI Dual-Inference Before/After Resolution Verification ---")
        # Municipal Admin / Officer triggers Before/After AI verification
        r_ai_verify = client.post(f"/api/incidents/{master_id}/verify-resolution", headers=officer_headers)
        assert r_ai_verify.status_code == 200, f"AI verification failed: {r_ai_verify.text}"
        verified_inc = r_ai_verify.json()

        assert verified_inc["status"] == "Resolved", f"Expected 'Resolved', got {verified_inc['status']}"
        assert verified_inc.get("ai_verification") is not None, "Verification data missing"
        ai_ver_data = verified_inc["ai_verification"]
        assert ai_ver_data["verified"] is True, "AI should verify obstruction is cleared"
        assert ai_ver_data["current_accessibility_score"] == 100.0, "Accessibility should be restored to 100%"
        assert ai_ver_data.get("comparison_image_url") is not None
        print(f"  [+] Before/After AI Engine Result:")
        print(f"    - Obstruction Cleared: {ai_ver_data['verified']}")
        print(f"    - Status: {verified_inc['status']}")
        print(f"    - Verification Message: {ai_ver_data['status']}")
        print(f"    - Restored Accessibility Score: {ai_ver_data['current_accessibility_score']}%")
        print(f"    - Side-by-Side Comparison Canvas: {ai_ver_data['comparison_image_url']}")

        # Verify audit trail comments contain AI resolution log
        comments = verified_inc.get("comments", [])
        ai_comment = next((c for c in comments if c.get("role") == "ai" and ("Verification" in c.get("text", "") or "VERIFIED" in c.get("text", ""))), None)
        assert ai_comment is not None, "AI Resolution audit comment must be recorded"
        print(f"    - Audit Log Entry: {ai_comment['text']}")

        # ------------------------------------------------------------------
        # PHASE 6: CITIZEN REPORT TRACKING VERIFICATION
        # ------------------------------------------------------------------
        print("\n--- [PHASE 6] Citizen Report Tracking (My Reports) ---")
        r_my_reports = client.get("/api/incidents?my_reports=true", headers=c1_headers)
        assert r_my_reports.status_code == 200
        my_reports = r_my_reports.json()
        resolved_report = next((r for r in my_reports if r["id"] == master_id), None)
        assert resolved_report is not None, "Resolved incident must appear in citizen's My Reports"
        assert resolved_report["status"] == "Resolved"
        print(f"  [+] Citizen verified incident {master_num} is marked 'Resolved' in My Reports")

        # ------------------------------------------------------------------
        # PHASE 7: HOTSPOT & KPI LIVE ANALYTICS REFLECTION
        # ------------------------------------------------------------------
        print("\n--- [PHASE 7] Hotspot & Municipal KPI Live Analytics ---")
        r_hotspots = client.get("/api/analytics/hotspots", headers=admin_headers)
        assert r_hotspots.status_code == 200
        hotspots = r_hotspots.json()
        assert len(hotspots) > 0
        mg_road_hotspot = next((h for h in hotspots if "MG Road" in h["area"]), None)
        assert mg_road_hotspot is not None
        print(f"  [+] Hotspot Live Metrics for MG Road:")
        print(f"    - Total Incidents: {mg_road_hotspot['incidents']}")
        print(f"    - Active Obstacles: {mg_road_hotspot['active']}")
        print(f"    - Resolution Rate: {mg_road_hotspot['resolution_rate']}")

        r_kpis = client.get("/api/analytics/kpis", headers=admin_headers)
        assert r_kpis.status_code == 200
        kpis = r_kpis.json()
        print(f"  [+] Live KPIs: Total={kpis['total_incidents']}, Verified={kpis['verified']}, Resolution Rate={kpis['resolution_rate_pct']}%, Avg Score={kpis['avg_accessibility_score']}%")

    print("\n======================================================================")
    print("ALL END-TO-END CITIZEN-TO-OFFICER WORKFLOW TESTS PASSED 100%!")
    print("======================================================================")

if __name__ == "__main__":
    run_e2e_workflow_tests()
