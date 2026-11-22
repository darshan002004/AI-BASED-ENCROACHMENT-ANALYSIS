import os
import cv2
from fastapi.testclient import TestClient
from app.main import app
from app.ai.verification import verification_engine

def run_verification_tests():
    with TestClient(app) as client:
        print("=== 1. Testing verification_engine.verify_resolution Directly ===")
        before_path = os.path.join("uploads", "original", "vendor_mg_road.jpg")
        after_clear_path = os.path.join("uploads", "original", "clear_street.jpg")
        after_persists_path = os.path.join("uploads", "original", "vehicle_indiranagar.jpg")

        # Case 1: Obstruction Cleared
        res_cleared = verification_engine.verify_resolution(
            before_image_path=before_path,
            after_image_path=after_clear_path,
            expected_obstruction_type="Street Vendor"
        )
        print("  Case 1 (Clear after inspection):")
        print(f"    - Verified: {res_cleared['verified']}")
        print(f"    - Status: {res_cleared['status']}")
        print(f"    - Current Accessibility Score: {res_cleared['current_accessibility_score']}")
        print(f"    - Comparison Image: {res_cleared['comparison_image_url']}")

        assert res_cleared["verified"] is True
        assert "VERIFIED" in res_cleared["status"]
        assert res_cleared["current_accessibility_score"] == 100.0
        assert os.path.exists(os.path.join("uploads", "annotated", os.path.basename(res_cleared["comparison_image_url"])))

        # Case 2: Obstruction Persists
        res_persists = verification_engine.verify_resolution(
            before_image_path=before_path,
            after_image_path=after_persists_path,
            expected_obstruction_type="Street Vendor"
        )
        print("\n  Case 2 (Obstruction persists after inspection):")
        print(f"    - Verified: {res_persists['verified']}")
        print(f"    - Status: {res_persists['status']}")
        print(f"    - Current Accessibility Score: {res_persists['current_accessibility_score']}")

        assert res_persists["verified"] is False
        assert "STILL PRESENT" in res_persists["status"] or "NEEDS HUMAN REVIEW" in res_persists["status"]

        print("\n=== 2. Testing POST /api/ai/verify Endpoint ===")
        with open(before_path, "rb") as bf, open(after_clear_path, "rb") as af:
            r_ai_verify = client.post(
                "/api/ai/verify",
                files={
                    "before_file": ("before.jpg", bf.read(), "image/jpeg"),
                    "after_file": ("after.jpg", af.read(), "image/jpeg")
                },
                data={"expected_type": "Street Vendor"}
            )
        assert r_ai_verify.status_code == 200, f"Error: {r_ai_verify.text}"
        api_verify_data = r_ai_verify.json()
        assert api_verify_data["verified"] is True
        assert "comparison_image_url" in api_verify_data
        print(f"  POST /api/ai/verify -> verified={api_verify_data['verified']}, comparison_image={api_verify_data['comparison_image_url']}")

        print("\n=== 3. Testing Full Incident Lifecycle: Inspection Upload -> AI Resolution Verification ===")
        # Authenticate as Officer
        r_auth = client.post("/api/auth/demo-switch/officer")
        assert r_auth.status_code == 200
        token = r_auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3a. Create test incident
        inc_payload = {
            "title": "Vendor stall obstructing MG Road pedestrian zone",
            "location_name": "MG Road, Bengaluru",
            "latitude": 12.9756,
            "longitude": 77.6066,
            "image_url": "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": 25.0,
            "accessibility_score": 60.0,
            "severity": "Medium"
        }
        r_inc = client.post("/api/incidents", json=inc_payload, headers=headers)
        assert r_inc.status_code == 200
        inc_data = r_inc.json()
        inc_id = inc_data["id"]
        print(f"  Created test incident: {inc_data['incident_number']} (Status: {inc_data['status']})")

        # 3b. Field Officer submits inspection with clear street photo
        inspect_payload = {
            "inspection_image_url": "/uploads/original/clear_street.jpg",
            "inspection_notes": "Vendor stall removed and sidewalk cleared completely. Pedestrian movement restored."
        }
        r_inspect = client.post(f"/api/incidents/{inc_id}/inspect", json=inspect_payload, headers=headers)
        assert r_inspect.status_code == 200
        inspected_inc = r_inspect.json()
        assert inspected_inc["status"] == "In Progress"
        assert inspected_inc["inspection_image_url"] == "/uploads/original/clear_street.jpg"
        print(f"  Inspection submitted -> Status: {inspected_inc['status']}")

        # 3c. Municipal Admin / System runs Before/After AI Verification
        r_verify_res = client.post(f"/api/incidents/{inc_id}/verify-resolution", headers=headers)
        assert r_verify_res.status_code == 200
        verified_inc = r_verify_res.json()
        print(f"  Verification result -> Status: {verified_inc['status']}, Resolution Date: {verified_inc['resolution_date']}")
        print(f"  Accessibility Score upgraded to: {verified_inc['accessibility_score']}%")

        assert verified_inc["status"] == "Resolved"
        assert verified_inc["resolution_date"] is not None
        assert verified_inc["ai_verification"]["verified"] is True
        assert verified_inc["accessibility_score"] == 100.0

        print("\nALL BEFORE/AFTER VERIFICATION TESTS PASSED 100%!")

if __name__ == "__main__":
    run_verification_tests()
