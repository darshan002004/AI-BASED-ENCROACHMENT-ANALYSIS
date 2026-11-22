import asyncio
import logging
from datetime import datetime, timedelta
from app.auth import get_password_hash
from app.database import get_db

logger = logging.getLogger("encrowatch.seed")

DEMO_USERS = [
    {
        "_id": "usr_admin_01",
        "id": "usr_admin_01",
        "email": "admin@encrowatch.ai",
        "password": get_password_hash("admin123"),
        "full_name": "Admin",
        "role": "admin",
        "phone": "+91 80 2297 5000",
        "badge_id": "BBMP-HQ-01",
        "assigned_area": "Bengaluru Smart City Control Centre",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-01-10T08:00:00Z"
    },
    {
        "_id": "usr_officer_01",
        "id": "usr_officer_01",
        "email": "officer@encrowatch.ai",
        "password": get_password_hash("officer123"),
        "full_name": "Ramesh Kumar",
        "role": "officer",
        "phone": "+91 98450 12345",
        "badge_id": "BLR-OFF-402",
        "assigned_area": "MG Road & Central Ward",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-01-15T09:30:00Z"
    },
    {
        "_id": "usr_officer_02",
        "id": "usr_officer_02",
        "email": "priya.officer@encrowatch.ai",
        "password": get_password_hash("officer123"),
        "full_name": "Priya Sharma",
        "role": "officer",
        "phone": "+91 98451 98765",
        "badge_id": "BLR-OFF-215",
        "assigned_area": "Indiranagar & East Ward",
        "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-02-01T10:15:00Z"
    },
    {
        "_id": "usr_citizen_01",
        "id": "usr_citizen_01",
        "email": "citizen@encrowatch.ai",
        "password": get_password_hash("citizen123"),
        "full_name": "Darshan B",
        "role": "citizen",
        "phone": "+91 98860 55443",
        "badge_id": None,
        "assigned_area": "BTM Layout",
        "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
        "created_at": "2026-03-05T14:20:00Z"
    }
]

