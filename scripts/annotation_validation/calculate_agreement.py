#!/usr/bin/env python3
"""
EncroWatch AI - Stage 1.5: Inter-Annotator Agreement & Quality Assurance Engine
Part of Stage 1.5 Execution.

Implements mathematical evaluation of agreement between independent annotators:
1. Categorical Agreement: Cohen's Kappa (kappa) across the 8 custom classes.
2. Spatial Precision: Bounding Box Intersection-over-Union (IoU_box) with greedy matching.
3. Contour Precision: Polygon IoU (IoU_poly) and Boundary F1-Score (BF1).
4. Dual-Annotation Quality Gate: Verification that kappa >= 0.80, mean IoU >= 0.80.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from shapely.geometry import Polygon, box

CUSTOM_CLASSES = [
    "motorcycle",            # 0
    "car",                   # 1
    "vendor_cart",           # 2
    "construction_debris",   # 3
    "commercial_signboard",  # 4
    "shop_extension",        # 5
    "umbrella_canopy",       # 6
    "pedestrian"             # 7
]

CLASS_TO_ID = {c: i for i, c in enumerate(CUSTOM_CLASSES)}
ID_TO_CLASS = {i: c for i, c in enumerate(CUSTOM_CLASSES)}

def compute_box_iou(box1: List[float], box2: List[float]) -> float:
    """Computes IoU between two [x_c, y_c, w, h] normalized boxes."""
    x1_min, y1_min = box1[0] - box1[2]/2.0, box1[1] - box1[3]/2.0
    x1_max, y1_max = box1[0] + box1[2]/2.0, box1[1] + box1[3]/2.0
    
    x2_min, y2_min = box2[0] - box2[2]/2.0, box2[1] - box2[3]/2.0
    x2_max, y2_max = box2[0] + box2[2]/2.0, box2[1] + box2[3]/2.0

    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)

    inter_w = max(0.0, inter_xmax - inter_xmin)
    inter_h = max(0.0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h

    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union_area = area1 + area2 - inter_area

    return float(inter_area / union_area) if union_area > 0 else 0.0

def compute_polygon_iou(poly1_coords: List[float], poly2_coords: List[float]) -> float:
    """Computes IoU between two flat normalized coordinate lists [x1, y1, x2, y2, ...]."""
    try:
        pts1 = [(poly1_coords[i], poly1_coords[i+1]) for i in range(0, len(poly1_coords), 2)]
        pts2 = [(poly2_coords[i], poly2_coords[i+1]) for i in range(0, len(poly2_coords), 2)]
        
        p1 = Polygon(pts1).buffer(0)
        p2 = Polygon(pts2).buffer(0)
        
        if not p1.is_valid or not p2.is_valid:
            return 0.0
        
        inter = p1.intersection(p2).area
        union = p1.union(p2).area
        return float(inter / union) if union > 0 else 0.0
    except Exception:
        return 0.0

def compute_boundary_f1(poly1_coords: List[float], poly2_coords: List[float], threshold: float = 0.02) -> float:
    """
    Computes Boundary F1 (BF1) score measuring contour precision within threshold distance.
    Threshold default 0.02 represents 2% of normalized image dimension (~12.8 pixels at 640x640).
    """
    try:
        pts1 = [(poly1_coords[i], poly1_coords[i+1]) for i in range(0, len(poly1_coords), 2)]
        pts2 = [(poly2_coords[i], poly2_coords[i+1]) for i in range(0, len(poly2_coords), 2)]
        
        p1 = Polygon(pts1).boundary
        p2 = Polygon(pts2).boundary
        
        b1_buf = p1.buffer(threshold)
        b2_buf = p2.buffer(threshold)
        
        precision = b2_buf.intersection(p1).length / p1.length if p1.length > 0 else 0.0
        recall = b1_buf.intersection(p2).length / p2.length if p2.length > 0 else 0.0
        
        if precision + recall == 0:
            return 0.0
        return float(2 * precision * recall / (precision + recall))
    except Exception:
        return 0.0

def compute_cohens_kappa(confusion_matrix: np.ndarray) -> float:
    """
    Computes Cohen's Kappa (kappa) from an K x K confusion matrix:
    kappa = (P_o - P_e) / (1 - P_e)
    Where:
      P_o = observed fractional agreement
      P_e = expected fractional agreement by chance
    """
    n = np.sum(confusion_matrix)
    if n == 0:
        return 0.0
    p_o = float(np.trace(confusion_matrix) / n)
    row_sums = np.sum(confusion_matrix, axis=1)
    col_sums = np.sum(confusion_matrix, axis=0)
    p_e = float(np.sum(row_sums * col_sums) / (n ** 2))
    
    if p_e >= 1.0:
        return 1.0
    return float((p_o - p_e) / (1.0 - p_e))

def evaluate_paired_annotations(annos_a: List[Dict[str, Any]], 
                                annos_b: List[Dict[str, Any]], 
                                iou_threshold: float = 0.50) -> Dict[str, Any]:
    """
    Matches annotations from Annotator A and Annotator B.
    Computes class confusion matrix, bounding box IoUs, and agreement criteria.
    """
    k = len(CUSTOM_CLASSES)
    conf_matrix = np.zeros((k, k), dtype=np.int64)
    matched_ious = []
    unmatched_a = 0
    unmatched_b = 0
    
    # Simple greedy matching based on box IoU
    used_b = set()
    for item_a in annos_a:
        best_iou = 0.0
        best_idx_b = -1
        box_a = item_a["box"]
        cls_a = item_a["class_id"]
        
        for idx_b, item_b in enumerate(annos_b):
            if idx_b in used_b:
                continue
            box_b = item_b["box"]
            iou = compute_box_iou(box_a, box_b)
            if iou > best_iou:
                best_iou = iou
                best_idx_b = idx_b
        
        if best_iou >= iou_threshold and best_idx_b >= 0:
            used_b.add(best_idx_b)
            cls_b = annos_b[best_idx_b]["class_id"]
            if 0 <= cls_a < k and 0 <= cls_b < k:
                conf_matrix[cls_a, cls_b] += 1
            matched_ious.append(best_iou)
        else:
            unmatched_a += 1
            
    unmatched_b = len(annos_b) - len(used_b)
    
    kappa = compute_cohens_kappa(conf_matrix)
    mean_iou = float(np.mean(matched_ious)) if matched_ious else 0.0
    
    return {
        "total_annotator_a": len(annos_a),
        "total_annotator_b": len(annos_b),
        "matched_pairs": len(matched_ious),
        "unmatched_a": unmatched_a,
        "unmatched_b": unmatched_b,
        "cohens_kappa": round(kappa, 4),
        "mean_matched_box_iou": round(mean_iou, 4),
        "kappa_threshold_met": kappa >= 0.80,
        "box_iou_threshold_met": mean_iou >= 0.80,
        "confusion_matrix": conf_matrix.tolist()
    }

def run_demonstration():
    print("=" * 70)
    print("ENCROWATCH AI — STAGE 1.5 ANNOTATION QUALITY & AGREEMENT ENGINE")
    print("=" * 70)
    print("Classes (8):")
    for i, c in enumerate(CUSTOM_CLASSES):
        print(f"  [{i}] {c}")
    print("-" * 70)
    print("Protocol Thresholds:")
    print("  Categorical Agreement (Cohen's Kappa): >= 0.80 (Substantial / Near-Perfect)")
    print("  Spatial Bounding Box Precision (IoU) : >= 0.80")
    print("  Polygon Boundary Precision (BF1)     : >= 0.75")
    print("=" * 70)

if __name__ == "__main__":
    run_demonstration()
