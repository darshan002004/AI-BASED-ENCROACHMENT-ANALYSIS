"""
EncroWatch AI — Multi-Stage Deep Learning & Risk Assessment Framework
=====================================================================

Academic Research Implementation:
"A Multi-Stage Deep Learning Framework for Urban Footpath Encroachment Detection,
 Accessibility Assessment, and Risk-Aware Monitoring"

Candidate Level: MCA Final-Year Major Academic Research
Hardware Optimization: NVIDIA GeForce RTX 2050 (4 GB VRAM)
Software Stack: Python 3.12, PyTorch 2.6, Shapely 2.0, NumPy

Pipeline Stages:
  Stage A: Object Detection (8 Classes)
  Stage B: Spatial Segmentation (Footpath Surface Polygon & Roadway Boundary)
  Stage C: Ground-Contact Geometric Analysis (Lower 40% Proxy & Polygon Overlap)
  Stage D: Temporal Tracking (Persistent Association across Frames)
  Stage E: Temporal Persistence Filtering (Transient vs Persistent Classification)
  Stage F: Physical Accessibility Assessment (IRC:103-2012 Clearance & LOS Grading)
  Stage G: Explainable Decomposable Risk Scoring (0–100 Multi-Criteria Index)
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Any
import json
import numpy as np
from shapely.geometry import Polygon, box, mapping
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Class Hazard Severity Weights (Domain Knowledge from Municipal By-laws & IRC)
# ---------------------------------------------------------------------------
CLASS_HAZARD_WEIGHTS: Dict[str, float] = {
    "permanent_structure": 100.0,
    "construction_material": 90.0,
    "shop_extension": 80.0,
    "vendor_cart": 75.0,
    "parked_motorcycle": 70.0,
    "debris": 65.0,
    "parked_bicycle": 50.0,
    "tree_pole": 40.0,
}

CLASS_NAME_TO_ID: Dict[str, int] = {
    "construction_material": 0,
    "debris": 1,
    "parked_bicycle": 2,
    "parked_motorcycle": 3,
    "permanent_structure": 4,
    "shop_extension": 5,
    "tree_pole": 6,
    "vendor_cart": 7,
}

ID_TO_CLASS_NAME: Dict[int, str] = {v: k for k, v in CLASS_NAME_TO_ID.items()}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------
@dataclass
class BoundingBox:
    """Represents a standard bounding box in pixel coordinates [x_min, y_min, x_max, y_max]."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0)

    def to_shapely(self) -> Polygon:
        return box(self.x_min, self.y_min, self.x_max, self.y_max)

    def ground_contact_proxy(self, bottom_ratio: float = 0.40) -> Polygon:
        """
        Stage C: Ground-Contact Proxy Heuristic.
        Approximates the ground-level physical footprint from a 2D bounding box
        by taking the bottom 40% vertical slice:
        [x_min, y_max - 0.40 * h, x_max, y_max]
        This eliminates air-space false positives (e.g., awnings, canopies, handle-bars).
        """
        proxy_y_min = self.y_max - (bottom_ratio * self.height)
        return box(self.x_min, proxy_y_min, self.x_max, self.y_max)


@dataclass
class Detection:
    """Stage A detection record."""
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None
    custom_footprint: Optional[Polygon] = None


@dataclass
class FootpathSurface:
    """Stage B spatial surface representation."""
    polygon: Polygon
    nominal_width_m: float = 1.80       # Target clearance per IRC:103-2012
    pixels_per_meter: float = 100.0     # Calibrated spatial scale factor

    @property
    def area_sq_m(self) -> float:
        return self.polygon.area / (self.pixels_per_meter ** 2)


