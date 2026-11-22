import cv2
import json
from pathlib import Path
from ultralytics import YOLO

base_dir = Path('C:/Users/Darshan B/.gemini/antigravity/scratch/encrowatch-ai')
model = YOLO('yolo11n.pt')

# Select clean unburnt images
clean_images = [
    base_dir / "backend" / "uploads" / "test_street.jpg",
    base_dir / "backend" / "uploads" / "clear_street.jpg",
    base_dir / "backend" / "uploads" / "original" / "upload_66cb1df9a5.jpg",
    base_dir / "backend" / "uploads" / "original" / "privacy_test_real.jpg",
    base_dir / "backend" / "uploads" / "original" / "ev_16e9eab453.jpg",
    base_dir / "backend" / "uploads" / "original" / "upload_3394f0c8be.jpg",
    base_dir / "backend" / "uploads" / "original" / "ev_20bae89b43.jpg"
]

print("Scanning clean images for candidate object proposals:")
for p in clean_images:
    if not p.exists():
        continue
    res = model.predict(source=str(p), imgsz=640, device='cuda:0', half=True, verbose=False)[0]
    boxes = res.boxes
    print(f"\nImage: {p.name} ({res.orig_shape[1]}x{res.orig_shape[0]})")
    if boxes is not None and len(boxes) > 0:
        for b in boxes:
            cls_name = res.names[int(b.cls[0])]
            conf = float(b.conf[0])
            xywhn = b.xywhn[0].tolist()
            print(f"  Proposed: {cls_name} ({conf:.2f}) at [{xywhn[0]:.3f}, {xywhn[1]:.3f}, {xywhn[2]:.3f}, {xywhn[3]:.3f}]")
    else:
        print("  Proposed: [No high-confidence detections]")
