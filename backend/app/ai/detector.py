import cv2
import numpy as np
import os
import uuid
from typing import List, Dict, Any, Tuple, Optional

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
]

SUPPORTED_URBAN_COCO_CLASSES = {
    "Vehicles": ["car", "motorcycle", "bus", "truck", "bicycle"],
    "Pedestrians": ["person"],
    "Portable / Street Objects": [
        "umbrella", "bench", "chair", "dining table", "potted plant", "backpack", "handbag", "suitcase"
    ],
    "Roadside Fixtures": ["traffic light", "fire hydrant", "stop sign", "parking meter"]
}

UNSUPPORTED_SPECIALIZED_CLASSES = [
    {
        "class_name": "Street Vendor Pushcart / Hawker Stall",
        "reason": (
            "Standard COCO-80 YOLOv5n does not include a 'pushcart' or 'vendor_stall' class. "
            "It can only detect associated COCO objects such as 'person', 'umbrella' (canopy), 'bench', 'chair', or 'dining table'."
        ),
        "requirement": "Requires fine-tuning YOLO on a custom urban street-vending dataset (e.g., 1,500+ annotated pushcart/stall images)."
    },
    {
        "class_name": "Construction Material (Bricks, Sand, Gravel, Cement Bags)",
        "reason": "Standard COCO-80 YOLOv5n has no class for loose aggregate mounds, bricks, or construction material.",
        "requirement": "Requires custom annotated training data for municipal construction material and aggregate stockpiles."
    },
    {
        "class_name": "Roadside Debris / Rubble / Garbage Dump",
        "reason": "Standard COCO-80 YOLOv5n has no class for municipal solid waste, rubble piles, or litter dumps.",
        "requirement": "Requires training on datasets such as TACO (Trash Annotations in Context) + Indian municipal waste imagery."
    },
    {
        "class_name": "Commercial A-Frame Signboard / Shopboard",
        "reason": "COCO-80 includes 'stop sign' and 'traffic light', but not portable commercial sidewalk signboards or banners.",
        "requirement": "Requires custom annotation of retail sidewalk signage and A-frame boards."
    },
    {
        "class_name": "Unauthorized Shop Counter Extension",
        "reason": "COCO-80 cannot distinguish a building's legal property line from an extended shop counter.",
        "requirement": "Requires custom storefront encroachment training data combined with parcel/curb segmentation."
    }
]


