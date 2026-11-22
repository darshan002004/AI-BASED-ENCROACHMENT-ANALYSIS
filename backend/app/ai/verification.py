import cv2
import numpy as np
import os
import uuid
from typing import Dict, Any
from app.ai.segmentor import segmentor
from app.ai.detector import detector
from app.ai.encroachment_engine import encroachment_engine
from app.ai.metrics import metrics_engine
from app.config import settings


class BeforeAfterVerificationEngine:
    """
    Before/After AI Resolution Verification.
    Runs real YOLOv5n-ONNX detection and Prototype Footpath ROI overlap analysis on both
    the Before and After images, without inventing hardcoded confidence or square-metre values.
    """

    def verify_resolution(
        self,
        before_image_path: str,
        after_image_path: str,
        expected_obstruction_type: str = "Street Object"
    ) -> Dict[str, Any]:
        before_img = cv2.imread(before_image_path) if before_image_path and os.path.exists(before_image_path) else None
        after_img = cv2.imread(after_image_path) if after_image_path and os.path.exists(after_image_path) else None

        if after_img is None:
            raise ValueError(f"After inspection image could not be loaded from '{after_image_path}'.")

        if before_img is None:
            # If original image file is missing on disk, use a blank comparison frame on the left
            before_img = np.zeros_like(after_img)
            cv2.putText(before_img, "Before Image Unavailable", (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
            before_occ_pct = None
            before_enc_count = None
        else:
            _, geom_before = segmentor.segment(before_img)
            raw_before, _ = detector.detect(before_img)
            proc_before, enc_sum_before = encroachment_engine.analyze(raw_before, geom_before)
            before_occ_pct = enc_sum_before["roi_pixel_occupancy_pct"]
            before_enc_count = enc_sum_before["encroaching_objects_count"]

        seg_after, geom_after = segmentor.segment(after_img)
        raw_after, _ = detector.detect(after_img)
        proc_after, enc_sum_after = encroachment_engine.analyze(raw_after, geom_after)
        acc_after = metrics_engine.calculate_accessibility(geom_after, enc_sum_after, proc_after)

        after_enc_objs = [o for o in proc_after if o["classification"] == "Potential encroachment"]
        after_rev_objs = [o for o in proc_after if o["classification"] == "Needs human review"]
        after_occ_pct = enc_sum_after["roi_pixel_occupancy_pct"]

        # Calculate actual confidence from detections if any exist, otherwise None
        all_confs = [o["confidence"] for o in proc_after]
        mean_conf = round(float(np.mean(all_confs)), 4) if all_confs else None

        if len(after_enc_objs) == 0 and len(after_rev_objs) == 0:
            is_cleared = True
            result_status = "RESOLUTION VERIFIED (NO OBSTRUCTION DETECTED)"
            current_status = "No encroachment or uncertain object detected in Prototype Footpath ROI (0% pixel overlap)"
        elif len(after_enc_objs) == 0 and len(after_rev_objs) > 0:
            is_cleared = False
            result_status = "NEEDS HUMAN REVIEW"
            current_status = f"{len(after_rev_objs)} object(s) flagged as 'Needs human review' in after-inspection image"
        else:
            is_cleared = False
            result_status = "ENCROACHMENT STILL PRESENT (NEEDS HUMAN REVIEW)"
            current_status = (
                f"{len(after_enc_objs)} potential encroachment(s) detected ({after_enc_objs[0]['label']}, "
                f"{after_occ_pct}% Prototype Footpath ROI pixel overlap)"
            )

        original_status = (
            f"{before_enc_count} potential encroachment(s) ({before_occ_pct}% Footpath ROI pixel overlap)"
            if before_occ_pct is not None
            else "Original image not available for pixel comparison"
        )

        # Render side-by-side comparison image
        target_h, target_w = 400, 500
        b_resized = cv2.resize(before_img, (target_w, target_h))
        a_resized = cv2.resize(seg_after, (target_w, target_h))

        cv2.rectangle(b_resized, (0, 0), (target_w, 45), (15, 23, 42), -1)
        cv2.putText(b_resized, "BEFORE: ORIGINAL FRAME", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        header_color = (34, 197, 94) if is_cleared else (245, 158, 11)
        cv2.rectangle(a_resized, (0, 0), (target_w, 45), (15, 23, 42), -1)
        header_text = "AFTER: CLEAR" if is_cleared else "AFTER: NEEDS REVIEW / PERSISTS"
        cv2.putText(a_resized, header_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, header_color, 2)

        comparison_canvas = np.hstack([b_resized, a_resized])
        comp_filename = f"verify_{uuid.uuid4().hex[:10]}.jpg"
        comp_path = os.path.join(settings.UPLOAD_DIR, "annotated", comp_filename)
        os.makedirs(os.path.dirname(comp_path), exist_ok=True)
        cv2.imwrite(comp_path, comparison_canvas)

        return {
            "verified": is_cleared,
            "status": result_status,
            "confidence": mean_conf,
            "original_obstruction": original_status,
            "current_obstruction": current_status,
            "after_roi_pixel_occupancy_pct": after_occ_pct,
            "current_accessibility_score": acc_after["accessibility_score"],
            "current_accessibility_status": acc_after["accessibility_status"],
            "comparison_image_url": f"/uploads/annotated/{comp_filename}"
        }


verification_engine = BeforeAfterVerificationEngine()
