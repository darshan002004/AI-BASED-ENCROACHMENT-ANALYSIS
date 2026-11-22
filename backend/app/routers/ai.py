from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Dict, Any, Optional, List
import os
import uuid
import shutil
from app.config import settings
from app.ai.pipeline import run_ai_pipeline
from app.ai.detector import detector, SUPPORTED_URBAN_COCO_CLASSES, UNSUPPORTED_SPECIALIZED_CLASSES
from app.ai.segmentor import segmentor
from app.ai.metrics import CALIBRATION_REQUIREMENTS, SCORING_ASSUMPTIONS, ENGINEERING_ACCESSIBILITY_STANDARDS
from app.ai.tracker import tracker
from app.ai.verification import verification_engine
from app.utils.security import validate_file_content_and_type, generate_safe_storage_filename

router = APIRouter(prefix="/ai", tags=["AI Computer Vision"])

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_IMAGE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


@router.get("/capabilities")
async def get_ai_capabilities() -> Dict[str, Any]:
    """
    Returns complete, honest diagnostic metadata on which AI modules use real pretrained
    neural weights versus prototype geometric approximations, unsupported specialized classes,
    and camera calibration requirements.
    """
    return {
        "object_detection": {
            "primary_engine": (
                "Pretrained YOLOv5n-ONNX (COCO-80 via OpenCV 5.0 DNN)"
                if detector.yolo_loaded
                else "MODEL_LOAD_FAILED"
            ),
            "yolo_onnx_loaded": detector.yolo_loaded,
            "load_error": detector.load_error,
            "model_file": "yolov5n.onnx (COCO 80-class pretrained weights)",
            "supported_coco_classes": SUPPORTED_URBAN_COCO_CLASSES,
            "unsupported_specialized_classes": UNSUPPORTED_SPECIALIZED_CLASSES,
            "fabricated_boxes_removed": True,
            "hardcoded_confidences_removed": True,
            "mode": "REAL_PRETRAINED_YOLO" if detector.yolo_loaded else "ERROR_WEIGHTS_UNAVAILABLE"
        },
        "road_footpath_segmentation": {
            "is_ai_segmentation": segmentor.is_real_segmentation_model,
            "is_trained_model": segmentor.is_real_segmentation_model,
            "is_real_segmentation_model": segmentor.is_real_segmentation_model,
            "is_prototype": not segmentor.is_real_segmentation_model,
            "mode": "REAL_ONNX_SEG" if segmentor.is_real_segmentation_model else "PROTOTYPE_CORRIDOR_ROI",
            "mode_label": (
                "ONNX Semantic Segmentation"
                if segmentor.is_real_segmentation_model
                else "Prototype Region-of-Interest (Rule-Based Perspective Polygons — Not AI Segmentation)"
            ),
            "badge_label": (
                "Real AI Semantic Segmentation"
                if segmentor.is_real_segmentation_model
                else "Prototype Segmentation Overlay (Non-AI Geometric ROI)"
            ),
            "real_segmentation_requirements": {
                "recommended_models": [
                    "BiSeNetV2",
                    "DDRNet-23-slim",
                    "DeepLabV3+ (MobileNetV3)",
                    "SegFormer-B0"
                ],
                "training_datasets": [
                    "Cityscapes (road, sidewalk)",
                    "Indian Driving Dataset / IDD (road, sidewalk, curb, drivable/non-drivable)",
                    "Mapillary Vistas"
                ],
                "expected_weights_path": "backend/app/ai/weights/road_footpath_seg.onnx"
            }
        },
        "encroachment_classification": {
            "separated_from_detection": True,
            "engine": "Shapely 2D Polygon Overlap & Uncertainty Classifier",
            "outputs": [
                "Potential encroachment",
                "Needs human review",
                "Not an encroachment",
                "No obstruction detected"
            ]
        },
        "measurements_and_calibration": {
            "real_world_measurements_available": False,
            "measurement_unit": "2D Pixels (px / px²) & Prototype ROI Overlap (%)",
            "calibration_requirements": CALIBRATION_REQUIREMENTS,
            "scoring_assumptions": SCORING_ASSUMPTIONS,
            "engineering_standards": ENGINEERING_ACCESSIBILITY_STANDARDS,
            "supported_calibrated_modes": [
                "NOMINAL_STREET_PROFILE (e.g. 1.8m IRC minimum, 2.5m standard sidewalk, 3.0m wide promenade)",
                "EXPLICIT_SCALE (surveyed pixels-per-meter)"
            ]
        },
        "video_tracking": {
            "is_simulated": False,
            "engine": "OpenCV VideoCapture Frame Sampling + YOLOv5n-ONNX + IoU/Centroid Multi-Object Tracker",
            "persistence_threshold_sec": tracker.PERSISTENCE_THRESHOLD_SEC
        },
        "allowed_uploads": {
            "extensions": ["JPG", "JPEG", "PNG"],
            "max_size_mb": 25
        }
    }


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    allow_demo_mode: bool = Query(False, description="If True, returns explicit Demo Mode status instead of 503 when model weights fail to load."),
    nominal_footpath_width_m: Optional[float] = Query(None, description="Optional nominal corridor width in meters (e.g. 1.8, 2.5, 3.0) for IRC/ADA calibrated physical metric scale."),
    calibration_px_per_m: Optional[float] = Query(None, description="Optional surveyed ground-truth pixels-per-meter scale.")
):
    """
    Validates JPG/JPEG/PNG upload and runs:
      1. Prototype Road/Footpath ROI overlay
      2. Pure Pretrained YOLOv5n-ONNX object detection
      3. Separated spatial overlap & uncertainty classification ('Potential encroachment', 'Needs human review', 'Not an encroachment')
      4. Slice-by-slice corridor bottleneck analysis and dual-mode metrics (Calibrated vs Uncalibrated)
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No image file provided. Please upload a JPG, JPEG, or PNG image.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    content_type = (file.content_type or "").lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS or (content_type and content_type not in ALLOWED_IMAGE_MIME_TYPES):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{file.filename}' ({content_type or 'unknown'}). Only JPG, JPEG, and PNG images are allowed."
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty (0 bytes).")
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image file size ({len(file_bytes) / (1024 * 1024):.2f} MB) exceeds the maximum allowed size of 25 MB."
        )

    # Magic byte and content validation
    is_valid, detected_type, err_msg = validate_file_content_and_type(file_bytes, file.filename, is_video=False)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    unique_name = generate_safe_storage_filename(file.filename, prefix="upload")
    dest_path = os.path.join(settings.UPLOAD_DIR, "original", unique_name)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, "wb") as buffer:
        buffer.write(file_bytes)

    try:
        result = run_ai_pipeline(
            dest_path,
            output_prefix=f"seg_{uuid.uuid4().hex[:6]}",
            allow_demo_mode=allow_demo_mode,
            nominal_footpath_width_m=nominal_footpath_width_m,
            calibration_px_per_m=calibration_px_per_m
        )
        result["original_image_url"] = f"/uploads/original/{unique_name}"
        result["uploaded_filename"] = file.filename
        result["file_size_kb"] = round(len(file_bytes) / 1024.0, 1)
        return result

    except ValueError as ve:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re_err:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=503, detail=str(re_err))
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=500, detail=f"AI Computer Vision pipeline failed: {str(e)}")


@router.post("/track-video")
async def track_video_persistent(
    file: UploadFile = File(...)
):
    """
    Processes uploaded video stream frame-by-frame (sampled at ~2 FPS) using YOLOv5n-ONNX
    and performs IoU/centroid persistence tracking across frames.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No video file provided.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded video file is empty (0 bytes).")
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Uploaded video file exceeds the 25 MB limit.")

    # Magic byte and content validation
    is_valid, detected_type, err_msg = validate_file_content_and_type(file_bytes, file.filename, is_video=True)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    unique_name = generate_safe_storage_filename(file.filename, prefix="vid")
    dest_path = os.path.join(settings.UPLOAD_DIR, "original", unique_name)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, "wb") as buffer:
        buffer.write(file_bytes)

    try:
        tracking_results = tracker.process_video(dest_path)
        tracking_results["video_url"] = f"/uploads/original/{unique_name}"
        return tracking_results
    except ValueError as ve:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re_err:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=503, detail=str(re_err))
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=500, detail=f"Video tracking pipeline failed: {str(e)}")


