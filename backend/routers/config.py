"""
SmartSafety+ - Configuration Router
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
from datetime import datetime, timezone

from config import db, UPLOADS_DIR
from models.schemas import ConfigCategory, CostCenter
from utils.auth import get_current_user

router = APIRouter(prefix="/config", tags=["Configuration"])


# ================== CATEGORIES ==================

@router.get("/categories")
async def get_categories(
    config_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"is_active": True}
    if config_type:
        query["type"] = config_type
    categories = await db.config_categories.find(query, {"_id": 0}).to_list(1000)
    return categories


@router.post("/categories")
async def create_category(category: ConfigCategory, current_user: dict = Depends(get_current_user)):
    await db.config_categories.insert_one(category.model_dump())
    return category


@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    result = await db.config_categories.update_one(
        {"id": category_id},
        {"$set": updates}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return await db.config_categories.find_one({"id": category_id}, {"_id": 0})


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.config_categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"status": "deleted"}


# ================== COST CENTERS ==================

cost_centers_router = APIRouter(prefix="/cost-centers", tags=["Cost Centers"])


@cost_centers_router.get("")
async def get_cost_centers(current_user: dict = Depends(get_current_user)):
    centers = await db.cost_centers.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return centers


@cost_centers_router.post("")
async def create_cost_center(center: CostCenter, current_user: dict = Depends(get_current_user)):
    existing = await db.cost_centers.find_one({"code": center.code})
    if existing:
        raise HTTPException(status_code=400, detail="Cost center code already exists")
    
    await db.cost_centers.insert_one(center.model_dump())
    return center


@cost_centers_router.delete("/{center_id}")
async def delete_cost_center(center_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.cost_centers.update_one(
        {"id": center_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return {"status": "deleted"}


# ================== ORGANIZATION ==================

organization_router = APIRouter(prefix="/organization", tags=["Organization"])


@organization_router.get("/current")
async def get_current_organization(current_user: dict = Depends(get_current_user)):
    """Get or create default organization for the system"""
    import uuid
    
    org = await db.organizations.find_one({}, {"_id": 0})
    
    if not org:
        org = {
            "id": str(uuid.uuid4()),
            "name": "Mi Organizacion",
            "logo_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organizations.insert_one(org)
        org.pop("_id", None)
    
    return org


@organization_router.put("/current")
async def update_current_organization(
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update organization details"""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    allowed_fields = ["name"]
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.organizations.update_one(
        {"id": org["id"]},
        {"$set": update_data}
    )
    
    updated_org = await db.organizations.find_one({"id": org["id"]}, {"_id": 0})
    return updated_org


@organization_router.post("/current/logo")
async def upload_current_organization_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload logo for current organization (Admin or SuperAdmin)"""
    import uuid
    
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        org = {
            "id": str(uuid.uuid4()),
            "name": "Mi Organizacion",
            "logo_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organizations.insert_one(org)
    
    org_id = org["id"]
    
    allowed_types = ["image/png", "image/jpeg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes PNG, JPEG o WebP")
    
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"logo_{org_id}.{file_ext}"
    file_path = UPLOADS_DIR / filename
    
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no debe superar 2MB")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    logo_url = f"/api/uploads/{filename}"
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"logo_url": logo_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "logo_url": logo_url}


@organization_router.delete("/current/logo")
async def delete_current_organization_logo(
    current_user: dict = Depends(get_current_user)
):
    """Delete logo for current organization"""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org.get("logo_url"):
        filename = org["logo_url"].split("/")[-1]
        file_path = UPLOADS_DIR / filename
        if file_path.exists():
            file_path.unlink()
    
    await db.organizations.update_one(
        {"id": org["id"]},
        {"$set": {"logo_url": None, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "message": "Logo eliminado"}
