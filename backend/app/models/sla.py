from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SLARule(BaseModel):
    category: str  # "Street Vendor", "Vehicle", "Construction Material", "Bollard", "All"
    priority: str  # "Low", "Medium", "High", "Critical", "Urgent"
    response_target_hours: int = Field(ge=1, default=24)
    resolution_target_hours: int = Field(ge=1, default=72)
    warning_threshold_pct: float = Field(default=0.75, ge=0.1, le=0.95)
    auto_escalate: bool = True
    escalation_role: str = "admin"

class SLARuleUpdateRequest(BaseModel):
    rules: List[SLARule]

class SLAMilestone(BaseModel):
    milestone_name: str
    target_hours: int
    deadline: str
    completed_at: Optional[str] = None
    status: str  # "PENDING", "APPROACHING_DEADLINE", "OVERDUE", "COMPLETED", "PAUSED"
    elapsed_hours: float
    remaining_hours: float

class IncidentSLAStatus(BaseModel):
    incident_id: str
    incident_number: str
    category: str
    priority: str
    created_at: str
    overall_status: str  # "ON_TRACK", "APPROACHING_DEADLINE", "OVERDUE", "BREACHED", "COMPLETED"
    is_escalated: bool = False
    escalation_level: int = 0
    escalated_at: Optional[str] = None
    milestones: Dict[str, SLAMilestone] = {}
    time_to_respond_hours: Optional[float] = None
    time_to_resolve_hours: Optional[float] = None

class EscalationProcessResult(BaseModel):
    total_evaluated: int
    escalated_count: int
    already_escalated_count: int
    on_track_count: int
    escalated_incidents: List[str] = []
