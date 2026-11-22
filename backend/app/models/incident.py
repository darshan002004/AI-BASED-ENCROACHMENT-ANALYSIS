from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class CommentItem(BaseModel):
    author_name: str
    role: str
    text: str
    timestamp: str

class SupportingReportItem(BaseModel):
    report_id: str
    reporter_id: str
    reporter_name: str
    image_url: str
    description: Optional[str] = None
    date_reported: str
    time_reported: str
    distance_meters: float
    match_score: float


class IncidentCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_name: str
    latitude: float
    longitude: float
    image_url: str
    annotated_image_url: Optional[str] = None
    primary_encroachment_type: str = "Street Vendor"
    detected_objects: List[Dict[str, Any]] = []
    occupied_area_sqm: Optional[float] = None
    footpath_area_sqm: Optional[float] = None
    footpath_width_m: Optional[float] = None
    obstructed_width_m: Optional[float] = None
    remaining_width_m: Optional[float] = None
    bottleneck_blockage_pct: Optional[float] = None
    is_calibrated: Optional[bool] = False
    calibration_mode: Optional[str] = "UNCALIBRATED_PIXEL_ONLY"
    footpath_roi_area_px: Optional[float] = None
    occupied_footpath_px: Optional[float] = None
    footpath_width_px: Optional[int] = None
    remaining_width_px: Optional[int] = None
    bottleneck_y_px: Optional[int] = None
    occupancy_percentage: float = 0.0
    accessibility_score: float = 100.0
    accessibility_status: str = "NEEDS HUMAN REVIEW"
    severity: str = "Medium"
    severity_reason: Optional[str] = None
    warnings: List[str] = []
    confidence: Optional[float] = None
    evidence_images: Optional[List[Dict[str, Any]]] = []
    privacy_image_url: Optional[str] = None
    privacy_protected: Optional[bool] = False
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    why_flagged: Optional[List[Dict[str, Any]]] = []
    probability_status: Optional[str] = None
    path_continuity: Optional[str] = None
    path_continuity_reason: Optional[str] = None
    accessibility_category: Optional[str] = None
    obstruction_impact: Optional[str] = "LOW"
    remaining_pedestrian_region_pct: Optional[float] = None
    persistence_sec: Optional[float] = None
    is_persistent: Optional[bool] = False
    potential_encroachment: Optional[str] = None
    ai_explanation: Optional[str] = None
    review_status: Optional[str] = "NEEDS_REVIEW"
    reasoning: Optional[Dict[str, Any]] = None
    priority_score: Optional[float] = None
    priority_rank: Optional[str] = None
    priority_action: Optional[str] = None
    duplicate_dismissed: Optional[bool] = False
    evidence_inconsistency_flag: Optional[bool] = False
    evidence_inconsistency_reason: Optional[str] = None
    risk_forecast: Optional[Dict[str, Any]] = None
    original_ai_category: Optional[str] = None
    human_verified_category: Optional[str] = None
    human_review_reason: Optional[str] = None
    reviewed_by_id: Optional[str] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[str] = None
    privacy_metadata: Optional[Dict[str, Any]] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    severity: Optional[str] = None
    inspection_notes: Optional[str] = None
    inspection_image_url: Optional[str] = None
    client_sync_id: Optional[str] = None
    expected_updated_at: Optional[str] = None
    force_resolve_conflict: Optional[bool] = False

class BatchSyncItem(BaseModel):
    client_sync_id: str
    incident_id: str
    status: Optional[str] = None
    inspection_notes: Optional[str] = None
    expected_updated_at: Optional[str] = None
    force_resolve_conflict: Optional[bool] = False
    timestamp: Optional[str] = None

class BatchSyncRequest(BaseModel):
    items: List[BatchSyncItem]

class BatchSyncResultItem(BaseModel):
    client_sync_id: str
    incident_id: str
    status: str  # "SYNCED", "CONFLICT", "FAILED", "ALREADY_SYNCED"
    message: str
    server_incident: Optional[Dict[str, Any]] = None

class BatchSyncResponse(BaseModel):
    total: int
    synced_count: int
    conflict_count: int
    failed_count: int
    results: List[BatchSyncResultItem]

class IncidentInspectionSubmit(BaseModel):
    inspection_image_url: str
    inspection_notes: str

class ResolutionSubmitRequest(BaseModel):
    resolution_notes: str
    after_image_url: str
    before_image_url: Optional[str] = None

class ResolutionReviewRequest(BaseModel):
    decision: str  # "ACCEPT" or "REJECT"
    reason: Optional[str] = None
    notes: Optional[str] = None
    review_notes: Optional[str] = None

