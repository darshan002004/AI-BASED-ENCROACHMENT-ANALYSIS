"""
Audit Log Router & Cryptographic Integrity Verification (Batch 5 - Feature 4).
Logs administrative, officer, and system actions across the lifecycle with tamper-evident
SHA-256 hash chaining, outcome tracking, and multi-field governance filtering.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime
from app.database import get_db
from app.models.audit import AuditLogCreate, AuditLogItem
from app.auth import get_current_user
from app.utils.security import (
    GENESIS_HASH,
    compute_audit_record_hash,
    verify_audit_chain_integrity
)

logger = logging.getLogger("encrowatch.audit")
router = APIRouter(prefix="/audit", tags=["Audit Log"])


async def log_audit_event(
    db: Any,
    user: Dict[str, Any],
    action: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    outcome: str = "SUCCESS"
) -> Dict[str, Any]:
    """
    Internal helper to write tamper-evident entries to the audit_logs collection.
    Chains each record's SHA-256 hash to the previous record's hash.
    """
    try:
        audit_col = db["audit_logs"]

        # Fetch latest appended record to get prev_hash
        all_records = await audit_col.find({}).to_list(10000)
        prev_hash = all_records[-1].get("record_hash", GENESIS_HASH) if all_records else GENESIS_HASH

        now_iso = datetime.utcnow().isoformat() + "Z"
        rec_id = f"aud_{uuid.uuid4().hex[:10]}"
        user_id = user.get("id") or str(user.get("_id", "system"))
        user_name = user.get("full_name") or user.get("name") or "System"
        user_role = user.get("role") or "system"
        clean_action = action.upper().strip()
        clean_target = str(target_id or "")
        clean_details = details or {}

        # Strip any sensitive tokens, passwords, or secrets from details
        safe_details = {}
        for k, v in clean_details.items():
            if any(sens in k.lower() for sens in ("password", "token", "secret", "auth", "key")):
                safe_details[k] = "[REDACTED]"
            else:
                safe_details[k] = v

        details_str = str(safe_details)
        record_hash = compute_audit_record_hash(
            record_id=rec_id,
            timestamp=now_iso,
            user_id=user_id,
            action=clean_action,
            target_id=clean_target,
            outcome=outcome.upper(),
            details_str=details_str,
            prev_hash=prev_hash
        )

        doc = {
            "id": rec_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "action": clean_action,
            "target_id": clean_target,
            "details": safe_details,
            "outcome": outcome.upper(),
            "prev_hash": prev_hash,
            "record_hash": record_hash,
            "timestamp": now_iso
        }
        await audit_col.insert_one(doc)
        return doc
    except Exception as e:
        logger.error(f"Audit log write failed: {str(e)}", exc_info=True)
        # Fallback dictionary so caller does not crash, but logs are recorded in system error log
        return {
            "id": "aud_fallback_error",
            "action": action,
            "outcome": "LOG_FAILED",
            "error": str(e)
        }


@router.get("/logs")
async def get_audit_logs(
    action: Optional[str] = None,
    user_role: Optional[str] = None,
    actor: Optional[str] = None,
    resource: Optional[str] = None,
    outcome: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns audit logs with multi-field governance filters.
    Restricted to Administrator and Officer roles (Citizens receive HTTP 403).
    """
    role = (current_user.get("role") or "citizen").lower()
    if role not in ("admin", "officer"):
        await log_audit_event(
            db=db,
            user=current_user,
            action="PERMISSION_DENIED",
            target_id="audit_logs",
            details={"attempted_action": "VIEW_AUDIT_LOGS"},
            outcome="DENIED"
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Audit log inspection requires Administrator or Officer role."
        )

    audit_col = db["audit_logs"]
    query: Dict[str, Any] = {}

    if action and action != "ALL":
        query["action"] = action.upper()
    if user_role and user_role != "ALL":
        query["user_role"] = user_role.lower()
    if outcome and outcome != "ALL":
        query["outcome"] = outcome.upper()
    if resource:
        query["target_id"] = {"$regex": resource, "$options": "i"}

    # Time range filters
    time_filter = {}
    if start_date:
        time_filter["$gte"] = start_date
    if end_date:
        time_filter["$lte"] = end_date
    if time_filter:
        query["timestamp"] = time_filter

    cursor = audit_col.find(query).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(limit)

    logs = []
    for doc in docs:
        doc.pop("_id", None)
        # Actor filtering if specified
        if actor:
            act_lower = actor.lower()
            name_match = act_lower in (doc.get("user_name") or "").lower()
            id_match = act_lower in (doc.get("user_id") or "").lower()
            if not (name_match or id_match):
                continue
        logs.append(doc)

    return {
        "total": len(logs),
        "items": logs,
        "filters_applied": {
            "action": action,
            "user_role": user_role,
            "actor": actor,
            "outcome": outcome,
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.get("/verify-integrity")
async def verify_audit_log_integrity(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Verifies cryptographic SHA-256 hash chaining of all stored audit logs.
    Restricted to Administrator role.
    """
    role = (current_user.get("role") or "citizen").lower()
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Cryptographic audit log integrity verification is restricted to administrators."
        )

    audit_col = db["audit_logs"]
    # Sequential traversal in append order from genesis
    docs = await audit_col.find({}).to_list(10000)
    for d in docs:
        d.pop("_id", None)

    verification_result = verify_audit_chain_integrity(docs)
    return verification_result


@router.post("/logs")
async def record_audit_log(
    entry: AuditLogCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Explicitly records an audit entry.
    Restricted to Officer and Admin roles.
    """
    role = (current_user.get("role") or "citizen").lower()
    if role not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Forbidden: Cannot create audit entries.")

    doc = await log_audit_event(
        db=db,
        user=current_user,
        action=entry.action,
        target_id=entry.target_id,
        details=entry.details
    )
    doc.pop("_id", None)
    return doc
