from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class NotificationCreate(BaseModel):
    recipient_id: str
    recipient_role: str = "citizen"  # "citizen", "officer", "admin"
    type: str  # "STATUS_CHANGE", "EVIDENCE_REQUESTED", "RESOLUTION_SUBMITTED", "RESOLUTION_VERIFIED", "RESOLUTION_REJECTED", "INCIDENT_REOPENED", "SLA_BREACH", "ESCALATION", "OFFICER_ASSIGNED", "NEW_REPORT"
    title: str
    message: str
    incident_id: Optional[str] = None
    incident_number: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class NotificationItem(BaseModel):
    id: str
    recipient_id: str
    recipient_role: str
    type: str
    title: str
    message: str
    incident_id: Optional[str] = None
    incident_number: Optional[str] = None
    is_read: bool = False
    created_at: str
    data: Optional[Dict[str, Any]] = None

class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationItem]

class UnreadCountResponse(BaseModel):
    unread_count: int