# Primary incidents matching the exact rows on the dashboard mockup
DEMO_INCIDENTS = [
    {
        "_id": "inc_001",
        "id": "inc_001",
        "incident_number": "ENC-2026-1024",
        "title": "Unauthorized Street Vendor Stall Blocking Pedestrian Footpath",
        "description": "Large wooden fruit cart and crates occupying 32% of the pedestrian footpath width on MG Road near Metro Station.",
        "image_url": "/uploads/original/vendor_mg_road.jpg",
        "annotated_image_url": "/uploads/annotated/vendor_mg_road_annotated.jpg",
        "location_name": "MG Road",
        "latitude": 12.9756,
        "longitude": 77.6066,
        "date_reported": "22 Sep 2026",
        "time_reported": "10:24 AM",
        "primary_encroachment_type": "Street Vendor",
        "detected_objects": [
            {"id": "o1", "label": "Vendor", "confidence": 0.92, "bbox": [190, 560, 60, 90], "is_encroachment": True, "zone": "footpath", "area_sqm": 3.2},
            {"id": "o2", "label": "Vehicle", "confidence": 0.87, "bbox": [375, 560, 75, 90], "is_encroachment": False, "zone": "road", "area_sqm": 4.5}
        ],
        "occupied_area_sqm": 3.2,
        "footpath_area_sqm": 10.0,
        "occupancy_percentage": 32.0,
        "accessibility_score": 68.0,
        "accessibility_status": "PARTIALLY BLOCKED",
        "severity": "High",
        "severity_reason": "32% of pedestrian space is occupied and remaining accessible width is 1.8m.",
        "warnings": ["Wheelchair ramp obstruction detected.", "Pedestrian passage significantly reduced."],
        "confidence": 0.92,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Darshan B",
        "assigned_officer_id": "usr_officer_01",
        "assigned_officer_name": "Ramesh Kumar",
        "status": "Verified",
        "inspection_image_url": None,
        "inspection_notes": "AI detection confirmed by Central Command. Officer dispatched for clearance notice.",
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 4,
        "comments": [
            {"author_name": "System AI", "role": "ai", "text": "Automatic verification triggered with 92% confidence score.", "timestamp": "22 Sep 2026 10:24 AM"},
            {"author_name": "Admin", "role": "admin", "text": "Verified. Forwarded to Officer Ramesh for immediate field clearance.", "timestamp": "22 Sep 2026 10:35 AM"}
        ],
        "resolution_date": None,
        "created_at": "2026-09-22T10:24:00Z",
        "updated_at": "2026-09-22T10:35:00Z"
    },
    {
        "_id": "inc_002",
        "id": "inc_002",
        "incident_number": "ENC-2026-0914",
        "title": "Private Sedan Parked across Tactile Walkway",
        "description": "White sedan parked partially on footpath blocking tactile pavers and forcing pedestrians onto active road traffic.",
        "image_url": "/uploads/original/thumb_vehicle.jpg",
        "annotated_image_url": "/uploads/original/thumb_vehicle.jpg",
        "location_name": "Indiranagar",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "date_reported": "21 Sep 2026",
        "time_reported": "04:10 PM",
        "primary_encroachment_type": "Vehicle",
        "detected_objects": [
            {"id": "o3", "label": "Vehicle", "confidence": 0.89, "bbox": [10, 10, 80, 50], "is_encroachment": True, "zone": "footpath", "area_sqm": 4.8}
        ],
        "occupied_area_sqm": 4.8,
        "footpath_area_sqm": 12.0,
        "occupancy_percentage": 40.0,
        "accessibility_score": 60.0,
        "accessibility_status": "PARTIALLY BLOCKED",
        "severity": "Medium",
        "severity_reason": "40% of pedestrian path occupied by parked car.",
        "warnings": ["Tactile paving pathway completely blocked."],
        "confidence": 0.89,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Darshan B",
        "assigned_officer_id": None,
        "assigned_officer_name": None,
        "status": "Pending",
        "inspection_image_url": None,
        "inspection_notes": None,
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 2,
        "comments": [],
        "resolution_date": None,
        "created_at": "2026-09-21T16:10:00Z",
        "updated_at": "2026-09-21T16:10:00Z"
    },
    {
        "_id": "inc_003",
        "id": "inc_003",
        "incident_number": "ENC-2026-0882",
        "title": "Concrete Slabs and Building Material Dumped on Sidewalk",
        "description": "Piles of interlocking paver blocks and sand gravel obstructing entire walking section outside commercial complex.",
        "image_url": "/uploads/original/thumb_construction.jpg",
        "annotated_image_url": "/uploads/original/thumb_construction.jpg",
        "location_name": "BTM Layout",
        "latitude": 12.9166,
        "longitude": 77.6101,
        "date_reported": "21 Sep 2026",
        "time_reported": "11:45 AM",
        "primary_encroachment_type": "Construction",
        "detected_objects": [
            {"id": "o4", "label": "Construction", "confidence": 0.94, "bbox": [15, 15, 90, 60], "is_encroachment": True, "zone": "footpath", "area_sqm": 5.5}
        ],
        "occupied_area_sqm": 5.5,
        "footpath_area_sqm": 9.0,
        "occupancy_percentage": 61.1,
        "accessibility_score": 38.0,
        "accessibility_status": "SEVERELY BLOCKED",
        "severity": "High",
        "severity_reason": "61% of sidewalk blocked by heavy construction material with severe pedestrian hazard.",
        "warnings": ["Hazardous obstruction detected: Construction blocks pedestrian flow.", "Wheelchair ramp obstruction detected."],
        "confidence": 0.94,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Citizen User",
        "assigned_officer_id": "usr_officer_01",
        "assigned_officer_name": "Ramesh Kumar",
        "status": "Assigned",
        "inspection_image_url": None,
        "inspection_notes": "Notice issued to builder for immediate clearance within 24 hours.",
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 5,
        "comments": [
            {"author_name": "Ramesh Kumar", "role": "officer", "text": "Field visit conducted. Contractor instructed to remove blocks by tonight.", "timestamp": "21 Sep 2026 01:15 PM"}
        ],
        "resolution_date": None,
        "created_at": "2026-09-21T11:45:00Z",
        "updated_at": "2026-09-21T13:15:00Z"
    },
    {
        "_id": "inc_004",
        "id": "inc_004",
        "incident_number": "ENC-2026-0731",
        "title": "Commercial Bakery Display Counter Extended on Footpath",
        "description": "Metal display counter and advertising stand erected beyond shop shutter line onto the public walkway.",
        "image_url": "/uploads/original/thumb_shop.jpg",
        "annotated_image_url": "/uploads/original/thumb_shop.jpg",
        "location_name": "Koramangala",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "date_reported": "20 Sep 2026",
        "time_reported": "03:20 PM",
        "primary_encroachment_type": "Shop Extension",
        "detected_objects": [
            {"id": "o5", "label": "Shop Extension", "confidence": 0.88, "bbox": [10, 10, 70, 70], "is_encroachment": True, "zone": "footpath", "area_sqm": 2.5}
        ],
        "occupied_area_sqm": 2.5,
        "footpath_area_sqm": 8.0,
        "occupancy_percentage": 31.2,
        "accessibility_score": 96.0,
        "accessibility_status": "GOOD",
        "severity": "Medium",
        "severity_reason": "Shop extension cleared. Post-inspection verified safe walkway clearance.",
        "warnings": [],
        "confidence": 0.88,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Citizen User",
        "assigned_officer_id": "usr_officer_02",
        "assigned_officer_name": "Priya Sharma",
        "status": "Resolved",
        "inspection_image_url": "/uploads/inspections/vendor_resolved_inspection.jpg",
        "inspection_notes": "Shop owner pulled back the counter inside property boundary. AI verification confirms 100% clear walkway.",
        "inspection_date": "20 Sep 2026 05:40 PM",
        "ai_verification": {
            "verified": True,
            "status": "RESOLUTION VERIFIED",
            "confidence": 0.96,
            "original_obstruction": "Detected (31% Occupancy)",
            "current_obstruction": "Not Detected (Clear Footpath)",
            "cleared_percentage": 100.0,
            "current_accessibility_score": 96.0,
            "current_accessibility_status": "GOOD",
            "comparison_image_url": "/uploads/annotated/vendor_mg_road_annotated.jpg"
        },
        "duplicate_group_id": None,
        "supporting_reports_count": 1,
        "comments": [
            {"author_name": "Priya Sharma", "role": "officer", "text": "Cleared in presence of municipal squad. Uploaded verification photo.", "timestamp": "20 Sep 2026 05:35 PM"},
            {"author_name": "System AI", "role": "ai", "text": "Before/After AI Verification passed. Encroachment cleared.", "timestamp": "20 Sep 2026 05:40 PM"}
        ],
        "resolution_date": "20 Sep 2026 05:40 PM",
        "created_at": "2026-09-20T15:20:00Z",
        "updated_at": "2026-09-20T17:40:00Z"
    },
    {
        "_id": "inc_005",
        "id": "inc_005",
        "incident_number": "ENC-2026-0690",
        "title": "Commercial Waste and Garbage Bags Piled at Curbside",
        "description": "Garbage sacks and broken plastic packaging left on curb, slightly spilling onto walking path.",
        "image_url": "/uploads/original/thumb_garbage.jpg",
        "annotated_image_url": "/uploads/original/thumb_garbage.jpg",
        "location_name": "JP Nagar",
        "latitude": 12.9063,
        "longitude": 77.5857,
        "date_reported": "20 Sep 2026",
        "time_reported": "09:15 AM",
        "primary_encroachment_type": "Garbage",
        "detected_objects": [
            {"id": "o6", "label": "Garbage", "confidence": 0.85, "bbox": [20, 20, 50, 40], "is_encroachment": True, "zone": "curbside", "area_sqm": 1.2}
        ],
        "occupied_area_sqm": 1.2,
        "footpath_area_sqm": 10.0,
        "occupancy_percentage": 12.0,
        "accessibility_score": 82.0,
        "accessibility_status": "GOOD",
        "severity": "Low",
        "severity_reason": "Minor curbside garbage accumulation with minimal walkway disruption.",
        "warnings": [],
        "confidence": 0.85,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Citizen User",
        "assigned_officer_id": None,
        "assigned_officer_name": None,
        "status": "Pending",
        "inspection_image_url": None,
        "inspection_notes": None,
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 1,
        "comments": [],
        "resolution_date": None,
        "created_at": "2026-09-20T09:15:00Z",
        "updated_at": "2026-09-20T09:15:00Z"
    },
    {
        "_id": "inc_006",
        "id": "inc_006",
        "incident_number": "ENC-2026-0520",
        "title": "Two-Wheelers Parked on Newly Paved Footpath",
        "description": "Multiple motorbikes parked perpendicular to curb blocking accessible ramp near supermarket.",
        "image_url": "/uploads/original/thumb_vehicle.jpg",
        "annotated_image_url": "/uploads/original/thumb_vehicle.jpg",
        "location_name": "HSR Layout",
        "latitude": 12.9121,
        "longitude": 77.6446,
        "date_reported": "19 Sep 2026",
        "time_reported": "06:30 PM",
        "primary_encroachment_type": "Vehicle",
        "detected_objects": [
            {"id": "o7", "label": "Vehicle", "confidence": 0.91, "bbox": [10, 10, 60, 50], "is_encroachment": True, "zone": "footpath", "area_sqm": 3.0}
        ],
        "occupied_area_sqm": 3.0,
        "footpath_area_sqm": 10.0,
        "occupancy_percentage": 30.0,
        "accessibility_score": 65.0,
        "accessibility_status": "PARTIALLY BLOCKED",
        "severity": "Medium",
        "severity_reason": "Parked two-wheelers occupying 30% of footpath space.",
        "warnings": ["Wheelchair ramp obstruction detected."],
        "confidence": 0.91,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Citizen User",
        "assigned_officer_id": "usr_officer_02",
        "assigned_officer_name": "Priya Sharma",
        "status": "In Progress",
        "inspection_image_url": None,
        "inspection_notes": "Traffic police towing vehicle dispatched.",
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 3,
        "comments": [],
        "resolution_date": None,
        "created_at": "2026-09-19T18:30:00Z",
        "updated_at": "2026-09-19T19:00:00Z"
    },
    {
        "_id": "inc_007",
        "id": "inc_007",
        "incident_number": "ENC-2026-0410",
        "title": "Vegetable Carts Line Sidewalk Near 4th Block Complex",
        "description": "Row of 3 handcarts blocking school children crossing lane.",
        "image_url": "/uploads/original/vendor_mg_road.jpg",
        "annotated_image_url": "/uploads/annotated/vendor_mg_road_annotated.jpg",
        "location_name": "Jayanagar",
        "latitude": 12.9250,
        "longitude": 77.5938,
        "date_reported": "18 Sep 2026",
        "time_reported": "08:45 AM",
        "primary_encroachment_type": "Street Vendor",
        "detected_objects": [
            {"id": "o8", "label": "Vendor", "confidence": 0.93, "bbox": [20, 20, 70, 70], "is_encroachment": True, "zone": "footpath", "area_sqm": 3.8}
        ],
        "occupied_area_sqm": 3.8,
        "footpath_area_sqm": 11.0,
        "occupancy_percentage": 34.5,
        "accessibility_score": 64.0,
        "accessibility_status": "PARTIALLY BLOCKED",
        "severity": "High",
        "severity_reason": "School pedestrian corridor obstructed by vendor carts.",
        "warnings": ["Pedestrian passage significantly reduced below 1.5m minimum safe clearance."],
        "confidence": 0.93,
        "reporter_id": "usr_citizen_01",
        "reporter_name": "Citizen User",
        "assigned_officer_id": "usr_officer_01",
        "assigned_officer_name": "Ramesh Kumar",
        "status": "Verified",
        "inspection_image_url": None,
        "inspection_notes": "Vendors notified regarding relocation to designated vending zone.",
        "inspection_date": None,
        "ai_verification": None,
        "duplicate_group_id": None,
        "supporting_reports_count": 6,
        "comments": [],
        "resolution_date": None,
        "created_at": "2026-09-18T08:45:00Z",
        "updated_at": "2026-09-18T09:10:00Z"
    }
]

