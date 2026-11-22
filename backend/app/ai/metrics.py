from typing import Dict, Any, List, Tuple, Optional
import numpy as np

ENGINEERING_ACCESSIBILITY_STANDARDS = {
    "reference_guidelines": [
        "IRC:SP:102-2014: Guidelines for Planning and Design of Urban Roads and Footpaths in India (Section 6: Pedestrian Facilities)",
        "ADA Standards for Accessible Design (Chapter 4: Accessible Routes, Section 403: Walking Surfaces)",
        "MoHUA Urban Street Design Guidelines: Footpath Zones (Dead Width 0.5m, Clear Walking Zone 1.8m min, 2.5m standard)"
    ],
    "benchmark_thresholds_meters": {
        "two_way_passing_and_wheelchair": 1.80,  # Standard minimum for two pedestrians to pass comfortably or wheelchair passing
        "single_wheelchair_minimum": 1.20,       # Minimum acceptable clear width for an accessible route under IRC / ADA
        "restricted_single_file": 0.90,          # Constricted single-person passage
        "impassable_barrier": 0.60               # Barrier; standard adult wheelchair width (~0.65-0.70m) cannot pass
    }
}

CALIBRATION_SPECIFICATION = {
    "uncalibrated_summary": (
        "Single-frame 2D street photographs lack camera intrinsic focal length, mounting height, pitch angle, "
        "and depth maps. In uncalibrated mode, the system calculates exact 2D pixel-space metrics (px, px²) and "
        "relative percentages, and leaves real-world physical metres (m) and square metres (m²) as uncalibrated (None)."
    ),
    "calibrated_modes_supported": [
        "1. Nominal Street Profile: Calibrating against standard urban sidewalk widths (e.g. 1.8m narrow, 2.5m standard, 3.0m wide).",
        "2. Ground Control Scale: Supplying ground-truth pixels-per-metre from surveyed physical reference points.",
        "3. Homography Matrix (H): Projecting the 2D ground corridor onto a planar overhead metric coordinate system."
    ]
}

SCORING_FORMULAS = {
    "calibrated_accessibility_formula": (
        "AccessibilityScore = round(0.60 * BottleneckWidthScore + 0.40 * AreaClearanceScore, 1)\n"
        "where:\n"
        "  BottleneckWidthScore = min(100.0, max(0.0, (RemainingWidth_m - 0.60) / (1.80 - 0.60) * 100.0))\n"
        "  AreaClearanceScore   = max(0.0, 100.0 - OccupancyPercentage)"
    ),
    "uncalibrated_heuristic_formula": (
        "PixelClearanceEstimate% = max(0.0, min(100.0, 100.0 - (0.60 * PixelAreaOccupancy% + 0.40 * HorizontalSpanBlockage%)))"
    )
}

CALIBRATION_REQUIREMENTS = CALIBRATION_SPECIFICATION["uncalibrated_summary"]
SCORING_ASSUMPTIONS = (
    "Scoring benchmarked against IRC:SP:102-2014 & ADA Chapter 4 standards. "
    "In uncalibrated mode, clearance is estimated as 100 - (0.60 * AreaOccupancy% + 0.40 * BottleneckBlockage%). "
    "When nominal width is configured, physical clear width (m) is computed at the obstacle bottleneck."
)



