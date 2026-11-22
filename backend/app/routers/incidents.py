from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from app.models.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentInspectionSubmit, CommentItem,
    BatchSyncRequest, BatchSyncResponse, BatchSyncResultItem,
    ResolutionSubmitRequest, ResolutionReviewRequest, IncidentReopenRequest, CitizenCommentRequest
)
from app.database import get_db
from app.auth import get_current_user
from app.ai.duplicate_detector import duplicate_detector
from app.ai.verification import verification_engine
from app.ai.prioritizer import incident_prioritizer
from app.ai.hotspot_predictor import hotspot_predictor
from app.ai.pipeline import run_ai_pipeline
from app.ai.privacy import privacy_engine
from app.routers.audit import log_audit_event
from app.services.notification_service import notification_service
from datetime import datetime
import uuid
import os
import shutil
from app.config import settings
from app.utils.security import validate_file_content_and_type, generate_safe_storage_filename

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    encroachment_type: Optional[str] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    assigned_to_me: Optional[bool] = False,
    reporter_id: Optional[str] = None,
    my_reports: Optional[bool] = False,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")

    user_role = (current_user.get("role") or "citizen").lower() if current_user else "citizen"
    user_id = (current_user.get("id") or str(current_user.get("_id"))) if current_user else None

    query = {}
    if status and status.lower() != "all":
        query["status"] = {"$regex": f"^{status}$", "$options": "i"}
    if severity and severity.lower() != "all":
        query["severity"] = {"$regex": f"^{severity}$", "$options": "i"}
    if encroachment_type and encroachment_type.lower() != "all":
        query["primary_encroachment_type"] = {"$regex": f"^{encroachment_type}$", "$options": "i"}
    if location and location.lower() != "all":
        query["location_name"] = {"$regex": location, "$options": "i"}
    if assigned_to_me and current_user:
        query["assigned_officer_id"] = user_id

    # Filter for citizen's reported and endorsed incidents
    target_reporter = None
    if user_role == "citizen" and user_id:
        # Citizens can ONLY list their own reports
        target_reporter = user_id
    elif my_reports and current_user:
        target_reporter = user_id
    elif reporter_id:
        target_reporter = reporter_id

    if target_reporter:
        reporter_cond = [
            {"reporter_id": target_reporter},
            {"supporting_reports.reporter_id": target_reporter}
        ]
        if "$or" in query:
            query["$and"] = [{"$or": query.pop("$or")}, {"$or": reporter_cond}]
        else:
            query["$or"] = reporter_cond

    if search:
        search_cond = [
            {"incident_number": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"location_name": {"$regex": search, "$options": "i"}},
            {"primary_encroachment_type": {"$regex": search, "$options": "i"}}
        ]
        if "$or" in query:
            query["$and"] = [{"$or": query.pop("$or")}, {"$or": search_cond}]
        else:
            query["$or"] = search_cond

    docs = await incidents_col.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Feature 2: Role-based Privacy Separation
    # If unauthenticated or viewing public incidents as a citizen (not their own report),
    # mask raw evidence with privacy-protected images if available.
    user_role = (current_user.get("role") if current_user else "citizen") or "citizen"
    user_id = (current_user.get("id") or str(current_user.get("_id"))) if current_user else None

    for d in docs:
        if "id" not in d:
            d["id"] = str(d["_id"])
        is_authorized = user_role in ("admin", "officer") or (user_id and user_id == d.get("reporter_id"))
        if not is_authorized and d.get("privacy_image_url"):
            d["image_url"] = d["privacy_image_url"]

    return [IncidentResponse(**d) for d in docs]


