"""
AI Incident Prioritization Engine (Upgrade 11).
Computes Priority Score (1–100) and Recommended Actions for the Action Queue.
Allows administrator override while providing explainable justifications.
"""

from typing import Dict, Any, Optional


class IncidentPrioritizer:
    """
    Ranks incidents by risk to vulnerable pedestrians, severity, and recurrence.
    """

    def compute_priority(
        self,
        severity: str,
        accessibility_score: float,
        remaining_width_m: Optional[float] = None,
        bottleneck_blockage_pct: float = 0.0,
        supporting_reports_count: int = 1,
        location_incident_count: int = 0,
        persistence_sec: Optional[float] = None,
        is_wheelchair_blocked: bool = False
    ) -> Dict[str, Any]:
        score = 0.0
        reasons = []

        # 1. Base Severity (Max 30)
        sev_lower = (severity or "Medium").lower()
        if sev_lower == "high":
            score += 30.0
            reasons.append("High severity encroachment (+30)")
        elif sev_lower == "medium":
            score += 18.0
            reasons.append("Medium severity obstruction (+18)")
        else:
            score += 8.0
            reasons.append("Low severity advisory (+8)")

        # 2. Accessibility Impact & Wheelchair Obstruction (Max 30)
        if remaining_width_m is not None:
            if remaining_width_m < 0.60:
                score += 30.0
                reasons.append(f"Critical barrier impassable for wheelchairs ({remaining_width_m}m < 0.60m) (+30)")
            elif remaining_width_m < 1.20:
                score += 22.0
                reasons.append(f"Passage below 1.2m accessible sidewalk standard ({remaining_width_m}m) (+22)")
            elif remaining_width_m < 1.80:
                score += 12.0
                reasons.append("Constricted two-way wheelchair passing (+12)")
        else:
            if bottleneck_blockage_pct >= 70.0 or accessibility_score < 40.0:
                score += 25.0
                reasons.append(f"Heavy walkway constriction ({bottleneck_blockage_pct:.0f}% blocked) (+25)")
            elif bottleneck_blockage_pct >= 30.0 or accessibility_score < 60.0:
                score += 15.0
                reasons.append("Moderate pedestrian corridor restriction (+15)")

        # 3. Report Frequency & Duplicate Reports (Max 15)
        if supporting_reports_count >= 4:
            score += 15.0
            reasons.append(f"Extensive citizen reporting ({supporting_reports_count} merged complaints) (+15)")
        elif supporting_reports_count >= 2:
            score += 10.0
            reasons.append(f"Multiple citizens reported same obstruction ({supporting_reports_count} reports) (+10)")

        # 4. Location Recurrence (Max 15)
        if location_incident_count >= 5:
            score += 15.0
            reasons.append(f"Chronic recurring hotspot ({location_incident_count} historical incidents) (+15)")
        elif location_incident_count >= 2:
            score += 8.0
            reasons.append(f"Repeat obstruction location ({location_incident_count} past cases) (+8)")

        # 5. Temporal Persistence (Max 10)
        if persistence_sec is not None and persistence_sec >= 30.0:
            score += 10.0
            reasons.append(f"Persistent stationary obstruction confirmed ({persistence_sec:.0f}s) (+10)")

        priority_score = round(max(1.0, min(100.0, score)), 1)

        # Priority Rank & Action Recommendation
        if priority_score >= 80.0:
            rank = "Critical"
            action = "Immediate Dispatch — Field Officer Intervention"
        elif priority_score >= 60.0:
            rank = "Urgent"
            action = "High Priority — Schedule Same-Day Inspection"
        elif priority_score >= 40.0:
            rank = "Standard"
            action = "Routine Queue — Verification & Notice Issuance"
        else:
            rank = "Routine"
            action = "Standard Monitoring — Low Vulnerability Impact"

        return {
            "priority_score": priority_score,
            "priority_rank": rank,
            "recommended_action": action,
            "reasons": reasons,
            "justification": " | ".join(reasons)
        }


incident_prioritizer = IncidentPrioritizer()
