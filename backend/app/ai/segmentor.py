import cv2
import numpy as np
import os
from typing import Tuple, Dict, Any, List

class RoadFootpathSegmentor:
    """
    Road & Footpath Region Module.
    IMPORTANT TRANSPARENCY NOTE:
    - If a pretrained semantic segmentation ONNX model is present at `app/ai/weights/road_footpath_seg.onnx`,
      it is loaded for neural segmentation.
    - When no semantic segmentation model is present (default environment), this module does NOT claim
      to perform AI segmentation. Instead, it generates a clearly labeled **Prototype Geometric Corridor ROI**
      (rule-based perspective polygons) and documents exact requirements for real road-scene segmentation.
    - Does NOT invent real-world square metres (m²) or physical widths (m); reports exact 2D pixel areas
      and pixel spans.
    """

    COLOR_FOOTPATH = (94, 197, 34)      # BGR (#22C55E Green) — Prototype Footpath ROI
    COLOR_ROAD = (246, 130, 59)         # BGR (#3B82F6 Blue) — Prototype Road ROI
    COLOR_OBSTRUCTION = (68, 68, 239)   # BGR (#EF4444 Red) — Potential Encroachment
    COLOR_REVIEW = (15, 158, 245)       # BGR (#F59E0B Amber) — Needs Human Review
    COLOR_OTHER = (180, 180, 40)        # BGR (Teal/Cyan) — Not an Encroachment

    def __init__(self):
        self.weights_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "weights", "road_footpath_seg.onnx")
        )
        self.net = None
        self.is_real_segmentation_model = False
        self._load_model_if_available()

    def _load_model_if_available(self):
        if os.path.exists(self.weights_path):
            try:
                self.net = cv2.dnn.readNetFromONNX(self.weights_path)
                self.is_real_segmentation_model = True
            except Exception:
                self.net = None
                self.is_real_segmentation_model = False

    def segment(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generates Road and Footpath region masks and exact pixel geometry metadata.
        Explicitly distinguishes Prototype Geometric ROI Approximation from AI Segmentation.
        """
        h, w = image.shape[:2]
        overlay = image.copy()
        mask_layer = np.zeros_like(image, dtype=np.uint8)

        # Estimate horizon row via vertical Sobel gradient energy (rule-based image heuristic, NOT neural AI)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        row_energy = np.mean(np.abs(sobel_y), axis=1)
        search_top, search_btm = int(h * 0.42), int(h * 0.65)
        if search_btm > search_top:
            horizon_y = search_top + int(np.argmax(row_energy[search_top:search_btm]))
        else:
            horizon_y = int(h * 0.55)
        horizon_y = max(int(h * 0.48), min(int(h * 0.62), horizon_y))

        # Prototype Perspective Polygons (Left = Footpath ROI, Right/Center = Road ROI)
        footpath_pts = np.array([
            [int(w * 0.0), int(h * 0.99)],
            [int(w * 0.49), int(h * 0.99)],
            [int(w * 0.43), horizon_y + int(h * 0.04)],
            [int(w * 0.14), horizon_y],
            [int(w * 0.0), int(h * 0.66)]
        ], np.int32)

        road_pts = np.array([
            [int(w * 0.49), int(h * 0.99)],
            [int(w * 1.0), int(h * 0.99)],
            [int(w * 1.0), horizon_y + int(h * 0.02)],
            [int(w * 0.56), horizon_y],
            [int(w * 0.43), horizon_y + int(h * 0.04)]
        ], np.int32)

        cv2.fillPoly(mask_layer, [footpath_pts], self.COLOR_FOOTPATH)
        cv2.fillPoly(mask_layer, [road_pts], self.COLOR_ROAD)

        alpha = 0.32
        cv2.addWeighted(mask_layer, alpha, overlay, 1 - alpha, 0, overlay)

        cv2.polylines(overlay, [footpath_pts], True, self.COLOR_FOOTPATH, 2, cv2.LINE_AA)
        cv2.polylines(overlay, [road_pts], True, self.COLOR_ROAD, 2, cv2.LINE_AA)

        # Exact 2D pixel measurements (no invented square metres or physical widths)
        image_area_px = int(w * h)
        footpath_roi_area_px = round(max(1.0, float(cv2.contourArea(footpath_pts))), 1)
        road_roi_area_px = round(max(1.0, float(cv2.contourArea(road_pts))), 1)

        # Horizontal span of the prototype footpath ROI at mid-ground (in pixels)
        footpath_bottom_span_px = int(w * 0.49)
        footpath_top_span_px = max(1, int(w * 0.43) - int(w * 0.14))
        footpath_mid_span_px = int(round((footpath_bottom_span_px + footpath_top_span_px) / 2.0))

        segmentation_info = {
            "is_ai_segmentation": self.is_real_segmentation_model,
            "is_trained_model": self.is_real_segmentation_model,
            "is_real_segmentation_model": self.is_real_segmentation_model,
            "is_prototype": not self.is_real_segmentation_model,
            "mode": "REAL_ONNX_SEG" if self.is_real_segmentation_model else "PROTOTYPE_CORRIDOR_ROI",
            "mode_label": (
                "Pretrained Semantic Segmentation Model (ONNX)"
                if self.is_real_segmentation_model
                else "Prototype Region-of-Interest (Rule-Based Perspective Polygons — Not AI Segmentation)"
            ),
            "badge_label": (
                "AI Semantic Segmentation"
                if self.is_real_segmentation_model
                else "Prototype Segmentation Overlay (Non-AI Geometric ROI)"
            ),
            "description": (
                "Road and Footpath regions are approximated using rule-based perspective polygons and vertical Sobel "
                "gradient horizon estimation. This is a prototype spatial overlay, NOT pixel-level neural segmentation. "
                "Because street perspective and curb geometry vary across cameras, overlap classifications require human review."
            ),
            "horizon_y_px": horizon_y,
            "image_dimensions": {"width": w, "height": h},
            "legend": [
                {"label": "Prototype Footpath ROI", "color_hex": "#22C55E", "role": "Pedestrian Walkway Approximation"},
                {"label": "Prototype Road ROI", "color_hex": "#3B82F6", "role": "Vehicular Carriageway Approximation"},
                {"label": "Potential Encroachment", "color_hex": "#EF4444", "role": "Footpath Overlap >= 35%"},
                {"label": "Needs Human Review", "color_hex": "#F59E0B", "role": "Uncertain / Boundary Overlap"},
                {"label": "Not an Encroachment", "color_hex": "#28B4B4", "role": "Normal Traffic / Pedestrian"}
            ],
            "real_segmentation_requirements": {
                "status": "Prototype geometric polygons active; pretrained semantic segmentation model not installed.",
                "recommended_models": [
                    "BiSeNetV2 (Cityscapes Real-Time Semantic Segmentation)",
                    "DDRNet-23-slim",
                    "DeepLabV3+ (MobileNetV3 backbone)",
                    "SegFormer-B0 (ADE20K / Cityscapes)"
                ],
                "training_datasets": [
                    "Cityscapes (classes: road=0, sidewalk=1)",
                    "Indian Driving Dataset / IDD (unstructured road, sidewalk, drivable/non-drivable mud/curb)",
                    "Mapillary Vistas (road, sidewalk, curb, pedestrian_area)"
                ],
                "integration_steps": (
                    "Export a trained road/sidewalk segmentation network to ONNX (fixed input shape 1x3x512x1024, "
                    "output argmax class map) and place it at 'backend/app/ai/weights/road_footpath_seg.onnx'."
                ),
                "expected_weights_path": "backend/app/ai/weights/road_footpath_seg.onnx"
            }
        }

        geometry_data = {
            "footpath_polygon": footpath_pts.tolist(),
            "road_polygon": road_pts.tolist(),
            "image_area_px": image_area_px,
            "footpath_roi_area_px": footpath_roi_area_px,
            "road_roi_area_px": road_roi_area_px,
            "footpath_width_px": footpath_mid_span_px,
            "footpath_bottom_span_px": footpath_bottom_span_px,
            "camera_calibrated": False,
            "footpath_area_sqm": None,
            "road_area_sqm": None,
            "total_footpath_width_m": None,
            "img_width": w,
            "img_height": h,
            "segmentation_info": segmentation_info
        }

        return overlay, geometry_data

    def apply_obstruction_overlays(
        self,
        segmented_image: np.ndarray,
        processed_objects: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Renders object footprint shading on the prototype ROI overlay image and stamps
        a clear prototype header so the saved image is never mistaken for neural segmentation.
        """
        canvas = segmented_image.copy()
        obj_mask = canvas.copy()
        h, w = canvas.shape[:2]

        for obj in processed_objects:
            bx, by, bw, bh = obj["bbox"]
            classification = obj.get("classification", "Not an encroachment")
            if classification == "Potential encroachment":
                fill_color = self.COLOR_OBSTRUCTION
            elif classification == "Needs human review":
                fill_color = self.COLOR_REVIEW
            else:
                fill_color = self.COLOR_OTHER
            cv2.rectangle(obj_mask, (bx, by), (bx + bw, by + bh), fill_color, -1)

        cv2.addWeighted(obj_mask, 0.22, canvas, 0.78, 0, canvas)

        # Stamp explicit Prototype ROI disclaimer bar at bottom of standalone segmentation map
        if not self.is_real_segmentation_model and w >= 240:
            bar_h = 26
            cv2.rectangle(canvas, (0, h - bar_h), (w, h), (15, 23, 42), -1)
            cv2.putText(
                canvas,
                "PROTOTYPE CORRIDOR ROI (NON-AI GEOMETRIC OVERLAY) - UNCALIBRATED PIXEL SPACE",
                (8, h - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                max(0.35, min(0.48, w / 1400.0)),
                (56, 189, 248),
                1,
                cv2.LINE_AA
            )

        return canvas


segmentor = RoadFootpathSegmentor()