@dataclass
class TrackState:
    """Stage D & E temporal tracking and persistence representation."""
    track_id: int
    class_name: str
    first_frame: int
    last_frame: int
    consecutive_hits: int = 1
    total_frames_observed: int = 1
    centroid_history: List[Tuple[float, float]] = field(default_factory=list)
    last_bbox: Optional[BoundingBox] = None
    fps: float = 10.0

    @property
    def duration_seconds(self) -> float:
        return self.total_frames_observed / max(1.0, self.fps)

    @property
    def persistence_category(self) -> str:
        """Categorize into Transient, Short-term, or Persistent."""
        tau = self.duration_seconds
        if tau < 3.0:
            return "TRANSIENT"       # Under 3s: transitory pedestrian or momentary bicycle
        elif tau < 10.0:
            return "SHORT_TERM"      # 3s to 10s: loading, momentary halt
        else:
            return "PERSISTENT"      # >= 10s: genuine stationary encroachment


@dataclass
class AccessibilityMetric:
    """Stage F accessibility and clearance calculation."""
    nominal_width_m: float
    effective_clear_width_m: float
    clearance_deficit_m: float
    width_reduction_pct: float
    level_of_service: str            # LOS A through LOS E
    wheelchair_accessible: bool      # True if clear width >= 1.20 m
    irc_compliant: bool              # True if clear width >= 1.80 m


@dataclass
class RiskDecomposition:
    """Stage G explainable risk index decomposition."""
    class_hazard_component: float       # H_i * w_h
    ground_overlap_component: float     # O_i * w_o
    persistence_component: float        # P_i * w_p
    accessibility_component: float      # A_i * w_a
    total_risk_score: float             # Sum in [0, 100]
    risk_tier: str                      # LOW, MODERATE, HIGH, CRITICAL
    rationale: str                      # Human-readable justification


@dataclass
class EncroachmentIncident:
    """Final unified incident report produced by the Multi-Stage Framework."""
    incident_id: str
    frame_id: int
    track_id: int
    class_name: str
    confidence: float
    ground_overlap_ratio: float
    persistence_seconds: float
    persistence_category: str
    accessibility: AccessibilityMetric
    risk: RiskDecomposition


# ---------------------------------------------------------------------------
# Core Analytical Engines
# ---------------------------------------------------------------------------
class GroundContactAnalyzer:
    """Stage C: Geometric Footprint Intersection."""

    @staticmethod
    def compute_ground_contact(
        detection: Detection,
        footpath: FootpathSurface,
        bottom_ratio: float = 0.40
    ) -> Tuple[float, Polygon]:
        """
        Computes the ratio of ground contact footprint overlapping the footpath.
        Returns:
            (overlap_ratio in [0.0, 1.0], intersection_polygon)
        """
        if detection.custom_footprint is not None:
            contact_geom = detection.custom_footprint
        else:
            contact_geom = detection.bbox.ground_contact_proxy(bottom_ratio)

        if not contact_geom.is_valid:
            contact_geom = contact_geom.buffer(0)

        if not footpath.polygon.is_valid:
            footpath_poly = footpath.polygon.buffer(0)
        else:
            footpath_poly = footpath.polygon

        if contact_geom.area <= 0.0:
            return 0.0, Polygon()

        intersection = contact_geom.intersection(footpath_poly)
        overlap_ratio = float(intersection.area / contact_geom.area)
        return min(1.0, max(0.0, overlap_ratio)), intersection


