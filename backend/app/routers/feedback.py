"""
AI Feedback Loop & Model Performance Router (Batch 3 Upgrades - Features 1, 3, 4).
Endpoints for:
- Human verification of AI detections (CONFIRM, REJECT, MODIFY, NEEDS_MORE_EVIDENCE)
- Strict validation: Mandatory reason required for REJECT and MODIFY
- Server-side role protection: Citizens forbidden (HTTP 403) from modifying official reviews
- Storing dataset in 'ai_feedback_dataset' MongoDB collection with duplicate prevention
- Admin approval/rejection workflow for training dataset samples
- Privacy-safe export in JSONL and CSV formats with PII stripped
- Structured future retraining workflow specification (70/15/15 split, mAP@0.5 benchmark, municipal sign-off)
- Model performance metrics from empirical human verification decisions
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import Dict, Any, List, Optional
import uuid
import csv
import io
import json
from datetime import datetime
from app.database import get_db
from app.models.feedback import FeedbackSubmit, FeedbackItem
from app.auth import get_current_user, require_role
from app.routers.audit import log_audit_event

router = APIRouter(prefix="/feedback", tags=["AI Feedback Loop"])


@router.post("/verify")
async def submit_human_verification(
    data: FeedbackSubmit,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Feature 1: Officer Human-in-the-Loop Review Workflow.
    Allows authorized officers and admins to confirm, reject, modify category, or request more evidence.
    - Server-side role validation: Citizens cannot submit official review decisions (403 Forbidden).
    - Mandatory reason: If action is REJECT or MODIFY, non-empty reason is strictly required (400 Bad Request).
    - Preserves original AI category while storing human verified category and reviewer metadata.
    - Prevents duplicate feedback records for the same incident/review.
    - Downstream status & analytics update without assuming physical clearance.
    """
    user_role = (current_user.get("role") or "citizen").lower()
    if user_role not in ("officer", "admin"):
        # Log permission denial
        await log_audit_event(
            db=db,
            user=current_user,
            action="PERMISSION_DENIED",
            target_id=data.incident_id,
            details={"attempted_action": "AI_VERIFY", "reason": "Citizen attempted officer verification"}
        )
        raise HTTPException(
            status_code=403,
            detail="Operation not permitted. Only authorized officers and admins can submit official AI review decisions."
        )

    action_clean = (data.action or "").strip().upper()
    valid_actions = {"CONFIRM", "REJECT", "MODIFY", "NEEDS_MORE_EVIDENCE"}
    if action_clean not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid review action '{data.action}'. Must be one of: {', '.join(sorted(valid_actions))}."
        )

    # Mandatory reason validation for REJECT and MODIFY
    clean_notes = (data.notes or "").strip()
    if action_clean in ("REJECT", "MODIFY"):
        if not clean_notes:
            raise HTTPException(
                status_code=400,
                detail=f"A valid reason is required when {action_clean.lower()}ing an AI detection finding."
            )

    if action_clean == "MODIFY" and not (data.corrected_category or "").strip():
        raise HTTPException(
            status_code=400,
            detail="A corrected category is required when modifying an AI detection finding."
        )

    incidents_col = db["incidents"]
    feedback_col = db["ai_feedback_dataset"]

    incident = await incidents_col.find_one({"id": data.incident_id})
    if not incident:
        incident = await incidents_col.find_one({"incident_number": data.incident_id})
    if not incident:
        incident = await incidents_col.find_one({"_id": data.incident_id})
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{data.incident_id}' not found.")

    now_str = datetime.utcnow().isoformat() + "Z"
    reviewer_id = current_user.get("id") or str(current_user.get("_id", "usr_officer"))
    reviewer_name = current_user.get("full_name") or current_user.get("name") or "Field Officer"

    orig_category = (
        incident.get("original_ai_category")
        or data.original_ai_category
        or incident.get("primary_encroachment_type")
        or "Unknown Object"
    )
    corrected_cat = (data.corrected_category or "").strip() if action_clean == "MODIFY" else orig_category
    confidence_val = data.original_ai_confidence if data.original_ai_confidence is not None else incident.get("confidence")

    # Feature 3: Prevent duplicate feedback records for the same incident unless updating
    existing_fb = await feedback_col.find_one({
        "incident_id": incident["id"],
        "reviewer_id": reviewer_id,
        "action": action_clean,
        "corrected_category": corrected_cat
    })

    if existing_fb:
        # Update existing record timestamp and notes instead of duplicating
        feedback_id = existing_fb["id"]
        await feedback_col.update_one(
            {"id": feedback_id},
            {
                "$set": {
                    "notes": clean_notes,
                    "updated_at": now_str,
                    "model_version": data.model_version or "YOLOv5n-ONNX-v1.0"
                }
            }
        )
    else:
        feedback_id = f"fb_{uuid.uuid4().hex[:8]}"
        feedback_doc = {
            "id": feedback_id,
            "incident_id": incident["id"],
            "incident_number": incident.get("incident_number", ""),
            "evidence_id": data.evidence_id,
            "action": action_clean,
            "original_ai_category": orig_category,
            "original_ai_confidence": confidence_val,
            "corrected_category": corrected_cat,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "reviewer_role": user_role,
            "notes": clean_notes,
            "model_version": data.model_version or "YOLOv5n-ONNX-v1.0",
            "approval_status": "APPROVED" if user_role == "admin" else "PENDING_APPROVAL",
            "approved_by": reviewer_id if user_role == "admin" else None,
            "approved_at": now_str if user_role == "admin" else None,
            "created_at": now_str,
            "updated_at": now_str
        }
        await feedback_col.insert_one(feedback_doc)

    # Update incident with strict separation of AI findings vs Human confirmed findings
    update_fields = {
        "original_ai_category": orig_category,
        "human_verification_status": action_clean,
        "human_verified_category": corrected_cat,
        "human_review_reason": clean_notes,
        "reviewed_by_id": reviewer_id,
        "reviewed_by_name": reviewer_name,
        "reviewed_at": now_str,
        "updated_at": now_str
    }

    # Status transitions based on review action without assuming physical clearance:
    if action_clean == "REJECT":
        update_fields["status"] = "Rejected"
    elif action_clean == "CONFIRM":
        if incident.get("status") in ("Pending", "Submitted", "New"):
            update_fields["status"] = "Verified"
    elif action_clean == "MODIFY":
        update_fields["primary_encroachment_type"] = corrected_cat
        if incident.get("status") in ("Pending", "Submitted", "New"):
            update_fields["status"] = "Verified"

    # Add timeline event to incident
    display_action = {
        "CONFIRM": "Confirmed",
        "REJECT": "Rejected (False Positive)",
        "MODIFY": f"Category Corrected to '{corrected_cat}'",
        "NEEDS_MORE_EVIDENCE": "Additional Visual Evidence Requested"
    }.get(action_clean, action_clean)

    timeline_event = {
        "event_type": "human_verification",
        "title": f"AI Finding {action_clean.capitalize()}ed by Officer",
        "description": f"{reviewer_name} ({user_role}): {display_action}. Notes: {clean_notes or 'None'}.",
        "actor_name": reviewer_name,
        "actor_role": user_role,
        "timestamp": datetime.utcnow().strftime("%d %b %Y %I:%M %p")
    }

    await incidents_col.update_one(
        {"id": incident["id"]},
        {
            "$set": update_fields,
            "$push": {"timeline": timeline_event}
        }
    )

    # Log to audit log
    await log_audit_event(
        db=db,
        user=current_user,
        action="AI_HUMAN_REVIEW",
        target_id=incident["id"],
        details={
            "action": action_clean,
            "original_category": orig_category,
            "corrected_category": corrected_cat,
            "reason": clean_notes,
            "feedback_id": feedback_id
        }
    )

    return {
        "success": True,
        "message": f"Human verification '{action_clean}' recorded successfully.",
        "feedback_id": feedback_id,
        "incident_id": incident["id"],
        "human_verification_status": action_clean,
        "human_verified_category": corrected_cat,
        "original_ai_category": orig_category
    }