@router.post("/verify")
async def verify_before_after(
    before_file: UploadFile = File(...),
    after_file: UploadFile = File(...),
    expected_type: str = Form("Street Object")
):
    """
    Compares before and after images using YOLOv5n-ONNX detection and Prototype Footpath ROI overlap.
    """
    before_bytes = await before_file.read()
    after_bytes = await after_file.read()

    is_v1, _, err1 = validate_file_content_and_type(before_bytes, before_file.filename, is_video=False)
    if not is_v1:
        raise HTTPException(status_code=400, detail=f"Before image: {err1}")
    is_v2, _, err2 = validate_file_content_and_type(after_bytes, after_file.filename, is_video=False)
    if not is_v2:
        raise HTTPException(status_code=400, detail=f"After image: {err2}")

    b_name = generate_safe_storage_filename(before_file.filename, prefix="before")
    a_name = generate_safe_storage_filename(after_file.filename, prefix="after")
    b_path = os.path.join(settings.UPLOAD_DIR, "original", b_name)
    a_path = os.path.join(settings.UPLOAD_DIR, "inspections", a_name)
    os.makedirs(os.path.dirname(b_path), exist_ok=True)
    os.makedirs(os.path.dirname(a_path), exist_ok=True)

    with open(b_path, "wb") as buffer:
        buffer.write(before_bytes)
    with open(a_path, "wb") as buffer:
        buffer.write(after_bytes)

    try:
        verification_res = verification_engine.verify_resolution(b_path, a_path, expected_type)
        verification_res["before_url"] = f"/uploads/original/{b_name}"
        verification_res["after_url"] = f"/uploads/inspections/{a_name}"
        return verification_res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re_err:
        raise HTTPException(status_code=503, detail=str(re_err))


