from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from app.database import get_db
from app.auth import get_current_user
from app.models.sla import SLARule, SLARuleUpdateRequest, IncidentSLAStatus, EscalationProcessResult
from app.services.sla_engine import sla_engine
from app.routers.audit import log_audit_event

router = APIRouter(prefix="/sla", tags=["Municipal SLA & Escalations"])

def require_admin(current_user: Dict[str, Any]):
    role = (current_user.get("role") or "citizen").lower()
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: SLA configuration and management requires Administrator privileges."
        )

@router.get("/rules", response_model=List[SLARule])
async def get_sla_rules(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns active municipal SLA response and resolution rules.
    Accessible to Admin and Officer roles.
    """
    role = (current_user.get("role") or "citizen").lower()
    if role not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Forbidden: SLA inspection requires municipal authorization.")
    return await sla_engine.get_rules(db)

@router.put("/rules", response_model=List[SLARule])
async def update_sla_rules(
    req: SLARuleUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Updates persistent municipal SLA rules.
    Restricted to Administrator role.
    """
    require_admin(current_user)
    updated = await sla_engine.update_rules(db, [r.model_dump() for r in req.rules])
    await log_audit_event(
        db=db,
        user=current_user,
        action="SLA_RULES_UPDATED",
        target_id="sla_rules",
        details={"updated_rules_count": len(updated)}
    )
    return updated

@router.post("/evaluate", response_model=EscalationProcessResult)
async def evaluate_sla_escalations(
    incident_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Evaluates active cases against configured SLA milestones and flags overdue incidents.
    Idempotent and safe on repeated calls.
    Restricted to Administrator and Officer roles.
    """
    role = (current_user.get("role") or "citizen").lower()
    if role not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Forbidden: Cannot trigger SLA evaluations.")
    
    result = await sla_engine.evaluate_and_escalate_incidents(db, specific_incident_id=incident_id)
    return result

@router.get("/incident/{incident_id}", response_model=IncidentSLAStatus)
async def get_incident_sla_status(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns real-time SLA status and milestone countdown for a specific incident.
    """
    incidents_col = db["incidents"]
    inc = await incidents_col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Access control: Citizen can only see SLA of their own report
    role = (current_user.get("role") or "citizen").lower()
    user_id = str(current_user.get("id") or current_user.get("_id"))
    if role == "citizen" and str(inc.get("reporter_id")) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot inspect another citizen's SLA tracking.")

    rules = await sla_engine.get_rules(db)
    cat = inc.get("primary_encroachment_type", "Street Vendor")
    prio = inc.get("priority_rank") or inc.get("severity") or "Medium"
    rule = sla_engine.find_matching_rule(rules, cat, prio)

    sla_info = sla_engine.calculate_incident_sla(inc, rule)
    return sla_info