@router.get("/review-queue")
async def get_review_queue(
    filter_type: Optional[str] = Query("ALL", description="ALL, UNCERTAIN, CONFLICTING, LOW_CONFIDENCE"),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature 1: Officer Review Queue for AI-Generated Incident Analyses.
    Surfaces incidents that require municipal human attention:
    - Uncertain detections ('Needs human review')
    - Conflicting multi-image evidence ('evidence_inconsistency_flag' == True)
    - Low-confidence detections (< 60% confidence)
    - Poor image quality or pending officer review
    Restricted to authorized officers and administrators.
    """
    user_role = (current_user.get("role") or "citizen").lower()
    if user_role not in ("officer", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Access to the officer AI review queue is restricted to municipal officers and administrators."
        )

    db = get_db()
    incidents_col = db.get_collection("incidents")

    base_query = {
        "status": {"$nin": ["Resolved", "Rejected", "Duplicate Merged"]},
        "$or": [
            {"human_verification_status": {"$in": ["NEEDS_REVIEW", "PENDING_REVIEW"]}},
            {"review_status": "NEEDS_REVIEW"},
            {"potential_encroachment": "NEEDS REVIEW"},
            {"evidence_inconsistency_flag": True},
            {"confidence": {"$ne": None, "$lt": 0.60}}
        ]
    }

    if filter_type == "CONFLICTING":
        base_query = {"status": {"$nin": ["Resolved", "Rejected", "Duplicate Merged"]}, "evidence_inconsistency_flag": True}
    elif filter_type == "LOW_CONFIDENCE":
        base_query = {"status": {"$nin": ["Resolved", "Rejected", "Duplicate Merged"]}, "confidence": {"$ne": None, "$lt": 0.60}}
    elif filter_type == "UNCERTAIN":
        base_query = {
            "status": {"$nin": ["Resolved", "Rejected", "Duplicate Merged"]},
            "$or": [{"potential_encroachment": "NEEDS REVIEW"}, {"human_verification_status": "NEEDS_REVIEW"}]
        }

    docs = await incidents_col.find(base_query).sort("created_at", -1).limit(limit).to_list(limit)
    items = []
    for d in docs:
        if "id" not in d:
            d["id"] = str(d["_id"])

        reasons = []
        if d.get("evidence_inconsistency_flag"):
            reasons.append("Conflicting Multi-Image Evidence")
        if d.get("confidence") is not None and d.get("confidence") < 0.60:
            reasons.append(f"Low AI Confidence ({int(d['confidence'] * 100)}%)")
        if d.get("potential_encroachment") == "NEEDS REVIEW":
            reasons.append("Boundary Uncertainty")
        if not reasons:
            reasons.append("Awaiting Officer Ground-Truth Verification")

        items.append({
            "incident": IncidentResponse(**d),
            "review_reasons": reasons,
            "has_inconsistent_evidence": d.get("evidence_inconsistency_flag", False),
            "inconsistency_reason": d.get("evidence_inconsistency_reason"),
            "confidence": d.get("confidence"),
            "uncertainty_warning": reasons[0]
        })

    conflicting_count = sum(1 for i in items if i["has_inconsistent_evidence"])
    low_conf_count = sum(1 for i in items if (i["confidence"] or 1.0) < 0.60)

    return {
        "total_queued": len(items),
        "conflicting_evidence_count": conflicting_count,
        "low_confidence_count": low_conf_count,
        "items": items
    }


@router.get("/{incident_id}/raw-evidence")
async def get_raw_evidence_image(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature 2: Role-based Raw Evidence Access.
    Only authorized officers, admins, or the verified ticket reporter can view unredacted raw photos.
    Unauthorized citizens receive 403 Forbidden.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")
    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_role = (current_user.get("role") or "citizen").lower()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    reporter_id = doc.get("reporter_id")

    if user_role not in ("admin", "officer") and user_id != reporter_id:
        await log_audit_event(
            db=db,
            user=current_user,
            action="PERMISSION_DENIED",
            target_id=incident_id,
            details={"attempted_action": "RAW_EVIDENCE_ACCESS", "reason": "Unauthorized citizen access"}
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied. Unredacted raw evidence is restricted to authorized municipal officers, admins, or the verified ticket reporter."
        )

    await log_audit_event(
        db=db,
        user=current_user,
        action="RAW_EVIDENCE_ACCESS",
        target_id=incident_id,
        details={"user_role": user_role}
    )

    return {
        "incident_id": str(doc.get("id") or doc.get("_id")),
        "raw_image_url": doc.get("image_url"),
        "privacy_image_url": doc.get("privacy_image_url"),
        "authorized_viewer": current_user.get("full_name") or current_user.get("name"),
        "viewer_role": user_role
    }


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")
    doc = await incidents_col.find_one({"_id": incident_id})
    if not doc:
        doc = await incidents_col.find_one({"id": incident_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if "id" not in doc:
        doc["id"] = str(doc["_id"])

    # Role and Ownership Access Control
    user_role = (current_user.get("role") if current_user else "citizen") or "citizen"
    user_id = (current_user.get("id") or str(current_user.get("_id"))) if current_user else None

    is_owner = (user_id and user_id == doc.get("reporter_id")) or any(
        s.get("reporter_id") == user_id for s in doc.get("supporting_reports", [])
    )
    is_staff = user_role in ("admin", "officer")

    if user_role == "citizen" and not is_owner:
        # If not the owner and not privacy-protected, access to private report is forbidden
        if not doc.get("privacy_protected") and not doc.get("privacy_image_url"):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You are not authorized to access another citizen's private report."
            )

    # Privacy Masking for Non-Staff / Non-Owner
    is_authorized_raw = is_staff or is_owner
    if not is_authorized_raw and doc.get("privacy_image_url"):
        doc["image_url"] = doc["privacy_image_url"]
        if doc.get("evidence_images"):
            for ev in doc["evidence_images"]:
                if ev.get("privacy_image_url"):
                    ev["image_url"] = ev["privacy_image_url"]

    return IncidentResponse(**doc)

@router.post("", response_model=IncidentResponse)
async def create_incident(
    incident_in: IncidentCreate,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")

    now = datetime.utcnow()
    user_name = current_user.get("full_name", "Anonymous Citizen") if current_user else "Citizen User"
    user_id = (current_user.get("id") or str(current_user.get("_id"))) if current_user else "usr_anon"

    # 1. Run Duplicate Detector against active incidents (within 60m radius)
    active_incidents = await incidents_col.find({"status": {"$nin": ["Resolved", "Rejected"]}}).to_list(150)
    for a in active_incidents:
        if "id" not in a:
            a["id"] = str(a["_id"])

    dup_match = duplicate_detector.find_duplicate_incident(
        new_lat=incident_in.latitude,
        new_lng=incident_in.longitude,
        new_type=incident_in.primary_encroachment_type,
        active_incidents=active_incidents,
        new_image_url=incident_in.image_url
    )

    if dup_match:
        # Merge report into master incident
        master_id = dup_match["master_incident_id"]
        master = await incidents_col.find_one({"$or": [{"_id": master_id}, {"id": master_id}]})
        if master:
            report_sub_id = f"sub_{uuid.uuid4().hex[:8]}"
            supporting_entry = {
                "report_id": report_sub_id,
                "reporter_id": user_id,
                "reporter_name": user_name,
                "image_url": incident_in.image_url,
                "description": incident_in.description or f"Citizen confirmed active encroachment: {incident_in.primary_encroachment_type}",
                "date_reported": now.strftime("%d %b %Y"),
                "time_reported": now.strftime("%I:%M %p"),
                "distance_meters": dup_match["distance_meters"],
                "match_score": dup_match["match_score"]
            }

            new_supporting_count = (master.get("supporting_reports_count") or 1) + 1

            # Escalate severity on multiple citizen endorsements
            current_sev = master.get("severity", "Low")
            new_sev = current_sev
            if new_supporting_count >= 5 and current_sev != "High":
                new_sev = "High"
            elif new_supporting_count >= 3 and current_sev == "Low":
                new_sev = "Medium"

            merge_comment = {
                "author_name": "System AI (Duplicate Merger)",
                "role": "ai",
                "text": (
                    f"Duplicate report merged from {user_name} ({dup_match['reason']}). "
                    f"Total supporting citizen reports: {new_supporting_count}."
                ),
                "timestamp": now.strftime("%d %b %Y %I:%M %p")
            }

            await incidents_col.update_one(
                {"_id": master["_id"]},
                {
                    "$inc": {"supporting_reports_count": 1},
                    "$push": {
                        "supporting_reports": supporting_entry,
                        "comments": merge_comment
                    },
                    "$set": {
                        "severity": new_sev,
                        "updated_at": now.isoformat() + "Z"
                    }
                }
            )

            # Return updated master with duplicate merge markers
            updated_master = await incidents_col.find_one({"_id": master["_id"]})
            if "id" not in updated_master:
                updated_master["id"] = str(updated_master["_id"])
            updated_master["is_duplicate_merged"] = True
            updated_master["merged_with_master_id"] = str(master["_id"])
            return IncidentResponse(**updated_master)


    # 2. Create new Master Incident
    now = datetime.utcnow()
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"
    inc_num = f"ENC-{now.year}-{len(active_incidents) + 1025:04d}"

    user_name = current_user.get("full_name", "Anonymous Citizen") if current_user else "Citizen User"
    user_id = (current_user.get("id") or str(current_user.get("_id"))) if current_user else "usr_anon"

    # Multi-Image Evidence handling (Upgrade 7)
    evidence_images = incident_in.evidence_images or []
    if not evidence_images and incident_in.image_url:
        evidence_images = [
            {
                "id": f"ev_{uuid.uuid4().hex[:6]}",
                "image_url": incident_in.image_url,
                "annotated_image_url": incident_in.annotated_image_url or incident_in.image_url,
                "privacy_image_url": incident_in.privacy_image_url,
                "caption": "Primary Evidence",
                "uploaded_at": now.strftime("%d %b %Y %I:%M %p")
            }
        ]

    # Priority Calculation (Upgrade 11)
    priority_calc = incident_prioritizer.compute_priority(
        severity=incident_in.severity,
        accessibility_score=incident_in.accessibility_score,
        remaining_width_m=incident_in.remaining_width_m,
        bottleneck_blockage_pct=incident_in.bottleneck_blockage_pct or 0.0,
        supporting_reports_count=1,
        location_incident_count=0
    )

    initial_timeline = [
        {
            "event_type": "ai_detection",
            "title": "AI Encroachment Analysis Completed",
            "description": f"AI identified {incident_in.primary_encroachment_type} (Score: {incident_in.accessibility_score:.1f}/100, Continuity: {incident_in.path_continuity or 'CLEAR'}).",
            "actor_name": "EncroWatch AI Engine",
            "actor_role": "ai",
            "timestamp": now.strftime("%d %b %Y %I:%M %p")
        },
        {
            "event_type": "report_submitted",
            "title": "Citizen Report Submitted",
            "description": f"Report submitted by {user_name} for {incident_in.location_name}.",
            "actor_name": user_name,
            "actor_role": "citizen",
            "timestamp": now.strftime("%d %b %Y %I:%M %p")
        }
    ]

    new_doc = {
        "_id": incident_id,
        "id": incident_id,
        "incident_number": inc_num,
        "title": incident_in.title or f"{incident_in.primary_encroachment_type} Encroachment at {incident_in.location_name}",
        "description": incident_in.description or f"AI detected {incident_in.primary_encroachment_type} occupying {incident_in.occupancy_percentage}% of footpath space.",
        "image_url": incident_in.image_url,
        "annotated_image_url": incident_in.annotated_image_url or incident_in.image_url,
        "location_name": incident_in.location_name,
        "latitude": incident_in.latitude,
        "longitude": incident_in.longitude,
        "date_reported": now.strftime("%d %b %Y"),
        "time_reported": now.strftime("%I:%M %p"),
        "primary_encroachment_type": incident_in.primary_encroachment_type,
        "detected_objects": incident_in.detected_objects,
        "occupied_area_sqm": incident_in.occupied_area_sqm,
        "footpath_area_sqm": incident_in.footpath_area_sqm,
        "footpath_width_m": incident_in.footpath_width_m,
        "obstructed_width_m": incident_in.obstructed_width_m,
        "remaining_width_m": incident_in.remaining_width_m,
        "bottleneck_blockage_pct": incident_in.bottleneck_blockage_pct,
        "is_calibrated": incident_in.is_calibrated or False,
        "calibration_mode": incident_in.calibration_mode or "UNCALIBRATED_PIXEL_ONLY",
        "footpath_roi_area_px": incident_in.footpath_roi_area_px,
        "occupied_footpath_px": incident_in.occupied_footpath_px,
        "footpath_width_px": incident_in.footpath_width_px,
        "remaining_width_px": incident_in.remaining_width_px,
        "bottleneck_y_px": incident_in.bottleneck_y_px,
        "occupancy_percentage": incident_in.occupancy_percentage,
        "accessibility_score": incident_in.accessibility_score,
        "accessibility_status": incident_in.accessibility_status,
        "accessibility_category": incident_in.accessibility_category or "Good",
        "obstruction_impact": incident_in.obstruction_impact or "LOW",
        "remaining_pedestrian_region_pct": incident_in.remaining_pedestrian_region_pct or round(max(0.0, 100.0 - incident_in.occupancy_percentage), 1),
        "path_continuity": incident_in.path_continuity or "CLEAR",
        "path_continuity_reason": incident_in.path_continuity_reason or "",
        "warnings": incident_in.warnings,
        "severity": incident_in.severity,
        "severity_reason": incident_in.severity_reason or f"{int(incident_in.occupancy_percentage)}% of pedestrian space occupied.",
        "confidence": incident_in.confidence,
        "reporter_id": user_id,
        "reporter_name": user_name,
        "assigned_officer_id": None,
        "assigned_officer_name": None,
        "status": "Pending",
        "inspection_image_url": None,
        "inspection_notes": None,
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 1,
        "supporting_reports": [],
        "evidence_images": evidence_images,
        "privacy_image_url": incident_in.privacy_image_url,
        "privacy_protected": incident_in.privacy_protected or False,
        "risk_score": incident_in.risk_score,
        "risk_level": incident_in.risk_level,
        "risk_factors": incident_in.risk_factors,
        "why_flagged": incident_in.why_flagged or [],
        "probability_status": incident_in.probability_status,
        "potential_encroachment": incident_in.potential_encroachment or "YES",
        "ai_explanation": incident_in.ai_explanation or incident_in.description,
        "persistence_sec": incident_in.persistence_sec,
        "is_persistent": incident_in.is_persistent or False,
        "review_status": incident_in.review_status or ("NEEDS_REVIEW" if incident_in.potential_encroachment == "NEEDS REVIEW" else "PENDING"),
        "reasoning": incident_in.reasoning,
        "priority_score": incident_in.priority_score or priority_calc["priority_score"],
        "priority_rank": incident_in.priority_rank or priority_calc["priority_rank"],
        "priority_action": incident_in.priority_action or priority_calc["recommended_action"],
        "original_ai_category": incident_in.original_ai_category or incident_in.primary_encroachment_type,
        "human_verification_status": (
            "NEEDS_REVIEW"
            if (incident_in.potential_encroachment == "NEEDS REVIEW" or (incident_in.confidence is not None and incident_in.confidence < 0.60))
            else "PENDING_REVIEW"
        ),
        "timeline": initial_timeline,
        "comments": [
            {
                "author_name": "System AI",
                "role": "ai",
                "text": (
                    f"Incident reported with YOLOv5n-ONNX confidence {incident_in.confidence * 100:.1f}%."
                    if incident_in.confidence is not None
                    else "Incident reported (manual / uncalibrated review)."
                ),
                "timestamp": now.strftime("%d %b %Y %I:%M %p")
            }
        ],
        "resolution_date": None,
        "created_at": now.isoformat() + "Z",
        "updated_at": now.isoformat() + "Z"
    }

    await incidents_col.insert_one(new_doc)

    # Insert notification for admin
    notif_col = db.get_collection("notifications")
    await notif_col.insert_one({
        "_id": f"notif_{uuid.uuid4().hex[:8]}",
        "recipient_role": "admin",
        "title": f"New {new_doc['severity']} Severity Incident",
        "message": f"{new_doc['primary_encroachment_type']} reported at {new_doc['location_name']}.",
        "type": "new_incident",
        "incident_id": incident_id,
        "read": False,
        "created_at": now.isoformat() + "Z"
    })

    # Log to audit log (Upgrade 25)
    await log_audit_event(
        db=db,
        user={"id": user_id, "name": user_name, "role": "citizen"},
        action="INCIDENT_CREATE",
        target_id=incident_id,
        details={
            "incident_number": inc_num,
            "type": new_doc["primary_encroachment_type"],
            "severity": new_doc["severity"],
            "location": new_doc["location_name"]
        }
    )

    return IncidentResponse(**new_doc)

VALID_TRANSITIONS = {
    "Pending": ["Pending", "Verified", "Rejected", "In Progress", "Under Investigation", "Assigned", "Pending Review", "Awaiting Evidence"],
    "Pending Review": ["Pending Review", "Verified", "Rejected", "In Progress", "Under Investigation", "Assigned", "Awaiting Evidence"],
    "Verified": ["Verified", "Assigned", "In Progress", "Under Investigation", "Rejected", "Awaiting Evidence"],
    "Assigned": ["Assigned", "In Progress", "Under Investigation", "Resolved", "Resolved - Pending Verification", "Pending Review", "Awaiting Evidence"],
    "In Progress": ["In Progress", "Under Investigation", "Resolved", "Resolved - Pending Verification", "Resolved - Verified", "Assigned", "Pending Review", "Awaiting Evidence"],
    "Under Investigation": ["Under Investigation", "In Progress", "Resolved", "Resolved - Pending Verification", "Resolved - Verified", "Assigned", "Pending Review", "Awaiting Evidence"],
    "Awaiting Evidence": ["Awaiting Evidence", "Pending Review", "In Progress", "Under Investigation", "Assigned", "Rejected"],
    "Resolved - Pending Verification": ["Resolved - Pending Verification", "Resolved - Verified", "Resolved", "Resolution Rejected", "In Progress", "Under Investigation"],
    "Resolved": ["Resolved", "Resolved - Verified", "In Progress", "Under Investigation", "Reopened", "Closed"],
    "Resolved - Verified": ["Resolved - Verified", "In Progress", "Under Investigation", "Reopened", "Closed"],
    "Resolution Rejected": ["Resolution Rejected", "In Progress", "Under Investigation", "Assigned"],
    "Reopened": ["Reopened", "In Progress", "Under Investigation", "Assigned", "Resolved - Pending Verification", "Resolved", "Resolved - Verified"],
    "Closed": ["Closed", "Reopened"],
    "Rejected": ["Rejected", "Pending", "Reopened"]
}

@router.post("/batch-sync", response_model=BatchSyncResponse)
async def batch_sync_incidents(
    batch_req: BatchSyncRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")
    user_role = (current_user.get("role") or "citizen").lower()
    user_name = current_user.get("full_name") or current_user.get("name") or "Field Officer"

    if user_role not in ("admin", "officer"):
        await log_audit_event(
            db=db,
            user=current_user,
            action="PERMISSION_DENIED",
            target_id="batch_sync",
            details={"attempted_action": "BATCH_SYNC", "reason": "Unauthorized citizen role"}
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only officers and administrators can synchronize queued incident updates."
        )

    synced_count = 0
    conflict_count = 0
    failed_count = 0
    results: List[BatchSyncResultItem] = []

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    iso_now = datetime.utcnow().isoformat() + "Z"

    for item in batch_req.items:
        inc = await incidents_col.find_one({"$or": [{"_id": item.incident_id}, {"id": item.incident_id}]})
        if not inc:
            failed_count += 1
            results.append(BatchSyncResultItem(
                client_sync_id=item.client_sync_id,
                incident_id=item.incident_id,
                status="FAILED",
                message=f"Incident '{item.incident_id}' not found."
            ))
            continue

        # 1. Duplicate check (idempotency)
        processed = inc.get("processed_sync_ids") or []
        if item.client_sync_id in processed:
            synced_count += 1
            results.append(BatchSyncResultItem(
                client_sync_id=item.client_sync_id,
                incident_id=item.incident_id,
                status="ALREADY_SYNCED",
                message="Update was already processed on server.",
                server_incident={"id": str(inc.get("id") or inc["_id"]), "status": inc.get("status"), "updated_at": inc.get("updated_at")}
            ))
            continue

        # 2. Conflict detection
        server_updated = inc.get("updated_at")
        curr_status = inc.get("status", "Pending")
        curr_notes = inc.get("inspection_notes")

        if item.expected_updated_at and not item.force_resolve_conflict:
            if server_updated and server_updated != item.expected_updated_at:
                if (item.status and item.status != curr_status) or (item.inspection_notes and item.inspection_notes != curr_notes):
                    conflict_count += 1
                    await log_audit_event(
                        db=db,
                        user=current_user,
                        action="SYNC_CONFLICT_DETECTED",
                        target_id=str(inc.get("id") or inc["_id"]),
                        details={
                            "client_sync_id": item.client_sync_id,
                            "expected_updated_at": item.expected_updated_at,
                            "server_updated_at": server_updated
                        }
                    )
                    results.append(BatchSyncResultItem(
                        client_sync_id=item.client_sync_id,
                        incident_id=item.incident_id,
                        status="CONFLICT",
                        message="Conflict detected: Incident modified on server while officer was offline.",
                        server_incident={
                            "id": str(inc.get("id") or inc["_id"]),
                            "status": curr_status,
                            "inspection_notes": curr_notes,
                            "updated_at": server_updated,
                            "assigned_officer_name": inc.get("assigned_officer_name")
                        }
                    ))
                    continue

        # 3. Valid status transition check
        if item.status:
            allowed = VALID_TRANSITIONS.get(curr_status, [curr_status])
            if user_role == "officer" and curr_status in ("Resolved", "Rejected") and item.status != curr_status:
                failed_count += 1
                results.append(BatchSyncResultItem(
                    client_sync_id=item.client_sync_id,
                    incident_id=item.incident_id,
                    status="FAILED",
                    message=f"Officers cannot modify {curr_status} incidents. Admin authorization required."
                ))
                continue
            if item.status not in allowed:
                failed_count += 1
                results.append(BatchSyncResultItem(
                    client_sync_id=item.client_sync_id,
                    incident_id=item.incident_id,
                    status="FAILED",
                    message=f"Invalid status transition from '{curr_status}' to '{item.status}'."
                ))
                continue

        # 4. Apply update
        set_fields = {"updated_at": iso_now}
        timeline_events = []
        if item.status:
            set_fields["status"] = item.status
            if item.status.lower() == "resolved":
                set_fields["resolution_date"] = now_str
            timeline_events.append({
                "event_type": "status_change",
                "title": f"Status Changed to {item.status} (Offline Sync)",
                "description": f"Incident marked as {item.status} via synchronized field update by {user_name}.",
                "actor_name": user_name,
                "actor_role": user_role,
                "timestamp": now_str
            })

        if item.inspection_notes:
            set_fields["inspection_notes"] = item.inspection_notes
            timeline_events.append({
                "event_type": "field_note",
                "title": "Field Inspection Note (Offline Sync)",
                "description": f"Field note recorded: {item.inspection_notes}",
                "actor_name": user_name,
                "actor_role": user_role,
                "timestamp": now_str
            })

        if item.force_resolve_conflict:
            timeline_events.append({
                "event_type": "conflict_resolved",
                "title": "Conflict Resolved",
                "description": f"Conflict explicitly resolved by {user_name}.",
                "actor_name": user_name,
                "actor_role": user_role,
                "timestamp": now_str
            })

        update_op = {
            "$set": set_fields,
            "$addToSet": {"processed_sync_ids": item.client_sync_id}
        }
        if timeline_events:
            update_op["$push"] = {"timeline": {"$each": timeline_events}}

        await incidents_col.update_one({"_id": inc["_id"]}, update_op)

        await log_audit_event(
            db=db,
            user=current_user,
            action="OFFLINE_SYNC_SUCCESS" if not item.force_resolve_conflict else "CONFLICT_RESOLVED",
            target_id=str(inc.get("id") or inc["_id"]),
            details={"client_sync_id": item.client_sync_id, "new_status": item.status}
        )

        synced_count += 1
        results.append(BatchSyncResultItem(
            client_sync_id=item.client_sync_id,
            incident_id=item.incident_id,
            status="SYNCED",
            message="Successfully synchronized update.",
            server_incident={"id": str(inc.get("id") or inc["_id"]), "status": item.status or curr_status, "updated_at": iso_now}
        ))

    return BatchSyncResponse(
        total=len(batch_req.items),
        synced_count=synced_count,
        conflict_count=conflict_count,
        failed_count=failed_count,
        results=results
    )

@router.patch("/{incident_id}", response_model=IncidentResponse)
@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    update_data: IncidentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_role = (current_user.get("role") or "citizen").lower()
    user_name = current_user.get("full_name") or current_user.get("name") or "Administrator"

    # Strict server-side authorization check
    if user_role not in ("admin", "officer"):
        await log_audit_event(
            db=db,
            user=current_user,
            action="PERMISSION_DENIED",
            target_id=incident_id,
            details={"attempted_action": "INCIDENT_UPDATE", "reason": "Unauthorized citizen update attempt"}
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only field officers and municipal administrators can modify incident status or assignments."
        )

    # 1. Duplicate submission check (idempotency)
    processed = doc.get("processed_sync_ids") or []
    if update_data.client_sync_id and update_data.client_sync_id in processed:
        doc["id"] = str(doc.get("id") or doc["_id"])
        return IncidentResponse(**doc)

    # 2. Conflict detection
    server_updated = doc.get("updated_at")
    curr_status = doc.get("status", "Pending")
    curr_notes = doc.get("inspection_notes")

    if update_data.expected_updated_at and not update_data.force_resolve_conflict:
        if server_updated and server_updated != update_data.expected_updated_at:
            if (update_data.status and update_data.status != curr_status) or \
               (update_data.inspection_notes and update_data.inspection_notes != curr_notes):
                await log_audit_event(
                    db=db,
                    user=current_user,
                    action="SYNC_CONFLICT_DETECTED",
                    target_id=str(doc.get("id") or doc["_id"]),
                    details={
                        "client_sync_id": update_data.client_sync_id,
                        "expected_updated_at": update_data.expected_updated_at,
                        "server_updated_at": server_updated
                    }
                )
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Conflict detected: Incident has been updated by another user or administrator.",
                        "incident_id": str(doc.get("id") or doc["_id"]),
                        "server_updated_at": server_updated,
                        "server_status": curr_status,
                        "server_notes": curr_notes,
                        "client_expected_at": update_data.expected_updated_at,
                        "client_proposed_status": update_data.status
                    }
                )

    # 3. Valid status transition check
    if update_data.status:
        allowed = VALID_TRANSITIONS.get(curr_status, [curr_status])
        if user_role == "officer" and curr_status in ("Resolved", "Rejected") and update_data.status != curr_status:
            raise HTTPException(
                status_code=400,
                detail=f"Officers cannot modify {curr_status} incidents. Municipal administrator review required."
            )
        if update_data.status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{curr_status}' to '{update_data.status}'. Permitted: {', '.join(allowed)}."
            )

    iso_now = datetime.utcnow().isoformat() + "Z"
    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    set_fields = {"updated_at": iso_now}
    timeline_events = []

    if update_data.status:
        set_fields["status"] = update_data.status
        if update_data.status.lower() == "resolved":
            set_fields["resolution_date"] = now_str
        timeline_events.append({
            "event_type": "status_change",
            "title": f"Status Changed to {update_data.status}",
            "description": f"Incident marked as {update_data.status} by {user_name}.",
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        })

    if update_data.severity:
        set_fields["severity"] = update_data.severity
        timeline_events.append({
            "event_type": "severity_update",
            "title": f"Severity Set to {update_data.severity}",
            "description": f"Severity adjusted by {user_name}.",
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        })

    if update_data.assigned_officer_id:
        set_fields["assigned_officer_id"] = update_data.assigned_officer_id
        set_fields["assigned_officer_name"] = update_data.assigned_officer_name
        set_fields["status"] = "Assigned"
        timeline_events.append({
            "event_type": "officer_assigned",
            "title": f"Assigned to {update_data.assigned_officer_name}",
            "description": f"Field inspection dispatched to Officer {update_data.assigned_officer_name}.",
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        })

    if update_data.inspection_notes:
        set_fields["inspection_notes"] = update_data.inspection_notes
        timeline_events.append({
            "event_type": "field_note",
            "title": "Field Inspection Note",
            "description": f"Note: {update_data.inspection_notes}",
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        })

    if update_data.inspection_image_url:
        set_fields["inspection_image_url"] = update_data.inspection_image_url

    if update_data.force_resolve_conflict:
        timeline_events.append({
            "event_type": "conflict_resolved",
            "title": "Conflict Resolved",
            "description": f"Conflicting update explicitly resolved by {user_name}.",
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        })

    update_op = {"$set": set_fields}
    if timeline_events:
        update_op["$push"] = {"timeline": {"$each": timeline_events}}
    if update_data.client_sync_id:
        update_op["$addToSet"] = {"processed_sync_ids": update_data.client_sync_id}

    await incidents_col.update_one({"_id": doc["_id"]}, update_op)

    inc_id_str = str(doc.get("id") or doc["_id"])
    inc_num = doc.get("incident_number", "ENC-0000")

    # Send notifications on status change or assignment
    if update_data.status and doc.get("reporter_id"):
        await notification_service.notify_citizen(
            db=db,
            reporter_id=doc["reporter_id"],
            notif_type="STATUS_CHANGE",
            title=f"Incident Status: {update_data.status}",
            message=f"Your report {inc_num} at {doc.get('location_name')} is now '{update_data.status}'.",
            incident_id=inc_id_str,
            incident_number=inc_num,
            data={"status": update_data.status}
        )

    if update_data.assigned_officer_id:
        await notification_service.notify_officer(
            db=db,
            officer_id=update_data.assigned_officer_id,
            notif_type="OFFICER_ASSIGNED",
            title=f"New Assignment: {inc_num}",
            message=f"You have been assigned to inspect {doc.get('primary_encroachment_type')} at {doc.get('location_name')}.",
            incident_id=inc_id_str,
            incident_number=inc_num,
            data={"assigned_by": user_name}
        )

    # Log to audit log
    await log_audit_event(
        db=db,
        user=current_user,
        action="CONFLICT_RESOLVED" if update_data.force_resolve_conflict else "INCIDENT_UPDATE",
        target_id=str(doc["_id"]),
        details={"status": update_data.status, "assigned_to": update_data.assigned_officer_name}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/inspect", response_model=IncidentResponse)
async def submit_inspection(
    incident_id: str,
    inspection_in: IncidentInspectionSubmit,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    officer_name = current_user.get("full_name") or current_user.get("name") or "Field Officer"

    comment = {
        "author_name": officer_name,
        "role": "officer",
        "text": f"Inspection completed. Notes: {inspection_in.inspection_notes}",
        "timestamp": now_str
    }

    timeline_event = {
        "event_type": "officer_inspection",
        "title": "Field Officer On-Site Inspection",
        "description": f"Officer {officer_name} conducted inspection: '{inspection_in.inspection_notes}'. Verification evidence uploaded.",
        "actor_name": officer_name,
        "actor_role": "officer",
        "timestamp": now_str
    }

    comments = doc.get("comments", [])
    comments.append(comment)

    await incidents_col.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "inspection_image_url": inspection_in.inspection_image_url,
                "inspection_notes": inspection_in.inspection_notes,
                "inspection_date": now_str,
                "status": "In Progress",
                "comments": comments,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            },
            "$push": {
                "timeline": timeline_event
            }
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_INSPECT",
        target_id=str(doc["_id"]),
        details={"notes": inspection_in.inspection_notes}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/verify-resolution", response_model=IncidentResponse)
async def verify_resolution(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    inspection_url = doc.get("inspection_image_url")
    if not inspection_url:
        raise HTTPException(status_code=400, detail="Cannot run verification without an inspection image from the field officer.")

    # Resolve local disk paths
    def to_disk_path(url_path: str) -> str:
        if not url_path:
            return ""
        clean = url_path.lstrip("/")
        if clean.startswith("uploads/"):
            clean = clean[len("uploads/"):]
        return os.path.normpath(os.path.join(settings.UPLOAD_DIR, *clean.split("/")))

    before_path = to_disk_path(doc.get("image_url", ""))
    after_path = to_disk_path(inspection_url)

    verification_res = verification_engine.verify_resolution(
        before_image_path=before_path,
        after_image_path=after_path,
        expected_obstruction_type=doc.get("primary_encroachment_type", "Street Vendor")
    )

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    comments = doc.get("comments", [])
    conf_val = verification_res.get("confidence")
    conf_str = f" with {conf_val * 100:.1f}% mean confidence" if conf_val is not None else " (0 objects detected in after-frame)"
    comments.append({
        "author_name": "System AI",
        "role": "ai",
        "text": f"Before/After AI Verification: {verification_res['status']}{conf_str}.",
        "timestamp": now_str
    })

    new_status = "Resolved" if verification_res["verified"] else "In Progress"
    res_date = now_str if verification_res["verified"] else None

    timeline_event = {
        "event_type": "resolution_verified",
        "title": "Before/After AI Resolution Verified" if verification_res["verified"] else "Resolution Incomplete",
        "description": f"AI Verification Engine: {verification_res['status']}. Accessibility updated to {verification_res['current_accessibility_score']:.1f}/100.",
        "actor_name": "EncroWatch AI Verification Engine",
        "actor_role": "ai",
        "timestamp": now_str
    }

    await incidents_col.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "ai_verification": verification_res,
                "status": new_status,
                "resolution_date": res_date,
                "accessibility_score": verification_res["current_accessibility_score"],
                "accessibility_status": verification_res["current_accessibility_status"],
                "comments": comments,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            },
            "$push": {
                "timeline": timeline_event
            }
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="AI_RESOLUTION_VERIFY",
        target_id=str(doc["_id"]),
        details={"verified": verification_res["verified"], "new_status": new_status}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/submit-resolution", response_model=IncidentResponse)
async def submit_resolution(
    incident_id: str,
    req: ResolutionSubmitRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature C: Formal Resolution Submission by Authorized Field Officer.
    Requires resolution notes and after-clearing evidence photograph.
    Transitions status to 'Resolved - Pending Verification'.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    user_role = (current_user.get("role") or "citizen").lower()
    if user_role not in ("officer", "admin"):
        raise HTTPException(status_code=403, detail="Forbidden: Only officers and administrators can submit resolutions.")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    clean_notes = (req.resolution_notes or "").strip()
    if len(clean_notes) < 10:
        raise HTTPException(status_code=400, detail="Resolution note is mandatory and must be at least 10 characters detailing on-site enforcement/clearance.")
    if not req.after_image_url:
        raise HTTPException(status_code=400, detail="After-evidence photograph is strictly required to submit clearance resolution.")

    user_id = str(current_user.get("id") or current_user.get("_id"))
    user_name = current_user.get("full_name") or current_user.get("name") or "Field Officer"
    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    iso_now = datetime.utcnow().isoformat() + "Z"

    after_entry = {
        "url": req.after_image_url,
        "notes": clean_notes,
        "submitted_at": iso_now,
        "submitted_by_name": user_name,
        "submitted_by_id": user_id
    }

    timeline_event = {
        "event_type": "resolution_submitted",
        "title": "Clearance Resolution Submitted",
        "description": f"Officer {user_name} submitted on-site resolution evidence. Notes: '{clean_notes}'. Awaiting supervisory review.",
        "actor_name": user_name,
        "actor_role": user_role,
        "timestamp": now_str
    }

    await incidents_col.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "status": "Resolved - Pending Verification",
                "resolution_notes": clean_notes,
                "inspection_image_url": req.after_image_url,
                "resolution_submitted_at": iso_now,
                "resolved_by_id": user_id,
                "resolved_by_name": user_name,
                "updated_at": iso_now
            },
            "$push": {
                "after_images": after_entry,
                "timeline": timeline_event
            }
        }
    )

    inc_id_str = str(doc.get("id") or doc["_id"])
    inc_num = doc.get("incident_number", "ENC-0000")

    # Notify Admins and Citizen
    await notification_service.notify_admins(
        db=db,
        notif_type="RESOLUTION_SUBMITTED",
        title=f"Resolution Submitted: {inc_num}",
        message=f"Officer {user_name} submitted clearance evidence for {inc_num} ({doc.get('location_name')}). Review required.",
        incident_id=inc_id_str,
        incident_number=inc_num
    )

    if doc.get("reporter_id"):
        await notification_service.notify_citizen(
            db=db,
            reporter_id=doc["reporter_id"],
            notif_type="RESOLUTION_SUBMITTED",
            title=f"Clearance Action Taken: {inc_num}",
            message=f"Municipal enforcement officer has completed on-site clearance for your report. Final verification is pending.",
            incident_id=inc_id_str,
            incident_number=inc_num
        )

    await log_audit_event(
        db=db,
        user=current_user,
        action="RESOLUTION_SUBMITTED",
        target_id=inc_id_str,
        details={"incident_number": inc_num, "notes": clean_notes, "after_image": req.after_image_url}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/review-resolution", response_model=IncidentResponse)
async def review_resolution(
    incident_id: str,
    req: ResolutionReviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature C: Resolution Verification Review.
    Authorized reviewer (Admin or Supervising Officer) accepts or rejects the resolution submission.
    - If accepted: Status transitions to 'Resolved - Verified'.
    - If rejected: Reason is strictly mandatory. Status returns to 'Under Investigation' with rejection reason.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    user_role = (current_user.get("role") or "citizen").lower()
    if user_role not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Forbidden: Only administrators and supervisory officers can review resolutions.")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    decision = req.decision.upper().strip()
    if decision not in ("ACCEPT", "REJECT"):
        raise HTTPException(status_code=400, detail="Decision must be 'ACCEPT' or 'REJECT'.")

    user_id = str(current_user.get("id") or current_user.get("_id"))
    user_name = current_user.get("full_name") or current_user.get("name") or "Reviewer"
    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    iso_now = datetime.utcnow().isoformat() + "Z"
    inc_id_str = str(doc.get("id") or doc["_id"])
    inc_num = doc.get("incident_number", "ENC-0000")

    if decision == "ACCEPT":
        new_status = "Resolved - Verified"
        timeline_event = {
            "event_type": "resolution_accepted",
            "title": "Resolution Verified & Approved",
            "description": f"Clearance evidence reviewed and verified by {user_name}. {req.notes or ''}".strip(),
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        }

        await incidents_col.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "status": new_status,
                    "resolution_date": now_str,
                    "resolution_verified_at": iso_now,
                    "verified_by_id": user_id,
                    "verified_by_name": user_name,
                    "resolution_rejection_reason": None,
                    "updated_at": iso_now
                },
                "$push": {
                    "timeline": timeline_event
                }
            }
        )

        # Notify Citizen & Officer
        if doc.get("reporter_id"):
            await notification_service.notify_citizen(
                db=db,
                reporter_id=doc["reporter_id"],
                notif_type="RESOLUTION_VERIFIED",
                title=f"Issue Resolved: {inc_num}",
                message=f"Your report {inc_num} at {doc.get('location_name')} has been officially verified and closed.",
                incident_id=inc_id_str,
                incident_number=inc_num
            )

        if doc.get("resolved_by_id"):
            await notification_service.notify_officer(
                db=db,
                officer_id=doc["resolved_by_id"],
                notif_type="RESOLUTION_VERIFIED",
                title=f"Resolution Approved: {inc_num}",
                message=f"Your resolution submission for {inc_num} was approved by {user_name}.",
                incident_id=inc_id_str,
                incident_number=inc_num
            )

        action_name = "RESOLUTION_ACCEPTED"
        audit_details = {"decision": "ACCEPT", "verified_by": user_name, "notes": req.notes}

    else:  # REJECT
        clean_reason = (req.reason or req.review_notes or req.notes or "").strip()
        if not clean_reason:
            raise HTTPException(status_code=400, detail="A non-empty reason is strictly mandatory when rejecting a resolution submission.")

        new_status = "Under Investigation"
        timeline_event = {
            "event_type": "resolution_rejected",
            "title": "Resolution Rejected — Returned for Clearance",
            "description": f"Resolution rejected by {user_name}. Reason: '{clean_reason}'. Returned to field officer for further action.",
            "actor_name": user_name,
            "actor_role": user_role,
            "timestamp": now_str
        }

        await incidents_col.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "status": new_status,
                    "resolution_rejection_reason": clean_reason,
                    "updated_at": iso_now
                },
                "$push": {
                    "timeline": timeline_event
                }
            }
        )

        target_off = doc.get("assigned_officer_id") or doc.get("resolved_by_id")
        if target_off:
            await notification_service.notify_officer(
                db=db,
                officer_id=target_off,
                notif_type="RESOLUTION_REJECTED",
                title=f"Resolution Rejected: {inc_num}",
                message=f"Resolution for {inc_num} was rejected by {user_name}: {clean_reason}. Further action required.",
                incident_id=inc_id_str,
                incident_number=inc_num,
                data={"rejection_reason": clean_reason}
            )

        action_name = "RESOLUTION_REJECTED"
        audit_details = {"decision": "REJECT", "rejected_by": user_name, "reason": clean_reason}

    await log_audit_event(
        db=db,
        user=current_user,
        action=action_name,
        target_id=inc_id_str,
        details=audit_details
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/reopen", response_model=IncidentResponse)
async def reopen_incident(
    incident_id: str,
    req: IncidentReopenRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature C: Authorized Incident Reopening Workflow.
    Allows administrators, officers, or the original citizen reporter to reopen a previously resolved/closed case.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_role = (current_user.get("role") or "citizen").lower()
    user_id = str(current_user.get("id") or current_user.get("_id"))
    user_name = current_user.get("full_name") or current_user.get("name") or "User"

    if user_role == "citizen" and str(doc.get("reporter_id")) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot reopen another citizen's incident.")

    curr_status = doc.get("status", "Pending")
    if curr_status not in ("Resolved", "Resolved - Verified", "Closed", "Rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reopen incident in active status '{curr_status}'. Reopening is only applicable for resolved, closed, or rejected cases."
        )

    clean_reason = (req.reason or "").strip()
    if len(clean_reason) < 10:
        raise HTTPException(status_code=400, detail="Reopening reason is strictly mandatory and must be at least 10 characters justifying recurrence or dispute.")

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    iso_now = datetime.utcnow().isoformat() + "Z"
    inc_id_str = str(doc.get("id") or doc["_id"])
    inc_num = doc.get("incident_number", "ENC-0000")

    timeline_event = {
        "event_type": "incident_reopened",
        "title": "Incident Reopened",
        "description": f"Case reopened by {user_name} ({user_role}). Reason: '{clean_reason}'. Returned to active queue.",
        "actor_name": user_name,
        "actor_role": user_role,
        "timestamp": now_str
    }

    update_set: Dict[str, Any] = {
        "status": "Reopened",
        "reopened_at": iso_now,
        "reopened_by_id": user_id,
        "reopened_by_name": user_name,
        "reopen_reason": clean_reason,
        "resolution_date": None,
        "updated_at": iso_now
    }

    update_ops: Dict[str, Any] = {
        "$set": update_set,
        "$push": {"timeline": timeline_event}
    }

    if req.new_evidence_image_url:
        new_ev_item = {
            "image_url": req.new_evidence_image_url,
            "caption": f"Reopening Evidence: {clean_reason[:50]}",
            "uploaded_at": iso_now,
            "uploaded_by": user_name
        }
        update_ops["$push"]["evidence_images"] = new_ev_item

    await incidents_col.update_one({"_id": doc["_id"]}, update_ops)

    if doc.get("assigned_officer_id"):
        await notification_service.notify_officer(
            db=db,
            officer_id=doc["assigned_officer_id"],
            notif_type="INCIDENT_REOPENED",
            title=f"Incident Reopened: {inc_num}",
            message=f"Incident {inc_num} was reopened by {user_name}. Reason: {clean_reason}",
            incident_id=inc_id_str,
            incident_number=inc_num,
            data={"reopen_reason": clean_reason}
        )

    await notification_service.notify_admins(
        db=db,
        notif_type="INCIDENT_REOPENED",
        title=f"Incident Reopened: {inc_num}",
        message=f"Case {inc_num} reopened by {user_name} ({user_role}). Reason: {clean_reason}",
        incident_id=inc_id_str,
        incident_number=inc_num,
        data={"reopen_reason": clean_reason}
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="INCIDENT_REOPENED",
        target_id=inc_id_str,
        details={"incident_number": inc_num, "reopen_reason": clean_reason, "reopened_by": user_name}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/citizen-comment", response_model=IncidentResponse)
async def add_citizen_comment(
    incident_id: str,
    req: CitizenCommentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature A: Citizen Supplementary Comment and Evidence Workflow.
    Allows the reporting citizen to provide clarification, updates, or response to evidence requests.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_role = (current_user.get("role") or "citizen").lower()
    user_id = str(current_user.get("id") or current_user.get("_id"))
    user_name = current_user.get("full_name") or current_user.get("name") or "Citizen"

    if user_role == "citizen" and str(doc.get("reporter_id")) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only comment on your own reports.")

    clean_text = (req.text or "").strip()
    if len(clean_text) < 3:
        raise HTTPException(status_code=400, detail="Comment text must be at least 3 characters.")

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    iso_now = datetime.utcnow().isoformat() + "Z"
    inc_id_str = str(doc.get("id") or doc["_id"])
    inc_num = doc.get("incident_number", "ENC-0000")

    comment_item = {
        "author_name": user_name,
        "role": user_role,
        "text": clean_text,
        "timestamp": now_str
    }

    timeline_event = {
        "event_type": "citizen_update",
        "title": "Citizen Update Provided",
        "description": f"{user_name}: '{clean_text}'",
        "actor_name": user_name,
        "actor_role": user_role,
        "timestamp": now_str
    }

    update_set: Dict[str, Any] = {"updated_at": iso_now}
    # If case was Awaiting Evidence, advance to Under Investigation
    if doc.get("status") == "Awaiting Evidence":
        update_set["status"] = "Under Investigation"

    update_ops: Dict[str, Any] = {
        "$set": update_set,
        "$push": {
            "comments": comment_item,
            "timeline": timeline_event
        }
    }

    if req.evidence_image_url:
        update_ops["$push"]["evidence_images"] = {
            "image_url": req.evidence_image_url,
            "caption": "Supplementary Evidence from Citizen",
            "uploaded_at": iso_now,
            "uploaded_by": user_name
        }

    await incidents_col.update_one({"_id": doc["_id"]}, update_ops)

    if doc.get("assigned_officer_id"):
        await notification_service.notify_officer(
            db=db,
            officer_id=doc["assigned_officer_id"],
            notif_type="CITIZEN_COMMENT",
            title=f"Citizen Update on {inc_num}",
            message=f"Reporter {user_name} provided a comment: {clean_text[:80]}...",
            incident_id=inc_id_str,
            incident_number=inc_num
        )

    await log_audit_event(
        db=db,
        user=current_user,
        action="CITIZEN_COMMENT_ADDED",
        target_id=inc_id_str,
        details={"incident_number": inc_num, "text": clean_text}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

@router.post("/{incident_id}/evidence", response_model=IncidentResponse)
async def add_evidence_image(
    incident_id: str,
    file: UploadFile = File(...),
    caption: Optional[str] = Query("Additional Evidence"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature 2: Multi-Image Evidence Fusion & Inconsistency Detection.
    Allows citizens or officers to attach additional perspective photos to the incident.
    Runs separate AI computer vision inference on the photo and checks for evidence inconsistency.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_role = (current_user.get("role") or "citizen").lower()
    user_id = str(current_user.get("id") or current_user.get("_id"))
    if user_role == "citizen":
        if str(doc.get("reporter_id")) != user_id:
            raise HTTPException(status_code=403, detail="Forbidden: You can only upload evidence to your own reports.")
        if doc.get("status") in ("Closed", "Rejected"):
            raise HTTPException(status_code=400, detail="Cannot attach evidence to a closed or rejected incident.")

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No evidence file provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    content_type = (file.content_type or "").lower()
    allowed_exts = {"jpg", "jpeg", "png"}
    allowed_mimes = {"image/jpeg", "image/jpg", "image/png"}

    if ext not in allowed_exts or (content_type and content_type not in allowed_mimes):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{file.filename}'. Only JPG, JPEG, and PNG images are allowed."
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded evidence file is empty (0 bytes).")
    if len(file_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Evidence file exceeds the 25 MB limit.")

    is_valid, detected_type, err_msg = validate_file_content_and_type(file_bytes, file.filename, is_video=False)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    unique_name = generate_safe_storage_filename(file.filename, prefix="ev")
    dest_path = os.path.join(settings.UPLOAD_DIR, "original", unique_name)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Run separate AI computer vision pipeline on this evidence photo
    try:
        ai_res = run_ai_pipeline(dest_path, output_prefix="ev_annotated", allow_demo_mode=True)
        annotated_url = ai_res.get("annotated_image_url")
        detected_objects = ai_res.get("detected_objects", [])
        evidence_classification = ai_res.get("potential_encroachment")
        evidence_type = ai_res.get("primary_encroachment_type")
        evidence_occupancy = ai_res.get("occupancy_percentage")
    except Exception:
        annotated_url = f"/uploads/original/{unique_name}"
        detected_objects = []
        evidence_classification = "UNKNOWN"
        evidence_type = "Object"
        evidence_occupancy = 0.0

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    user_name = current_user.get("full_name") or current_user.get("name") or "User"

    # Run privacy redaction on this evidence photo
    try:
        privacy_res = privacy_engine.redact_image(dest_path, detected_objects=detected_objects)
        ev_privacy_url = privacy_res.get("privacy_image_url")
    except Exception:
        ev_privacy_url = None

    new_evidence = {
        "id": f"ev_{uuid.uuid4().hex[:6]}",
        "image_url": f"/uploads/original/{unique_name}",
        "annotated_image_url": annotated_url,
        "privacy_image_url": ev_privacy_url,
        "caption": caption,
        "uploaded_by": user_name,
        "uploaded_at": now_str,
        "file_size_kb": round(len(file_bytes) / 1024.0, 1),
        "ai_classification": evidence_classification,
        "ai_primary_type": evidence_type,
        "occupancy_percentage": evidence_occupancy,
        "detected_objects_count": len(detected_objects)
    }

    # Cross-Perspective Consistency Evaluation
    inconsistency_flag = doc.get("evidence_inconsistency_flag", False)
    inconsistency_reason = doc.get("evidence_inconsistency_reason")

    orig_class = doc.get("potential_encroachment")
    orig_type = doc.get("primary_encroachment_type")
    orig_occ = float(doc.get("occupancy_percentage") or 0.0)

    if evidence_classification in ["YES", "NO"] and orig_class in ["YES", "NO"]:
        if evidence_classification != orig_class and abs(evidence_occupancy - orig_occ) >= 35.0:
            inconsistency_flag = True
            inconsistency_reason = (
                f"Contradictory findings between initial report ({orig_type}, {orig_occ:.1f}% occupancy) "
                f"and newly attached perspective '{caption}' ({evidence_type}, {evidence_occupancy:.1f}% occupancy). "
                "Flagged for human visual verification."
            )
        elif orig_type and evidence_type and orig_type != evidence_type and orig_type not in ["Clear", "Other"] and evidence_type not in ["Clear", "Other"]:
            inconsistency_flag = True
            inconsistency_reason = (
                f"Contradictory obstruction classes: Original ticket shows '{orig_type}', but attached photo '{caption}' "
                f"shows '{evidence_type}'. Officer review required to classify primary obstruction."
            )

    timeline_event = {
        "event_type": "evidence_added",
        "title": "Additional Evidence Image Attached",
        "description": f"{user_name} attached photo '{caption}' with separate AI analysis ({evidence_type}, {evidence_occupancy:.1f}% occupancy).",
        "actor_name": user_name,
        "actor_role": current_user.get("role", "citizen"),
        "timestamp": now_str
    }

    update_fields = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "evidence_inconsistency_flag": inconsistency_flag,
        "evidence_inconsistency_reason": inconsistency_reason
    }
    if inconsistency_flag:
        update_fields["human_verification_status"] = "NEEDS_REVIEW"

    await incidents_col.update_one(
        {"_id": doc["_id"]},
        {
            "$push": {
                "evidence_images": new_evidence,
                "timeline": timeline_event
            },
            "$set": update_fields
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="ADD_EVIDENCE",
        target_id=str(doc["_id"]),
        details={"caption": caption, "inconsistency_flag": inconsistency_flag}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)


@router.get("/{incident_id}/possible-duplicates")
async def get_possible_duplicates(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature 1: Duplicate Incident Intelligence.
    Scans active incidents for geographic, temporal, category, and visual correlation against this incident.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    target = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not target:
        raise HTTPException(status_code=404, detail="Incident not found")

    target_id = str(target["_id"])
    active_pool = await incidents_col.find({
        "$and": [
            {"_id": {"$ne": target["_id"]}},
            {"status": {"$nin": ["Resolved", "Rejected", "Duplicate Merged"]}}
        ]
    }).to_list(200)

    for a in active_pool:
        if "id" not in a:
            a["id"] = str(a["_id"])

    candidates = duplicate_detector.find_all_potential_duplicates(
        new_lat=target.get("latitude"),
        new_lng=target.get("longitude"),
        new_type=target.get("primary_encroachment_type", "Other"),
        active_incidents=active_pool,
        new_image_url=target.get("image_url"),
        new_location_name=target.get("location_name"),
        new_date=target.get("date_reported"),
        new_time=target.get("time_reported")
    )

    return {
        "incident_id": target_id,
        "incident_number": target.get("incident_number"),
        "total_candidates": len(candidates),
        "candidates": candidates,
        "is_duplicate_merged": target.get("is_duplicate_merged", False),
        "merged_with_master_id": target.get("merged_with_master_id"),
        "duplicate_dismissed": target.get("duplicate_dismissed", False)
    }


@router.post("/{incident_id}/keep-separate")
async def keep_incident_separate(
    incident_id: str,
    reason: Optional[str] = Query("Admin verified this is a distinct physical incident"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature 1: Duplicate Dismissal / Keep Separate.
    Allows authorized administrators or officers to dismiss duplicate warnings and keep the ticket independent.
    """
    if current_user.get("role") not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Managing incident duplicates requires Admin or Officer privileges.")

    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    user_name = current_user.get("full_name") or current_user.get("name") or "Administrator"

    timeline_event = {
        "event_type": "duplicate_dismissed",
        "title": "Duplicate Match Kept Separate",
        "description": f"{user_name} confirmed this is an independent case: '{reason}'.",
        "actor_name": user_name,
        "actor_role": current_user.get("role", "admin"),
        "timestamp": now_str
    }

    await incidents_col.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "duplicate_dismissed": True,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            },
            "$push": {"timeline": timeline_event}
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="KEEP_SEPARATE",
        target_id=str(doc["_id"]),
        details={"reason": reason}
    )

    return {
        "success": True,
        "message": f"Incident {doc.get('incident_number')} marked as independent. Duplicate alert dismissed."
    }


