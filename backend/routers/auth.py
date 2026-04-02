"""SmartSafety+ - Auth & Users Router"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from config import db, logger
from models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from utils.auth import hash_password, verify_password, create_token, get_current_user
from datetime import datetime, timezone
import uuid

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "hashed_password": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.email, user_data.role)
    user_response = UserResponse(
        id=user_id, email=user_data.email, name=user_data.name,
        role=user_data.role, created_at=user_doc["created_at"], is_active=True
    )
    return TokenResponse(access_token=token, user=user_response)


@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    logger.info(f"🔑 Login attempt: {credentials.email}")
    
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        logger.warning(f"❌ User not found: {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.info(f"✅ User found: {user.get('email')} | has hashed_password: {'hashed_password' in user}")
    
    if not verify_password(credentials.password, user["hashed_password"]):
        logger.warning(f"❌ Password mismatch for: {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    user_response = UserResponse(
        id=user["id"], email=user["email"], name=user["name"],
        role=user["role"], created_at=user["created_at"],
        is_active=user.get("is_active", True)
    )
    logger.info(f"✅ Login success: {credentials.email}")
    return TokenResponse(access_token=token, user=user_response)


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)


# ================== DEBUG (temporary) ==================

@router.get("/auth/debug-users")
async def debug_users():
    """Temporary debug endpoint - shows users in DB (remove in production)"""
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(100)
    count = await db.users.count_documents({})
    
    # Test password for admin
    admin = await db.users.find_one({"email": "admin@smartsafety.cl"}, {"_id": 0})
    admin_pwd_ok = False
    admin_has_hash = False
    if admin:
        admin_has_hash = "hashed_password" in admin
        if admin_has_hash:
            try:
                admin_pwd_ok = verify_password("admin123", admin["hashed_password"])
            except Exception as e:
                admin_pwd_ok = f"error: {str(e)}"
    
    return {
        "total_users": count,
        "users": [{"email": u.get("email"), "role": u.get("role"), "has_hash": "hashed_password" in u, "fields": list(u.keys())} for u in users],
        "admin_test": {
            "found": admin is not None,
            "has_hashed_password": admin_has_hash,
            "password_verify": admin_pwd_ok,
        }
    }


# ================== USERS MANAGEMENT ==================

@router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    users = await db.users.find({"role": {"$ne": "superadmin"}}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.users.update_one({"id": user_id}, {"$set": {"role": role}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

@router.put("/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    update_data = {k: v for k, v in profile.items() if v is not None and k != "password"}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = await db.users.update_one({"id": user_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Profile updated"}
