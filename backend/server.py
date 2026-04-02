"""
SmartSafety+ API - Main Server (Modular Architecture)
Gestión integral de seguridad operativa y prevención de riesgos

All business logic lives in routers/. This file only:
  1. Creates the FastAPI app
  2. Configures security middleware (CORS, rate limiting, audit trail)
  3. Mounts all routers under /api
  4. Seeds initial users on startup
"""
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
import os
import uuid
import asyncio
from datetime import datetime, timezone

from config import db, UPLOADS_DIR, logger
from utils.auth import hash_password
from utils.rate_limit import limiter, rate_limit_handler
from utils.middleware import AuditTrailMiddleware
from utils.escalation import escalation_loop

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
from routers.ai_engine import router as ai_router
from routers.search import router as search_router

# ─── App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SmartSafety+ API",
    description="Gestión integral de seguridad operativa y prevención de riesgos",
    version="2.1.0"
)

# ─── Rate Limiter ──────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# ─── CORS ─────────────────────────────────────────────────────────────
# Always include production domains + whatever is in env
_production_origins = [
    "https://smartsafety.tecops.cl",
    "http://smartsafety.tecops.cl",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
_env_cors = os.environ.get('CORS_ORIGINS', '')
_env_cors = _env_cors.strip().strip('"').strip("'")
_extra = [o.strip() for o in _env_cors.split(',') if o.strip() and o.strip() != '*']
_cors_origins = list(set(_production_origins + _extra))

logger.info(f"🌐 CORS origins: {_cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Audit Trail Middleware ────────────────────────────────────────────
app.add_middleware(AuditTrailMiddleware)

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
api.include_router(ai_router)
api.include_router(search_router)

app.include_router(api)

# ─── Static Files ──────────────────────────────────────────────────────
app.mount("/api/uploads/scans", StaticFiles(directory=str(UPLOADS_DIR / "scans")), name="scan-images")
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ─── Health Check ──────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "SmartSafety+ API", "version": "2.1.0"}

# ─── Startup: Seed initial users ──────────────────────────────────────
@app.on_event("startup")
async def setup_initial_data():
    # Ensure directories exist
    (UPLOADS_DIR / "scans").mkdir(exist_ok=True)

    # Create MongoDB indexes for audit trail
    await db.audit_log.create_index([("timestamp", -1)])
    await db.audit_log.create_index("user_email")
    await db.audit_log.create_index("method")

    # Create MongoDB indexes for notifications
    await db.in_app_notifications.create_index([("created_at", -1)])
    await db.in_app_notifications.create_index("target_roles")
    await db.in_app_notifications.create_index("read_by")

    # Create indexes for AI collections
    await db.ai_chat_history.create_index([("created_at", -1)])
    await db.ai_chat_history.create_index("user_id")
    await db.action_plans.create_index([("created_at", -1)])

    logger.info("Verificando usuarios iniciales para SmartSafety+...")
    initial_users = [
        {"email": "superadmin@smartsafety.cl", "password": "super123", "name": "Super Admin Safety", "role": "superadmin"},
        {"email": "admin@smartsafety.cl", "password": "admin123", "name": "Admin Safety", "role": "admin"},
        {"email": "colaborador@smartsafety.cl", "password": "colab123", "name": "Colaborador Safety", "role": "collaborator"}
    ]
    for user_data in initial_users:
        existing = await db.users.find_one({"email": user_data["email"]})
        if existing:
            # Always update password hash to ensure it matches
            await db.users.update_one(
                {"email": user_data["email"]},
                {"$set": {"hashed_password": hash_password(user_data["password"]), "role": user_data["role"], "is_active": True}}
            )
            logger.info(f"🔄 Password actualizado: {user_data['email']}")
        else:
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

    logger.info("🔒 Security: CORS restrictivo, Rate limiting, Audit trail activos")

    # Start background escalation engine (checks every 30 min)
    asyncio.create_task(escalation_loop(interval_minutes=30))
    logger.info("🔔 Escalation engine started")

# ─── Shutdown ──────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown():
    from config import client
    client.close()
