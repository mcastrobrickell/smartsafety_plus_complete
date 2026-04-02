"""SmartSafety+ - Config, Cost Centers & Organization Router"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional
from config import db, UPLOADS_DIR, logger
from models.schemas import ConfigCategory, CostCenter
from utils.auth import get_current_user
from datetime import datetime, timezone
import uuid
import io

router = APIRouter(tags=["config"])
cost_centers_router = APIRouter(tags=["cost-centers"])
organization_router = APIRouter(tags=["organization"])

@router.get("/config/categories")
async def get_config_categories(config_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if config_type:
        query["type"] = config_type
    categories = await db.config_categories.find(query, {"_id": 0}).to_list(1000)
    return categories

@router.post("/config/categories")
async def create_config_category(category: ConfigCategory, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.config_categories.insert_one(category.model_dump())
    return category

@router.put("/config/categories/{category_id}")
async def update_config_category(category_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.config_categories.update_one({"id": category_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category updated"}

@router.delete("/config/categories/{category_id}")
async def delete_config_category(category_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.config_categories.delete_one({"id": category_id})
    return {"message": "Category deleted"}

@cost_centers_router.get("/cost-centers")
async def get_cost_centers(current_user: dict = Depends(get_current_user)):
    centers = await db.cost_centers.find({}, {"_id": 0}).to_list(1000)
    return centers

@cost_centers_router.post("/cost-centers")
async def create_cost_center(center: CostCenter, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.cost_centers.insert_one(center.model_dump())
    return center

@cost_centers_router.put("/cost-centers/{center_id}")
async def update_cost_center(center_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.cost_centers.update_one({"id": center_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return {"message": "Cost center updated"}

@cost_centers_router.delete("/cost-centers/{center_id}")
async def delete_cost_center(center_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.cost_centers.delete_one({"id": center_id})
    return {"message": "Cost center deleted"}

@organization_router.get("/organization/current")
async def get_current_organization(current_user: dict = Depends(get_current_user)):
    """Get or create default organization for the system"""
    
    # Try to find existing organization
    org = await db.organizations.find_one({}, {"_id": 0})
    
    if not org:
        # Create default organization
        org = {
            "id": str(uuid.uuid4()),
            "name": "Mi Organización",
            "logo_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organizations.insert_one(org)
        org.pop("_id", None)
    
    return org


@organization_router.put("/organization/current")
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


@organization_router.post("/organization/current/logo")
async def upload_current_organization_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload logo for current organization (Admin or SuperAdmin)"""
    
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get or create organization
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        org = {
            "id": str(uuid.uuid4()),
            "name": "Mi Organización",
            "logo_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organizations.insert_one(org)
    
    org_id = org["id"]
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes PNG, JPEG o WebP")
    
    # Save file
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"logo_{org_id}.{file_ext}"
    file_path = UPLOADS_DIR / filename
    
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:  # 2MB limit
        raise HTTPException(status_code=400, detail="El archivo no debe superar 2MB")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update organization
    logo_url = f"/api/uploads/{filename}"
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"logo_url": logo_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "logo_url": logo_url}


@organization_router.delete("/organization/current/logo")
async def delete_current_organization_logo(
    current_user: dict = Depends(get_current_user)
):
    """Delete logo for current organization"""
    
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Delete file if exists
    if org.get("logo_url"):
        filename = org["logo_url"].split("/")[-1]
        file_path = UPLOADS_DIR / filename
        if file_path.exists():
            file_path.unlink()
    
    # Update organization
    await db.organizations.update_one(
        {"id": org["id"]},
        {"$set": {"logo_url": None, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "message": "Logo eliminado"}


@organization_router.post("/organizations/{org_id}/logo")
async def upload_organization_logo(
    org_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload organization logo"""
    
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="SuperAdmin access required")
    
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes PNG, JPEG o WebP")
    
    # Save file
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"logo_{org_id}.{file_ext}"
    file_path = UPLOADS_DIR / filename
    
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:  # 2MB limit
        raise HTTPException(status_code=400, detail="El archivo no debe superar 2MB")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update organization
    logo_url = f"/api/uploads/{filename}"
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"logo_url": logo_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "logo_url": logo_url}


@organization_router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Serve uploaded files"""
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type
    ext = filename.split('.')[-1].lower()
    content_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp"
    }
    content_type = content_types.get(ext, "application/octet-stream")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type
    )

