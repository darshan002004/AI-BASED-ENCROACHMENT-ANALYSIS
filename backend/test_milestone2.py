import os
import tempfile
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.ai.detector import detector


def run_milestone2_tests():
    with TestClient(app) as client:
        print("=== 1. Testing GET /api/ai/capabilities ===")
        r = client.get("/api/ai/capabilities")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        cap = r.json()
        assert cap["object_detection"]["yolo_onnx_loaded"] is True
        assert cap["object_detection"]["fabricated_boxes_removed"] is True
        assert cap["object_detection"]["hardcoded_confidences_removed"] is True
        assert len(cap["object_detection"]["unsupported_specialized_classes"]) >= 5
        assert cap["road_footpath_segmentation"]["is_ai_segmentation"] is False
        assert cap["road_footpath_segmentation"]["is_prototype"] is True
        assert cap["road_footpath_segmentation"]["mode"] == "PROTOTYPE_CORRIDOR_ROI"
        assert cap["measurements_and_calibration"]["real_world_measurements_available"] is False
        print("Capabilities verified: Pretrained YOLOv5n-ONNX + Prototype ROI + Uncalibrated Pixel Space.")

        print("\n=== 2. Testing Invalid, Empty, Corrupted, and Oversized (>25MB) Uploads ===")
        # Invalid extension (.txt)
        r_txt = client.post("/api/ai/analyze", files={"file": ("invalid.txt", b"not an image", "text/plain")})
        assert r_txt.status_code == 400, f"Expected 400 for .txt, got {r_txt.status_code}"
        print("Rejected .txt -> 400:", r_txt.json()["detail"])

        # Invalid extension (.gif)
        r_gif = client.post("/api/ai/analyze", files={"file": ("anim.gif", b"GIF89a...", "image/gif")})
        assert r_gif.status_code == 400, f"Expected 400 for .gif, got {r_gif.status_code}"
        print("Rejected .gif -> 400:", r_gif.json()["detail"])

        # Empty 0-byte .jpg
        r_empty = client.post("/api/ai/analyze", files={"file": ("empty.jpg", b"", "image/jpeg")})
        assert r_empty.status_code == 400, f"Expected 400 for empty file, got {r_empty.status_code}"
        print("Rejected empty .jpg -> 400:", r_empty.json()["detail"])

        # Corrupted non-image bytes with .jpg extension
        r_corrupt = client.post("/api/ai/analyze", files={"file": ("corrupt.jpg", b"not_jpeg_bytes_12345", "image/jpeg")})
        assert r_corrupt.status_code == 400, f"Expected 400 for corrupt image, got {r_corrupt.status_code}"
        print("Rejected corrupt .jpg -> 400:", r_corrupt.json()["detail"])

        # Oversized (> 25 MB) .jpg file
        oversized_bytes = b"\xff\xd8\xff" + (b"\x00" * (25 * 1024 * 1024 + 2048))
        r_huge = client.post("/api/ai/analyze", files={"file": ("huge.jpg", oversized_bytes, "image/jpeg")})
        assert r_huge.status_code == 400, f"Expected 400 for >25MB file, got {r_huge.status_code}"
        print("Rejected >25MB .jpg -> 400:", r_huge.json()["detail"])

        print("\n=== 3. Testing No-Obstruction / Clear Street Image (0 Detections, No Fabricated Boxes) ===")
        clear_path = os.path.join("uploads", "original", "clear_street.jpg")
        with open(clear_path, "rb") as f:
            clear_bytes = f.read()
        r_clear = client.post("/api/ai/analyze", files={"file": ("clear_street.jpg", clear_bytes, "image/jpeg")})
        assert r_clear.status_code == 200, f"Expected 200, got {r_clear.status_code}: {r_clear.text}"
        res_clear = r_clear.json()
        assert res_clear["processing_status"] == "COMPLETED"
        assert len(res_clear["detected_objects"]) == 0, f"Expected 0 detections on clear image, got {len(res_clear['detected_objects'])}"
        assert res_clear["overall_classification"] == "No obstruction detected"
        assert res_clear["confidence"] is None, f"Confidence must be None when 0 objects detected, got {res_clear['confidence']}"
        assert res_clear["roi_pixel_occupancy_pct"] == 0.0
        assert res_clear["occupied_footpath_px"] == 0.0
        assert res_clear["occupied_area_sqm"] is None
        assert res_clear["footpath_area_sqm"] is None
        print("Clear image verified -> 0 objects detected, overall_classification='No obstruction detected', confidence=None")

        print("\n=== 4. Testing Varied Street Images with Real YOLOv5n-ONNX Detections (JPG, JPEG, PNG) ===")
        # 4a. vendor_mg_road.jpg: Elevated umbrella canopy + person on footpath ('Needs human review') + car on road ('Not an encroachment')
        sample_jpg_path = os.path.join("uploads", "original", "vendor_mg_road.jpg")
        with open(sample_jpg_path, "rb") as f:
            jpg_bytes = f.read()

        r_jpg = client.post("/api/ai/analyze", files={"file": ("vendor_mg_road.jpg", jpg_bytes, "image/jpeg")})
        assert r_jpg.status_code == 200
        res_jpg = r_jpg.json()
        assert res_jpg["processing_status"] == "COMPLETED"
        assert res_jpg["detection_metadata"]["is_mock"] is False
        assert res_jpg["segmentation_info"]["is_ai_segmentation"] is False
        assert res_jpg["segmentation_info"]["is_prototype"] is True
        assert res_jpg["occupied_area_sqm"] is None
        assert res_jpg["footpath_area_sqm"] is None
        assert res_jpg["footpath_width_m"] is None
        assert res_jpg["footpath_roi_area_px"] > 0
        assert len(res_jpg["detected_objects"]) == 4

        print(f"Scene A (vendor_mg_road.jpg) -> {len(res_jpg['detected_objects'])} pure YOLOv5n-ONNX objects:")
        scene_a_classes = set()
        for obj in res_jpg["detected_objects"]:
            scene_a_classes.add(obj["classification"])
            print(
                f"  - COCO='{obj['coco_class']}' | cat='{obj['category']}' | conf={obj['confidence']} | "
                f"class='{obj['classification']}' | fp_overlap={obj['footpath_overlap_pct']}% | rd_overlap={obj['road_overlap_pct']}%"
            )
            assert obj["area_sqm"] is None

        assert "Needs human review" in scene_a_classes
        assert "Not an encroachment" in scene_a_classes

        # 4b. vehicle_indiranagar.jpg: Car directly inside Prototype Footpath ROI ('Potential encroachment')
        veh_path = os.path.join("uploads", "original", "vehicle_indiranagar.jpg")
        with open(veh_path, "rb") as vf:
            veh_bytes = vf.read()
        r_veh = client.post("/api/ai/analyze", files={"file": ("vehicle_indiranagar.jpg", veh_bytes, "image/jpeg")})
        assert r_veh.status_code == 200
        res_veh = r_veh.json()
        print(f"Scene B (vehicle_indiranagar.jpg) -> {len(res_veh['detected_objects'])} pure YOLOv5n-ONNX objects:")
        scene_b_classes = set()
        for obj in res_veh["detected_objects"]:
            scene_b_classes.add(obj["classification"])
            print(
                f"  - COCO='{obj['coco_class']}' | cat='{obj['category']}' | conf={obj['confidence']} | "
                f"class='{obj['classification']}' | fp_overlap={obj['footpath_overlap_pct']}% | rd_overlap={obj['road_overlap_pct']}%"
            )
        assert "Potential encroachment" in scene_b_classes
        assert "Not an encroachment" in scene_b_classes
        assert res_veh["roi_pixel_occupancy_pct"] > 0.0

        # Test JPEG and PNG formats
        assert client.post("/api/ai/analyze", files={"file": ("scene.jpeg", jpg_bytes, "image/jpeg")}).status_code == 200
        img_arr = cv2.imread(veh_path)
        _, png_buf = cv2.imencode(".png", img_arr)
        assert client.post("/api/ai/analyze", files={"file": ("scene.png", png_buf.tobytes(), "image/png")}).status_code == 200
        print("JPG, JPEG, and PNG uploads verified!")

        print("\n=== 5. Testing Model-Loading Failure & Explicit Demo Mode ===")
        try:
            loaded = detector.load_weights("non_existent_corrupt_weights.onnx")
            assert loaded is False
            assert detector.yolo_loaded is False

            # Default allow_demo_mode=False must return HTTP 503 Service Unavailable
            r_fail = client.post("/api/ai/analyze", files={"file": ("vendor_mg_road.jpg", jpg_bytes, "image/jpeg")})
            assert r_fail.status_code == 503, f"Expected 503 when model weights fail to load, got {r_fail.status_code}"
            print("Model Load Failure (default) -> 503:", r_fail.json()["detail"])

            # Explicit allow_demo_mode=True must return labeled DEMO_MODE_WEIGHTS_UNAVAILABLE with 0 fabricated boxes
            r_demo = client.post(
                "/api/ai/analyze?allow_demo_mode=true",
                files={"file": ("vendor_mg_road.jpg", jpg_bytes, "image/jpeg")}
            )
            assert r_demo.status_code == 200
            res_demo = r_demo.json()
            assert res_demo["processing_status"] == "DEMO_MODE_WEIGHTS_UNAVAILABLE"
            assert res_demo["detection_metadata"]["is_demo_mode"] is True
            assert len(res_demo["detected_objects"]) == 0
            print("Model Load Failure (allow_demo_mode=true) -> status='DEMO_MODE_WEIGHTS_UNAVAILABLE', 0 fabricated boxes")
        finally:
            # Always restore real YOLOv5n-ONNX weights
            restored = detector.load_weights()
            assert restored is True and detector.yolo_loaded is True

        print("\n=== 6. Testing Real Video Frame Processing & Tracking (Valid, Short Clip, and Unreadable Video) ===")
        # 6a. Unreadable / invalid video bytes -> Honest UNSUPPORTED_OR_UNREADABLE_VIDEO status
        r_bad_vid = client.post("/api/ai/track-video", files={"file": ("corrupt.mp4", b"not_a_real_video", "video/mp4")})
        assert r_bad_vid.status_code == 200
        bad_vid_data = r_bad_vid.json()
        assert bad_vid_data["processing_status"] == "UNSUPPORTED_OR_UNREADABLE_VIDEO"
        assert bad_vid_data["is_simulated"] is False
        assert bad_vid_data["frames_decoded"] == 0
        print("Unreadable video -> status:", bad_vid_data["processing_status"])

        # 6b. Real 4.0-second MJPEG AVI video (40 frames at 10 FPS) generated from vendor_mg_road.jpg
        with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp_vid:
            tmp_vid_path = tmp_vid.name
        try:
            h, w = img_arr.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter(tmp_vid_path, fourcc, 10.0, (w, h))
            for _ in range(40):  # 4.0 seconds at 10 FPS
                writer.write(img_arr)
            writer.release()

            with open(tmp_vid_path, "rb") as vf:
                r_real_vid = client.post("/api/ai/track-video", files={"file": ("street_clip.avi", vf.read(), "video/x-msvideo")})
            assert r_real_vid.status_code == 200, f"Expected 200 for real video, got {r_real_vid.status_code}: {r_real_vid.text}"
            vid_data = r_real_vid.json()
            assert vid_data["processing_status"] == "COMPLETED"
            assert vid_data["is_simulated"] is False
            assert vid_data["frames_decoded"] == 40
            assert vid_data["frames_analyzed"] >= 7
            assert len(vid_data["all_tracks"]) >= 3
            assert len(vid_data["persistent_obstructions"]) >= 1
            print(
                f"Real 4.0s Video Tracked -> frames_decoded={vid_data['frames_decoded']}, "
                f"frames_analyzed={vid_data['frames_analyzed']}, persistent_obstructions={len(vid_data['persistent_obstructions'])}"
            )
        finally:
            if os.path.exists(tmp_vid_path):
                os.remove(tmp_vid_path)

        print("\n=== 7. Testing Incident Creation & Existing Workflow Regressions ===")
        auth_res = client.post("/api/auth/demo-switch/admin")
        assert auth_res.status_code == 200
        token = auth_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        inc_payload = {
            "location_name": "MG Road, Bengaluru",
            "latitude": 12.9756,
            "longitude": 77.6066,
            "image_url": res_jpg["original_image_url"],
            "annotated_image_url": res_jpg["annotated_image_url"],
            "primary_encroachment_type": res_jpg["primary_encroachment_type"],
            "description": res_jpg["explanation"],
            "detected_objects": res_jpg["detected_objects"],
            "occupied_area_sqm": res_jpg["occupied_area_sqm"],  # None
            "footpath_area_sqm": res_jpg["footpath_area_sqm"],  # None
            "occupancy_percentage": res_jpg["roi_pixel_occupancy_pct"],
            "accessibility_score": res_jpg["accessibility_score"],
            "accessibility_status": res_jpg["accessibility_status"],
            "severity": res_jpg["severity"],
            "severity_reason": res_jpg["severity_reason"],
            "warnings": res_jpg["warnings"],
            "confidence": res_jpg["confidence"]
        }
        r_inc = client.post("/api/incidents", json=inc_payload, headers=headers)
        assert r_inc.status_code == 200, f"Expected 200 on incident creation, got {r_inc.status_code}: {r_inc.text}"
        print("Incident Creation with uncalibrated pixel data -> 200 OK:", r_inc.json()["incident_number"])

        for role in ["admin", "officer", "citizen"]:
            assert client.post(f"/api/auth/demo-switch/{role}").status_code == 200
        assert client.get("/api/incidents", headers=headers).status_code == 200
        assert client.get("/api/analytics/kpis", headers=headers).status_code == 200
        assert client.get("/api/analytics/hotspots", headers=headers).status_code == 200
        assert client.get("/api/reports/csv", headers=headers).status_code == 200
        print("All 7 Verification Suites Passed 100%!")


if __name__ == "__main__":
    run_milestone2_tests()
