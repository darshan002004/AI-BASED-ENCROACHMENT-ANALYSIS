from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class CitizenFeedbackSubmit(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Overall satisfaction rating from 1 to 5")
    satisfaction_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Alias for satisfaction rating")
    timeliness_rating: Optional[int] = Field(ge=1, le=5, default=5, description="Satisfaction with resolution speed")
    satisfaction_level: Optional[str] = Field(default="Satisfied", description="Very Satisfied, Satisfied, Neutral, Dissatisfied, Very Dissatisfied")
    comments: Optional[str] = Field(default=None, max_length=1000)
    feedback_text: Optional[str] = Field(default=None, max_length=1000)

    def get_rating(self) -> int:
        if self.satisfaction_rating is not None:
            return self.satisfaction_rating
        if self.rating is not None:
            return self.rating
        return 5

    def get_comments(self) -> Optional[str]:
        return self.feedback_text if self.feedback_text is not None else self.comments

class CitizenFeedbackItem(BaseModel):
    id: str
    incident_id: str
    incident_number: str
    reporter_id: str
    reporter_name: Optional[str] = "Citizen"
    rating: int
    satisfaction_rating: Optional[int] = None
    timeliness_rating: int = 5
    satisfaction_level: str = "Satisfied"
    comments: Optional[str] = None
    feedback_text: Optional[str] = None
    created_at: str
    updated_at: str
    is_updated: bool = False

class ServiceQualitySummary(BaseModel):
    total_feedback_count: int
    total_feedbacks: Optional[int] = None
    average_rating: float
    average_satisfaction: Optional[float] = None
    average_timeliness: float
    rating_distribution: Dict[str, int]
    satisfaction_breakdown: Dict[str, int]
    response_rate_pct: float
    recent_comments: List[Dict[str, Any]] = []
