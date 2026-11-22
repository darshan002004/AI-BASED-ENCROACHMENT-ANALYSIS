from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from app.database import get_db
from app.auth import get_current_user
from app.models.service_feedback import CitizenFeedbackSubmit, CitizenFeedbackItem, ServiceQualitySummary
from app.routers.audit import log_audit_event

router = APIRouter(tags=["Citizen Service Feedback & Quality"])

def require_admin(current_user: Dict[str, Any]):
    role = (current_user.get("role") or "citizen").lower()
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Service quality administration requires Administrator privileges."
        )

@router.post("/incidents/{incident_id}/citizen-feedback", response_model=CitizenFeedbackItem)
async def submit_citizen_feedback(
    incident_id: str,
    feedback_in: CitizenFeedbackSubmit,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Allows the original citizen reporter to submit or update service satisfaction feedback.
    - Ownership Check: Strictly restricted to the original reporting citizen.
    - Eligible Status: Case must be in a verified resolved or closed status.
    - Idempotency / Duplicate Policy: One feedback record per incident; updates existing without ballot stuffing.
    - Separate: Stored in 'service_feedback' collection, independent of AI retraining datasets.
    """
    user_id = str(current_user.get("id") or current_user.get("_id"))
    user_name = current_user.get("full_name") or current_user.get("name") or "Citizen"

    incidents_col = db["incidents"]
    inc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    # 1. Authorization: Only the original reporter can submit feedback
    reporter_id = str(inc.get("reporter_id") or "")
    if reporter_id and reporter_id != user_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only the citizen who submitted this report can provide service feedback."
        )

    # 2. Eligible Status Check
    status_lower = (inc.get("status") or "").lower()
    if status_lower not in ("resolved - verified", "resolved", "closed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit feedback for incident with status '{inc.get('status')}'. Service feedback is only eligible once the incident is verified resolved."
        )

    feedback_col = db["service_feedback"]
    now_iso = datetime.utcnow().isoformat() + "Z"
    inc_num = inc.get("incident_number", "ENC-0000")

    effective_rating = feedback_in.get_rating()
    effective_comments = feedback_in.get_comments()

    # Check for existing feedback
    existing = await feedback_col.find_one({"incident_id": str(inc["_id"])})

    if existing:
        # Update existing feedback (one feedback per incident policy)
        update_data = {
            "rating": effective_rating,
            "satisfaction_rating": effective_rating,
            "timeliness_rating": feedback_in.timeliness_rating or 5,
            "satisfaction_level": feedback_in.satisfaction_level or "Satisfied",
            "comments": effective_comments,
            "feedback_text": effective_comments,
            "updated_at": now_iso,
            "is_updated": True
        }
        await feedback_col.update_one({"_id": existing["_id"]}, {"$set": update_data})
        updated = await feedback_col.find_one({"_id": existing["_id"]})
        updated["id"] = str(updated.get("id") or updated["_id"])
        updated["satisfaction_rating"] = effective_rating
        updated["feedback_text"] = effective_comments
        
        # Link summary in incident
        await incidents_col.update_one(
            {"_id": inc["_id"]},
            {"$set": {"service_feedback": {"rating": effective_rating, "satisfaction_rating": effective_rating, "satisfaction_level": feedback_in.satisfaction_level}}}
        )

        await log_audit_event(
            db=db,
            user=current_user,
            action="FEEDBACK_UPDATED",
            target_id=str(inc["_id"]),
            details={"rating": effective_rating, "incident_number": inc_num}
        )
        return CitizenFeedbackItem(**updated)
    else:
        # Create new feedback record
        fb_id = f"fb_{uuid.uuid4().hex[:10]}"
        new_doc = {
            "id": fb_id,
            "incident_id": str(inc["_id"]),
            "incident_number": inc_num,
            "reporter_id": user_id,
            "reporter_name": user_name,
            "rating": effective_rating,
            "satisfaction_rating": effective_rating,
            "timeliness_rating": feedback_in.timeliness_rating or 5,
            "satisfaction_level": feedback_in.satisfaction_level or "Satisfied",
            "comments": effective_comments,
            "feedback_text": effective_comments,
            "created_at": now_iso,
            "updated_at": now_iso,
            "is_updated": False
        }
        await feedback_col.insert_one(new_doc)

        # Link summary in incident
        await incidents_col.update_one(
            {"_id": inc["_id"]},
            {"$set": {"service_feedback": {"rating": effective_rating, "satisfaction_rating": effective_rating, "satisfaction_level": feedback_in.satisfaction_level}}}
        )

        await log_audit_event(
            db=db,
            user=current_user,
            action="FEEDBACK_SUBMITTED",
            target_id=str(inc["_id"]),
            details={"rating": effective_rating, "incident_number": inc_num}
        )
        return CitizenFeedbackItem(**new_doc)

@router.get("/incidents/{incident_id}/citizen-feedback", response_model=Optional[CitizenFeedbackItem])
async def get_incident_feedback(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Retrieves citizen feedback for a specific incident.
    Restricted to original reporter and municipal staff.
    """
    feedback_col = db["service_feedback"]
    fb = await feedback_col.find_one({"incident_id": incident_id})
    if not fb:
        return None

    user_id = str(current_user.get("id") or current_user.get("_id"))
    role = (current_user.get("role") or "citizen").lower()
    if role == "citizen" and fb.get("reporter_id") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot view feedback for another citizen's report.")

    fb["id"] = str(fb.get("id") or fb["_id"])
    return CitizenFeedbackItem(**fb)

@router.get("/service-quality/summary", response_model=ServiceQualitySummary)
async def get_service_quality_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns aggregate municipal service quality and citizen satisfaction metrics.
    Restricted to Administrator role.
    """
    require_admin(current_user)

    feedback_col = db["service_feedback"]
    all_fb = await feedback_col.find({}).to_list(2000)

    incidents_col = db["incidents"]
    resolved_count = await incidents_col.count_documents({"status": {"$in": ["Resolved", "Resolved - Verified", "Closed"]}})

    total_fb = len(all_fb)
    if total_fb == 0:
        return ServiceQualitySummary(
            total_feedback_count=0,
            average_rating=0.0,
            average_timeliness=0.0,
            rating_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            satisfaction_breakdown={},
            response_rate_pct=0.0,
            recent_comments=[]
        )

    avg_rating = round(sum(f.get("rating", 0) for f in all_fb) / total_fb, 2)
    avg_timeliness = round(sum(f.get("timeliness_rating", 0) for f in all_fb) / total_fb, 2)

    dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    sat_breakdown: Dict[str, int] = {}
    recent_comments = []

    for f in all_fb:
        r_str = str(f.get("rating", 5))
        dist[r_str] = dist.get(r_str, 0) + 1

        sat = f.get("satisfaction_level", "Satisfied")
        sat_breakdown[sat] = sat_breakdown.get(sat, 0) + 1

        if f.get("comments"):
            recent_comments.append({
                "rating": f.get("rating"),
                "satisfaction_level": sat,
                "comments": f.get("comments"),
                "date": f.get("created_at")[:10],
                "incident_number": f.get("incident_number")
            })

    response_rate = round((total_fb / resolved_count * 100.0), 1) if resolved_count > 0 else 0.0

    return ServiceQualitySummary(
        total_feedback_count=total_fb,
        total_feedbacks=total_fb,
        average_rating=avg_rating,
        average_satisfaction=avg_rating,
        average_timeliness=avg_timeliness,
        rating_distribution=dist,
        satisfaction_breakdown=sat_breakdown,
        response_rate_pct=min(100.0, response_rate),
        recent_comments=recent_comments[-10:]
    )