class IncidentReopenRequest(BaseModel):
    reason: str
    new_evidence_image_url: Optional[str] = None

class CitizenCommentRequest(BaseModel):
    text: str
    evidence_image_url: Optional[str] = None

class IncidentResponse(BaseModel):
    id: str
    incident_number: str
    title: str
    description: Optional[str] = None
    image_url: str
    annotated_image_url: Optional[str] = None
    location_name: str
    latitude: float
    longitude: float
    date_reported: str
    time_reported: str
    detected_objects: List[Dict[str, Any]] = []
    primary_encroachment_type: str
    occupied_area_sqm: Optional[float] = None
    footpath_area_sqm: Optional[float] = None
    footpath_width_m: Optional[float] = None
    obstructed_width_m: Optional[float] = None
    remaining_width_m: Optional[float] = None
    bottleneck_blockage_pct: Optional[float] = None
    is_calibrated: Optional[bool] = False
    calibration_mode: Optional[str] = "UNCALIBRATED_PIXEL_ONLY"
    footpath_roi_area_px: Optional[float] = None
    occupied_footpath_px: Optional[float] = None
    footpath_width_px: Optional[int] = None
    remaining_width_px: Optional[int] = None
    bottleneck_y_px: Optional[int] = None
    occupancy_percentage: float = 0.0
    accessibility_score: float = 100.0
    accessibility_status: str
    warnings: List[str] = []
    severity: str
    severity_reason: str
    confidence: Optional[float] = None
    reporter_id: Optional[str] = None
    reporter_name: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    status: str
    inspection_image_url: Optional[str] = None
    inspection_notes: Optional[str] = None
    inspection_date: Optional[str] = None
    ai_verification: Optional[Dict[str, Any]] = None
    duplicate_group_id: Optional[str] = None
    supporting_reports_count: int = 1
    supporting_reports: List[SupportingReportItem] = []
    is_duplicate_merged: Optional[bool] = False
    merged_with_master_id: Optional[str] = None
    comments: List[CommentItem] = []
    resolution_date: Optional[str] = None
    evidence_images: Optional[List[Dict[str, Any]]] = []
    privacy_image_url: Optional[str] = None
    privacy_protected: Optional[bool] = False
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    why_flagged: Optional[List[Dict[str, Any]]] = []
    probability_status: Optional[str] = None
    path_continuity: Optional[str] = None
    path_continuity_reason: Optional[str] = None
    accessibility_category: Optional[str] = None
    obstruction_impact: Optional[str] = "LOW"
    remaining_pedestrian_region_pct: Optional[float] = None
    persistence_sec: Optional[float] = None
    is_persistent: Optional[bool] = False
    potential_encroachment: Optional[str] = None
    ai_explanation: Optional[str] = None
    review_status: Optional[str] = "NEEDS_REVIEW"
    reasoning: Optional[Dict[str, Any]] = None
    priority_score: Optional[float] = None
    priority_rank: Optional[str] = None
    priority_action: Optional[str] = None
    human_verification_status: Optional[str] = "PENDING_REVIEW"
    duplicate_dismissed: Optional[bool] = False
    evidence_inconsistency_flag: Optional[bool] = False
    evidence_inconsistency_reason: Optional[str] = None
    risk_forecast: Optional[Dict[str, Any]] = None
    original_ai_category: Optional[str] = None
    human_verified_category: Optional[str] = None
    human_review_reason: Optional[str] = None
    reviewed_by_id: Optional[str] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[str] = None
    privacy_metadata: Optional[Dict[str, Any]] = None
    timeline: Optional[List[Dict[str, Any]]] = []
    processed_sync_ids: Optional[List[str]] = []
    after_images: Optional[List[Dict[str, Any]]] = []
    resolution_notes: Optional[str] = None
    resolution_submitted_at: Optional[str] = None
    resolved_by_id: Optional[str] = None
    resolved_by_name: Optional[str] = None
    resolution_verified_at: Optional[str] = None
    verified_by_id: Optional[str] = None
    verified_by_name: Optional[str] = None
    resolution_rejection_reason: Optional[str] = None
    is_escalated: Optional[bool] = False
    escalation_level: Optional[int] = 0
    escalated_at: Optional[str] = None
    reopened_at: Optional[str] = None
    reopened_by_id: Optional[str] = None
    reopened_by_name: Optional[str] = None
    reopen_reason: Optional[str] = None
    sla_status: Optional[Dict[str, Any]] = None
    service_feedback: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
