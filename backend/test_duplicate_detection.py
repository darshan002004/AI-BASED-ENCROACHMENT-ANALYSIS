import os
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.ai.duplicate_detector import duplicate_detector, haversine_distance_meters

def run_duplicate_detection_tests():
    with TestClient(app) as client:
        print("=== 1. Testing Haversine Distance & Spatial Correlation ===")
        # Test coordinates in Indiranagar, Bengaluru
        lat1, lng1 = 12.9716, 77.6412
        # ~18 meters away
        lat2, lng2 = 12.9717, 77.6413
        d1 = haversine_distance_meters(lat1, lng1, lat2, lng2)
        print(f"  Distance between point 1 and 2: {d1:.1f} meters")
        assert 10.0 <= d1 <= 25.0

        # ~500 meters away
        lat3, lng3 = 12.9756, 77.6412
        d2 = haversine_distance_meters(lat1, lng1, lat3, lng3)
        print(f"  Distance between point 1 and 3: {d2:.1f} meters")
        assert d2 > 400.0

        print("\n=== 2. Creating Master Incident 1 (Citizen A) ===")
        r_auth_citizen = client.post("/api/auth/demo-switch/citizen")
        assert r_auth_citizen.status_code == 200
        token_citizen = r_auth_citizen.json()["access_token"]
        headers_citizen = {"Authorization": f"Bearer {token_citizen}"}

        # Unique coordinate for isolated test run
        import random
        base_lat = 12.8500 + random.uniform(0.01, 0.09)
        base_lng = 77.5500 + random.uniform(0.01, 0.09)

        master_payload = {
            "title": "Commercial Pushcart Encroachment at Test Corridors",
            "location_name": "Test Corridor Road, Jayanagar",
            "latitude": base_lat,
            "longitude": base_lng,
            "image_url": "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupied_area_sqm": 4.5,
            "footpath_area_sqm": 25.0,
            "occupancy_percentage": 18.0,
            "accessibility_score": 72.0,
            "severity": "Low",
            "severity_reason": "Pushcart restricts 18% of walkway."
        }

        r_master = client.post("/api/incidents", json=master_payload, headers=headers_citizen)
        assert r_master.status_code == 200, f"Error: {r_master.text}"
        master_inc = r_master.json()
        master_id = master_inc["id"]
        master_num = master_inc["incident_number"]
        print(f"  Master Incident Created: {master_num} (ID: {master_id})")
        assert master_inc["supporting_reports_count"] == 1
        assert len(master_inc.get("supporting_reports", [])) == 0

        print("\n=== 3. Submitting Duplicate Report at Proximity (Citizen B - 16m away) ===")
        # Switch to officer / second citizen account to simulate second citizen
        r_auth_b = client.post("/api/auth/demo-switch/citizen")
        token_b = r_auth_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        dup_payload_1 = {
            "title": "Vegetable cart blocking sidewalk path",
            "location_name": "Test Corridor near Station",
            "latitude": base_lat + 0.0001, # ~11m away
            "longitude": base_lng + 0.0001,
            "image_url": "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": 20.0,
            "accessibility_score": 68.0,
            "severity": "Low"
        }

        r_dup1 = client.post("/api/incidents", json=dup_payload_1, headers=headers_b)
        assert r_dup1.status_code == 200, f"Error: {r_dup1.text}"
        dup1_res = r_dup1.json()

        print(f"  Duplicate report response:")
        print(f"    - Merged with Master: {dup1_res.get('is_duplicate_merged')}")
        print(f"    - Incident Number: {dup1_res['incident_number']}")
        print(f"    - Supporting Reports Count: {dup1_res['supporting_reports_count']}")

        assert dup1_res["id"] == master_id
        assert dup1_res["incident_number"] == master_num
        assert dup1_res["is_duplicate_merged"] is True
        assert dup1_res["supporting_reports_count"] == 2
        assert len(dup1_res["supporting_reports"]) == 1
        assert dup1_res["supporting_reports"][0]["distance_meters"] <= 25.0

        print("\n=== 4. Submitting Third Duplicate Report & Testing Severity Auto-Escalation ===")
        dup_payload_2 = {
            "title": "Vendor blocking footpath entrance",
            "location_name": "Test Corridor Footpath Junction",
            "latitude": base_lat + 0.00005, # ~6m away
            "longitude": base_lng + 0.00005,
            "image_url": "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": 25.0,
            "accessibility_score": 65.0,
            "severity": "Low"
        }

        r_dup2 = client.post("/api/incidents", json=dup_payload_2, headers=headers_b)
        assert r_dup2.status_code == 200
        dup2_res = r_dup2.json()

        print(f"  Third endorsement merged:")
        print(f"    - Supporting Reports Count: {dup2_res['supporting_reports_count']}")
        print(f"    - Escalated Severity: {dup2_res['severity']}")
        print(f"    - Total Comments on Master: {len(dup2_res['comments'])}")

        assert dup2_res["id"] == master_id
        assert dup2_res["supporting_reports_count"] == 3
        # Auto-escalated to Medium because 3 citizens confirmed the active encroachment
        assert dup2_res["severity"] in ["Medium", "High"]
        assert len(dup2_res["supporting_reports"]) == 2

        print("\n=== 5. Submitting Distant Report (300m away) -> Must NOT Merge ===")
        distant_payload = {
            "title": "Parked Car on Sidewalk in Far Zone",
            "location_name": "Far Zone Road",
            "latitude": base_lat + 0.0035, # ~390m away
            "longitude": base_lng + 0.0035,
            "image_url": "/uploads/original/vehicle_indiranagar.jpg",
            "primary_encroachment_type": "Vehicle",
            "occupancy_percentage": 30.0,
            "accessibility_score": 50.0,
            "severity": "Medium"
        }

        r_dist = client.post("/api/incidents", json=distant_payload, headers=headers_citizen)
        assert r_dist.status_code == 200
        dist_res = r_dist.json()

        print(f"  Distant report response:")
        print(f"    - Distinct ID: {dist_res['id']} (Master was {master_id})")
        print(f"    - New Incident Number: {dist_res['incident_number']}")
        print(f"    - Merged: {dist_res.get('is_duplicate_merged')}")

        assert dist_res["id"] != master_id
        assert dist_res["incident_number"] != master_num
        assert dist_res.get("is_duplicate_merged") is not True
        assert dist_res["supporting_reports_count"] == 1

        print("\n=== 6. Testing Citizen Filter (Viewing Endorsed Merged Incidents) ===")
        # Fetch incidents list with reporter filter
        r_list = client.get("/api/incidents?my_reports=true", headers=headers_b)
        assert r_list.status_code == 200
        my_list = r_list.json()
        my_ids = [inc["id"] for inc in my_list]
        print(f"  Citizen B my_reports returned {len(my_list)} incident(s)")
        assert master_id in my_ids, f"Citizen B should see master incident {master_id} among their endorsed reports!"

        print("\nALL DUPLICATE INCIDENT DETECTION & MERGING TESTS PASSED 100%!")

if __name__ == "__main__":
    run_duplicate_detection_tests()
