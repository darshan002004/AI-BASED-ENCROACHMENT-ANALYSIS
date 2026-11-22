import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.services.notification_service import notification_service
from app.routers.audit import log_audit_event

logger = logging.getLogger("encrowatch.sla")

DEFAULT_SLA_RULES = [
    {
        "category": "All",
        "priority": "Critical",
        "response_target_hours": 4,
        "resolution_target_hours": 24,
        "warning_threshold_pct": 0.75,
        "auto_escalate": True,
        "escalation_role": "admin"
    },
    {
        "category": "All",
        "priority": "High",
        "response_target_hours": 12,
        "resolution_target_hours": 48,
        "warning_threshold_pct": 0.75,
        "auto_escalate": True,
        "escalation_role": "admin"
    },
    {
        "category": "All",
        "priority": "Medium",
        "response_target_hours": 24,
        "resolution_target_hours": 96,
        "warning_threshold_pct": 0.75,
        "auto_escalate": True,
        "escalation_role": "admin"
    },
    {
        "category": "All",
        "priority": "Low",
        "response_target_hours": 48,
        "resolution_target_hours": 168,
        "warning_threshold_pct": 0.75,
        "auto_escalate": True,
        "escalation_role": "admin"
    }
]

def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        clean = dt_str.rstrip("Z")
        return datetime.fromisoformat(clean)
    except Exception:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
        except Exception:
            return None

