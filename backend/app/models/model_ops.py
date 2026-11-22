"""
Pydantic Schemas for Model Operations, Evaluation, Registry, and Training (Batch 5).
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class PerClassMetric(BaseModel):
    class_name: str
    sample_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    ap50: Optional[float] = None


class ModelEvaluationSummary(BaseModel):
    precision: float
    recall: float
    f1_score: float
    map50: Optional[float] = None
    mean_iou: Optional[float] = None
    accuracy: Optional[float] = None


class ModelEvaluationRecord(BaseModel):
    id: str
    model_name: str
    model_version: str
    task: str  # object_detection, classification, segmentation
    dataset_name: str
    dataset_version: str
    dataset_split: str  # test, validation
    sample_count: int
    valid_samples: int
    missing_or_invalid_annotations: int
    class_distribution: Dict[str, int]
    evaluated_at: str
    evaluated_by: str
    iou_threshold: float = 0.50
    confidence_threshold: float = 0.25
    overall_metrics: ModelEvaluationSummary
    per_class_metrics: List[PerClassMetric]
    confusion_matrix: Optional[Dict[str, Dict[str, int]]] = None
    status: str  # COMPLETED, INSUFFICIENT_DATA, FAILED
    status_note: Optional[str] = None
    disclaimer: str = (
        "Benchmark evaluation reflects historical ground-truth test data performance. "
        "It does not guarantee identical accuracy under uncalibrated live field conditions."
    )


class ModelEvaluationRequest(BaseModel):
    model_version: str = "v1.0.0-prod"
    dataset_name: Optional[str] = "bengaluru_urban_test_v1"
    iou_threshold: float = 0.50
    confidence_threshold: float = 0.25
    custom_annotations: Optional[List[Dict[str, Any]]] = None


class ModelCandidateRegister(BaseModel):
    name: str = "YOLOv5n-Urban-Encroachment"
    version: str
    task: str = "object_detection"
    framework: str = "OpenCV DNN ONNX"
    weights_filename: str
    description: str
    base_model_version: Optional[str] = "v1.0.0-prod"
    training_dataset_version: Optional[str] = None
    parameters_count: Optional[str] = "1.9M"
    metadata: Optional[Dict[str, Any]] = None


class ModelPromoteRequest(BaseModel):
    candidate_version: str
    reason: str
    expected_previous_version: Optional[str] = None
    evaluation_id: Optional[str] = None


class ModelRollbackRequest(BaseModel):
    target_version: str
    reason: str


class ModelRegistryItem(BaseModel):
    id: str
    name: str
    version: str
    task: str
    framework: str
    status: str  # PRODUCTION, CANDIDATE, ARCHIVED, REJECTED
    weights_path: str
    weights_sha256: str
    file_size_bytes: int
    description: str
    registered_at: str
    registered_by: str
    promoted_at: Optional[str] = None
    promoted_by: Optional[str] = None
    evaluation_summary: Optional[ModelEvaluationSummary] = None
    metadata: Optional[Dict[str, Any]] = None


class TrainingDatasetValidateRequest(BaseModel):
    dataset_path: Optional[str] = None
    require_ground_truth_boxes: bool = True


class TrainingPrepareRequest(BaseModel):
    dataset_version: str = "feedback_export_v1"
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    random_seed: int = 42
    epochs_planned: int = 50
    batch_size: int = 16
    learning_rate: float = 0.001