# Notifications for notification bell
DEMO_NOTIFICATIONS = [
    {
        "_id": "notif_001",
        "id": "notif_001",
        "recipient_role": "admin",
        "title": "High Severity Encroachment Detected",
        "message": "Street vendor cart blocking 32% of MG Road pedestrian walkway. Immediate action recommended.",
        "type": "high_severity",
        "incident_id": "inc_001",
        "read": False,
        "created_at": "2026-09-22T10:25:00Z"
    },
    {
        "_id": "notif_002",
        "id": "notif_002",
        "recipient_role": "admin",
        "title": "Before/After AI Verification Passed",
        "message": "Incident ENC-2026-0731 at Koramangala has been verified cleared by Officer Priya Sharma.",
        "type": "resolution_verified",
        "incident_id": "inc_004",
        "read": False,
        "created_at": "2026-09-20T17:41:00Z"
    },
    {
        "_id": "notif_003",
        "id": "notif_003",
        "recipient_role": "officer",
        "title": "New Incident Assigned",
        "message": "High severity construction encroachment at BTM Layout assigned to Officer Ramesh Kumar.",
        "type": "assignment",
        "incident_id": "inc_003",
        "read": True,
        "created_at": "2026-09-21T11:50:00Z"
    }
]

async def seed_database():
    db = get_db()
    users_col = db.get_collection("users")
    incidents_col = db.get_collection("incidents")
    notifications_col = db.get_collection("notifications")

    # Upsert Users
    for u in DEMO_USERS:
        existing = await users_col.find_one({"email": u["email"]})
        if not existing:
            await users_col.insert_one(u)
    logger.info(f"Ensured {len(DEMO_USERS)} default users in database.")

    # Upsert Incidents
    for inc in DEMO_INCIDENTS:
        if "priority_score" not in inc:
            inc["priority_score"] = 78.0 if inc.get("severity") == "High" else 52.0
            inc["priority_rank"] = "Critical" if inc.get("severity") == "High" else "Standard"
            inc["priority_action"] = "Immediate Field Inspection" if inc.get("severity") == "High" else "Routine Verification"
        if "timeline" not in inc or not inc.get("timeline"):
            inc["timeline"] = [
                {
                    "event_type": "ai_detection",
                    "title": "AI Encroachment Analysis Completed",
                    "description": f"AI identified {inc.get('primary_encroachment_type')} at {inc.get('location_name')}.",
                    "actor_name": "EncroWatch AI Engine",
                    "actor_role": "ai",
                    "timestamp": inc.get("date_reported", "2026-09-22")
                },
                {
                    "event_type": "report_submitted",
                    "title": "Citizen Report Submitted",
                    "description": f"Report filed by {inc.get('reporter_name', 'Citizen')}.",
                    "actor_name": inc.get("reporter_name", "Citizen"),
                    "actor_role": "citizen",
                    "timestamp": inc.get("date_reported", "2026-09-22")
                }
            ]
        if "evidence_images" not in inc or not inc.get("evidence_images"):
            inc["evidence_images"] = [
                {
                    "id": f"ev_{inc['id']}",
                    "image_url": inc.get("image_url", ""),
                    "annotated_image_url": inc.get("annotated_image_url", ""),
                    "caption": "Initial Evidence Photo",
                    "uploaded_at": inc.get("date_reported", "2026-09-22")
                }
            ]
        if "accessibility_category" not in inc:
            inc["accessibility_category"] = "Moderately Affected"
        if "path_continuity" not in inc:
            inc["path_continuity"] = "PARTIALLY BLOCKED"
        if "human_verification_status" not in inc:
            inc["human_verification_status"] = "CONFIRMED" if inc.get("status") in ["Verified", "Resolved"] else "PENDING_REVIEW"

        existing = await incidents_col.find_one({"$or": [{"_id": inc["_id"]}, {"incident_number": inc["incident_number"]}]})
        if not existing:
            await incidents_col.insert_one(inc)
        else:
            update_missing = {}
            for k in ["priority_score", "priority_rank", "priority_action", "timeline", "evidence_images", "accessibility_category", "path_continuity", "human_verification_status"]:
                if k not in existing or not existing[k]:
                    update_missing[k] = inc[k]
            if update_missing:
                await incidents_col.update_one({"_id": existing["_id"]}, {"$set": update_missing})
    logger.info(f"Ensured {len(DEMO_INCIDENTS)} realistic sample incidents in database.")

    # Upsert Notifications
    for n in DEMO_NOTIFICATIONS:
        existing = await notifications_col.find_one({"$or": [{"_id": n["_id"]}, {"title": n["title"]}]})
        if not existing:
            await notifications_col.insert_one(n)
    logger.info("Demo notifications ready.")
