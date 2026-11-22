import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger("encrowatch.notifications")

class NotificationService:
    """
    Persistent In-App Notification Service with deduplication and privacy protection.
    """

    async def create_notification(
        self,
        db: Any,
        recipient_id: str,
        recipient_role: str,
        notif_type: str,
        title: str,
        message: str,
        incident_id: Optional[str] = None,
        incident_number: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if not recipient_id or recipient_id == "system":
            return None

        notif_col = db["notifications"]
        now = datetime.utcnow()
        now_iso = now.isoformat() + "Z"

        # Deduplication check: Avoid sending duplicate notifications within 5 minutes
        five_mins_ago = (now - timedelta(minutes=5)).isoformat() + "Z"
        existing = await notif_col.find_one({
            "recipient_id": str(recipient_id),
            "type": notif_type,
            "incident_id": str(incident_id) if incident_id else None,
            "created_at": {"$gte": five_mins_ago}
        })
        if existing:
            logger.info(f"Deduplicated notification {notif_type} for recipient {recipient_id}")
            return existing

        notif_id = f"notif_{uuid.uuid4().hex[:10]}"
        safe_data = data or {}

        doc = {
            "id": notif_id,
            "recipient_id": str(recipient_id),
            "recipient_role": recipient_role.lower(),
            "type": notif_type,
            "title": title,
            "message": message,
            "incident_id": str(incident_id) if incident_id else None,
            "incident_number": incident_number,
            "is_read": False,
            "created_at": now_iso,
            "data": safe_data
        }

        await notif_col.insert_one(doc)
        logger.info(f"Created notification {notif_id} ({notif_type}) for user {recipient_id}")
        return doc

    async def notify_citizen(
        self,
        db: Any,
        reporter_id: str,
        notif_type: str,
        title: str,
        message: str,
        incident_id: str,
        incident_number: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        return await self.create_notification(
            db=db,
            recipient_id=reporter_id,
            recipient_role="citizen",
            notif_type=notif_type,
            title=title,
            message=message,
            incident_id=incident_id,
            incident_number=incident_number,
            data=data
        )

    async def notify_officer(
        self,
        db: Any,
        officer_id: str,
        notif_type: str,
        title: str,
        message: str,
        incident_id: str,
        incident_number: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        return await self.create_notification(
            db=db,
            recipient_id=officer_id,
            recipient_role="officer",
            notif_type=notif_type,
            title=title,
            message=message,
            incident_id=incident_id,
            incident_number=incident_number,
            data=data
        )

    async def notify_admins(
        self,
        db: Any,
        notif_type: str,
        title: str,
        message: str,
        incident_id: str,
        incident_number: str,
        data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        users_col = db["users"]
        admins = await users_col.find({"role": "admin"}).to_list(100)
        results = []
        for admin in admins:
            admin_id = str(admin.get("id") or admin.get("_id"))
            res = await self.create_notification(
                db=db,
                recipient_id=admin_id,
                recipient_role="admin",
                notif_type=notif_type,
                title=title,
                message=message,
                incident_id=incident_id,
                incident_number=incident_number,
                data=data
            )
            if res:
                results.append(res)
        return results

notification_service = NotificationService()
