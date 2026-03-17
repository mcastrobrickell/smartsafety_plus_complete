"""
SmartSafety+ - Authentication Router
"""
from fastapi import APIRouter, HTTPException, Depends
from config import db
from models.schemas import UserCreate, UserLogin, UserInDB
from utils.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_in_db = UserInDB(
        email=user.email,
        hashed_password=hash_password(user.password),
        name=user.name,
        role=user.role
    )
    await db.users.insert_one(user_in_db.model_dump())
    
    return {
        "id": user_in_db.id,
        "email": user_in_db.email,
        "name": user_in_db.name,
        "role": user_in_db.role
    }


@router.post("/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"], user["name"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    return users
