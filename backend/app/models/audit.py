"""
Audit Log Models (Upgrade 25).
Logs system and user actions for full transparency and governance.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    user_id: Optional[str] = "system"
    user_name: Optional[str] = "System Automated"
    user_role: Optional[str] = "system"
    action: str  # LOGIN, INCIDENT_CREATE, AI_VERIFY, STATUS_CHANGE, OFFICER_ASSIGN, MERGE_DUPLICATE, REPORT_GENERATE, AI_CORRECT
    target_id: Optional[str] = None  # incident_id, user_id, etc.
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None


class AuditLogItem(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_role: str
    action: str
    target_id: Optional[str] = None
    details: Dict[str, Any] = {}
    timestamp: str