class AccessibilityEngine:
    """Stage F: Accessibility Assessment based on Indian Road Congress IRC:103-2012."""

    IRC_RECOMMENDED_WIDTH_M: float = 1.80
    WHEELCHAIR_MINIMUM_WIDTH_M: float = 1.20

    @classmethod
    def evaluate_clearance(
        cls,
        nominal_width_m: float,
        lateral_occlusion_m: float
    ) -> AccessibilityMetric:
        """
        Calculates effective clear width and assigns IRC Level of Service (LOS).
        LOS Grades:
            LOS A: >= 1.80 m (Full IRC compliance, unimpeded bi-directional flow)
            LOS B: 1.50 - 1.79 m (Minor constraint, adequate for single wheelchair + pedestrian)
            LOS C: 1.20 - 1.49 m (Bare wheelchair threshold, passing requires deceleration)
            LOS D: 0.90 - 1.19 m (Severely constricted, sub-standard wheelchair passage)
            LOS E: < 0.90 m (Wheelchair completely obstructed, pedestrians forced into roadway)
        """
        effective_clear = max(0.0, nominal_width_m - lateral_occlusion_m)
        deficit = max(0.0, cls.IRC_RECOMMENDED_WIDTH_M - effective_clear)
        reduction_pct = (lateral_occlusion_m / max(0.01, nominal_width_m)) * 100.0

        if effective_clear >= 1.80:
            los = "LOS A"
        elif effective_clear >= 1.50:
            los = "LOS B"
        elif effective_clear >= 1.20:
            los = "LOS C"
        elif effective_clear >= 0.90:
            los = "LOS D"
        else:
            los = "LOS E"

        wheelchair_ok = effective_clear >= cls.WHEELCHAIR_MINIMUM_WIDTH_M
        irc_ok = effective_clear >= cls.IRC_RECOMMENDED_WIDTH_M

        return AccessibilityMetric(
            nominal_width_m=round(nominal_width_m, 2),
            effective_clear_width_m=round(effective_clear, 2),
            clearance_deficit_m=round(deficit, 2),
            width_reduction_pct=round(reduction_pct, 1),
            level_of_service=los,
            wheelchair_accessible=wheelchair_ok,
            irc_compliant=irc_ok,
        )


class ExplainableRiskEngine:
    """Stage G: Explainable Decomposable Multi-Criteria Risk Scoring."""

    # Weights summing to 1.0
    W_HAZARD: float = 0.30
    W_OVERLAP: float = 0.25
    W_PERSISTENCE: float = 0.20
    W_ACCESSIBILITY: float = 0.25

    @classmethod
    def calculate_risk(
        cls,
        class_name: str,
        overlap_ratio: float,
        duration_seconds: float,
        clearance_deficit_m: float,
        nominal_width_m: float,
    ) -> RiskDecomposition:
        """
        Computes a strictly explainable Risk Score in [0, 100] via:
            Risk = w_h * H + w_o * O + w_p * P + w_a * A
        where each component is normalized to [0, 100].
        """
        # 1. Class Hazard Severity (0 - 100)
        h_score = CLASS_HAZARD_WEIGHTS.get(class_name, 50.0)

        # 2. Footpath Ground Contact Overlap (0 - 100)
        o_score = overlap_ratio * 100.0

        # 3. Temporal Persistence (0 - 100): Saturates at 10.0 seconds
        p_score = min(100.0, (duration_seconds / 10.0) * 100.0)

        # 4. Accessibility Clearance Deficit (0 - 100): Normalized to nominal width
        a_score = min(100.0, (clearance_deficit_m / max(0.1, nominal_width_m)) * 100.0)

        # Weighted components
        c_hazard = cls.W_HAZARD * h_score
        c_overlap = cls.W_OVERLAP * o_score
        c_persistence = cls.W_PERSISTENCE * p_score
        c_accessibility = cls.W_ACCESSIBILITY * a_score

        total_risk = round(c_hazard + c_overlap + c_persistence + c_accessibility, 2)

        # Risk Tier
        if total_risk >= 75.0:
            tier = "CRITICAL"
        elif total_risk >= 50.0:
            tier = "HIGH"
        elif total_risk >= 25.0:
            tier = "MODERATE"
        else:
            tier = "LOW"

        rationale = (
            f"Class '{class_name}' ({h_score:.0f} pts) contributes {c_hazard:.1f} pts; "
            f"Ground overlap ({o_score:.1f}%) contributes {c_overlap:.1f} pts; "
            f"Persistence ({duration_seconds:.1f}s, sat {p_score:.1f}%) contributes {c_persistence:.1f} pts; "
            f"Accessibility deficit ({clearance_deficit_m:.2f}m) contributes {c_accessibility:.1f} pts. "
            f"Assigned Tier: {tier} ({total_risk}/100)."
        )

        return RiskDecomposition(
            class_hazard_component=round(c_hazard, 2),
            ground_overlap_component=round(c_overlap, 2),
            persistence_component=round(c_persistence, 2),
            accessibility_component=round(c_accessibility, 2),
            total_risk_score=total_risk,
            risk_tier=tier,
            rationale=rationale,
        )


