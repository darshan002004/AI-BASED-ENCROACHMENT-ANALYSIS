"""
AI Feedback Loop Models (Batch 3 Upgrade - Features 1 & 3).
Captures human-in-the-loop verification, corrections, approval status, and retraining dataset schemas.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class FeedbackSubmit(BaseModel):
    incident_id: str
    action: str  # CONFIRM, REJECT, MODIFY, NEEDS_MORE_EVIDENCE
    original_ai_category: str
    original_ai_confidence: Optional[float] = None
    corrected_category: Optional[str] = None
    notes: Optional[str] = None
    evidence_id: Optional[str] = None
    bbox_corrected: Optional[List[int]] = None
    model_version: Optional[str] = "YOLOv5n-ONNX-v1.0"


class FeedbackItem(BaseModel):
    id: str
    incident_id: str
    incident_number: Optional[str] = None
    evidence_id: Optional[str] = None
    action: str
    original_ai_category: str
    original_ai_confidence: Optional[float] = None
    corrected_category: Optional[str] = None
    reviewer_id: str
    reviewer_name: str
    reviewer_role: str
    notes: Optional[str] = None
    model_version: str = "YOLOv5n-ONNX-v1.0"
    approval_status: str = "APPROVED"  # PENDING_APPROVAL, APPROVED, REJECTED
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
