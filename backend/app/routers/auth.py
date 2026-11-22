from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from app.models.user import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
    OfficerRegisterRequest,
    OfficerReviewAction,
    OfficerRegistrationResponse
)
from app.database import get_db
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user, require_role
from app.routers.audit import log_audit_event
from app.config import settings
from datetime import datetime
import uuid
import re

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserCreate):
    """
    Public Citizen Registration endpoint.
    Strictly forces role='citizen', approval_status='approved', and is_active=True.
    Public registration can never assign admin or officer roles.
    """
    db = get_db()
    users_col = db.get_collection("users")
    
    clean_email = user_in.email.lower().strip()
    existing = await users_col.find_one({"email": clean_email})
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    if len(user_in.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    user_doc = {
        "_id": user_id,
        "id": user_id,
        "email": clean_email,
        "password": get_password_hash(user_in.password),
        "full_name": user_in.full_name.strip(),
        "role": "citizen",  # Strictly enforced: public registration is for citizens only
        "phone": user_in.phone.strip() if user_in.phone else None,
        "address": user_in.address.strip() if user_in.address else None,
        "badge_id": None,
        "employee_id": None,
        "department": None,
        "designation": None,
        "assigned_area": None,
        "approval_status": "approved",
        "is_active": True,
        "avatar_url": user_in.avatar_url or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
        "created_at": now_iso
    }
    
    await users_col.insert_one(user_doc)
    
    await log_audit_event(
        db=db,
        user=user_doc,
        action="CITIZEN_REGISTERED",
        target_id=user_id,
        details={"email": user_doc["email"], "full_name": user_doc["full_name"]}
    )

    token = create_access_token(data={"sub": user_id, "role": "citizen", "email": user_doc["email"]})
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user_doc)
    )