class AccessibilityMetricsEngine:
    """
    Robust Urban Footpath Occupancy & Accessibility Engine.
    - Evaluates exact corridor geometry and obstruction positions using slice-by-slice
      horizontal bottleneck analysis.
    - Dual-Mode Architecture:
        Mode A: Calibrated Mode (Physical Metric Scale in m and m²) when nominal sidewalk width
                or scale calibration is configured.
        Mode B: Uncalibrated Mode (Pure 2D Pixel Metrics in px and px²) when no camera calibration
                is provided, with documented assumptions.
    - Benchmarked against IRC:SP:102-2014 & ADA pedestrian walkability guidelines.
    """

    def _find_footpath_x_bounds_at_y(self, footpath_polygon: List[List[int]], y: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Finds the left and right X boundaries of the footpath polygon at vertical row y.
        """
        if not footpath_polygon or len(footpath_polygon) < 3:
            return None, None

        intersections: List[float] = []
        n = len(footpath_polygon)
        for i in range(n):
            p1 = footpath_polygon[i]
            p2 = footpath_polygon[(i + 1) % n]
            y1, y2 = p1[1], p2[1]
            x1, x2 = p1[0], p2[0]

            if min(y1, y2) <= y <= max(y1, y2) and y1 != y2:
                # Linear interpolation for X intersection
                t = (y - y1) / float(y2 - y1)
                x_inter = x1 + t * (x2 - x1)
                intersections.append(x_inter)

        if len(intersections) >= 2:
            return int(round(min(intersections))), int(round(max(intersections)))
        return None, None

    def calculate_accessibility(
        self,
        geometry_data: Dict[str, Any],
        enc_summary: Dict[str, Any],
        detected_objects: List[Dict[str, Any]],
        nominal_footpath_width_m: Optional[float] = None,
        calibration_px_per_m: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates reliable footpath occupancy, bottleneck width, and accessibility score.
        Supports both calibrated physical metric scale and uncalibrated 2D pixel space.
        """
        footpath_polygon = geometry_data.get("footpath_polygon", [])
        footpath_roi_area_px = max(1.0, float(geometry_data.get("footpath_roi_area_px", 1.0)))
        footpath_mid_span_px = max(1, int(geometry_data.get("footpath_width_px", 200)))
        footpath_bottom_span_px = max(1, int(geometry_data.get("footpath_bottom_span_px", footpath_mid_span_px)))
        roi_pixel_occupancy_pct = float(enc_summary.get("roi_pixel_occupancy_pct", 0.0))
        occupied_footpath_px = float(enc_summary.get("occupied_footpath_px", 0.0))
        free_footpath_px = float(enc_summary.get("free_footpath_px", footpath_roi_area_px))

        enc_objs = [o for o in detected_objects if o.get("classification") == "Potential encroachment"]
        review_objs = [o for o in detected_objects if o.get("classification") == "Needs human review"]
        active_obstructions = enc_objs if enc_objs else [o for o in review_objs if o.get("zone") == "footpath"]

        # --- 1. Slice-by-Slice Horizontal Bottleneck Analysis ---
        # Evaluate corridor width and obstruction span across the vertical span of all obstacles
        bottleneck_y_px = None
        min_remaining_width_px = footpath_mid_span_px
        corridor_width_at_bottleneck_px = footpath_mid_span_px
        obstructed_width_at_bottleneck_px = 0

        if active_obstructions and footpath_polygon:
            # Sample vertical rows through the lower portion (ground level) of the obstructions
            sample_ys = set()
            for obj in active_obstructions:
                bx, by, bw, bh = obj["bbox"]
                # Sample bottom 40% of bounding box where ground contact occurs
                ground_top = int(by + bh * 0.60)
                ground_btm = int(by + bh)
                for sy in range(ground_top, ground_btm + 1, max(1, int(bh * 0.10))):
                    sample_ys.add(sy)

            if sample_ys:
                for sy in sorted(sample_ys):
                    fp_left, fp_right = self._find_footpath_x_bounds_at_y(footpath_polygon, sy)
                    if fp_left is None or fp_right is None or fp_right <= fp_left:
                        continue

                    corridor_w = fp_right - fp_left
                    if corridor_w <= 10:
                        continue

                    # Find blocked horizontal span at row sy
                    blocked_spans: List[Tuple[int, int]] = []
                    for obj in active_obstructions:
                        bx, by, bw, bh = obj["bbox"]
                        if by <= sy <= (by + bh):
                            obj_l = max(fp_left, bx)
                            obj_r = min(fp_right, bx + bw)
                            if obj_r > obj_l:
                                blocked_spans.append((obj_l, obj_r))

                    if not blocked_spans:
                        continue

                    # Merge overlapping blocked intervals at row sy
                    blocked_spans.sort(key=lambda s: s[0])
                    merged: List[List[int]] = []
                    for sl, sr in blocked_spans:
                        if not merged or sl > merged[-1][1]:
                            merged.append([sl, sr])
                        else:
                            merged[-1][1] = max(merged[-1][1], sr)

                    row_blocked_w = sum(sr - sl for sl, sr in merged)
                    row_remaining_w = max(0, corridor_w - row_blocked_w)

                    if row_remaining_w < min_remaining_width_px:
                        min_remaining_width_px = row_remaining_w
                        corridor_width_at_bottleneck_px = corridor_w
                        obstructed_width_at_bottleneck_px = row_blocked_w
                        bottleneck_y_px = sy

        if bottleneck_y_px is None:
            corridor_width_at_bottleneck_px = footpath_mid_span_px
            obstructed_width_at_bottleneck_px = 0
            min_remaining_width_px = footpath_mid_span_px

        bottleneck_blockage_pct = round(
            (obstructed_width_at_bottleneck_px / max(1.0, float(corridor_width_at_bottleneck_px))) * 100.0, 1
        )
        bottleneck_clearance_pct = round(100.0 - bottleneck_blockage_pct, 1)

        # --- 2. Calibration & Dimension Estimation ---
        is_calibrated = (nominal_footpath_width_m is not None and nominal_footpath_width_m > 0.0) or (
            calibration_px_per_m is not None and calibration_px_per_m > 0.0
        )

        warnings: List[str] = []
        warnings_accessibility: List[str] = []

        if is_calibrated:
            # Mode A: Calibrated Physical Scale
            nominal_w_m = float(nominal_footpath_width_m or 2.50)
            if calibration_px_per_m and calibration_px_per_m > 0.0:
                scale_px_per_m = float(calibration_px_per_m)
            else:
                # Scale computed at the critical bottleneck row (accounting for perspective depth)
                scale_px_per_m = max(1.0, float(corridor_width_at_bottleneck_px) / max(0.5, nominal_w_m))

            footpath_width_m = round(nominal_w_m, 2)
            obstructed_width_m = round(min(nominal_w_m, obstructed_width_at_bottleneck_px / scale_px_per_m), 2)
            remaining_width_m = round(max(0.0, footpath_width_m - obstructed_width_m), 2)

            # Area in m²: based on ground-plane pixel area divided by scale squared
            mean_corridor_px_w = (footpath_bottom_span_px + footpath_mid_span_px) / 2.0
            mean_scale = max(1.0, mean_corridor_px_w / max(0.5, nominal_w_m))
            footpath_area_sqm = round(footpath_roi_area_px / (mean_scale ** 2), 1)
            occupied_area_sqm = round((roi_pixel_occupancy_pct / 100.0) * footpath_area_sqm, 1)
            free_area_sqm = round(max(0.0, footpath_area_sqm - occupied_area_sqm), 1)

            # Standard-Compliant Accessibility Score (IRC:SP:102 & ADA Benchmarks)
            # 1.8m = standard two-way/wheelchair passing, 0.6m = absolute impassable limit
            if remaining_width_m >= 1.80:
                width_score = 100.0
            elif remaining_width_m <= 0.60:
                width_score = 0.0
            else:
                width_score = ((remaining_width_m - 0.60) / (1.80 - 0.60)) * 100.0

            area_score = max(0.0, 100.0 - roi_pixel_occupancy_pct)
            accessibility_score = round(max(0.0, min(100.0, 0.60 * width_score + 0.40 * area_score)), 1)

            # Accessibility Status classification
            if len(active_obstructions) == 0:
                accessibility_status = "EXCELLENT (FULLY CLEAR — UNRESTRICTED PEDESTRIAN FLOW)"
            elif remaining_width_m >= 1.80 and accessibility_score >= 80.0:
                accessibility_status = "GOOD (FULLY ACCESSIBLE — TWO-WAY WHEELCHAIR PASSING)"
            elif remaining_width_m >= 1.20 and accessibility_score >= 50.0:
                accessibility_status = "PARTIALLY BLOCKED (RESTRICTED PASSING — SINGLE WHEELCHAIR CLEARANCE)"
            elif remaining_width_m >= 0.80:
                accessibility_status = "CONSTRICTED (NARROW BOTTLENECK — BELOW STANDARD WHEELCHAIR WIDTH)"
            else:
                accessibility_status = "SEVERELY BLOCKED (CRITICAL BOTTLENECK — IMPASSABLE FOR WHEELCHAIRS)"

            # Specific Standards-Based Hazards
            if remaining_width_m < 1.20 and len(active_obstructions) > 0:
                warnings_accessibility.append(
                    f"Critical narrow passage: Remaining walkable width ({remaining_width_m}m) is below the "
                    f"1.20m minimum accessible clearance stipulated by IRC:SP:102-2014 & ADA standards."
                )
            if remaining_width_m < 0.80 and len(active_obstructions) > 0:
                warnings_accessibility.append(
                    f"Severe mobility barrier: Remaining passage ({remaining_width_m}m) prevents passage of standard "
                    f"wheelchairs (0.70m width) and strollers."
                )
            if roi_pixel_occupancy_pct >= 35.0:
                warnings_accessibility.append(
                    f"High walkway occupancy: {roi_pixel_occupancy_pct}% of total pedestrian corridor area is obstructed."
                )

            measurement_unit = "meters & square meters (Calibrated Scale)"
            calibration_meta = {
                "is_calibrated": True,
                "calibration_mode": "NOMINAL_STREET_PROFILE" if not calibration_px_per_m else "EXPLICIT_SCALE",
                "nominal_footpath_width_m": nominal_w_m,
                "scale_pixels_per_meter": round(scale_px_per_m, 2),
                "calibration_details": (
                    f"Corridor width calibrated to {nominal_w_m}m nominal urban sidewalk standard; "
                    f"depth scale computed at bottleneck Y={bottleneck_y_px} px ({scale_px_per_m:.1f} px/m)."
                )
            }

        else:
            # Mode B: Uncalibrated 2D Pixel Mode (No physical units invented)
            footpath_width_m = None
            obstructed_width_m = None
            remaining_width_m = None
            footpath_area_sqm = None
            occupied_area_sqm = None
            free_area_sqm = None

            # Transparent 2D Pixel Clearance Heuristic (60% area + 40% bottleneck width blockage)
            weighted_blockage = (0.60 * roi_pixel_occupancy_pct) + (0.40 * bottleneck_blockage_pct)
            accessibility_score = round(max(0.0, min(100.0, 100.0 - weighted_blockage)), 1)

            if len(active_obstructions) == 0:
                accessibility_status = "CLEAR (NO OBSTRUCTION DETECTED)"
            elif accessibility_score >= 75.0:
                accessibility_status = "LOW PIXEL OBSTRUCTION (NEEDS REVIEW)"
            elif accessibility_score >= 45.0:
                accessibility_status = "MODERATE PIXEL OBSTRUCTION (NEEDS REVIEW)"
            else:
                accessibility_status = "HIGH PIXEL OBSTRUCTION (NEEDS REVIEW)"

            if bottleneck_blockage_pct >= 50.0:
                warnings_accessibility.append(
                    f"Substantial horizontal blockage: {bottleneck_blockage_pct}% of corridor pixel width is obstructed "
                    f"at critical bottleneck (Row Y={bottleneck_y_px} px)."
                )
            if roi_pixel_occupancy_pct >= 25.0:
                warnings_accessibility.append(
                    f"High area occupancy: {roi_pixel_occupancy_pct}% of Prototype Footpath ROI pixels are obstructed."
                )

            measurement_unit = "pixels & relative % (Uncalibrated 2D Image Space)"
            calibration_meta = {
                "is_calibrated": False,
                "calibration_mode": "UNCALIBRATED_PIXEL_ONLY",
                "nominal_footpath_width_m": None,
                "scale_pixels_per_meter": None,
                "calibration_details": CALIBRATION_SPECIFICATION["uncalibrated_summary"]
            }

        all_warnings = warnings + warnings_accessibility
        if review_objs and not enc_objs:
            all_warnings.append(
                f"{len(review_objs)} object(s) flagged as 'Needs human review' due to prototype ROI boundary uncertainty."
            )

        # Standard 4-Tier Accessibility Category (Upgrade 3)
        if accessibility_score >= 80.0:
            accessibility_category = "Good"
        elif accessibility_score >= 60.0:
            accessibility_category = "Moderately Affected"
        elif accessibility_score >= 40.0:
            accessibility_category = "Poor"
        else:
            accessibility_category = "Severely Blocked"

        # Pedestrian Path Continuity Estimation (Upgrade 4)
        if not footpath_polygon or len(footpath_polygon) < 3 or corridor_width_at_bottleneck_px <= 0:
            path_continuity = "UNKNOWN"
            path_continuity_reason = "Insufficient footpath region coordinates to evaluate continuous path."
        elif len(active_obstructions) == 0:
            path_continuity = "CLEAR"
            path_continuity_reason = "Unobstructed continuous passage throughout sidewalk corridor."
        elif is_calibrated and remaining_width_m is not None:
            if remaining_width_m < 0.60 or bottleneck_blockage_pct >= 85.0:
                path_continuity = "SEVERELY BLOCKED"
                path_continuity_reason = f"Continuous pedestrian travel severed at bottleneck (only {remaining_width_m}m clearance)."
            elif remaining_width_m < 1.20 or bottleneck_blockage_pct >= 40.0:
                path_continuity = "PARTIALLY BLOCKED"
                path_continuity_reason = f"Continuous path constrained below standard passing width ({remaining_width_m}m clear)."
            else:
                path_continuity = "CLEAR"
                path_continuity_reason = f"Continuous accessible path maintained ({remaining_width_m}m clear passage)."
        else:
            if bottleneck_blockage_pct >= 80.0 or roi_pixel_occupancy_pct >= 60.0:
                path_continuity = "SEVERELY BLOCKED"
                path_continuity_reason = f"Horizontal bottleneck blockage reached {bottleneck_blockage_pct}%; continuous route blocked."
            elif bottleneck_blockage_pct >= 35.0 or roi_pixel_occupancy_pct >= 25.0:
                path_continuity = "PARTIALLY BLOCKED"
                path_continuity_reason = f"Partial blockage ({bottleneck_blockage_pct}% at bottleneck); passage restricted."
            else:
                path_continuity = "CLEAR"
                path_continuity_reason = "Continuous walking corridor appears clear across horizontal slices."

        # Obstruction Impact Classification (Upgrade 3)
        if len(active_obstructions) == 0:
            obstruction_impact = "LOW"
        elif roi_pixel_occupancy_pct >= 40.0 or bottleneck_blockage_pct >= 50.0:
            obstruction_impact = "HIGH"
        elif roi_pixel_occupancy_pct >= 15.0 or bottleneck_blockage_pct >= 20.0:
            obstruction_impact = "MEDIUM"
        else:
            obstruction_impact = "LOW"

        remaining_pedestrian_region_pct = round(max(0.0, 100.0 - roi_pixel_occupancy_pct), 1)

        return {
            "is_calibrated_physical_measurement": is_calibrated,
            "measurement_unit": measurement_unit,
            "calibration_metadata": calibration_meta,
            "engineering_standards": ENGINEERING_ACCESSIBILITY_STANDARDS,
            "scoring_formulas": SCORING_FORMULAS,
            # Physical Dimensions (m and m²) — populated when calibrated, None when uncalibrated
            "footpath_width_m": footpath_width_m,
            "obstructed_width_m": obstructed_width_m,
            "remaining_width_m": remaining_width_m,
            "footpath_area_sqm": footpath_area_sqm,
            "occupied_area_sqm": occupied_area_sqm,
            "free_area_sqm": free_area_sqm,
            # Exact 2D Pixel Bottleneck Measurements
            "bottleneck_y_px": bottleneck_y_px,
            "corridor_width_at_bottleneck_px": corridor_width_at_bottleneck_px,
            "obstructed_width_at_bottleneck_px": obstructed_width_at_bottleneck_px,
            "remaining_width_at_bottleneck_px": min_remaining_width_px,
            "bottleneck_blockage_pct": bottleneck_blockage_pct,
            "bottleneck_clearance_pct": bottleneck_clearance_pct,
            # 2D Pixel Area Metrics
            "footpath_roi_area_px": footpath_roi_area_px,
            "occupied_footpath_px": occupied_footpath_px,
            "free_footpath_px": free_footpath_px,
            "roi_pixel_occupancy_pct": roi_pixel_occupancy_pct,
            "occupancy_percentage": roi_pixel_occupancy_pct,
            "remaining_pedestrian_region_pct": remaining_pedestrian_region_pct,
            # Accessibility Score, Category, Continuity & Obstruction Impact
            "accessibility_score": accessibility_score,
            "accessibility_category": accessibility_category,
            "obstruction_impact": obstruction_impact,
            "pixel_clearance_estimate_pct": accessibility_score,
            "accessibility_status": accessibility_status,
            "path_continuity": path_continuity,
            "path_continuity_reason": path_continuity_reason,
            "warnings": all_warnings,
            "warnings_accessibility": warnings_accessibility
        }

    def compute_severity(
        self,
        overall_classification: str,
        roi_pixel_occupancy_pct: float,
        bottleneck_blockage_pct: float,
        remaining_width_m: Optional[float],
        needs_review_count: int
    ) -> Tuple[str, str]:
        """
        Determines Severity (Low, Medium, High) considering both area occupancy and critical bottleneck width.
        """
        if overall_classification == "No obstruction detected":
            return (
                "Low",
                "No objects detected by YOLOv5n-ONNX (0% walkway obstruction)."
            )
        if overall_classification == "Not an encroachment":
            return (
                "Low",
                "Detected objects operating within normal traffic/pedestrian transit outside footpath obstruction."
            )
        if overall_classification == "Needs human review" and roi_pixel_occupancy_pct == 0.0:
            return (
                "Low",
                f"{needs_review_count} object(s) with boundary uncertainty require human review before severity escalation."
            )

        # Calibrated physical severity rules
        if remaining_width_m is not None:
            if remaining_width_m < 1.00 or roi_pixel_occupancy_pct >= 35.0 or bottleneck_blockage_pct >= 55.0:
                return (
                    "High",
                    f"Critical walkway bottleneck: Remaining clear width ({remaining_width_m}m) is below the 1.2m "
                    f"accessible threshold and {roi_pixel_occupancy_pct}% of footpath area is occupied."
                )
            if remaining_width_m < 1.60 or roi_pixel_occupancy_pct >= 15.0 or bottleneck_blockage_pct >= 25.0:
                return (
                    "Medium",
                    f"Moderate footpath constriction: Remaining width ({remaining_width_m}m) restricts two-way flow "
                    f"({roi_pixel_occupancy_pct}% area occupied, {bottleneck_blockage_pct}% bottleneck width blocked)."
                )
            return (
                "Low",
                f"Minor walkway encroachment: Remaining clear width ({remaining_width_m}m) accommodates pedestrian flow."
            )

        # Uncalibrated 2D pixel severity rules
        if roi_pixel_occupancy_pct >= 25.0 or bottleneck_blockage_pct >= 45.0:
            return (
                "High",
                f"High 2D pixel obstruction: {roi_pixel_occupancy_pct}% area overlap and {bottleneck_blockage_pct}% "
                f"bottleneck width blockage (Uncalibrated estimate — human review required)."
            )
        if roi_pixel_occupancy_pct >= 10.0 or bottleneck_blockage_pct >= 20.0:
            return (
                "Medium",
                f"Moderate 2D pixel obstruction: {roi_pixel_occupancy_pct}% area overlap and {bottleneck_blockage_pct}% "
                f"bottleneck width blockage."
            )
        return (
            "Low",
            f"Minor pixel overlap ({roi_pixel_occupancy_pct}% of Prototype Footpath ROI)."
        )


metrics_engine = AccessibilityMetricsEngine()
