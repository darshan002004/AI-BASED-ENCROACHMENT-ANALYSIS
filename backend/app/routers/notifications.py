from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from app.database import get_db
from app.auth import get_current_user
from app.models.notifications import NotificationListResponse, UnreadCountResponse, NotificationItem

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])

@router.get("", response_model=NotificationListResponse)
async def list_user_notifications(
    limit: int = 50,
    unread_only: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns in-app notifications for the authenticated citizen, officer, or admin.
    """
    user_id = str(current_user.get("id") or current_user.get("_id"))
    notif_col = db["notifications"]

    query: Dict[str, Any] = {"recipient_id": user_id}
    if unread_only:
        query["is_read"] = False

    cursor = notif_col.find(query).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(limit)

    for d in docs:
        d.pop("_id", None)

    unread_docs = await notif_col.find({"recipient_id": user_id, "is_read": False}).to_list(1000)

    return {
        "total": len(docs),
        "unread_count": len(unread_docs),
        "items": docs
    }

@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Returns unread notification badge count for the current user.
    """
    user_id = str(current_user.get("id") or current_user.get("_id"))
    notif_col = db["notifications"]
    unread_docs = await notif_col.find({"recipient_id": user_id, "is_read": False}).to_list(1000)
    return {"unread_count": len(unread_docs)}

@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Marks a specific notification as read.
    Enforces ownership: Users cannot mutate another user's notifications.
    """
    user_id = str(current_user.get("id") or current_user.get("_id"))
    notif_col = db["notifications"]

    notif = await notif_col.find_one({"id": notification_id})
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(notif.get("recipient_id")) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot access another user's notifications.")

    await notif_col.update_one({"id": notification_id}, {"$set": {"is_read": True}})
    return {"success": True, "message": "Notification marked as read"}

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Marks all notifications as read for the current user.
    """
    user_id = str(current_user.get("id") or current_user.get("_id"))
    notif_col = db["notifications"]
    await notif_col.update_many({"recipient_id": user_id, "is_read": False}, {"$set": {"is_read": True}})
    return {"success": True, "message": "All notifications marked as read"}
