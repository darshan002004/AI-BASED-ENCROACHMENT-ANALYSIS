"""
Dynamic Encroachment Risk & Severity Scoring Engine.
Upgrade 5:
- Replaces static or arbitrary severity with an explainable 0–100 risk score.
- 0–39: LOW
- 40–69: MEDIUM
- 70–100: HIGH
- Measurable factors:
  1. Object Impact (0–30 pts)
  2. Footpath Overlap (0–25 pts)
  3. Persistence Duration (0–20 pts)
  4. Accessibility Impact (0–25 pts)
- Strict data integrity: transparent mathematical formula and factor breakdown.
"""

from typing import Dict, Any, List, Optional


class DynamicRiskEngine:
    """
    Computes an explainable, multi-factor Encroachment Risk Score (0–100).
    """

    OBJECT_IMPACT_WEIGHTS = {
        "vehicle": 28.0,
        "truck": 30.0,
        "bus": 30.0,
        "car": 26.0,
        "motorcycle": 22.0,
        "auto": 24.0,
        "construction": 26.0,
        "debris": 24.0,
        "vendor": 22.0,
        "cart": 20.0,
        "signboard": 14.0,
        "umbrella": 12.0,
        "chair": 10.0,
        "bench": 10.0,
        "street object": 12.0,
        "pedestrian": 0.0,
        "person": 0.0,
        "default": 15.0
    }

    def compute_risk_score(
        self,
        category: str,
        coco_class: str,
        footpath_overlap_pct: float,
        accessibility_score: float,
        persistence_sec: Optional[float] = None,
        is_video: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates the 0–100 Risk Score and returns transparent breakdown.
        """
        # Factor 1: Object Impact (Max 30 pts)
        cat_lower = (category or "").lower()
        class_lower = (coco_class or "").lower()

        if "pedestrian" in cat_lower or "person" in class_lower:
            object_impact = 0.0
        elif class_lower in self.OBJECT_IMPACT_WEIGHTS:
            object_impact = self.OBJECT_IMPACT_WEIGHTS[class_lower]
        elif cat_lower in self.OBJECT_IMPACT_WEIGHTS:
            object_impact = self.OBJECT_IMPACT_WEIGHTS[cat_lower]
        elif "vehicle" in cat_lower:
            object_impact = 26.0
        elif "construction" in cat_lower:
            object_impact = 25.0
        elif "vendor" in cat_lower or "stall" in cat_lower:
            object_impact = 20.0
        elif "sign" in cat_lower:
            object_impact = 14.0
        else:
            object_impact = self.OBJECT_IMPACT_WEIGHTS["default"]

        # Factor 2: Footpath Overlap (Max 25 pts)
        # Directly proportional to geometric overlap percentage within the pedestrian zone
        overlap_clamped = max(0.0, min(100.0, float(footpath_overlap_pct)))
        overlap_score = round((overlap_clamped / 100.0) * 25.0, 1)

        # Factor 3: Persistence Duration (Max 20 pts)
        if is_video and persistence_sec is not None:
            if persistence_sec >= 60.0:
                persistence_score = 20.0
                persistence_note = f"Observed stationary for {persistence_sec:.1f}s (>= 60s peak persistence: 20/20 pts)"
            elif persistence_sec >= 30.0:
                persistence_score = 15.0
                persistence_note = f"Observed stationary for {persistence_sec:.1f}s (>= 30s substantial persistence: 15/20 pts)"
            elif persistence_sec >= 10.0:
                persistence_score = 10.0
                persistence_note = f"Observed stationary for {persistence_sec:.1f}s (>= 10s moderate persistence: 10/20 pts)"
            elif persistence_sec >= 3.0:
                persistence_score = 5.0
                persistence_note = f"Observed briefly for {persistence_sec:.1f}s (transient: 5/20 pts)"
            else:
                persistence_score = 2.0
                persistence_note = f"Brief appearance ({persistence_sec:.1f}s: 2/20 pts)"
        else:
            # Single-frame still photo: temporal persistence cannot be observed.
            # Assign baseline neutral expectation of 10.0 pts (50% of weight), clearly qualified.
            persistence_score = 10.0
            persistence_note = "Single-frame photographic capture (baseline 10/20 pts applied; video required for temporal tracking)"

        # Factor 4: Accessibility Impact (Max 25 pts)
        # Inversely proportional to accessibility score (lower accessibility = higher risk impact)
        acc_clamped = max(0.0, min(100.0, float(accessibility_score)))
        accessibility_impact_score = round(((100.0 - acc_clamped) / 100.0) * 25.0, 1)

        # Total Raw Score
        raw_score = object_impact + overlap_score + persistence_score + accessibility_impact_score
        total_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Severity Classification
        if total_score >= 70.0:
            level = "HIGH"
            severity_str = "High"
            action = "Immediate inspection and clearance recommended"
        elif total_score >= 40.0:
            level = "MEDIUM"
            severity_str = "Medium"
            action = "Scheduled officer review and warning issuance"
        else:
            level = "LOW"
            severity_str = "Low"
            action = "Routine monitoring; minimal pedestrian hindrance"

        return {
            "score": total_score,
            "risk_score": total_score,
            "level": level,
            "risk_level": level,
            "severity": severity_str,
            "action_recommendation": action,
            "factors": {
                "object_impact": {
                    "points": round(object_impact, 1),
                    "max_points": 30.0,
                    "detail": f"Class '{coco_class}' ({category})"
                },
                "footpath_overlap": {
                    "points": overlap_score,
                    "max_points": 25.0,
                    "detail": f"{overlap_clamped:.1f}% geometric footprint overlap"
                },
                "persistence": {
                    "points": round(persistence_score, 1),
                    "max_points": 20.0,
                    "detail": persistence_note
                },
                "accessibility_impact": {
                    "points": accessibility_impact_score,
                    "max_points": 25.0,
                    "detail": f"Walkway accessibility score {acc_clamped:.1f}/100"
                }
            },
            "formula": (
                "RiskScore = ObjectImpact(max 30) + FootpathOverlap(max 25) + "
                "Persistence(max 20) + AccessibilityImpact(max 25)"
            )
        }


risk_engine = DynamicRiskEngine()