class SLAEngine:
    """
    Municipal Service Level Agreement (SLA) & Escalation Service.
    """

    async def get_rules(self, db: Any) -> List[Dict[str, Any]]:
        col = db["sla_rules"]
        rules = await col.find({}).to_list(100)
        if not rules:
            for r in DEFAULT_SLA_RULES:
                await col.insert_one(dict(r))
            rules = await col.find({}).to_list(100)
        for r in rules:
            r.pop("_id", None)
        return rules

    async def update_rules(self, db: Any, new_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        col = db["sla_rules"]
        await col.delete_many({})
        for r in new_rules:
            await col.insert_one(dict(r))
        return await self.get_rules(db)

    def find_matching_rule(self, rules: List[Dict[str, Any]], category: str, priority_or_severity: str) -> Dict[str, Any]:
        target_prio = (priority_or_severity or "Medium").capitalize()
        # 1. Exact match on category and priority
        for r in rules:
            if r.get("category", "").lower() == category.lower() and r.get("priority", "").lower() == target_prio.lower():
                return r
        # 2. Priority match with category "All"
        for r in rules:
            if r.get("category") == "All" and r.get("priority", "").lower() == target_prio.lower():
                return r
        # 3. Fallback
        return DEFAULT_SLA_RULES[2]  # Medium fallback

    def calculate_incident_sla(self, incident: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        created_dt = parse_iso_datetime(incident.get("created_at")) or parse_iso_datetime(incident.get("date_reported")) or now
        current_status = incident.get("status", "Pending")
        is_paused = current_status == "Awaiting Evidence"

        resp_target_hours = rule.get("response_target_hours", 24)
        resol_target_hours = rule.get("resolution_target_hours", 96)
        warn_pct = rule.get("warning_threshold_pct", 0.75)

        resp_deadline = created_dt + timedelta(hours=resp_target_hours)
        resol_deadline = created_dt + timedelta(hours=resol_target_hours)

        # Milestone 1: Initial Response / Assignment
        assigned_officer_id = incident.get("assigned_officer_id")
        response_completed_dt = parse_iso_datetime(incident.get("reviewed_at")) or parse_iso_datetime(incident.get("assigned_at"))
        if not response_completed_dt and assigned_officer_id:
            response_completed_dt = parse_iso_datetime(incident.get("updated_at")) or created_dt

        elapsed_resp_hours = (now - created_dt).total_seconds() / 3600.0
        if response_completed_dt:
            resp_status = "COMPLETED"
            time_to_respond = (response_completed_dt - created_dt).total_seconds() / 3600.0
            rem_resp_hours = 0.0
        elif is_paused:
            resp_status = "PAUSED"
            time_to_respond = None
            rem_resp_hours = max(0.0, (resp_deadline - now).total_seconds() / 3600.0)
        elif now > resp_deadline:
            resp_status = "OVERDUE"
            time_to_respond = None
            rem_resp_hours = -((now - resp_deadline).total_seconds() / 3600.0)
        elif elapsed_resp_hours >= (resp_target_hours * warn_pct):
            resp_status = "APPROACHING_DEADLINE"
            time_to_respond = None
            rem_resp_hours = max(0.0, (resp_deadline - now).total_seconds() / 3600.0)
        else:
            resp_status = "PENDING"
            time_to_respond = None
            rem_resp_hours = max(0.0, (resp_deadline - now).total_seconds() / 3600.0)

        # Milestone 2: Resolution
        is_resolved = current_status in ("Resolved", "Resolved - Verified", "Closed")
        resolution_completed_dt = parse_iso_datetime(incident.get("resolution_verified_at")) or parse_iso_datetime(incident.get("resolution_submitted_at"))
        if is_resolved and not resolution_completed_dt:
            resolution_completed_dt = parse_iso_datetime(incident.get("resolution_date")) or now

        elapsed_resol_hours = (now - created_dt).total_seconds() / 3600.0
        if is_resolved and resolution_completed_dt:
            resol_status = "COMPLETED"
            time_to_resolve = (resolution_completed_dt - created_dt).total_seconds() / 3600.0
            rem_resol_hours = 0.0
        elif is_paused:
            resol_status = "PAUSED"
            time_to_resolve = None
            rem_resol_hours = max(0.0, (resol_deadline - now).total_seconds() / 3600.0)
        elif now > resol_deadline:
            resol_status = "OVERDUE"
            time_to_resolve = None
            rem_resol_hours = -((now - resol_deadline).total_seconds() / 3600.0)
        elif elapsed_resol_hours >= (resol_target_hours * warn_pct):
            resol_status = "APPROACHING_DEADLINE"
            time_to_resolve = None
            rem_resol_hours = max(0.0, (resol_deadline - now).total_seconds() / 3600.0)
        else:
            resol_status = "PENDING"
            time_to_resolve = None
            rem_resol_hours = max(0.0, (resol_deadline - now).total_seconds() / 3600.0)

        # Overall Status
        if resol_status == "COMPLETED":
            overall = "COMPLETED"
        elif resol_status == "OVERDUE" or resp_status == "OVERDUE":
            overall = "OVERDUE"
        elif is_paused:
            overall = "PAUSED"
        elif resol_status == "APPROACHING_DEADLINE" or resp_status == "APPROACHING_DEADLINE":
            overall = "APPROACHING_DEADLINE"
        else:
            overall = "ON_TRACK"

        return {
            "incident_id": str(incident.get("id") or incident["_id"]),
            "incident_number": incident.get("incident_number", "ENC-UNKNOWN"),
            "category": incident.get("primary_encroachment_type", "Street Vendor"),
            "priority": rule.get("priority", "Medium"),
            "created_at": created_dt.isoformat() + "Z",
            "overall_status": overall,
            "is_escalated": bool(incident.get("is_escalated", False)),
            "escalation_level": int(incident.get("escalation_level", 0)),
            "escalated_at": incident.get("escalated_at"),
            "time_to_respond_hours": round(time_to_respond, 2) if time_to_respond is not None else None,
            "time_to_resolve_hours": round(time_to_resolve, 2) if time_to_resolve is not None else None,
            "milestones": {
                "initial_response": {
                    "milestone_name": "Initial Response / Assignment",
                    "target_hours": resp_target_hours,
                    "deadline": resp_deadline.isoformat() + "Z",
                    "completed_at": response_completed_dt.isoformat() + "Z" if response_completed_dt else None,
                    "status": resp_status,
                    "elapsed_hours": round(elapsed_resp_hours, 2),
                    "remaining_hours": round(rem_resp_hours, 2)
                },
                "final_resolution": {
                    "milestone_name": "Resolution & Verification",
                    "target_hours": resol_target_hours,
                    "deadline": resol_deadline.isoformat() + "Z",
                    "completed_at": resolution_completed_dt.isoformat() + "Z" if resolution_completed_dt else None,
                    "status": resol_status,
                    "elapsed_hours": round(elapsed_resol_hours, 2),
                    "remaining_hours": round(rem_resol_hours, 2)
                }
            }
        }

    async def evaluate_and_escalate_incidents(self, db: Any, specific_incident_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Idempotent background SLA evaluation.
        Identifies overdue incidents, sets escalation flag, notifies assigned officer and supervisors.
        """
        incidents_col = db["incidents"]
        rules = await self.get_rules(db)

        query: Dict[str, Any] = {"status": {"$nin": ["Resolved", "Resolved - Verified", "Closed", "Rejected"]}}
        if specific_incident_id:
            query = {"$or": [{"_id": specific_incident_id}, {"id": specific_incident_id}]}

        cursor = incidents_col.find(query)
        incidents = await cursor.to_list(500)

        now = datetime.utcnow()
        now_str = now.strftime("%d %b %Y %I:%M %p")
        iso_now = now.isoformat() + "Z"

        escalated_incidents = []
        already_escalated_count = 0
        on_track_count = 0

        for inc in incidents:
            cat = inc.get("primary_encroachment_type", "Street Vendor")
            prio = inc.get("priority_rank") or inc.get("severity") or "Medium"
            rule = self.find_matching_rule(rules, cat, prio)

            sla_calc = self.calculate_incident_sla(inc, rule)

            # Check if overdue
            if sla_calc["overall_status"] == "OVERDUE":
                is_already_escalated = inc.get("is_escalated", False)
                last_escalated_at = inc.get("escalated_at")
                
                # Deduplication / Cooldown: Do not re-escalate if escalated within past 24 hours
                if is_already_escalated and last_escalated_at:
                    last_dt = parse_iso_datetime(last_escalated_at)
                    if last_dt and (now - last_dt) < timedelta(hours=24):
                        already_escalated_count += 1
                        continue

                new_level = int(inc.get("escalation_level", 0)) + 1
                inc_id = str(inc.get("id") or inc["_id"])
                inc_num = inc.get("incident_number", "ENC-UNKNOWN")

                timeline_event = {
                    "event_type": "sla_escalation",
                    "title": f"SLA Breach Escalation (Level {new_level})",
                    "description": f"Target resolution time breached for {prio} priority case. Case escalated to Municipal Supervisor.",
                    "actor_name": "Municipal SLA Engine",
                    "actor_role": "system",
                    "timestamp": now_str
                }

                await incidents_col.update_one(
                    {"_id": inc["_id"]},
                    {
                        "$set": {
                            "is_escalated": True,
                            "escalation_level": new_level,
                            "escalated_at": iso_now,
                            "sla_status": sla_calc,
                            "updated_at": iso_now
                        },
                        "$push": {
                            "timeline": timeline_event
                        }
                    }
                )

                # Send notifications to officer and admins
                assigned_officer_id = inc.get("assigned_officer_id")
                if assigned_officer_id:
                    await notification_service.notify_officer(
                        db=db,
                        officer_id=assigned_officer_id,
                        notif_type="SLA_BREACH",
                        title=f"SLA Breach Warning: {inc_num}",
                        message=f"Incident {inc_num} at {inc.get('location_name')} is overdue and has been escalated.",
                        incident_id=inc_id,
                        incident_number=inc_num,
                        data={"escalation_level": new_level}
                    )

                await notification_service.notify_admins(
                    db=db,
                    notif_type="ESCALATION",
                    title=f"Municipal SLA Escalation: {inc_num}",
                    message=f"Incident {inc_num} ({cat}, {prio}) exceeded resolution target and requires administrative review.",
                    incident_id=inc_id,
                    incident_number=inc_num,
                    data={"escalation_level": new_level, "assigned_officer": inc.get("assigned_officer_name")}
                )

                # Log to audit trail
                await log_audit_event(
                    db=db,
                    user={"id": "system", "role": "system", "full_name": "SLA Engine"},
                    action="SLA_ESCALATED",
                    target_id=inc_id,
                    details={"incident_number": inc_num, "escalation_level": new_level, "priority": prio}
                )

                escalated_incidents.append(inc_num)
            else:
                on_track_count += 1
                # Store calculated SLA status without mutating core risk
                await incidents_col.update_one(
                    {"_id": inc["_id"]},
                    {"$set": {"sla_status": sla_calc}}
                )

        return {
            "total_evaluated": len(incidents),
            "escalated_count": len(escalated_incidents),
            "already_escalated_count": already_escalated_count,
            "on_track_count": on_track_count,
            "escalated_incidents": escalated_incidents
        }

sla_engine = SLAEngine()