class SimpleTemporalTracker:
    """Stage D: Multi-Object Association across Video Frames."""

    def __init__(self, iou_threshold: float = 0.30, max_disappeared: int = 15, fps: float = 10.0):
        self.iou_threshold = iou_threshold
        self.max_disappeared = max_disappeared
        self.fps = fps
        self.next_track_id = 1
        self.tracks: Dict[int, TrackState] = {}
        self.disappeared: Dict[int, int] = {}

    def update(self, frame_id: int, detections: List[Detection]) -> List[Detection]:
        """Associates incoming detections to active tracks via 2D bounding box IoU."""
        if len(self.tracks) == 0:
            for det in detections:
                t_id = self.next_track_id
                self.next_track_id += 1
                det.track_id = t_id
                self.tracks[t_id] = TrackState(
                    track_id=t_id,
                    class_name=det.class_name,
                    first_frame=frame_id,
                    last_frame=frame_id,
                    consecutive_hits=1,
                    total_frames_observed=1,
                    centroid_history=[det.bbox.center],
                    last_bbox=det.bbox,
                    fps=self.fps,
                )
                self.disappeared[t_id] = 0
            return detections

        track_ids = list(self.tracks.keys())
        if len(detections) == 0:
            for t_id in track_ids:
                self.disappeared[t_id] += 1
                if self.disappeared[t_id] > self.max_disappeared:
                    del self.tracks[t_id]
                    del self.disappeared[t_id]
            return []

        # Compute IoU matrix between existing track last_bbox and current detections
        iou_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)
        for i, t_id in enumerate(track_ids):
            prev_poly = self.tracks[t_id].last_bbox.to_shapely()
            for j, det in enumerate(detections):
                curr_poly = det.bbox.to_shapely()
                if prev_poly.intersects(curr_poly):
                    inter_area = prev_poly.intersection(curr_poly).area
                    union_area = prev_poly.area + curr_poly.area - inter_area
                    iou_matrix[i, j] = inter_area / max(1e-6, union_area)

        assigned_tracks = set()
        assigned_dets = set()

        # Greedy match based on max IoU
        while True:
            max_iou = np.max(iou_matrix) if iou_matrix.size > 0 else 0.0
            if max_iou < self.iou_threshold:
                break
            i, j = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
            t_id = track_ids[i]
            detections[j].track_id = t_id

            # Update track
            track = self.tracks[t_id]
            track.last_frame = frame_id
            track.total_frames_observed += 1
            track.consecutive_hits += 1
            track.last_bbox = detections[j].bbox
            track.centroid_history.append(detections[j].bbox.center)
            self.disappeared[t_id] = 0

            assigned_tracks.add(t_id)
            assigned_dets.add(j)
            iou_matrix[i, :] = -1.0
            iou_matrix[:, j] = -1.0

        # Unmatched tracks
        for t_id in track_ids:
            if t_id not in assigned_tracks:
                self.disappeared[t_id] += 1
                if self.disappeared[t_id] > self.max_disappeared:
                    del self.tracks[t_id]
                    del self.disappeared[t_id]

        # Unmatched detections -> spawn new tracks
        for j, det in enumerate(detections):
            if j not in assigned_dets:
                t_id = self.next_track_id
                self.next_track_id += 1
                det.track_id = t_id
                self.tracks[t_id] = TrackState(
                    track_id=t_id,
                    class_name=det.class_name,
                    first_frame=frame_id,
                    last_frame=frame_id,
                    consecutive_hits=1,
                    total_frames_observed=1,
                    centroid_history=[det.bbox.center],
                    last_bbox=det.bbox,
                    fps=self.fps,
                )
                self.disappeared[t_id] = 0

        return detections


