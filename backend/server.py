"""
SmartSafety+ API - Main Server (Modular Architecture)
Gestión integral de seguridad operativa y prevención de riesgos

All business logic lives in routers/. This file only:
  1. Creates the FastAPI app
  2. Configures CORS middleware
  3. Mounts all routers under /api
  4. Seeds initial users on startup
"""
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import uuid
from datetime import datetime, timezone

from config import db, UPLOADS_DIR, logger
from utils.auth import hash_password

# Import all routers
from routers.auth import router as auth_router
from routers.config_routes import router as config_router, cost_centers_router, organization_router
from routers.epp import router as epp_router
from routers.incidents import router as incidents_router, investigations_router
from routers.scans import router as scans_router
from routers.procedures import router as procedures_router
from routers.risk_matrix import router as risk_matrix_router
from routers.dashboard import router as dashboard_router
from routers.notifications import router as notifications_router
from routers.reports import router as reports_router
from routers.ecosystem import router as ecosystem_router

# ─── App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SmartSafety+ API",
    description="Gestión integral de seguridad operativa y prevención de riesgos",
    version="2.0.0"
)

# ─── CORS ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Router (prefix /api) ──────────────────────────────────────────
api = APIRouter(prefix="/api")

api.include_router(auth_router)
api.include_router(config_router)
api.include_router(cost_centers_router)
api.include_router(organization_router)
api.include_router(epp_router)
api.include_router(incidents_router)
api.include_router(investigations_router)
api.include_router(scans_router)
api.include_router(procedures_router)
api.include_router(risk_matrix_router)
api.include_router(dashboard_router)
api.include_router(notifications_router)
api.include_router(reports_router)
api.include_router(ecosystem_router)

app.include_router(api)

# ─── Static Files ──────────────────────────────────────────────────────
app.mount("/api/uploads/scans", StaticFiles(directory=str(UPLOADS_DIR / "scans")), name="scan-images")
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ─── Health Check ──────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "SmartSafety+ API", "version": "2.0.0"}

# ─── Startup: Seed initial users ──────────────────────────────────────
@app.on_event("startup")
async def setup_initial_data():
    # Ensure directories exist
    (UPLOADS_DIR / "scans").mkdir(exist_ok=True)
    
    logger.info("Verificando usuarios iniciales para SmartSafety+...")
    initial_users = [
        {"email": "superadmin@smartsafety.cl", "password": "super123", "name": "Super Admin Safety", "role": "superadmin"},
        {"email": "admin@smartsafety.cl", "password": "admin123", "name": "Admin Safety", "role": "admin"},
        {"email": "colaborador@smartsafety.cl", "password": "colab123", "name": "Colaborador Safety", "role": "collaborator"}
    ]
    for user_data in initial_users:
        existing = await db.users.find_one({"email": user_data["email"]})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": user_data["email"],
                "hashed_password": hash_password(user_data["password"]),
                "name": user_data["name"],
                "role": user_data["role"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"✅ Usuario creado: {user_data['email']}")

# ─── Shutdown ──────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown():
    from config import client
    client.close()
