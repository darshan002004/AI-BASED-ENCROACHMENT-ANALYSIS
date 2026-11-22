from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DetectedObject(BaseModel):
    id: str
    label: str
    confidence: float
    bbox: List[int] = Field(description="[x, y, width, height]")
    is_encroachment: bool = False
    zone: str = "footpath"  # "footpath", "road", "vending_zone", "other"
    area_sqm: float = 0.0

class SegmentationMaskInfo(BaseModel):
    road_area_sqm: float = 0.0
    footpath_area_sqm: float = 0.0
    obstruction_area_sqm: float = 0.0
    pedestrian_clear_width_m: float = 1.8
    total_footpath_width_m: float = 3.0

class AccessibilityMetrics(BaseModel):
    footpath_width_m: float = 3.0
    obstructed_width_m: float = 1.2
    remaining_width_m: float = 1.8
    accessibility_score: float = 68.0  # 0 to 100%
    status: str = "PARTIALLY BLOCKED"  # "GOOD", "PARTIALLY BLOCKED", "SEVERELY BLOCKED"
    warnings: List[str] = []

class AIAnalysisResult(BaseModel):
    detected_objects: List[DetectedObject] = []
    primary_encroachment_type: str = "Street Vendor"
    confidence: float = 0.92
    footpath_area_sqm: float = 10.0
    occupied_area_sqm: float = 3.2
    free_area_sqm: float = 6.8
    occupancy_percentage: float = 32.0
    accessibility_score: float = 68.0
    accessibility_status: str = "PARTIALLY BLOCKED"
    severity: str = "High"
    severity_reason: str = "32% of pedestrian space is occupied and remaining accessible width is 1.8m."
    warnings: List[str] = []
    annotated_image_url: str = ""
    processing_time_sec: float = 2.3
    engine: str = "OpenCV Vision Pipeline"

class VideoTrackingItem(BaseModel):
    object_id: str
    label: str
    start_time_sec: float
    duration_sec: float
    is_persistent: bool
    status: str  # "Persistent Obstruction", "Temporary Movement"
