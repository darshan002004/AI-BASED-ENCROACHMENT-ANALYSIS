from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class PublicIncidentItem(BaseModel):
    id: Optional[str] = None
    incident_number: str
    category: str
    public_status: str  # "Under Investigation", "Action Required", "Verified Resolved", "Closed", "Reported"
    generalized_location: str  # Ward/Neighborhood e.g. "Indiranagar, Ward 112"
    generalized_latitude: float  # Rounded to 2 decimals (~1.1km grid)
    generalized_longitude: float
    date_reported: str
    resolution_date: Optional[str] = None
    verified_resolved: bool = False
    has_privacy_cleared_image: bool = False
    privacy_image_url: Optional[str] = None  # ONLY blurred privacy photo, never raw unredacted

class PublicStatisticsResponse(BaseModel):
    total_reports_received: int
    verified_resolutions: int
    officer_reported_pending_verification: int
    open_cases: int
    overdue_cases: int
    resolution_rate_pct: float
    average_resolution_days: float
    category_breakdown: Dict[str, int]
    ward_breakdown: Dict[str, int]
    time_period: str
    methodology: Dict[str, str]
