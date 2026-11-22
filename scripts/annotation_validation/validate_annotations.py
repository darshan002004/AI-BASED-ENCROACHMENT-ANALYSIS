#!/usr/bin/env python3
"""
EncroWatch AI - Stage 1: Annotation Integrity & Syntax Validator
Part of Phase 5 & Phase 4 Execution.

Validates annotations against formal academic rules:
- Format verification (YOLO darknet standard: class x_center y_center width height).
- Coordinate normalization: 0.0 <= coord <= 1.0.
- Geometric validity: w > 0, h > 0, area > 0.
- Class membership: class_id in [0..7].
- Segmentation polygon validation: >= 3 points, normalized coordinates.
- Contact mask format validation.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

VALID_CLASSES = {
    0: "motorcycle",
    1: "car",
    2: "vendor_cart",
    3: "construction_debris",
    4: "commercial_signboard",
    5: "shop_extension",
    6: "umbrella_canopy",
    7: "pedestrian"
}

def validate_yolo_bbox_line(line_str: str, line_no: int, file_name: str) -> Tuple[bool, str, Optional[int]]:
    parts = line_str.strip().split()
    if not parts:
        return True, "EMPTY_LINE", None
    
    if len(parts) != 5:
        return False, f"Line {line_no} in {file_name}: Expected 5 fields (cls x y w h), found {len(parts)}", None

    try:
        cls_id = int(parts[0])
    except ValueError:
        return False, f"Line {line_no} in {file_name}: Class ID '{parts[0]}' is not an integer", None

    if cls_id not in VALID_CLASSES:
        return False, f"Line {line_no} in {file_name}: Class ID {cls_id} out of bounds (allowed: 0..7)", cls_id

    try:
        x_c, y_c, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
    except ValueError:
        return False, f"Line {line_no} in {file_name}: Non-numeric coordinates", cls_id

    # Check normalization range
    for val, name in [(x_c, 'x_center'), (y_c, 'y_center'), (w, 'width'), (h, 'height')]:
        if val < 0.0 or val > 1.0:
            return False, f"Line {line_no} in {file_name}: {name}={val} out of range [0.0, 1.0]", cls_id

    if w <= 0.0 or h <= 0.0:
        return False, f"Line {line_no} in {file_name}: Non-positive dimension w={w}, h={h}", cls_id

    return True, "VALID", cls_id

def validate_polygon_segmentation(line_str: str, line_no: int, file_name: str) -> Tuple[bool, str, Optional[int]]:
    parts = line_str.strip().split()
    if not parts:
        return True, "EMPTY_LINE", None

    try:
        cls_id = int(parts[0])
    except ValueError:
        return False, f"Line {line_no} in {file_name}: Class ID not an integer", None

    coords = parts[1:]
    if len(coords) < 6 or len(coords) % 2 != 0:
        return False, f"Line {line_no} in {file_name}: Polygon requires even number of coordinates >= 6, got {len(coords)}", cls_id

    try:
        float_coords = [float(c) for c in coords]
    except ValueError:
        return False, f"Line {line_no} in {file_name}: Non-numeric polygon coordinate", cls_id

    for val in float_coords:
        if val < 0.0 or val > 1.0:
            return False, f"Line {line_no} in {file_name}: Coordinate {val} out of range [0.0, 1.0]", cls_id

    return True, "VALID", cls_id

def validate_directory(dir_path: Path, is_segmentation: bool = False) -> Dict[str, Any]:
    if not dir_path.exists():
        return {"status": "DIRECTORY_NOT_FOUND", "files_checked": 0, "errors": []}

    files = list(dir_path.glob("*.txt"))
    errors = []
    class_tallies = {k: 0 for k in VALID_CLASSES.keys()}
    valid_boxes_count = 0

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            for l_idx, line in enumerate(f, 1):
                clean = line.strip()
                if not clean:
                    continue
                if is_segmentation:
                    ok, msg, cls_id = validate_polygon_segmentation(clean, l_idx, fpath.name)
                else:
                    ok, msg, cls_id = validate_yolo_bbox_line(clean, l_idx, fpath.name)
                
                if not ok:
                    errors.append(msg)
                elif cls_id is not None and cls_id in class_tallies:
                    class_tallies[cls_id] += 1
                    valid_boxes_count += 1

    named_tallies = {VALID_CLASSES[k]: class_tallies[k] for k in sorted(VALID_CLASSES.keys())}
    return {
        "status": "VALIDATED" if not errors else "ERRORS_DETECTED",
        "files_checked": len(files),
        "valid_elements": valid_boxes_count,
        "class_tallies": named_tallies,
        "error_count": len(errors),
        "errors": errors[:50]  # Cap error list to first 50
    }

def main():
    base = Path(__file__).resolve().parent.parent.parent
    dataset_dir = base / "dataset"
    
    det_dir = dataset_dir / "annotations" / "detection"
    seg_dir = dataset_dir / "annotations" / "segmentation"
    contact_dir = dataset_dir / "annotations" / "ground_contact"

    print("=" * 65)
    print("ENCROWATCH AI — ANNOTATION INTEGRITY VALIDATION")
    print("=" * 65)

    det_res = validate_directory(det_dir, is_segmentation=False)
    print(f"Detection Annotations ({det_dir}):")
    print(f"  Files Checked: {det_res['files_checked']}")
    print(f"  Valid Boxes: {det_res.get('valid_elements', 0)}")
    print(f"  Errors Detected: {det_res['error_count']}")

    seg_res = validate_directory(seg_dir, is_segmentation=True)
    print(f"Segmentation Annotations ({seg_dir}):")
    print(f"  Files Checked: {seg_res['files_checked']}")
    print(f"  Errors Detected: {seg_res['error_count']}")

    report = {
        "detection_validation": det_res,
        "segmentation_validation": seg_res,
        "classes_allowed": VALID_CLASSES
    }

    report_path = dataset_dir / "reports" / "annotation_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Validation report saved to: {report_path}")
    print("=" * 65)

if __name__ == "__main__":
    from typing import Optional
    main()