@router.get("/{incident_id}/risk-forecast")
async def get_incident_risk_forecast(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Feature 4: Historical Reoccurrence Risk Forecast for Incident Hotspot.
    Calculates localized future recurrence forecast using historical records in the area.
    """
    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    from app.ai.duplicate_detector import haversine_distance_meters

    target_lat = doc.get("latitude")
    target_lng = doc.get("longitude")
    target_area = (doc.get("location_name") or "").lower()

    all_incidents = await incidents_col.find({}).to_list(1500)
    localized_history = []

    for inc in all_incidents:
        inc_lat = inc.get("latitude")
        inc_lng = inc.get("longitude")
        if target_lat and target_lng and inc_lat and inc_lng:
            dist = haversine_distance_meters(target_lat, target_lng, inc_lat, inc_lng)
            if dist <= 500.0:
                localized_history.append(inc)
                continue
        loc_name = (inc.get("location_name") or "").lower()
        if any(w in loc_name for w in target_area.split(",") if len(w.strip()) > 3):
            localized_history.append(inc)

    forecast = hotspot_predictor.predict_risk(localized_history)
    return forecast


@router.post("/{incident_id}/merge-duplicate")
async def merge_duplicate_incident(
    incident_id: str,
    master_incident_id: str = Query(..., description="Target Master Incident ID to merge into"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upgrade 6: Admin Duplicate Incident Intelligence.
    Merges duplicate report into master incident with full audit trailing.
    """
    if current_user.get("role") not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Merging incidents requires Admin or Officer privileges.")

    db = get_db()
    incidents_col = db.get_collection("incidents")

    dup_doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    master_doc = await incidents_col.find_one({"$or": [{"_id": master_incident_id}, {"id": master_incident_id}]})

    if not dup_doc or not master_doc:
        raise HTTPException(status_code=404, detail="One or both incidents could not be located.")

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    user_name = current_user.get("full_name") or current_user.get("name") or "Administrator"

    # Create supporting report record in master
    supporting_entry = {
        "report_id": f"sub_{uuid.uuid4().hex[:8]}",
        "reporter_id": dup_doc.get("reporter_id", "usr_anon"),
        "reporter_name": dup_doc.get("reporter_name", "Citizen"),
        "image_url": dup_doc.get("image_url", ""),
        "description": dup_doc.get("description", "Merged duplicate citizen report"),
        "date_reported": dup_doc.get("date_reported", now_str),
        "time_reported": dup_doc.get("time_reported", ""),
        "distance_meters": 0.0,
        "match_score": 1.0
    }

    # Add duplicate's evidence images into master
    dup_evidence = dup_doc.get("evidence_images", [])

    # Update master
    await incidents_col.update_one(
        {"_id": master_doc["_id"]},
        {
            "$inc": {"supporting_reports_count": 1},
            "$push": {
                "supporting_reports": supporting_entry,
                "evidence_images": {"$each": dup_evidence} if dup_evidence else supporting_entry,
                "timeline": {
                    "event_type": "duplicate_merged",
                    "title": f"Duplicate Incident {dup_doc.get('incident_number')} Merged",
                    "description": f"{user_name} merged report {dup_doc.get('incident_number')} into this case.",
                    "actor_name": user_name,
                    "actor_role": current_user.get("role", "admin"),
                    "timestamp": now_str
                }
            },
            "$set": {"updated_at": datetime.utcnow().isoformat() + "Z"}
        }
    )

    # Mark duplicate as merged
    await incidents_col.update_one(
        {"_id": dup_doc["_id"]},
        {
            "$set": {
                "status": "Duplicate Merged",
                "is_duplicate_merged": True,
                "merged_with_master_id": str(master_doc["_id"]),
                "updated_at": datetime.utcnow().isoformat() + "Z"
            },
            "$push": {
                "timeline": {
                    "event_type": "merged_into_master",
                    "title": f"Merged into Master Case {master_doc.get('incident_number')}",
                    "description": f"Incident consolidated into master ticket {master_doc.get('incident_number')}.",
                    "actor_name": user_name,
                    "actor_role": current_user.get("role", "admin"),
                    "timestamp": now_str
                }
            }
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="MERGE_DUPLICATE",
        target_id=str(dup_doc["_id"]),
        details={"master_incident_id": str(master_doc["_id"])}
    )

    return {
        "success": True,
        "message": f"Successfully merged {dup_doc.get('incident_number')} into master case {master_doc.get('incident_number')}."
    }

@router.post("/{incident_id}/override-priority", response_model=IncidentResponse)
async def override_incident_priority(
    incident_id: str,
    priority_score: float = Query(..., ge=1.0, le=100.0),
    priority_rank: str = Query(..., description="'Critical', 'Urgent', 'Standard', 'Routine'"),
    priority_action: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upgrade 11: Admin Override of AI Recommended Priority Queue.
    """
    if current_user.get("role") not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Prioritization override requires Admin privileges.")

    db = get_db()
    incidents_col = db.get_collection("incidents")

    doc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not doc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now_str = datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    user_name = current_user.get("full_name") or current_user.get("name") or "Administrator"

    timeline_event = {
        "event_type": "priority_override",
        "title": f"Priority Overridden: {priority_rank} ({priority_score}/100)",
        "description": f"{user_name} adjusted priority to {priority_rank}. Action: {priority_action}.",
        "actor_name": user_name,
        "actor_role": current_user.get("role", "admin"),
        "timestamp": now_str
    }

    await incidents_col.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "priority_score": priority_score,
                "priority_rank": priority_rank,
                "priority_action": priority_action,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            },
            "$push": {"timeline": timeline_event}
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="PRIORITY_OVERRIDE",
        target_id=str(doc["_id"]),
        details={"score": priority_score, "rank": priority_rank, "action": priority_action}
    )

    updated_doc = await incidents_col.find_one({"_id": doc["_id"]})
    updated_doc["id"] = str(updated_doc["_id"])
    return IncidentResponse(**updated_doc)