@router.post("/analyze-multiple")
async def analyze_multiple_images(
    files: List[UploadFile] = File(...),
    allow_demo_mode: bool = Query(False)
) -> Dict[str, Any]:
    """
    Feature 2: Multi-Image Evidence Analysis & Consistency Engine.
    Validates multiple photos (up to 5), runs YOLOv5n-ONNX AI analysis on each perspective,
    extracts metadata, and cross-checks for conflicting/inconsistent findings.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided for multi-image analysis.")

    if len(files) > 5:
        raise HTTPException(status_code=400, detail="A maximum of 5 evidence photos can be uploaded per incident.")

    evidence_results: List[Dict[str, Any]] = []

    for idx, f in enumerate(files):
        if not f or not f.filename:
            continue

        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        content_type = (f.content_type or "").lower()

        if ext not in ALLOWED_IMAGE_EXTENSIONS or (content_type and content_type not in ALLOWED_IMAGE_MIME_TYPES):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format for photo #{idx + 1} '{f.filename}'. Only JPG, JPEG, and PNG images are allowed."
            )

        file_bytes = await f.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail=f"Evidence photo #{idx + 1} '{f.filename}' is empty (0 bytes).")
        if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Evidence photo #{idx + 1} exceeds the 25 MB limit."
            )

        unique_name = f"multi_{uuid.uuid4().hex[:10]}.{ext}"
        dest_path = os.path.join(settings.UPLOAD_DIR, "original", unique_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, "wb") as buffer:
            buffer.write(file_bytes)

        try:
            analysis = run_ai_pipeline(
                dest_path,
                output_prefix=f"multi_seg_{idx+1}",
                allow_demo_mode=allow_demo_mode
            )
            analysis["evidence_id"] = f"ev_{uuid.uuid4().hex[:6]}"
            analysis["original_image_url"] = f"/uploads/original/{unique_name}"
            analysis["uploaded_filename"] = f.filename
            analysis["file_size_kb"] = round(len(file_bytes) / 1024.0, 1)
            analysis["photo_index"] = idx + 1
            analysis["perspective_label"] = f"Perspective #{idx + 1}"
            evidence_results.append(analysis)
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed for evidence photo #{idx + 1} '{f.filename}': {str(e)}"
            )

    if len(evidence_results) == 0:
        raise HTTPException(status_code=400, detail="Zero valid images could be processed.")

    # Cross-Perspective Consistency Evaluation (Feature 2)
    is_inconsistent = False
    inconsistency_reason = None

    if len(evidence_results) >= 2:
        classifications = [r.get("potential_encroachment") for r in evidence_results]
        types = [r.get("primary_encroachment_type") for r in evidence_results if r.get("primary_encroachment_type")]
        occupancies = [float(r.get("occupancy_percentage") or 0.0) for r in evidence_results]

        has_yes = any(c == "YES" for c in classifications)
        has_no = any(c == "NO" for c in classifications)
        max_occ_diff = max(occupancies) - min(occupancies)

        if has_yes and has_no and max_occ_diff >= 35.0:
            is_inconsistent = True
            inconsistency_reason = (
                f"Contradictory findings: Perspective #{classifications.index('YES')+1} flagged an active encroachment "
                f"({types[0] if types else 'Obstacle'}, {max(occupancies):.1f}% occupancy), but Perspective "
                f"#{classifications.index('NO')+1} shows clear walkway ({min(occupancies):.1f}% occupancy). "
                "Flagged for municipal officer visual verification."
            )
        elif len(set(types)) > 1 and all(t not in ["Clear", "Other"] for t in types):
            # Divergent obstruction categories
            is_inconsistent = True
            inconsistency_reason = (
                f"Divergent obstruction classes across evidence photos: {', '.join(set(types))}. "
                "Officer review required to classify primary obstruction."
            )
        else:
            is_inconsistent = False
            inconsistency_reason = "Evidence is consistent across all uploaded perspectives."

    # Pick dominant or worst-case primary analysis
    primary = max(evidence_results, key=lambda r: float(r.get("risk_score") or 0.0))

    return {
        "total_images": len(evidence_results),
        "total_photos": len(evidence_results),
        "evidence_analyses": evidence_results,
        "evidence_results": evidence_results,
        "is_inconsistent": is_inconsistent,
        "inconsistency_reason": inconsistency_reason,
        "primary_analysis": primary,
        "primary_result": primary
    }