class MultiStageEncroachmentPipeline:
    """Master Orchestrator connecting Stages A through G."""

    def __init__(self, nominal_footpath_width_m: float = 1.80, pixels_per_meter: float = 100.0, fps: float = 10.0):
        self.nominal_footpath_width_m = nominal_footpath_width_m
        self.pixels_per_meter = pixels_per_meter
        self.tracker = SimpleTemporalTracker(fps=fps)
        self.incident_log: List[EncroachmentIncident] = []

    def process_frame(
        self,
        frame_id: int,
        detections: List[Detection],
        footpath_surface: FootpathSurface
    ) -> List[EncroachmentIncident]:
        """
        Executes end-to-end framework analysis on a single video frame.
        """
        # Stage D: Temporal Tracking update
        tracked_detections = self.tracker.update(frame_id, detections)
        frame_incidents: List[EncroachmentIncident] = []

        for det in tracked_detections:
            track = self.tracker.tracks[det.track_id]

            # Stage C: Ground-contact intersection analysis
            overlap_ratio, _ = GroundContactAnalyzer.compute_ground_contact(
                detection=det,
                footpath=footpath_surface,
                bottom_ratio=0.40
            )

            # If obstacle does not contact the footpath ground surface, skip or mark air clearance
            if overlap_ratio < 0.05:
                continue

            # Stage E: Temporal persistence classification
            tau = track.duration_seconds
            pers_cat = track.persistence_category

            # Stage F: Accessibility clearance calculation
            # Lateral occlusion in meters (estimated from proxy ground contact box width)
            lateral_occlusion_m = det.bbox.width / footpath_surface.pixels_per_meter
            # Bounded by nominal footpath width
            lateral_occlusion_m = min(lateral_occlusion_m, footpath_surface.nominal_width_m)

            accessibility = AccessibilityEngine.evaluate_clearance(
                nominal_width_m=footpath_surface.nominal_width_m,
                lateral_occlusion_m=lateral_occlusion_m
            )

            # Stage G: Explainable Risk Scoring
            risk = ExplainableRiskEngine.calculate_risk(
                class_name=det.class_name,
                overlap_ratio=overlap_ratio,
                duration_seconds=tau,
                clearance_deficit_m=accessibility.clearance_deficit_m,
                nominal_width_m=footpath_surface.nominal_width_m
            )

            incident = EncroachmentIncident(
                incident_id=f"INC_{frame_id:05d}_TRK_{det.track_id:03d}",
                frame_id=frame_id,
                track_id=det.track_id,
                class_name=det.class_name,
                confidence=det.confidence,
                ground_overlap_ratio=round(overlap_ratio, 3),
                persistence_seconds=round(tau, 2),
                persistence_category=pers_cat,
                accessibility=accessibility,
                risk=risk,
            )
            frame_incidents.append(incident)
            self.incident_log.append(incident)

        return frame_incidents


