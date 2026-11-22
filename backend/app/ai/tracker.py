import cv2
import numpy as np
import os
import math
from typing import List, Dict, Any
from app.ai.detector import detector, compute_iou
from app.ai.segmentor import segmentor
from app.ai.encroachment_engine import encroachment_engine


class PersistentTracker:
    """
    Real Frame-Sampling & Multi-Object IoU/Centroid Video Tracker.
    - Processes actual video frames via `cv2.VideoCapture` and `detector.detect(frame)` (YOLOv5n-ONNX).
    - Never fabricates simulated video tracks or hardcoded confidence values.
    - If a video stream cannot be decoded by OpenCV or lacks sufficient duration, returns an
      honest, explicit status (`UNSUPPORTED_OR_UNREADABLE_VIDEO` or `COMPLETED_CLIP_SHORTER_THAN_THRESHOLD`).
    """

    PERSISTENCE_THRESHOLD_SEC = 3.0  # Minimum continuous stationary presence (seconds)

    def process_video(self, video_path: str) -> Dict[str, Any]:
        if not video_path or not os.path.exists(video_path):
            raise ValueError(f"Video file not found at path: {video_path}")

        if os.path.getsize(video_path) == 0:
            raise ValueError("Uploaded video file is empty (0 bytes).")

        if not detector.yolo_loaded:
            raise RuntimeError(
                f"AI Model Loading Failure: Cannot process video because YOLOv5n-ONNX weights are not loaded ({detector.load_error})."
            )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            return {
                "processing_status": "UNSUPPORTED_OR_UNREADABLE_VIDEO",
                "is_simulated": False,
                "status_explanation": (
                    "OpenCV VideoCapture could not open or decode the uploaded file. "
                    "Ensure the file is a valid MP4/AVI container with a supported video codec."
                ),
                "total_duration_sec": 0.0,
                "duration_formatted": "00:00",
                "frames_decoded": 0,
                "frames_analyzed": 0,
                "persistent_obstructions": [],
                "all_tracks": [],
                "temporary_movements_count": 0,
                "incident_triggered": False
            }

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0.1 or math.isnan(fps):
            fps = 25.0

        ret, first_frame = cap.read()
        if not ret or first_frame is None:
            cap.release()
            return {
                "processing_status": "UNSUPPORTED_OR_UNREADABLE_VIDEO",
                "is_simulated": False,
                "status_explanation": (
                    "Video container opened, but zero video frames could be decoded by OpenCV."
                ),
                "total_duration_sec": 0.0,
                "duration_formatted": "00:00",
                "frames_decoded": 0,
                "frames_analyzed": 0,
                "persistent_obstructions": [],
                "all_tracks": [],
                "temporary_movements_count": 0,
                "incident_triggered": False
            }

        h, w = first_frame.shape[:2]
        _, geom_data = segmentor.segment(first_frame)

        # Sample ~2 frames per second up to 60 seconds
        sample_step = max(1, int(round(fps / 2.0)))
        max_frames_to_read = int(round(fps * 60.0))

        tracks: List[Dict[str, Any]] = []
        next_track_id = 1
        frame_idx = 0
        frames_analyzed = 0

        # Process first_frame at frame_idx = 0 and continue reading
        current_frame = first_frame
        while current_frame is not None and frame_idx < max_frames_to_read:
            if frame_idx % sample_step == 0:
                timestamp_sec = round(frame_idx / fps, 2)
                raw_dets, _ = detector.detect(current_frame)
                proc_dets, _ = encroachment_engine.analyze(raw_dets, geom_data)
                frames_analyzed += 1

                matched_track_ids = set()
                for det in proc_dets:
                    bx, by, bw, bh = det["bbox"]
                    cx = bx + bw / 2.0
                    cy = by + bh / 2.0

                    best_track = None
                    best_score = -1.0

                    for trk in tracks:
                        if trk["id"] in matched_track_ids:
                            continue
                        if trk["coco_class"] != det["coco_class"]:
                            continue
                        # Match only if seen within the last 2.5 seconds
                        if (timestamp_sec - trk["last_seen_sec"]) > 2.5:
                            continue

                        iou = compute_iou(trk["last_bbox"], det["bbox"])
                        last_cx, last_cy = trk["centroids"][-1]
                        dist_px = math.hypot(cx - last_cx, cy - last_cy)
                        norm_dist = dist_px / max(1.0, float(w))

                        if iou >= 0.25 or norm_dist <= 0.12:
                            score = iou + (1.0 - min(1.0, norm_dist))
                            if score > best_score:
                                best_score = score
                                best_track = trk

                    if best_track is not None:
                        matched_track_ids.add(best_track["id"])
                        best_track["last_seen_sec"] = timestamp_sec
                        best_track["frames_seen"] += 1
                        best_track["last_bbox"] = det["bbox"]
                        best_track["confidences"].append(float(det["confidence"]))
                        best_track["classifications"].append(det["classification"])
                        best_track["footpath_overlaps"].append(float(det["footpath_overlap_pct"]))
                        best_track["centroids"].append((cx, cy))
                    else:
                        trk_id_str = f"trk_{next_track_id:03d}"
                        next_track_id += 1
                        matched_track_ids.add(trk_id_str)
                        tracks.append({
                            "id": trk_id_str,
                            "coco_class": det["coco_class"],
                            "category": det["category"],
                            "label": det["label"],
                            "first_seen_sec": timestamp_sec,
                            "last_seen_sec": timestamp_sec,
                            "frames_seen": 1,
                            "last_bbox": det["bbox"],
                            "confidences": [float(det["confidence"])],
                            "classifications": [det["classification"]],
                            "footpath_overlaps": [float(det["footpath_overlap_pct"])],
                            "centroids": [(cx, cy)]
                        })

            frame_idx += 1
            ret, next_f = cap.read()
            current_frame = next_f if ret else None

        cap.release()

        total_duration_sec = round(frame_idx / fps, 2)
        mins = int(total_duration_sec // 60)
        secs = int(round(total_duration_sec % 60))
        duration_str = f"{mins:02d}:{secs:02d} ({total_duration_sec}s)"

        persistent_obstructions: List[Dict[str, Any]] = []
        summarized_tracks: List[Dict[str, Any]] = []
        temporary_movements_count = 0

        for trk in tracks:
            obs_duration = round(trk["last_seen_sec"] - trk["first_seen_sec"], 2)
            mean_conf = round(float(np.mean(trk["confidences"])), 4)
            mean_fp_overlap = round(float(np.mean(trk["footpath_overlaps"])), 1)

            # Calculate maximum displacement from initial centroid
            c0_x, c0_y = trk["centroids"][0]
            max_disp_px = max(math.hypot(cx - c0_x, cy - c0_y) for cx, cy in trk["centroids"])
            is_stationary = max_disp_px <= (0.12 * w)

            # Determine dominant classification across frames
            if "Potential encroachment" in trk["classifications"]:
                dom_class = "Potential encroachment"
            elif "Needs human review" in trk["classifications"]:
                dom_class = "Needs human review"
            else:
                dom_class = "Not an encroachment"

            is_persistent_obstruction = (
                is_stationary
                and obs_duration >= self.PERSISTENCE_THRESHOLD_SEC
                and dom_class in ("Potential encroachment", "Needs human review")
            )

            if not is_stationary or obs_duration < self.PERSISTENCE_THRESHOLD_SEC:
                temporary_movements_count += 1

            t_mins = int(obs_duration // 60)
            t_secs = int(round(obs_duration % 60))
            obs_dur_str = f"{t_mins:02d}:{t_secs:02d} ({obs_duration}s)"

            track_summary = {
                "object_id": trk["id"],
                "coco_class": trk["coco_class"],
                "category": trk["category"],
                "label": trk["label"],
                "start_time_sec": trk["first_seen_sec"],
                "end_time_sec": trk["last_seen_sec"],
                "duration_sec": obs_duration,
                "duration_formatted": obs_dur_str,
                "frames_observed": trk["frames_seen"],
                "max_displacement_px": round(max_disp_px, 1),
                "is_stationary": is_stationary,
                "is_persistent": is_persistent_obstruction,
                "classification": dom_class,
                "footpath_overlap_pct": mean_fp_overlap,
                "status": (
                    f"Persistent Stationary ({dom_class})"
                    if is_persistent_obstruction
                    else ("Transient / Moving Object" if not is_stationary else "Short Duration (< 3.0s)")
                ),
                "confidence": mean_conf,
                "recommended_action": "Needs Human Review / Create Incident" if is_persistent_obstruction else "Ignore (Transient)"
            }
            summarized_tracks.append(track_summary)
            if is_persistent_obstruction:
                persistent_obstructions.append(track_summary)

        if total_duration_sec < self.PERSISTENCE_THRESHOLD_SEC:
            status_code = "COMPLETED_CLIP_SHORTER_THAN_THRESHOLD"
            status_explanation = (
                f"Processed {frames_analyzed} sampled frames across {total_duration_sec}s ({frame_idx} total frames). "
                f"Clip duration ({total_duration_sec}s) is shorter than the {self.PERSISTENCE_THRESHOLD_SEC}s persistence threshold."
            )
        else:
            status_code = "COMPLETED"
            status_explanation = (
                f"Processed {frames_analyzed} sampled frames across {total_duration_sec}s ({frame_idx} total frames) "
                f"using real YOLOv5n-ONNX inference and IoU/centroid tracking."
            )

        return {
            "processing_status": status_code,
            "is_simulated": False,
            "status_explanation": status_explanation,
            "persistence_threshold_sec": self.PERSISTENCE_THRESHOLD_SEC,
            "total_duration_sec": total_duration_sec,
            "duration_formatted": duration_str,
            "frames_decoded": frame_idx,
            "frames_analyzed": frames_analyzed,
            "persistent_obstructions": persistent_obstructions,
            "all_tracks": summarized_tracks,
            "temporary_movements_count": temporary_movements_count,
            "incident_triggered": len(persistent_obstructions) > 0
        }


tracker = PersistentTracker()