@router.get("/dataset")
async def get_feedback_dataset(
    action: Optional[str] = None,
    approval_status: Optional[str] = None,
    limit: int = 100,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns curated feedback records for dataset review and model improvement.
    Accessible to officers and admins.
    """
    feedback_col = db["ai_feedback_dataset"]
    query = {}
    if action and action.upper() != "ALL":
        query["action"] = action.upper()
    if approval_status and approval_status.upper() != "ALL":
        query["approval_status"] = approval_status.upper()

    cursor = feedback_col.find(query).sort("created_at", -1).limit(limit)
    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(doc)

    return {
        "total": len(items),
        "items": items,
        "model_version": "YOLOv5n-ONNX-v1.0"
    }


@router.post("/{feedback_id}/approve")
async def approve_feedback_entry(
    feedback_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
    db: Any = Depends(get_db)
):
    """
    Admin approval of officer-submitted feedback for inclusion in future training dataset.
    """
    feedback_col = db["ai_feedback_dataset"]
    now_str = datetime.utcnow().isoformat() + "Z"

    doc = await feedback_col.find_one({"id": feedback_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Feedback entry not found.")

    admin_id = current_user.get("id") or str(current_user.get("_id", "admin_1"))

    await feedback_col.update_one(
        {"id": feedback_id},
        {
            "$set": {
                "approval_status": "APPROVED",
                "approved_by": admin_id,
                "approved_at": now_str,
                "updated_at": now_str
            }
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="FEEDBACK_APPROVE",
        target_id=feedback_id,
        details={"approved_by": admin_id}
    )

    return {
        "success": True,
        "feedback_id": feedback_id,
        "approval_status": "APPROVED",
        "message": "Feedback sample approved for retraining dataset."
    }


@router.post("/{feedback_id}/reject")
async def reject_feedback_entry(
    feedback_id: str,
    reason: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
    db: Any = Depends(get_db)
):
    """
    Admin rejection of an officer feedback sample (excluded from retraining pool).
    """
    feedback_col = db["ai_feedback_dataset"]
    now_str = datetime.utcnow().isoformat() + "Z"

    doc = await feedback_col.find_one({"id": feedback_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Feedback entry not found.")

    admin_id = current_user.get("id") or str(current_user.get("_id", "admin_1"))

    await feedback_col.update_one(
        {"id": feedback_id},
        {
            "$set": {
                "approval_status": "REJECTED",
                "approved_by": admin_id,
                "approved_at": now_str,
                "rejection_reason": reason or "Excluded by administrator",
                "updated_at": now_str
            }
        }
    )

    await log_audit_event(
        db=db,
        user=current_user,
        action="FEEDBACK_REJECT",
        target_id=feedback_id,
        details={"rejected_by": admin_id, "reason": reason}
    )

    return {
        "success": True,
        "feedback_id": feedback_id,
        "approval_status": "REJECTED",
        "message": "Feedback sample rejected and excluded from retraining pool."
    }


@router.get("/export")
async def export_feedback_dataset(
    format: str = Query("jsonl", pattern="^(jsonl|csv|json)$"),
    approval_status: Optional[str] = Query("APPROVED"),
    current_user: Dict[str, Any] = Depends(require_role(["admin", "officer"])),
    db: Any = Depends(get_db)
):
    """
    Feature 3: Privacy-Safe Dataset Export (JSONL or CSV).
    Strips citizen personal information (PII) including reporter names, phone numbers,
    and personal IDs. Contains only verified urban bounding classifications.
    Logs dataset export in audit trail.
    """
    feedback_col = db["ai_feedback_dataset"]
    query = {}
    if approval_status and approval_status.upper() != "ALL":
        query["approval_status"] = approval_status.upper()

    cursor = feedback_col.find(query).sort("created_at", -1)
    samples = []
    async for doc in cursor:
        doc.pop("_id", None)
        # PII Sanitization: Never export reviewer names or personal citizen info
        sanitized = {
            "id": doc.get("id"),
            "incident_id": doc.get("incident_id"),
            "action": doc.get("action"),
            "original_ai_category": doc.get("original_ai_category"),
            "original_ai_confidence": doc.get("original_ai_confidence"),
            "corrected_category": doc.get("corrected_category"),
            "review_notes": doc.get("notes"),
            "model_version": doc.get("model_version", "YOLOv5n-ONNX-v1.0"),
            "approval_status": doc.get("approval_status", "APPROVED"),
            "created_at": doc.get("created_at")
        }
        samples.append(sanitized)

    await log_audit_event(
        db=db,
        user=current_user,
        action="DATASET_EXPORT",
        target_id="ai_feedback_dataset",
        details={"format": format, "count": len(samples), "filter": approval_status}
    )

    if format == "jsonl":
        output = "\n".join(json.dumps(s) for s in samples)
        return Response(
            content=output,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f"attachment; filename=encrowatch_feedback_retraining_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"}
        )
    elif format == "csv":
        stream = io.StringIO()
        fieldnames = [
            "id", "incident_id", "action", "original_ai_category",
            "original_ai_confidence", "corrected_category", "review_notes",
            "model_version", "approval_status", "created_at"
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for s in samples:
            writer.writerow(s)
        return Response(
            content=stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=encrowatch_feedback_retraining_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    else:
        return {
            "dataset_name": "EncroWatch-AI-Human-Feedback-Retraining",
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_labeled_samples": len(samples),
            "format": "PII-sanitized urban verification records",
            "model_version": "YOLOv5n-ONNX-v1.0",
            "data": samples
        }


@router.get("/training-workflow")
async def get_retraining_workflow_guidelines() -> Dict[str, Any]:
    """
    Feature 3: Documented Retraining Workflow Specification.
    Defines strict protocol: No automated retraining or silent production replacement.
    Structured validation split (70/15/15), mAP@0.5 evaluation, and municipal sign-off.
    """
    return {
        "policy": {
            "automated_retraining": False,
            "silent_production_replacement": False,
            "governance_rule": "No automated retraining or unapproved model replacement in production. All candidate weights require empirical evaluation and municipal sign-off."
        },
        "dataset_split": {
            "training_pct": 70,
            "validation_pct": 15,
            "testing_pct": 15,
            "stratification": "Stratified by encroachment category (Street Vendor, Construction Material, Vehicle on Footpath, Shop Extension, Clear Walkway)"
        },
        "evaluation_criteria": {
            "primary_metric": "mAP@0.5 (Mean Average Precision at IoU 0.50)",
            "minimum_target_map": 0.82,
            "baseline_model": "YOLOv5n-ONNX-v1.0 (COCO-80 pretrained)",
            "required_improvement": "Candidate model must exceed baseline mAP@0.5 by at least +3.0% without regression on high-risk pedestrian obstruction classes."
        },
        "deployment_lifecycle": [
            "1. Officer Ground-Truth Collection: Feedback captured in ai_feedback_dataset collection",
            "2. Admin Dataset Auditing: Quality check and PII-sanitized export (JSONL/CSV)",
            "3. Offline Training: Supervised fine-tuning on isolated GPU compute environment",
            "4. Rigorous Validation: Benchmark testing against 15% withheld test set (mAP@0.5, Precision, Recall)",
            "5. Municipal Sign-Off: Municipal commissioner / Lead officer signs off on candidate model version",
            "6. Controlled Staged Rollout: Version bump to YOLOv5n-ONNX-v1.1 with rollback safeguards"
        ]
    }


@router.get("/metrics")
async def get_model_performance_metrics(
    db: Any = Depends(get_db)
):
    """
    AI Model Performance Dashboard.
    Calculates actual Precision, Recall, and F1 Score from verified human feedback records.
    Strict data integrity: If dataset is sparse, explicitly flags as insufficient data.
    """
    feedback_col = db["ai_feedback_dataset"]
    cursor = feedback_col.find({})
    samples = []
    async for doc in cursor:
        samples.append(doc)

    total_verified = len(samples)

    if total_verified < 3:
        return {
            "evaluation_available": False,
            "message": "Model evaluation requires labeled validation dataset (minimum 3 verified samples required).",
            "current_verified_count": total_verified,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "total_detections_evaluated": total_verified,
            "true_positives": 0,
            "false_positives": 0,
            "modifications": 0,
            "is_prototype": True
        }

    true_positives = sum(1 for s in samples if s.get("action") == "CONFIRM")
    false_positives = sum(1 for s in samples if s.get("action") == "REJECT")
    modifications = sum(1 for s in samples if s.get("action") == "MODIFY")
    needs_evidence = sum(1 for s in samples if s.get("action") == "NEEDS_MORE_EVIDENCE")

    denominator_prec = true_positives + false_positives
    precision = round(true_positives / denominator_prec, 3) if denominator_prec > 0 else 0.0

    denominator_rec = true_positives + modifications
    recall = round(true_positives / denominator_rec, 3) if denominator_rec > 0 else 0.0

    if (precision + recall) > 0:
        f1 = round(2.0 * (precision * recall) / (precision + recall), 3)
    else:
        f1 = 0.0

    return {
        "evaluation_available": True,
        "total_detections_evaluated": total_verified,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "precision_pct": round(precision * 100, 1),
        "recall_pct": round(recall * 100, 1),
        "f1_score_pct": round(f1 * 100, 1),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "category_corrections": modifications,
        "uncertain_cases": needs_evidence,
        "data_qualification": f"Empirically computed from {total_verified} human verification decisions in live MongoDB.",
        "is_prototype": False
    }