# ---------------------------------------------------------------------------
# Self-Verification Simulation Test Harness
# ---------------------------------------------------------------------------
def run_framework_smoke_simulation() -> Dict[str, Any]:
    """Runs a 50-frame synthetic simulation demonstrating all 7 pipeline stages."""
    print("=" * 70)
    print("EncroWatch AI — Multi-Stage Framework Self-Verification Test Harness")
    print("=" * 70)

    # Footpath: rectangular corridor 180 pixels wide x 600 pixels high (1.8m nominal width)
    footpath_poly = Polygon([(100, 0), (280, 0), (280, 600), (100, 600)])
    footpath = FootpathSurface(polygon=footpath_poly, nominal_width_m=1.80, pixels_per_meter=100.0)

    pipeline = MultiStageEncroachmentPipeline(nominal_footpath_width_m=1.80, pixels_per_meter=100.0, fps=10.0)

    # Simulation cases:
    # 1. Parked Motorcycle: persistent, partially encroaching (x: 120-180, width 60px = 0.6m), present frames 1-40 (4.0s)
    # 2. Vendor Cart: persistent, severe encroachment (x: 150-270, width 120px = 1.2m), present frames 1-50 (5.0s)
    # 3. Transitory Bicycle: momentary (frames 10-15 = 0.5s)
    simulation_results = []

    for frame_id in range(1, 51):
        frame_dets = []

        # Motorcycle (active frames 1 to 40)
        if 1 <= frame_id <= 40:
            frame_dets.append(Detection(
                class_id=3,
                class_name="parked_motorcycle",
                confidence=0.88,
                bbox=BoundingBox(x_min=120.0, y_min=200.0, x_max=180.0, y_max=320.0)
            ))

        # Vendor Cart (active frames 1 to 50)
        if 1 <= frame_id <= 50:
            frame_dets.append(Detection(
                class_id=7,
                class_name="vendor_cart",
                confidence=0.92,
                bbox=BoundingBox(x_min=150.0, y_min=350.0, x_max=270.0, y_max=500.0)
            ))

        # Transitory Bicycle (active frames 10 to 15)
        if 10 <= frame_id <= 15:
            frame_dets.append(Detection(
                class_id=2,
                class_name="parked_bicycle",
                confidence=0.74,
                bbox=BoundingBox(x_min=200.0, y_min=50.0, x_max=240.0, y_max=110.0)
            ))

        incidents = pipeline.process_frame(frame_id, frame_dets, footpath)
        if frame_id in [1, 15, 30, 50]:
            print(f"\n[Frame {frame_id:02d}] Active Track Incidents ({len(incidents)}):")
            for inc in incidents:
                print(
                    f"  -> Track {inc.track_id} ({inc.class_name}): "
                    f"Dur={inc.persistence_seconds}s [{inc.persistence_category}] | "
                    f"ClearWidth={inc.accessibility.effective_clear_width_m}m [{inc.accessibility.level_of_service}] | "
                    f"Risk={inc.risk.total_risk_score} [{inc.risk.risk_tier}]"
                )

    # Assertions for verification
    # Vendor cart should reach 5.0 seconds duration, LOS D or E, and High/Critical risk
    vendor_cart_final = [inc for inc in pipeline.incident_log if inc.class_name == "vendor_cart" and inc.frame_id == 50][0]
    assert vendor_cart_final.persistence_seconds == 5.0, f"Expected 5.0s, got {vendor_cart_final.persistence_seconds}"
    assert vendor_cart_final.accessibility.effective_clear_width_m <= 0.65, f"Expected clear width <= 0.65m, got {vendor_cart_final.accessibility.effective_clear_width_m}"
    assert vendor_cart_final.accessibility.level_of_service == "LOS E", f"Expected LOS E, got {vendor_cart_final.accessibility.level_of_service}"
    assert vendor_cart_final.risk.total_risk_score >= 60.0, f"Expected high risk score, got {vendor_cart_final.risk.total_risk_score}"

    print("\n" + "=" * 70)
    print("SUCCESS: Multi-Stage Framework mathematical verification assertions PASSED.")
    print("=" * 70)

    return {
        "status": "VERIFIED",
        "total_frames_simulated": 50,
        "total_incidents_recorded": len(pipeline.incident_log),
        "vendor_cart_sample": asdict(vendor_cart_final)
    }


if __name__ == "__main__":
    result = run_framework_smoke_simulation()
    output_path = "results/evaluation/multistage_framework_simulation_output.json"
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Simulation payload written to {output_path}")
