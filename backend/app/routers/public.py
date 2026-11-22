from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.database import get_db
from app.models.public import PublicIncidentItem, PublicStatisticsResponse

router = APIRouter(prefix="/public", tags=["Public Transparency Portal"])

def generalize_coordinate(coord: Optional[float]) -> float:
    if coord is None:
        return 0.0
    # 2 decimal places represents ~1.1 km precision at the equator
    # effectively protecting individual residential privacy while providing district-level visibility
    return round(float(coord), 2)

def derive_public_status(raw_status: str) -> str:
    s = (raw_status or "").lower()
    if s in ("resolved - verified", "resolved", "closed"):
        return "Verified Resolved"
    elif s in ("resolved - pending verification",):
        return "Action Completed - Verification Pending"
    elif s in ("in progress", "under investigation", "assigned"):
        return "Under Active Investigation"
    elif s in ("awaiting evidence",):
        return "Supplementary Evidence Requested"
    elif s in ("rejected",):
        return "Closed (Non-Encroachment)"
    elif s in ("reopened",):
        return "Reopened for Further Review"
    else:
        return "Report Received"

@router.get("/incidents", response_model=List[PublicIncidentItem])
async def list_public_incidents(
    category: Optional[str] = None,
    status: Optional[str] = None,
    area: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db)
):
    """
    Public API returning citizen incident transparency records with strict field allowlist.
    - Anonymized: Excludes reporter identities, phone numbers, and raw unredacted photographs.
    - Privacy protection: Includes photograph URLs ONLY if privacy blur was performed and validated.
    - Coarse GIS: Coordinates are generalized to 2 decimal places (~1.1 km grid) to prevent home pinpointing.
    """
    incidents_col = db["incidents"]
    query: Dict[str, Any] = {}

    if category and category.lower() != "all":
        query["primary_encroachment_type"] = {"$regex": f"^{category}$", "$options": "i"}
    if area and area.lower() != "all":
        query["location_name"] = {"$regex": area, "$options": "i"}

    # Time range filters
    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        query["date_reported"] = date_q

    cursor = incidents_col.find(query).sort("date_reported", -1).limit(limit)
    docs = await cursor.to_list(limit)

    results: List[PublicIncidentItem] = []
    for d in docs:
        raw_status = d.get("status", "Pending")
        pub_status = derive_public_status(raw_status)

        if status and status.lower() != "all":
            if status.lower() not in pub_status.lower():
                continue

        is_verified_resolved = raw_status in ("Resolved - Verified", "Resolved", "Closed")

        # Check privacy blur protection
        has_privacy = bool(d.get("privacy_protected", False))
        privacy_url = d.get("privacy_image_url") if has_privacy else None

        results.append(PublicIncidentItem(
            id=d.get("id") or str(d.get("_id", "")),
            incident_number=d.get("incident_number", "ENC-0000"),
            category=d.get("primary_encroachment_type", "Street Vendor"),
            public_status=pub_status,
            generalized_location=d.get("location_name", "Bengaluru Urban Corridor"),
            generalized_latitude=generalize_coordinate(d.get("latitude")),
            generalized_longitude=generalize_coordinate(d.get("longitude")),
            date_reported=d.get("date_reported", "2026-01-01"),
            resolution_date=d.get("resolution_date") if is_verified_resolved else None,
            verified_resolved=is_verified_resolved,
            has_privacy_cleared_image=bool(privacy_url),
            privacy_image_url=privacy_url
        ))

    return results

@router.get("/statistics", response_model=PublicStatisticsResponse)
async def get_public_statistics(
    days: int = Query(30, ge=1, le=365),
    db: Any = Depends(get_db)
):
    """
    Computes public municipal performance statistics from actual persistent records.
    - Explicit denominator: Calculates resolution rate as verified resolutions / total reports received.
    - Separates officer-submitted resolutions from independently verified closures.
    """
    incidents_col = db["incidents"]
    all_docs = await incidents_col.find({}).to_list(5000)

    total_reports = len(all_docs)
    verified_resolutions = 0
    officer_reported_pending = 0
    open_cases = 0
    overdue_cases = 0
    category_counts: Dict[str, int] = {}
    ward_counts: Dict[str, int] = {}
    resolution_days_list: List[float] = []

    for d in all_docs:
        status = d.get("status", "Pending")
        cat = d.get("primary_encroachment_type", "Street Vendor")
        loc = d.get("location_name", "Other Area")

        category_counts[cat] = category_counts.get(cat, 0) + 1
        ward_counts[loc] = ward_counts.get(loc, 0) + 1

        if status in ("Resolved - Verified", "Resolved", "Closed"):
            verified_resolutions += 1
            # Calculate elapsed resolution days if dates available
            d_rep = d.get("date_reported")
            d_res = d.get("resolution_date")
            if d_rep and d_res:
                try:
                    # Parse dates
                    clean_rep = d_rep[:10]
                    clean_res = d_res[:10]
                    dt_rep = datetime.strptime(clean_rep, "%Y-%m-%d")
                    dt_res = datetime.strptime(clean_res, "%Y-%m-%d")
                    diff_days = max(0.5, (dt_res - dt_rep).total_seconds() / 86400.0)
                    resolution_days_list.append(diff_days)
                except Exception:
                    pass
        elif status == "Resolved - Pending Verification":
            officer_reported_pending += 1
            open_cases += 1
        elif status != "Rejected":
            open_cases += 1

        # Check overdue flag
        if d.get("is_escalated") or (d.get("sla_status", {}).get("overall_status") == "OVERDUE"):
            overdue_cases += 1

    resolution_rate = round((verified_resolutions / total_reports * 100.0), 1) if total_reports > 0 else 0.0
    avg_days = round(sum(resolution_days_list) / len(resolution_days_list), 1) if resolution_days_list else 0.0

    return {
        "total_reports_received": total_reports,
        "verified_resolutions": verified_resolutions,
        "officer_reported_pending_verification": officer_reported_pending,
        "open_cases": open_cases,
        "overdue_cases": overdue_cases,
        "resolution_rate_pct": resolution_rate,
        "average_resolution_days": avg_days,
        "category_breakdown": category_counts,
        "ward_breakdown": dict(sorted(ward_counts.items(), key=lambda x: x[1], reverse=True)[:8]),
        "time_period": f"Cumulative All-Time (Sampled over {total_reports} persistent municipal records)",
        "methodology": {
            "resolution_rate_formula": "Verified Resolutions / Total Reports Received * 100",
            "resolution_distinction": "Verified resolutions require formal supervisory sign-off or AI before/after clearance confirmation; unverified officer reports are counted separately under Pending Verification.",
            "privacy_standard": "All coordinates generalized to 2 decimal places (~1.1 km grid); citizen personal identities and unredacted source media are strictly suppressed."
        }
    }
