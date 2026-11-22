import math
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.config import settings


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


CATEGORY_CLUSTERS = {
    "vehicle": {"car", "truck", "bus", "motorcycle", "vehicle", "auto", "scooter", "van", "suv", "parked car", "moving car"},
    "vendor": {"vendor", "street vendor", "pushcart", "stall", "cart", "food stall", "hawker", "vendor cart"},
    "construction": {"construction", "construction material", "debris", "sand", "brick", "gravel", "cement", "unloading"},
    "sign_canopy": {"signboard", "board", "hoarding", "umbrella", "canopy", "shop extension", "banner", "stall seating"}
}


def get_category_cluster(cat_name: str) -> str:
    cleaned = (cat_name or "").lower().strip()
    for cluster_id, items in CATEGORY_CLUSTERS.items():
        if cleaned in items or any(item in cleaned for item in items):
            return cluster_id
    return "general_obstruction"


def parse_datetime_safe(date_str: Optional[str], time_str: Optional[str] = None) -> Optional[datetime]:
    """Parses various date/time formats into a datetime object safely."""
    if not date_str:
        return None
    
    # Try ISO format first
    try:
        clean = date_str.rstrip("Z")
        return datetime.fromisoformat(clean)
    except Exception:
        pass

    # Try standard string formats
    formats = [
        "%d %b %Y %I:%M %p",
        "%d %b %Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    combined = f"{date_str} {time_str}".strip() if time_str else date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt)
        except Exception:
            pass
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            pass
    return None


class DuplicateDetector:
    """
    Intelligent Duplicate Incident Detection & Merging Engine (Batch 2).
    Evaluates incidents against active municipal cases using multi-factor fusion:
      1. Spatial GPS Proximity (Haversine distance within 60-meter radius, handles missing GPS safely)
      2. Temporal Proximity (Time delta between incident reports)
      3. Encroachment Category & Semantic Cluster Similarity
      4. Computer Vision Image Correlation (HSV color histogram comparison when files exist)
      5. Active Incident Status Filtering (Excludes Resolved, Rejected, and already Merged cases)

    Data Integrity:
      - Does NOT claim the score is a calibrated statistical probability.
      - Explicitly labeled as a heuristic similarity score (0.0 to 1.0 / 0 to 100%).
    """

    MAX_DISTANCE_METERS = 60.0  # 60 meters spatial correlation boundary

    def _compute_image_similarity(self, url1: Optional[str], url2: Optional[str]) -> Optional[float]:
        """
        Computes normalized HSV color histogram correlation between two incident photos.
        Returns a float between 0.0 and 1.0, or None if files cannot be read.
        """
        if not url1 or not url2:
            return None

        def resolve_local_path(url: str) -> Optional[str]:
            if url.startswith("/uploads/"):
                rel_sub = url.replace("/uploads/", "")
                local_path = os.path.join(settings.UPLOAD_DIR, rel_sub.replace("/", os.sep))
                if os.path.exists(local_path):
                    return local_path
            return None

        p1 = resolve_local_path(url1)
        p2 = resolve_local_path(url2)
        if not p1 or not p2:
            return None

        try:
            img1 = cv2.imread(p1)
            img2 = cv2.imread(p2)
            if img1 is None or img2 is None:
                return None

            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

            hist1 = cv2.calcHist([hsv1], [0, 1], None, [50, 60], [0, 180, 0, 256])
            hist2 = cv2.calcHist([hsv2], [0, 1], None, [50, 60], [0, 180, 0, 256])

            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

            corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return float(max(0.0, min(1.0, corr)))
        except Exception:
            return None

    def _compute_time_proximity(self, dt1: Optional[datetime], dt2: Optional[datetime]) -> Tuple[float, str]:
        """
        Computes time proximity score (0.0 to 1.0) and human-readable time difference.
        """
        if not dt1 or not dt2:
            return 0.5, "Time difference unknown"

        delta_sec = abs((dt1 - dt2).total_seconds())
        hours = delta_sec / 3600.0
        days = hours / 24.0

        if hours <= 1.0:
            return 1.0, f"Reported within {int(round(delta_sec / 60.0))} minutes of each other"
        elif hours <= 12.0:
            return 0.95, f"Reported {hours:.1f} hours apart (same day)"
        elif days <= 1.0:
            return 0.90, "Reported within 24 hours"
        elif days <= 3.0:
            return 0.80, f"Reported {days:.1f} days apart"
        elif days <= 7.0:
            return 0.65, f"Reported {days:.1f} days apart (same week)"
        elif days <= 30.0:
            return 0.40, f"Reported {int(days)} days apart"
        else:
            return 0.20, f"Reported {int(days)} days apart (> 1 month difference)"

    def evaluate_pair(
        self,
        new_lat: Optional[float] | Dict[str, Any] = None,
        new_lng: Optional[float] | Dict[str, Any] = None,
        new_type: str = "",
        new_image_url: Optional[str] = None,
        new_location_name: Optional[str] = None,
        new_date: Optional[str] = None,
        new_time: Optional[str] = None,
        existing_incident: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates potential duplicate match between a new report and an existing incident.
        Accepts either separate fields or two incident dictionaries directly.
        Handles missing GPS, calculates multi-factor heuristic similarity, and returns match details.
        """
        if isinstance(new_lat, dict):
            report_a = new_lat
            report_b = new_lng if isinstance(new_lng, dict) else existing_incident
            if not report_b:
                return None
            new_lat = report_a.get("latitude")
            new_lng = report_a.get("longitude")
            new_type = report_a.get("primary_encroachment_type", "")
            new_image_url = report_a.get("image_url")
            new_location_name = report_a.get("location_name")
            new_date = report_a.get("date_reported") or report_a.get("created_at")
            new_time = report_a.get("time_reported")
            existing_incident = report_b

        if not existing_incident:
            return None

        status = (existing_incident.get("status") or "").lower()
        if status in ["resolved", "rejected", "duplicate merged"]:
            return None

        # Exclude self-matching
        inc_id = existing_incident.get("id") or str(existing_incident.get("_id"))

        # 1. Spatial Proximity
        has_new_gps = (new_lat is not None and new_lng is not None and (new_lat != 0.0 or new_lng != 0.0))
        inc_lat = existing_incident.get("latitude")
        inc_lng = existing_incident.get("longitude")
        has_inc_gps = (inc_lat is not None and inc_lng is not None and (inc_lat != 0.0 or inc_lng != 0.0))

        dist_meters = None
        geo_notes = ""

        if has_new_gps and has_inc_gps:
            dist_meters = haversine_distance_meters(new_lat, new_lng, inc_lat, inc_lng)
            if dist_meters > self.MAX_DISTANCE_METERS:
                return None  # Exceeds spatial boundary

            if dist_meters <= 12.0:
                geo_score = 1.0
                geo_notes = f"Immediate proximity ({dist_meters:.1f}m away)"
            elif dist_meters <= 25.0:
                geo_score = 0.85
                geo_notes = f"Close corridor proximity ({dist_meters:.1f}m away)"
            elif dist_meters <= 45.0:
                geo_score = 0.65
                geo_notes = f"Same street block ({dist_meters:.1f}m away)"
            else:
                geo_score = 0.40
                geo_notes = f"Within boundary radius ({dist_meters:.1f}m away)"
        else:
            # Missing GPS safe fallback
            loc1 = (new_location_name or "").lower().strip()
            loc2 = (existing_incident.get("location_name") or "").lower().strip()
            if loc1 and loc2 and (loc1 in loc2 or loc2 in loc1 or any(w in loc2 for w in loc1.split() if len(w) > 3)):
                geo_score = 0.55
                geo_notes = "Coordinates missing; matched by street/location name similarity"
            else:
                geo_score = 0.20
                geo_notes = "GPS coordinates missing and location text does not match"

        # 2. Category Similarity
        new_cluster = get_category_cluster(new_type)
        inc_type = existing_incident.get("primary_encroachment_type", "")
        inc_cluster = get_category_cluster(inc_type)

        if inc_type.lower().strip() == (new_type or "").lower().strip():
            type_score = 1.0
            cat_match = True
            type_notes = f"Exact category match ('{inc_type}')"
        elif inc_cluster == new_cluster and new_cluster != "general_obstruction":
            type_score = 0.85
            cat_match = True
            type_notes = f"Related category in same cluster ('{new_type}' vs '{inc_type}')"
        elif dist_meters is not None and dist_meters <= 18.0:
            type_score = 0.60
            cat_match = False
            type_notes = f"Different category ('{new_type}' vs '{inc_type}'), but within 18m corridor"
        else:
            type_score = 0.25
            cat_match = False
            type_notes = f"Different category ('{new_type}' vs '{inc_type}')"

        # 3. Temporal Proximity
        dt_new = parse_datetime_safe(new_date, new_time) or datetime.utcnow()
        dt_inc = parse_datetime_safe(
            existing_incident.get("created_at") or existing_incident.get("date_reported"),
            existing_incident.get("time_reported")
        )
        time_score, time_notes = self._compute_time_proximity(dt_new, dt_inc)

        # 4. Optional Computer Vision Image Correlation
        visual_score = self._compute_image_similarity(new_image_url, existing_incident.get("image_url"))
        visual_notes = f"{round(visual_score * 100, 1)}% HSV color histogram correlation" if visual_score is not None else "Image correlation not available"

        # 5. Composite Heuristic Match Score (0.0 to 1.0)
        if visual_score is not None:
            match_score = (0.40 * geo_score) + (0.25 * type_score) + (0.20 * time_score) + (0.15 * visual_score)
        else:
            match_score = (0.50 * geo_score) + (0.30 * type_score) + (0.20 * time_score)

        conf_pct = round(min(99.0, max(5.0, match_score * 100.0)), 1)

        # Decision threshold: >= 0.50 or immediate 18m proximity
        is_candidate = (match_score >= 0.50) or (dist_meters is not None and dist_meters <= 18.0 and (cat_match or type_score >= 0.60))

        if not is_candidate:
            return None

        reason = (
            f"Matches incident {existing_incident.get('incident_number', 'INC')} ({geo_notes}; "
            f"{type_notes}; {time_notes})."
        )

        return {
            "master_incident_id": inc_id,
            "incident_number": existing_incident.get("incident_number", "INC-MASTER"),
            "title": existing_incident.get("title", ""),
            "primary_encroachment_type": inc_type,
            "location_name": existing_incident.get("location_name", ""),
            "latitude": inc_lat,
            "longitude": inc_lng,
            "status": existing_incident.get("status", "Pending"),
            "severity": existing_incident.get("severity", "Medium"),
            "image_url": existing_incident.get("image_url", ""),
            "date_reported": existing_incident.get("date_reported", ""),
            "distance_meters": round(dist_meters, 1) if dist_meters is not None else None,
            "match_score": round(match_score, 3),
            "similarity_score": conf_pct,
            "is_duplicate_candidate": True,
            "match_confidence_pct": conf_pct,
            "category_match": cat_match,
            "reasons": [geo_notes, type_notes, time_notes] if geo_notes else [reason],
            "time_proximity_score": round(time_score, 2),
            "visual_similarity_score": round(visual_score, 2) if visual_score is not None else None,
            "matching_factors": {
                "spatial": {"score": round(geo_score, 2), "notes": geo_notes},
                "category": {"score": round(type_score, 2), "notes": type_notes},
                "temporal": {"score": round(time_score, 2), "notes": time_notes},
                "visual": {"score": round(visual_score, 2) if visual_score is not None else None, "notes": visual_notes}
            },
            "reason": reason,
            "score_type": "Heuristic Multi-Factor Similarity",
            "score_qualification": (
                "Heuristic similarity score (0-100) based on spatial distance, time delta, category, and visual features. "
                "Not a calibrated statistical probability."
            )
        }

    def find_duplicate_incident(
        self,
        new_lat: Optional[float],
        new_lng: Optional[float],
        new_type: str,
        active_incidents: List[Dict[str, Any]],
        new_image_url: Optional[str] = None,
        new_location_name: Optional[str] = None,
        new_date: Optional[str] = None,
        new_time: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the highest-confidence duplicate candidate for automatic or suggested merging.
        Requires high confidence (score >= 0.60 or immediate 18m proximity with category match).
        """
        candidates = self.find_all_potential_duplicates(
            new_lat=new_lat,
            new_lng=new_lng,
            new_type=new_type,
            active_incidents=active_incidents,
            new_image_url=new_image_url,
            new_location_name=new_location_name,
            new_date=new_date,
            new_time=new_time
        )
        if not candidates:
            return None

        best = candidates[0]
        # Only trigger automatic duplicate merge recommendation if score >= 0.60
        if best["match_score"] >= 0.60 or (best["distance_meters"] is not None and best["distance_meters"] <= 18.0 and best["category_match"]):
            return best
        return None

    def find_all_potential_duplicates(
        self,
        new_lat: Optional[float],
        new_lng: Optional[float],
        new_type: str,
        active_incidents: List[Dict[str, Any]],
        new_image_url: Optional[str] = None,
        new_location_name: Optional[str] = None,
        new_date: Optional[str] = None,
        new_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns all candidate duplicate matches for admin review and comparison, sorted by match score.
        """
        results: List[Dict[str, Any]] = []

        for inc in active_incidents:
            eval_res = self.evaluate_pair(
                new_lat=new_lat,
                new_lng=new_lng,
                new_type=new_type,
                new_image_url=new_image_url,
                new_location_name=new_location_name,
                new_date=new_date,
                new_time=new_time,
                existing_incident=inc
            )
            if eval_res is not None:
                results.append(eval_res)

        return sorted(results, key=lambda x: x["match_score"], reverse=True)


duplicate_detector = DuplicateDetector()
