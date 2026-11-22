"""
Encroachment Reasoning Engine & Explainable AI (XAI) Module.
Upgrades 1 & 13:
- Multi-factor spatial, semantic, and temporal reasoning for road & footpath encroachments.
- Does NOT classify every detected object as an encroachment.
- Generates structured, explainable 'WHY WAS THIS FLAGGED?' evidence breakdown.
- Follows strict data integrity: does not invent evidence; returns 'Needs Human Review' when evidence is uncertain.
"""

from typing import List, Dict, Any, Optional
import math


class EncroachmentReasoningEngine:
    """
    Encroachment Reasoning Engine:
    Combines:
    1. Object Category & Class (Vehicle, Street Vendor, Construction Material, Signboard, etc.)
    2. Spatial Position & Region (Footpath, Road, Boundary)
    3. Footpath Overlap % (Geometric intersection area)
    4. Remaining Pedestrian Space (Corridor bottleneck clearance)
    5. Persistence Duration (When video tracking is available)
    6. Accessibility Impact (IRC:SP:102-2014 & ADA compliance, wheelchair impassability)
    7. Location Incident History (Previous incidents at or near the coordinate)
    """

    # Mobility thresholds (IRC:SP:102-2014 & ADA Chapter 4)
    MIN_WHEELCHAIR_CLEARANCE_M = 1.20  # Standard accessible route minimum
    CRITICAL_IMPASSABLE_M = 0.60       # Physical barrier width

    def evaluate_detection(
        self,
        detection: Dict[str, Any],
        footpath_overlap_pct: float,
        road_overlap_pct: float,
        remaining_width_m: Optional[float] = None,
        remaining_width_px: Optional[int] = None,
        occupancy_pct: float = 0.0,
        persistence_sec: Optional[float] = None,
        location_history_count: int = 0,
        is_calibrated: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates a single detected object using multi-factor evidence.
        Returns explainable classification and 'WHY WAS THIS FLAGGED?' evidence items.
        """
        category = detection.get("category", "Object")
        coco_class = detection.get("coco_class") or detection.get("raw_coco_class", "object")
        label = detection.get("label", coco_class)
        det_confidence = float(detection.get("confidence", 0.0))

        evidence_items: List[Dict[str, Any]] = []
        is_encroachment = False
        needs_human_review = False
        probability_status = "NOT AN ENCROACHMENT"
        risk_level = "LOW"

        # 1. Object Type Evidence
        if category in ("Vehicle", "Street Vendor", "Construction Material", "Signboard"):
            evidence_items.append({
                "factor": "Object Type",
                "flagged": True,
                "text": f"{label} (COCO '{coco_class}') identified with {round(det_confidence * 100, 1)}% model confidence.",
                "importance": "High"
            })
        elif category == "Pedestrian":
            # Pedestrians are legitimate sidewalk users! Not an encroachment.
            evidence_items.append({
                "factor": "Object Type",
                "flagged": False,
                "text": f"Pedestrian detected ({label}). Pedestrians are authorized walkway users and do not constitute encroachment.",
                "importance": "Info"
            })
            return {
                "probability_status": "NOT AN ENCROACHMENT",
                "decision": "Not an encroachment",
                "confidence": det_confidence,
                "is_encroachment": False,
                "needs_human_review": False,
                "primary_reason": "Pedestrians are authorized sidewalk users.",
                "evidence_breakdown": evidence_items,
                "risk_level": "LOW"
            }
        else:
            evidence_items.append({
                "factor": "Object Type",
                "flagged": False,
                "text": f"{label} detected. Generic urban object requires context evaluation.",
                "importance": "Moderate"
            })

        # 2. Footpath / Road Overlap Evidence
        if footpath_overlap_pct >= 40.0:
            evidence_items.append({
                "factor": "Footpath Overlap",
                "flagged": True,
                "text": f"Significant overlap: {footpath_overlap_pct}% of ground contact area occupies the designated pedestrian corridor.",
                "importance": "High"
            })
        elif footpath_overlap_pct >= 15.0:
            evidence_items.append({
                "factor": "Footpath Overlap",
                "flagged": True,
                "text": f"Partial encroachment: {footpath_overlap_pct}% of ground contact area overlaps the pedestrian corridor.",
                "importance": "Moderate"
            })
        else:
            evidence_items.append({
                "factor": "Footpath Overlap",
                "flagged": False,
                "text": f"Minimal footpath overlap ({footpath_overlap_pct}%). Located primarily outside or on the roadway ({road_overlap_pct}%).",
                "importance": "Low"
            })

        # 3. Remaining Pedestrian Space & Accessibility Impact
        if is_calibrated and remaining_width_m is not None:
            if remaining_width_m < self.CRITICAL_IMPASSABLE_M:
                evidence_items.append({
                    "factor": "Remaining Pedestrian Space",
                    "flagged": True,
                    "text": f"Critical blockage: Remaining clear passage ({remaining_width_m}m) is impassable for standard wheelchairs (min 0.70m) and pedestrians.",
                    "importance": "Critical"
                })
            elif remaining_width_m < self.MIN_WHEELCHAIR_CLEARANCE_M:
                evidence_items.append({
                    "factor": "Remaining Pedestrian Space",
                    "flagged": True,
                    "text": f"Restricted passage: Remaining clear passage ({remaining_width_m}m) violates IRC:SP:102-2014 & ADA standard 1.20m minimum clearance.",
                    "importance": "High"
                })
            else:
                evidence_items.append({
                    "factor": "Remaining Pedestrian Space",
                    "flagged": False,
                    "text": f"Passable corridor: Remaining walkable width ({remaining_width_m}m) meets accessible passage threshold.",
                    "importance": "Low"
                })
        else:
            # Uncalibrated pixel mode
            if occupancy_pct >= 50.0:
                evidence_items.append({
                    "factor": "Remaining Pedestrian Space",
                    "flagged": True,
                    "text": f"High corridor occupancy: {occupancy_pct}% of the horizontal slice is obstructed (estimated in 2D pixel space).",
                    "importance": "High"
                })
            elif occupancy_pct >= 20.0:
                evidence_items.append({
                    "factor": "Remaining Pedestrian Space",
                    "flagged": True,
                    "text": f"Moderate corridor occupancy: {occupancy_pct}% obstruction in 2D pixel space.",
                    "importance": "Moderate"
                })
            else:
                evidence_items.append({
                    "factor": "Remaining Pedestrian Space",
                    "flagged": False,
                    "text": f"Corridor mostly free: Only {occupancy_pct}% occupied.",
                    "importance": "Low"
                })

        # 4. Persistence Duration Evidence (Video tracking)
        if persistence_sec is not None:
            if persistence_sec >= 30.0:
                evidence_items.append({
                    "factor": "Persistence Duration",
                    "flagged": True,
                    "text": f"Stationary obstacle: Object remained stationary for {persistence_sec}s (> 30s threshold indicates persistent encroachment).",
                    "importance": "High"
                })
            elif persistence_sec >= 5.0:
                evidence_items.append({
                    "factor": "Persistence Duration",
                    "flagged": True,
                    "text": f"Sustained presence: Object observed stationary for {persistence_sec}s.",
                    "importance": "Moderate"
                })
            else:
                evidence_items.append({
                    "factor": "Persistence Duration",
                    "flagged": False,
                    "text": f"Transient object: Observed for only {persistence_sec}s; may be a momentary drop-off or pedestrian movement.",
                    "importance": "Low"
                })

        # 5. Location History Evidence
        if location_history_count > 0:
            evidence_items.append({
                "factor": "Historical Location Risk",
                "flagged": True,
                "text": f"Recurring problem spot: {location_history_count} previous incident(s) recorded in this vicinity.",
                "importance": "Moderate"
            })
        else:
            evidence_items.append({
                "factor": "Historical Location Risk",
                "flagged": False,
                "text": "No previous recurring incident cluster recorded at this exact location.",
                "importance": "Low"
            })

        # Multi-factor Reasoning Decision Tree
        flagged_count = sum(1 for e in evidence_items if e["flagged"])
        critical_flags = sum(1 for e in evidence_items if e.get("importance") in ("Critical", "High") and e["flagged"])

        # Determine Encroachment Probability
        if category in ("Vehicle", "Construction Material", "Street Vendor") and footpath_overlap_pct >= 35.0:
            if det_confidence >= 0.50 and (critical_flags >= 2 or footpath_overlap_pct >= 60.0):
                probability_status = "HIGH-PROBABILITY ENCROACHMENT"
                decision = "Potential encroachment"
                is_encroachment = True
                needs_human_review = True  # Always maintain human-in-the-loop
                risk_level = "HIGH"
                primary_reason = f"{label} occupies a significant portion ({footpath_overlap_pct}%) of the pedestrian region and substantially constricts usable pedestrian space."
            else:
                probability_status = "MODERATE IMPACT ENCROACHMENT"
                decision = "Potential encroachment"
                is_encroachment = True
                needs_human_review = True
                risk_level = "MEDIUM"
                primary_reason = f"{label} partially occupies the pedestrian region ({footpath_overlap_pct}%). Requires officer verification."
        elif category in ("Signboard", "Street Object") and footpath_overlap_pct >= 25.0:
            probability_status = "MODERATE IMPACT ENCROACHMENT"
            decision = "Potential encroachment"
            is_encroachment = True
            needs_human_review = True
            risk_level = "MEDIUM"
            primary_reason = f"{label} creates a physical protrusion ({footpath_overlap_pct}% overlap) along the pedestrian walkway."
        elif footpath_overlap_pct >= 10.0 or (det_confidence < 0.40 and footpath_overlap_pct > 0.0):
            probability_status = "NEEDS HUMAN REVIEW"
            decision = "Needs human review"
            is_encroachment = False
            needs_human_review = True
            risk_level = "LOW"
            primary_reason = f"Borderline overlap ({footpath_overlap_pct}%) or modest detection confidence ({round(det_confidence*100,1)}%). Automatic decision withheld."
        else:
            probability_status = "NOT AN ENCROACHMENT"
            decision = "Not an encroachment"
            is_encroachment = False
            needs_human_review = False
            risk_level = "LOW"
            primary_reason = f"{label} is positioned outside the pedestrian footpath ({footpath_overlap_pct}% overlap) with adequate clearance maintained."

        # Standard 3-state potential_encroachment: YES / NO / NEEDS REVIEW
        if is_encroachment:
            potential_encroachment = "YES"
        elif needs_human_review:
            potential_encroachment = "NEEDS REVIEW"
        else:
            potential_encroachment = "NO"

        return {
            "potential_encroachment": potential_encroachment,
            "probability_status": probability_status,
            "decision": decision,
            "confidence": det_confidence,
            "is_encroachment": is_encroachment,
            "needs_human_review": needs_human_review,
            "primary_reason": primary_reason,
            "reason": primary_reason,
            "evidence_breakdown": evidence_items,
            "why_flagged": evidence_items,
            "risk_level": risk_level,
            "flagged_factors_count": flagged_count,
            "critical_factors_count": critical_flags
        }

    def generate_overall_explanation(
        self,
        evaluated_objects: List[Dict[str, Any]],
        overall_accessibility_score: float,
        footpath_occupancy_pct: float,
        path_continuity: str,
        is_calibrated: bool = False,
        remaining_width_m: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes an explainable executive summary for the overall scene:
        'WHY WAS THIS FLAGGED?'
        """
        encroachments = [obj for obj in evaluated_objects if obj.get("is_encroachment")]
        needs_review = [obj for obj in evaluated_objects if obj.get("needs_human_review") and not obj.get("is_encroachment")]

        checklist: List[Dict[str, Any]] = []

        if len(encroachments) > 0:
            checklist.append({
                "icon": "alert",
                "label": f"{len(encroachments)} Potential Encroachment(s) Detected",
                "detail": ", ".join(set(o.get("label", "Object") for o in encroachments)),
                "status": "flagged"
            })
        else:
            checklist.append({
                "icon": "check",
                "label": "No Major Obstacles Confirmed",
                "detail": "No detected objects exceeded encroachment footprint thresholds.",
                "status": "safe"
            })

        # Footpath overlap / occupancy
        if footpath_occupancy_pct >= 40.0:
            checklist.append({
                "icon": "alert",
                "label": f"Footpath Corridor Heavily Occupied ({round(footpath_occupancy_pct, 1)}%)",
                "detail": "Exceeds standard 30% obstruction threshold.",
                "status": "flagged"
            })
        elif footpath_occupancy_pct >= 15.0:
            checklist.append({
                "icon": "warning",
                "label": f"Footpath Corridor Moderately Occupied ({round(footpath_occupancy_pct, 1)}%)",
                "detail": "Walkway capacity reduced.",
                "status": "warning"
            })
        else:
            checklist.append({
                "icon": "check",
                "label": f"Clear Walkway Area ({100.0 - round(footpath_occupancy_pct, 1)}% free)",
                "detail": "Corridor remains largely unobstructed.",
                "status": "safe"
            })

        # Path continuity
        if path_continuity == "SEVERELY BLOCKED":
            checklist.append({
                "icon": "alert",
                "label": "Pedestrian Path Continuity: Severely Blocked",
                "detail": "Complete barrier detected across pedestrian travel line.",
                "status": "flagged"
            })
        elif path_continuity == "PARTIALLY BLOCKED":
            checklist.append({
                "icon": "warning",
                "label": "Pedestrian Path Continuity: Partially Blocked",
                "detail": "Constricted path forces single-file pedestrian movement.",
                "status": "warning"
            })
        elif path_continuity == "CLEAR":
            checklist.append({
                "icon": "check",
                "label": "Pedestrian Path Continuity: Clear",
                "detail": "Continuous walking corridor available.",
                "status": "safe"
            })
        else:
            checklist.append({
                "icon": "info",
                "label": "Pedestrian Path Continuity: Unknown",
                "detail": "Image perspective or ROI boundary insufficient for definitive continuity check.",
                "status": "neutral"
            })

        # Physical width if calibrated
        if is_calibrated and remaining_width_m is not None:
            if remaining_width_m < 1.20:
                checklist.append({
                    "icon": "alert",
                    "label": f"Wheelchair Passage Blocked ({remaining_width_m}m < 1.20m standard)",
                    "detail": "Fails IRC:SP:102-2014 accessibility guidelines.",
                    "status": "flagged"
                })
            else:
                checklist.append({
                    "icon": "check",
                    "label": f"Accessible Width Maintained ({remaining_width_m}m)",
                    "detail": "Meets minimum wheelchair clearance threshold.",
                    "status": "safe"
                })

        # Final conclusion
        if len(encroachments) > 0 and overall_accessibility_score < 50.0:
            overall_decision = "HIGH-PROBABILITY ENCROACHMENT"
            action_recommendation = "Priority inspection recommended — walkway impassable."
        elif len(encroachments) > 0:
            overall_decision = "POTENTIAL ENCROACHMENT"
            action_recommendation = "Verification recommended — human review required."
        elif len(needs_review) > 0:
            overall_decision = "NEEDS HUMAN REVIEW"
            action_recommendation = "Image exhibits ambiguous boundary overlap; officer inspection recommended."
        else:
            overall_decision = "CLEAR WALKWAY (NO ENCROACHMENT)"
            action_recommendation = "No intervention necessary at this time."

        # Overall potential_encroachment: YES / NO / NEEDS REVIEW
        if len(encroachments) > 0:
            potential_encroachment = "YES"
            primary_reason = f"{len(encroachments)} potential encroachment obstacle(s) occupy the pedestrian corridor."
        elif len(needs_review) > 0:
            potential_encroachment = "NEEDS REVIEW"
            primary_reason = f"{len(needs_review)} object(s) with boundary overlap uncertainty require human review."
        else:
            potential_encroachment = "NO"
            primary_reason = "Corridor is clear; no detected obstacles obstruct pedestrian travel."

        return {
            "potential_encroachment": potential_encroachment,
            "overall_decision": overall_decision,
            "action_recommendation": action_recommendation,
            "reason": primary_reason,
            "checklist": checklist,
            "encroaching_objects_count": len(encroachments),
            "review_objects_count": len(needs_review),
            "data_qualification": (
                "Calibrated real-world metric scale" if is_calibrated else "Estimated in uncalibrated 2D camera coordinate space"
            )
        }


reasoning_engine = EncroachmentReasoningEngine()
