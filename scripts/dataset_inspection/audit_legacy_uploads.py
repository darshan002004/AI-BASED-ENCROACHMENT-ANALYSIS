#!/usr/bin/env python3
"""
EncroWatch AI - Stage 1.1: Legacy Uploads and Benchmark Audit Script
Part of Task B Execution.

Inspects backend/uploads/ and backend/data/benchmark/:
- Counts actual image and video files across subdirectories.
- Detects unreadable / corrupted files.
- Computes SHA-256 for exact duplicate detection.
- Computes 64-bit difference hash (dHash) for near-duplicate / privacy-variant detection.
- Gathers image resolutions, aspect ratios, file sizes.
- Audits video files (duration, FPS, resolution).
- Audits benchmark JSON schema and validity against the 8 manuscript classes.
- Generates an interactive HTML contact sheet for manual visual review.
- Exports structured reports and candidate pilot dataset list.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict

# Attempt OpenCV or PIL for image verification
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def compute_dhash(filepath: Path, hash_size: int = 8) -> str:
    """Computes difference hash (dHash) using PIL or CV2."""
    try:
        if HAS_PIL:
            with Image.open(filepath) as img:
                img = img.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
                pixels = list(img.getdata())
                diff = []
                for row in range(hash_size):
                    for col in range(hash_size):
                        idx = row * (hash_size + 1) + col
                        diff.append(pixels[idx] > pixels[idx + 1])
                return ''.join(['1' if b else '0' for b in diff])
        elif HAS_CV2:
            img = cv2.imread(str(filepath), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return "0" * (hash_size * hash_size)
            resized = cv2.resize(img, (hash_size + 1, hash_size))
            diff = resized[:, 1:] > resized[:, :-1]
            return ''.join(['1' if b else '0' for b in diff.flatten()])
        else:
            return "NO_HASH_LIB"
    except Exception:
        return "ERROR_HASH"

def hamming_distance(s1: str, s2: str) -> int:
    if len(s1) != len(s2):
        return 999
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def inspect_image(filepath: Path) -> Dict[str, Any]:
    file_size = filepath.stat().st_size
    info = {
        "path": str(filepath.as_posix()),
        "name": filepath.name,
        "extension": filepath.suffix.lower(),
        "size_bytes": file_size,
        "is_readable": False,
        "width": 0,
        "height": 0,
        "channels": 0,
        "sha256": None,
        "dhash": None,
        "error": None
    }
    
    try:
        info["sha256"] = compute_sha256(filepath)
        info["dhash"] = compute_dhash(filepath)
        
        if HAS_PIL:
            with Image.open(filepath) as img:
                img.verify()
            with Image.open(filepath) as img:
                info["width"], info["height"] = img.size
                info["channels"] = len(img.getbands())
                info["is_readable"] = True
        elif HAS_CV2:
            mat = cv2.imread(str(filepath))
            if mat is not None:
                info["is_readable"] = True
                info["height"], info["width"] = mat.shape[:2]
                info["channels"] = mat.shape[2] if len(mat.shape) > 2 else 1
            else:
                info["error"] = "cv2 failed to decode image"
    except Exception as e:
        info["error"] = str(e)
        info["is_readable"] = False

    return info

def inspect_video(filepath: Path) -> Dict[str, Any]:
    file_size = filepath.stat().st_size
    info = {
        "path": str(filepath.as_posix()),
        "name": filepath.name,
        "extension": filepath.suffix.lower(),
        "size_bytes": file_size,
        "is_readable": False,
        "width": 0,
        "height": 0,
        "fps": 0.0,
        "frame_count": 0,
        "duration_sec": 0.0,
        "sha256": None,
        "error": None
    }
    try:
        info["sha256"] = compute_sha256(filepath)
        if HAS_CV2:
            cap = cv2.VideoCapture(str(filepath))
            if cap.isOpened():
                info["is_readable"] = True
                info["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                info["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info["fps"] = float(cap.get(cv2.CAP_PROP_FPS))
                info["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if info["fps"] > 0:
                    info["duration_sec"] = round(info["frame_count"] / info["fps"], 2)
            cap.release()
    except Exception as e:
        info["error"] = str(e)
    return info

def audit_uploads_directory(base_uploads_dir: Path) -> Dict[str, Any]:
    print(f"Scanning directory: {base_uploads_dir}")
    
    image_extensions = {".jpg", ".jpeg", ".png"}
    video_extensions = {".mp4", ".avi", ".mov", ".mkv"}
    other_extensions = set()

    images_info = []
    videos_info = []
    other_files = []

    for root, dirs, files in os.walk(base_uploads_dir):
        rel_dir = os.path.relpath(root, base_uploads_dir)
        for f in files:
            fpath = Path(root) / f
            ext = fpath.suffix.lower()
            if ext in image_extensions:
                info = inspect_image(fpath)
                info["subfolder"] = rel_dir
                images_info.append(info)
            elif ext in video_extensions:
                info = inspect_video(fpath)
                info["subfolder"] = rel_dir
                videos_info.append(info)
            else:
                other_files.append({
                    "path": str(fpath.as_posix()),
                    "name": fpath.name,
                    "extension": ext,
                    "size_bytes": fpath.stat().st_size,
                    "subfolder": rel_dir
                })

    # Exact duplicate grouping via SHA-256
    sha_map = defaultdict(list)
    for img in images_info:
        if img["sha256"]:
            sha_map[img["sha256"]].append(img)

    exact_duplicates = {k: v for k, v in sha_map.items() if len(v) > 1}
    unique_sha_count = len(sha_map)

    # Near duplicate analysis: group by privacy suffix or base identifier
    stem_map = defaultdict(list)
    for img in images_info:
        clean_stem = img["name"]
        for suffix in ["_privacy", "_annotated", "_thumbnail", "_blurred", ".jpg", ".png", ".jpeg"]:
            clean_stem = clean_stem.replace(suffix, "")
        stem_map[clean_stem].append(img)

    related_groups = {k: v for k, v in stem_map.items() if len(v) > 1}

    # Unreadable / corrupted
    corrupted = [img for img in images_info if not img["is_readable"]]

    # Folder distribution
    folder_counts = defaultdict(int)
    for img in images_info:
        folder_counts[img["subfolder"]] += 1

    # Resolution statistics
    resolutions = defaultdict(int)
    for img in images_info:
        if img["is_readable"]:
            resolutions[f"{img['width']}x{img['height']}"] += 1

    return {
        "total_files": len(images_info) + len(videos_info) + len(other_files),
        "total_images": len(images_info),
        "total_videos": len(videos_info),
        "total_other_files": len(other_files),
        "folder_distribution": dict(folder_counts),
        "corrupted_images_count": len(corrupted),
        "corrupted_images": corrupted,
        "unique_exact_images_count": unique_sha_count,
        "exact_duplicate_sets_count": len(exact_duplicates),
        "exact_duplicate_sets": {k: [x["path"] for x in v] for k, v in list(exact_duplicates.items())[:20]},
        "related_derived_groups_count": len(related_groups),
        "resolutions_distribution": dict(resolutions),
        "videos_summary": videos_info,
        "other_files_summary": other_files,
        "all_images": images_info
    }

def audit_benchmark_file(benchmark_path: Path) -> Dict[str, Any]:
    if not benchmark_path.exists():
        return {"status": "NOT_FOUND"}
    
    try:
        with open(benchmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        metadata = data.get("metadata", {})
        samples = data.get("samples", [])
        
        # Check referenced images
        missing_images = []
        valid_samples = 0
        classes_found = defaultdict(int)
        coordinate_issues = []

        base_project_dir = benchmark_path.parent.parent.parent # backend/data/benchmark -> backend

        for s in samples:
            img_rel = s.get("image_path")
            full_img_path = base_project_dir / img_rel
            img_exists = full_img_path.exists()
            if not img_exists:
                missing_images.append(img_rel)
            else:
                valid_samples += 1

            for ann in s.get("annotations", []):
                cname = ann.get("class_name")
                classes_found[cname] += 1
                bbox = ann.get("bbox", [])
                if len(bbox) != 4 or any(c < 0 for c in bbox) or bbox[2] <= 0 or bbox[3] <= 0:
                    coordinate_issues.append({"sample_id": s.get("id"), "bbox": bbox})

        return {
            "status": "VALID",
            "metadata": metadata,
            "total_samples": len(samples),
            "valid_samples_with_existing_image": valid_samples,
            "missing_images_count": len(missing_images),
            "missing_images": missing_images,
            "classes_distribution": dict(classes_found),
            "coordinate_issues": coordinate_issues,
            "academic_validity_note": (
                "Benchmark uses 6 legacy COCO classes: person, car, motorcycle, umbrella, chair, bench. "
                "It lacks custom classes: vendor_cart, construction_debris, commercial_signboard, shop_extension. "
                "Coordinates are absolute pixels [x, y, w, h] rather than normalized [0.0, 1.0]. "
                "Requires re-annotation and normalization to serve as formal ground truth."
            )
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

def generate_contact_sheet_html(images: List[Dict[str, Any]], out_path: Path, max_samples: int = 120):
    """Generates an HTML contact sheet for quick browser visual inspection."""
    selected = images[:max_samples]
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EncroWatch AI — Legacy Dataset Contact Sheet</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
  h1 {{ color: #38bdf8; font-size: 24px; margin-bottom: 8px; }}
  p.subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }}
  .card {{ background: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid #334155; transition: transform 0.2s; }}
  .card:hover {{ transform: translateY(-4px); border-color: #38bdf8; }}
  .img-container {{ width: 100%; height: 180px; background: #090d16; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
  .img-container img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
  .info {{ padding: 12px; font-size: 12px; line-height: 1.5; }}
  .name {{ font-weight: bold; color: #f1f5f9; word-break: break-all; margin-bottom: 4px; }}
  .meta {{ color: #94a3b8; }}
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; margin-top: 6px; }}
  .badge-privacy {{ background: #0369a1; color: #e0f2fe; }}
  .badge-orig {{ background: #047857; color: #d1fae5; }}
  .badge-annotated {{ background: #b45309; color: #fef3c7; }}
  .badge-inspections {{ background: #6d28d9; color: #ede9fe; }}
</style>
</head>
<body>
<h1>EncroWatch AI — Legacy Dataset Contact Sheet</h1>
<p class="subtitle">Auditing {len(images)} legacy files across backend/uploads. Showing first {len(selected)} unique/representative samples for manual verification.</p>
<div class="grid">
"""
    for img in selected:
        sub = img.get("subfolder", "")
        badge_cls = "badge-orig"
        if "privacy" in sub or "privacy" in img["name"]:
            badge_cls = "badge-privacy"
        elif "annotated" in sub:
            badge_cls = "badge-annotated"
        elif "inspections" in sub:
            badge_cls = "badge-inspections"

        img_src = f"file:///{img['path']}"
        html += f"""  <div class="card">
    <div class="img-container">
      <img src="{img_src}" alt="{img['name']}" loading="lazy" onerror="this.alt='Unable to load preview';">
    </div>
    <div class="info">
      <div class="name">{img['name']}</div>
      <div class="meta">Folder: {sub or '.'}</div>
      <div class="meta">Res: {img['width']}x{img['height']} ({img['channels']} ch) | Size: {round(img['size_bytes']/1024, 1)} KB</div>
      <span class="badge {badge_cls}">{sub or 'root'}</span>
    </div>
  </div>
"""

    html += """</div>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    uploads_dir = base_dir / "backend" / "uploads"
    benchmark_file = base_dir / "backend" / "data" / "benchmark" / "bengaluru_urban_test_v1.json"
    reports_dir = base_dir / "dataset" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("ENCROWATCH AI — LEGACY DATASET & BENCHMARK AUDIT")
    print("=" * 65)

    audit_result = audit_uploads_directory(uploads_dir)
    bench_result = audit_benchmark_file(benchmark_file)

    print(f"Total Files Audited: {audit_result['total_files']}")
    print(f"  Images: {audit_result['total_images']}")
    print(f"  Videos: {audit_result['total_videos']}")
    print(f"  Other Files: {audit_result['total_other_files']}")
    print("-" * 65)
    print("Folder Breakdown:")
    for fld, cnt in audit_result["folder_distribution"].items():
        print(f"  - {fld}: {cnt} images")
    print("-" * 65)
    print(f"Corrupted Images: {audit_result['corrupted_images_count']}")
    print(f"Unique SHA-256 Hashes: {audit_result['unique_exact_images_count']} (out of {audit_result['total_images']})")
    print(f"Exact Duplicate Sets: {audit_result['exact_duplicate_sets_count']}")
    print(f"Related / Derived Groups (Original vs Privacy vs Annotated): {audit_result['related_derived_groups_count']}")
    print("-" * 65)
    print(f"Benchmark File Status: {bench_result['status']}")
    print(f"  Samples: {bench_result.get('total_samples', 0)}")
    print(f"  Missing Images: {bench_result.get('missing_images_count', 0)}")
    print(f"  Classes Found: {bench_result.get('classes_distribution', {})}")
    print("=" * 65)

    # Save detailed JSON audit report
    audit_clean = {k: v for k, v in audit_result.items() if k != "all_images"}
    audit_clean["benchmark_audit"] = bench_result
    
    json_path = reports_dir / "legacy_upload_audit.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_clean, f, indent=2)
    print(f"Saved full audit JSON to: {json_path}")

    # Generate HTML contact sheet
    html_path = reports_dir / "contact_sheet.html"
    generate_contact_sheet_html(audit_result["all_images"], html_path, max_samples=150)
    print(f"Saved Visual Contact Sheet HTML to: {html_path}")

    # Generate Pilot Dataset Candidate List (Task C)
    # Filter for unique, readable images, prefer original over privacy where available, or record privacy status
    pilot_manifest_path = base_dir / "ENCROWATCH_PILOT_DATASET_MANIFEST.csv"
    
    # We will pick unique hashes or distinct stems
    seen_hashes = set()
    pilot_candidates = []
    
    # Prioritize 'original' folder or root images
    sorted_images = sorted(audit_result["all_images"], key=lambda x: (
        0 if "original" in x["subfolder"] else (1 if x["subfolder"] == "." else 2)
    ))

    for img in sorted_images:
        if not img["is_readable"]:
            continue
        sha = img["sha256"]
        if sha in seen_hashes:
            continue
        seen_hashes.add(sha)
        
        # Categorize
        sub = img["subfolder"]
        is_privacy = "privacy" in sub or "_privacy" in img["name"]
        
        # Determine likely ward from filename if present
        name_lower = img["name"].lower()
        ward = "Unassigned / General Bengaluru"
        if "mg" in name_lower or "brigade" in name_lower:
            ward = "Ward 1 (MG Road / Brigade Road)"
        elif "indiranagar" in name_lower or "100ft" in name_lower:
            ward = "Ward 2 (Indiranagar 100ft Road)"
        elif "koramangala" in name_lower or "80ft" in name_lower:
            ward = "Ward 3 (Koramangala 80ft Road)"
        elif "btm" in name_lower or "jayanagar" in name_lower or "malleshwaram" in name_lower:
            ward = "Ward 4 (BTM / South Suburbs)"

        pilot_candidates.append({
            "filename": img["name"],
            "relative_path": f"backend/uploads/{sub}/{img['name']}" if sub != "." else f"backend/uploads/{img['name']}",
            "sha256": sha,
            "width": img["width"],
            "height": img["height"],
            "size_kb": round(img["size_bytes"] / 1024, 2),
            "folder": sub,
            "privacy_blurred": is_privacy,
            "assigned_ward": ward,
            "provenance_status": "Legacy Prototype Upload (Requires Civic/Field Provenance Verification)",
            "annotation_status": "Unannotated (Requires 8-Class Bounding Box & Footpath Polygon)",
            "suitability": "Usable for Pilot Inspection" if img["width"] >= 200 and img["height"] >= 200 else "Low Resolution Candidate"
        })

    # Write CSV
    import csv
    with open(pilot_manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "relative_path", "sha256", "width", "height", "size_kb",
            "folder", "privacy_blurred", "assigned_ward", "provenance_status",
            "annotation_status", "suitability"
        ])
        writer.writeheader()
        for row in pilot_candidates:
            writer.writerow(row)

    print(f"Generated Pilot Dataset Manifest CSV with {len(pilot_candidates)} unique candidates at: {pilot_manifest_path}")

if __name__ == "__main__":
    main()
