import os
from fastapi.testclient import TestClient
from app.main import app

def run_hotspot_analytics_tests():
    with TestClient(app) as client:
        print("=== 1. Testing GET /api/analytics/hotspots (Baseline) ===")
        r_hotspots = client.get("/api/analytics/hotspots")
        assert r_hotspots.status_code == 200, f"Error: {r_hotspots.text}"
        hotspots = r_hotspots.json()
        assert len(hotspots) >= 1
        print(f"  Returned {len(hotspots)} hotspots:")
        for h in hotspots[:3]:
            print(f"    - Rank {h['rank']}: {h['area']} ({h['ward']}) -> {h['incidents']} total, {h['active']} active, status={h['status']}")

        assert hotspots[0]["rank"] == 1
        assert "incidents" in hotspots[0]
        assert "active" in hotspots[0]
        assert "resolution_rate" in hotspots[0]
        assert "primary_cause" in hotspots[0]
        assert "status" in hotspots[0]

        # Initial count for MG Road
        mg_initial = next(h for h in hotspots if h["area"] == "MG Road")
        mg_init_total = mg_initial["incidents"]
        mg_init_active = mg_initial["active"]

        print("\n=== 2. Creating New Incident in MG Road to Test Live Hotspot Data Updates ===")
        r_auth = client.post("/api/auth/demo-switch/citizen")
        assert r_auth.status_code == 200
        token = r_auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Distinct coordinate on MG Road (outside duplicate cluster radius)
        import time
        rand_off = float(int(time.time() * 1000) % 500) / 10000.0 + 0.02
        new_inc = {
            "title": "New Vendor Stand Obstruction on MG Road Promenade",
            "location_name": "MG Road, Bengaluru",
            "latitude": 12.9730 + rand_off,
            "longitude": 77.6180 + rand_off,
            "image_url": "/uploads/original/vendor_mg_road.jpg",
            "primary_encroachment_type": "Street Vendor",
            "occupancy_percentage": 28.0,
            "accessibility_score": 62.0,
            "severity": "High"
        }
        r_create = client.post("/api/incidents", json=new_inc, headers=headers)
        assert r_create.status_code == 200
        created_data = r_create.json()
        print(f"  Created test incident: {created_data['incident_number']} in MG Road")

        print("\n=== 3. Testing GET /api/analytics/hotspots (Live Dynamic Update) ===")
        r_hotspots_after = client.get("/api/analytics/hotspots")
        assert r_hotspots_after.status_code == 200
        hotspots_after = r_hotspots_after.json()
        mg_after = next(h for h in hotspots_after if h["area"] == "MG Road")
        print(f"  MG Road Hotspot updated live:")
        print(f"    - Total Incidents: {mg_init_total} -> {mg_after['incidents']}")
        print(f"    - Active Obstacles: {mg_init_active} -> {mg_after['active']}")
        assert mg_after["incidents"] == mg_init_total + 1
        assert mg_after["active"] == mg_init_active + 1

        print("\n=== 4. Testing GET /api/analytics/top-affected-areas ===")
        r_top = client.get("/api/analytics/top-affected-areas")
        assert r_top.status_code == 200
        top_areas = r_top.json()
        assert len(top_areas) >= 1
        print(f"  Top Affected Areas: {[a['area'] for a in top_areas]}")
        if len(top_areas) >= 2:
            assert top_areas[0]["incidents"] >= top_areas[1]["incidents"]

        print("\n=== 5. Testing GET /api/analytics/kpis ===")
        r_kpis = client.get("/api/analytics/kpis")
        assert r_kpis.status_code == 200
        kpis = r_kpis.json()
        print(f"  Live KPIs: Total={kpis['total_incidents']}, High Severity={kpis['high_severity']}, Avg Score={kpis['avg_accessibility_score']}%")
        assert kpis["total_incidents"] >= 0
        assert kpis["high_severity"] >= 0
        assert 0.0 <= kpis["avg_accessibility_score"] <= 100.0

        print("\n=== 6. Testing GET /api/analytics/encroachment-types ===")
        r_types = client.get("/api/analytics/encroachment-types")
        assert r_types.status_code == 200
        types = r_types.json()
        assert len(types) >= 1
        sum_pct = sum(t["percentage"] for t in types)
        print(f"  Encroachment Type breakdown (Total %: {sum_pct:.1f}%):")
        for t in types:
            print(f"    - {t['name']}: {t['value']} ({t['percentage']}%)")
        assert 95.0 <= sum_pct <= 105.0

        print("\nALL HOTSPOT ANALYTICS TESTS PASSED 100%!")

if __name__ == "__main__":
    run_hotspot_analytics_tests()
