"""
SmartSafety+ - Main Server (Modular Architecture)
Gestión integral de seguridad operativa y prevención de riesgos
"""
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import logging

from config import ROOT_DIR, UPLOADS_DIR

# Import routers
from routers.auth import router as auth_router
from routers.epp import router as epp_router
from routers.incidents import router as incidents_router, investigations_router
from routers.scans import router as scans_router
from routers.config import router as config_router, cost_centers_router, organization_router

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="SmartSafety+ API",
    description="Gestión integral de seguridad operativa y prevención de riesgos",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main API Router
api_router = APIRouter(prefix="/api")

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(epp_router)
api_router.include_router(incidents_router)
api_router.include_router(investigations_router)
api_router.include_router(scans_router)
api_router.include_router(config_router)
api_router.include_router(cost_centers_router)
api_router.include_router(organization_router)

# Mount API router
app.include_router(api_router)

# Static files for uploads
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "SmartSafety+ API", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