@router.post("/register-officer", response_model=OfficerRegistrationResponse)
@router.post("/register/officer", response_model=OfficerRegistrationResponse)
async def register_officer(req: OfficerRegisterRequest):
    """
    Municipal Officer Registration Request endpoint.
    Validates employee ID and official email uniqueness.
    Registers applicant with approval_status='pending_approval' and is_active=False.
    Does NOT issue an access token. Officer cannot log in until approved by an Admin.
    """
    db = get_db()
    users_col = db.get_collection("users")

    clean_email = req.email.lower().strip()
    existing_email = await users_col.find_one({"email": clean_email})
    if existing_email:
        raise HTTPException(status_code=400, detail="An account with this email address already exists")

    clean_emp_id = req.employee_id.strip()
    existing_emp = await users_col.find_one({
        "$or": [
            {"badge_id": {"$regex": f"^{re.escape(clean_emp_id)}$", "$options": "i"}},
            {"employee_id": {"$regex": f"^{re.escape(clean_emp_id)}$", "$options": "i"}}
        ]
    })
    if existing_emp:
        raise HTTPException(
            status_code=400,
            detail=f"An officer with Employee ID '{clean_emp_id}' is already registered or pending review."
        )

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user_id = f"usr_off_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.utcnow().isoformat() + "Z"

    user_doc = {
        "_id": user_id,
        "id": user_id,
        "email": clean_email,
        "password": get_password_hash(req.password),
        "full_name": req.full_name.strip(),
        "role": "officer",
        "phone": req.phone.strip(),
        "badge_id": clean_emp_id,
        "employee_id": clean_emp_id,
        "department": req.department.strip(),
        "designation": req.designation.strip(),
        "assigned_area": req.assigned_area.strip(),
        "approval_status": "pending_approval",
        "is_active": False,
        "rejection_reason": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80",
        "created_at": now_iso
    }

    await users_col.insert_one(user_doc)

    await log_audit_event(
        db=db,
        user={"id": user_id, "full_name": req.full_name.strip(), "role": "officer_applicant"},
        action="OFFICER_REGISTRATION_SUBMITTED",
        target_id=user_id,
        details={
            "email": clean_email,
            "employee_id": clean_emp_id,
            "department": req.department.strip(),
            "designation": req.designation.strip(),
            "assigned_area": req.assigned_area.strip()
        }
    )

    return OfficerRegistrationResponse(
        id=user_id,
        message="Your officer registration request has been submitted successfully and is awaiting administrator approval.",
        approval_status="pending_approval",
        email=clean_email,
        full_name=user_doc["full_name"],
        employee_id=clean_emp_id,
        department=user_doc["department"],
        designation=user_doc["designation"],
        assigned_area=user_doc["assigned_area"]
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Role-Based Login Authentication.
    Validates credentials and ensures officers/users with 'pending_approval',
    'rejected', or deactivated status are blocked with appropriate HTTP 403 details.
    """
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"email": credentials.email.lower().strip()})
    
    if not user or not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check approval status and account activation
    approval_status = user.get("approval_status", "approved")
    is_active = user.get("is_active", True)

    if approval_status == "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your officer registration is awaiting administrator approval."
        )

    if approval_status == "rejected":
        reason = user.get("rejection_reason")
        detail_msg = f"Your officer registration application was rejected: {reason}" if reason else "Your officer registration application has been rejected."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_msg
        )

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your municipal administrator."
        )

    user_id = user.get("id") or str(user.get("_id"))
    token = create_access_token(data={"sub": user_id, "role": user.get("role", "citizen"), "email": user.get("email")})
    
    if "id" not in user:
        user["id"] = user_id
        
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(**current_user)

@router.get("/officers", response_model=List[UserResponse])
async def list_approved_officers(current_user: Dict[str, Any] = Depends(require_role(["admin", "officer"]))):
    """
    List active, approved municipal officers (for dispatching, assignment dropdowns, etc.).
    Pending and rejected officer applications are excluded.
    """
    db = get_db()
    users_col = db.get_collection("users")
    query = {
        "role": "officer",
        "approval_status": {"$in": ["approved", None]},
        "is_active": {"$ne": False}
    }
    officers = await users_col.find(query).to_list(100)
    for o in officers:
        if "id" not in o:
            o["id"] = str(o["_id"])
    return [UserResponse(**o) for o in officers]

@router.get("/officers/pending", response_model=List[UserResponse])
async def list_pending_officers(current_user: Dict[str, Any] = Depends(require_role(["admin"]))):
    """
    Admin-only: Retrieve all officer registration applications awaiting administrator review.
    """
    db = get_db()
    users_col = db.get_collection("users")
    pending = await users_col.find({
        "role": "officer",
        "approval_status": "pending_approval"
    }).sort("created_at", -1).to_list(100)
    
    for o in pending:
        if "id" not in o:
            o["id"] = str(o["_id"])
    return [UserResponse(**o) for o in pending]

@router.get("/officers/all", response_model=List[UserResponse])
async def list_all_officers(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """
    Admin-only: Retrieve officers with optional filter by approval status ('approved', 'pending_approval', 'rejected', 'all').
    """
    db = get_db()
    users_col = db.get_collection("users")
    query: Dict[str, Any] = {"role": "officer"}
    
    if status_filter and status_filter.lower() != "all":
        query["approval_status"] = status_filter.lower()
        
    officers = await users_col.find(query).sort("created_at", -1).to_list(200)
    for o in officers:
        if "id" not in o:
            o["id"] = str(o["_id"])
    return [UserResponse(**o) for o in officers]

@router.post("/officers/{user_id}/approve", response_model=UserResponse)
async def approve_officer(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """
    Admin-only: Approve a pending municipal officer registration.
    Sets approval_status='approved', is_active=True, and role='officer'.
    Logs action to cryptographic audit trail.
    """
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"

    update_fields = {
        "approval_status": "approved",
        "is_active": True,
        "role": "officer",
        "reviewed_by": admin_identifier,
        "reviewed_at": now_iso,
        "rejection_reason": None
    }

    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_REGISTRATION_APPROVED",
        target_id=user["id"],
        details={
            "officer_email": user.get("email"),
            "officer_name": user.get("full_name"),
            "employee_id": user.get("badge_id") or user.get("employee_id"),
            "approved_by": admin_identifier
        }
    )

    return UserResponse(**user)

@router.post("/officers/{user_id}/reject", response_model=UserResponse)
async def reject_officer(
    user_id: str,
    action_in: Optional[OfficerReviewAction] = None,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """
    Admin-only: Reject an officer registration application with documented reason.
    Sets approval_status='rejected' and is_active=False.
    Logs action to cryptographic audit trail.
    """
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    reason = action_in.reason.strip() if action_in and action_in.reason and action_in.reason.strip() else "Application does not meet municipal verification criteria."
    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"

    update_fields = {
        "approval_status": "rejected",
        "is_active": False,
        "rejection_reason": reason,
        "reviewed_by": admin_identifier,
        "reviewed_at": now_iso
    }

    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_REGISTRATION_REJECTED",
        target_id=user["id"],
        details={
            "officer_email": user.get("email"),
            "officer_name": user.get("full_name"),
            "employee_id": user.get("badge_id") or user.get("employee_id"),
            "rejection_reason": reason,
            "rejected_by": admin_identifier
        }
    )

    return UserResponse(**user)

@router.post("/officers/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_officer(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """Admin-only: Deactivate an officer account."""
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"
    update_fields = {"is_active": False, "reviewed_by": admin_identifier, "reviewed_at": now_iso}
    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_STATUS_DEACTIVATED",
        target_id=user["id"],
        details={"officer_email": user.get("email"), "deactivated_by": admin_identifier}
    )
    return UserResponse(**user)

@router.post("/officers/{user_id}/activate", response_model=UserResponse)
async def activate_officer(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """Admin-only: Activate an approved officer account."""
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"
    update_fields = {"is_active": True, "approval_status": "approved", "reviewed_by": admin_identifier, "reviewed_at": now_iso}
    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_STATUS_ACTIVATED",
        target_id=user["id"],
        details={"officer_email": user.get("email"), "activated_by": admin_identifier}
    )
    return UserResponse(**user)

@router.post("/officers/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_officer_active(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """
    Admin-only: Toggle activation status (active/deactivated) of an approved officer.
    Logs action to cryptographic audit trail.
    """
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    current_active = user.get("is_active", True)
    new_active = not current_active
    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"

    update_fields = {
        "is_active": new_active,
        "reviewed_by": admin_identifier,
        "reviewed_at": now_iso
    }

    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_STATUS_TOGGLED",
        target_id=user["id"],
        details={
            "officer_email": user.get("email"),
            "previous_active": current_active,
            "new_active": new_active,
            "toggled_by": admin_identifier
        }
    )

    return UserResponse(**user)

@router.post("/officers/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_officer(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """Admin-only: Deactivate an officer account."""
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"
    update_fields = {"is_active": False, "reviewed_by": admin_identifier, "reviewed_at": now_iso}
    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_STATUS_DEACTIVATED",
        target_id=user["id"],
        details={"officer_email": user.get("email"), "deactivated_by": admin_identifier}
    )
    return UserResponse(**user)

@router.post("/officers/{user_id}/activate", response_model=UserResponse)
async def activate_officer(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """Admin-only: Activate an approved officer account."""
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    if not user:
        raise HTTPException(status_code=404, detail="Officer account not found")

    now_iso = datetime.utcnow().isoformat() + "Z"
    admin_identifier = current_user.get("email") or current_user.get("full_name") or "Administrator"
    update_fields = {"is_active": True, "approval_status": "approved", "reviewed_by": admin_identifier, "reviewed_at": now_iso}
    await users_col.update_one({"_id": user["_id"]}, {"$set": update_fields})
    user.update(update_fields)
    if "id" not in user:
        user["id"] = str(user["_id"])

    await log_audit_event(
        db=db,
        user=current_user,
        action="OFFICER_STATUS_ACTIVATED",
        target_id=user["id"],
        details={"officer_email": user.get("email"), "activated_by": admin_identifier}
    )
    return UserResponse(**user)

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    role_filter: Optional[str] = Query(None, alias="role"),
    approval_filter: Optional[str] = Query(None, alias="approval_status"),
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """
    Admin-only: Retrieve all registered system users with optional role and approval status filters.
    """
    db = get_db()
    users_col = db.get_collection("users")
    query: Dict[str, Any] = {}
    
    if role_filter and role_filter.lower() != "all":
        query["role"] = role_filter.lower()
    if approval_filter and approval_filter.lower() != "all":
        query["approval_status"] = approval_filter.lower()

    all_users = await users_col.find(query).sort("created_at", -1).to_list(200)
    for u in all_users:
        if "id" not in u:
            u["id"] = str(u["_id"])
    return [UserResponse(**u) for u in all_users]

@router.post("/demo-switch/{role}", response_model=TokenResponse)
async def demo_role_switcher(role: str):
    """Convenience endpoint to seamlessly switch between Admin, Officer, and Citizen roles for testing & viva presentation."""
    if not settings.ALLOW_DEMO_SWITCH:
        raise HTTPException(
            status_code=403,
            detail="Demo persona switching is disabled in production environment. Please authenticate via /api/auth/login with registered municipal credentials."
        )

    role = role.lower()
    if role not in ["admin", "officer", "citizen"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be admin, officer, or citizen.")
    
    email_map = {
        "admin": "admin@encrowatch.ai",
        "officer": "officer@encrowatch.ai",
        "citizen": "citizen@encrowatch.ai"
    }
    
    db = get_db()
    users_col = db.get_collection("users")
    user = await users_col.find_one({"email": email_map[role]})
    if not user:
        user = await users_col.find_one({"role": role})

    if not user:
        # Auto-provision demo user if database is fresh or unseeded
        user_id = f"usr_demo_{role}"
        now_iso = datetime.utcnow().isoformat() + "Z"
        user = {
            "_id": user_id,
            "id": user_id,
            "email": email_map[role],
            "password": get_password_hash("password123"),
            "full_name": f"Demo {role.title()}",
            "role": role,
            "phone": "+91 98765 43210",
            "badge_id": "ADM-001" if role == "admin" else ("OFF-012" if role == "officer" else None),
            "employee_id": "ADM-001" if role == "admin" else ("OFF-012" if role == "officer" else None),
            "department": "Municipal IT" if role == "admin" else ("Field Enforcement" if role == "officer" else None),
            "designation": "Administrator" if role == "admin" else ("Enforcement Officer" if role == "officer" else None),
            "assigned_area": "City Center" if role != "citizen" else None,
            "approval_status": "approved",
            "is_active": True,
            "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
            "created_at": now_iso
        }
        await users_col.insert_one(user)
        
    user_id = user.get("id") or str(user.get("_id"))
    token = create_access_token(data={"sub": user_id, "role": role, "email": user.get("email")})
    
    if "id" not in user:
        user["id"] = user_id

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user)
    )