def compute_iou(boxA: List[int], boxB: List[int]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = float(interW * interH)
    if interArea <= 0:
        return 0.0
    areaA = float(boxA[2] * boxA[3])
    areaB = float(boxB[2] * boxB[3])
    return interArea / max(1.0, areaA + areaB - interArea)


class ObjectDetector:
    """
    Pretrained YOLOv5n ONNX Object Detection Module (Stage 1: Pure Object Detection).
    - Uses ONLY real neural network predictions from `yolov5n.onnx` via OpenCV DNN.
    - Never fabricates bounding boxes, never hardcodes confidence values, and never guesses
      labels from pixel location or color heuristics.
    - Does NOT classify encroachments directly; encroachment analysis is strictly separated
      into `EncroachmentEngine`.
    - If model weights cannot be loaded, raises an explicit `RuntimeError` (or returns an
      explicitly labeled `DEMO_MODE_WEIGHTS_UNAVAILABLE` status if `allow_demo_mode=True`).
    """

    def __init__(self, weights_path: Optional[str] = None):
        from app.config import settings
        configured_path = getattr(settings, "YOLO_WEIGHTS_PATH", None)
        if configured_path and os.path.exists(configured_path):
            self.default_weights_path = configured_path
        else:
            self.default_weights_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "weights", "yolov5n.onnx")
            )
        self.weights_path = weights_path or self.default_weights_path
        self.net = None
        self.yolo_loaded = False
        self.load_error: Optional[str] = None
        self.confidence_threshold = 0.25
        self.nms_threshold = 0.45
        self.load_weights(self.weights_path)

    def load_weights(self, weights_path: Optional[str] = None) -> bool:
        """
        Loads (or reloads) the YOLOv5n ONNX model weights.
        Records exact error details if weights are missing or corrupt.
        """
        target_path = weights_path or self.default_weights_path
        self.weights_path = target_path
        if not os.path.exists(target_path):
            self.net = None
            self.yolo_loaded = False
            self.load_error = f"Model weights file not found at '{target_path}'."
            return False

        try:
            net = cv2.dnn.readNetFromONNX(target_path)
            self.net = net
            self.yolo_loaded = True
            self.load_error = None
            return True
        except Exception as e:
            self.net = None
            self.yolo_loaded = False
            self.load_error = f"OpenCV DNN failed to load ONNX weights '{target_path}': {str(e)}"
            return False

    def _map_coco_class(self, coco_label: str) -> Tuple[str, str]:
        """
        Maps a raw COCO-80 class name to its honest functional category and display label,
        preserving the exact underlying COCO class name without guessing unsupported classes.
        """
        if coco_label in SUPPORTED_URBAN_COCO_CLASSES["Vehicles"]:
            return "Vehicle", f"Vehicle ({coco_label})"
        if coco_label == "person":
            return "Pedestrian", "Pedestrian (person)"
        if coco_label in SUPPORTED_URBAN_COCO_CLASSES["Portable / Street Objects"]:
            return "Street Object", f"Street Object ({coco_label})"
        if coco_label in SUPPORTED_URBAN_COCO_CLASSES["Roadside Fixtures"]:
            return "Street Fixture", f"Street Fixture ({coco_label})"
        return "Other COCO Object", f"COCO Object ({coco_label})"

    def detect(
        self,
        image: np.ndarray,
        allow_demo_mode: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Runs YOLOv5n-ONNX inference on `image`.
        Returns `(detections, detection_metadata)`.
        - If weights are not loaded and `allow_demo_mode=False`, raises `RuntimeError`.
        - If weights are not loaded and `allow_demo_mode=True`, returns `([], metadata)` with
          explicit demo/unloaded status and zero fabricated boxes.
        """
        if not self.yolo_loaded or self.net is None:
            if not allow_demo_mode:
                raise RuntimeError(
                    f"AI Model Loading Failure: Pretrained YOLOv5n ONNX model is unavailable. "
                    f"Reason: {self.load_error or 'Weights not loaded.'}"
                )
            return [], {
                "model_status": "DEMO_MODE_WEIGHTS_UNAVAILABLE",
                "yolo_onnx_active": False,
                "is_demo_mode": True,
                "is_mock": True,
                "load_error": self.load_error,
                "yolo_weights": "Unavailable (Demo Mode)",
                "yolo_detections_count": 0,
                "supported_coco_classes": SUPPORTED_URBAN_COCO_CLASSES,
                "unsupported_specialized_classes": UNSUPPORTED_SPECIALIZED_CLASSES,
                "engine_summary": "Model Unavailable — Explicit Demo Mode (0 Predictions)"
            }

        h, w = image.shape[:2]
        blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (640, 640), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward()
        preds = outputs[0]

        boxes: List[List[int]] = []
        confidences: List[float] = []
        class_ids: List[int] = []

        x_factor = w / 640.0
        y_factor = h / 640.0

        for row in preds:
            obj_conf = float(row[4])
            if obj_conf >= self.confidence_threshold:
                scores = row[5:]
                class_id = int(np.argmax(scores))
                score = float(obj_conf * scores[class_id])
                if score >= self.confidence_threshold:
                    cx, cy, bw, bh = float(row[0]), float(row[1]), float(row[2]), float(row[3])
                    left = max(0, int(round((cx - 0.5 * bw) * x_factor)))
                    top = max(0, int(round((cy - 0.5 * bh) * y_factor)))
                    width = min(w - left, max(1, int(round(bw * x_factor))))
                    height = min(h - top, max(1, int(round(bh * y_factor))))
                    boxes.append([left, top, width, height])
                    confidences.append(score)
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
        yolo_detections: List[Dict[str, Any]] = []

        if len(indices) > 0:
            for i in indices.flatten():
                cid = int(class_ids[i])
                coco_name = COCO_CLASSES[cid] if 0 <= cid < len(COCO_CLASSES) else f"class_{cid}"
                bx, by, bw, bh = boxes[i]
                exact_conf = round(float(confidences[i]), 4)
                category, display_label = self._map_coco_class(coco_name)

                yolo_detections.append({
                    "id": f"yolo_{uuid.uuid4().hex[:6]}",
                    "coco_class": coco_name,
                    "raw_coco_class": coco_name,
                    "category": category,
                    "type": category,
                    "label": display_label,
                    "sub_label": display_label,
                    "confidence": exact_conf,
                    "bbox": [int(bx), int(by), int(bw), int(bh)],
                    "bbox_area_px": int(bw * bh),
                    "prediction_source": "YOLOv5n-ONNX (Pretrained COCO-80 Model)",
                    "is_mock": False
                })

        metadata = {
            "model_status": "LOADED_AND_ACTIVE",
            "yolo_onnx_active": True,
            "is_demo_mode": False,
            "is_mock": False,
            "load_error": None,
            "yolo_weights": "yolov5n.onnx (Pretrained COCO-80 via OpenCV 5.0 DNN)",
            "confidence_threshold": self.confidence_threshold,
            "nms_threshold": self.nms_threshold,
            "yolo_detections_count": len(yolo_detections),
            "supported_coco_classes": SUPPORTED_URBAN_COCO_CLASSES,
            "unsupported_specialized_classes": UNSUPPORTED_SPECIALIZED_CLASSES,
            "engine_summary": "Pretrained YOLOv5n-ONNX (COCO-80 Real Predictions Only)"
        }

        return yolo_detections, metadata


detector = ObjectDetector()
