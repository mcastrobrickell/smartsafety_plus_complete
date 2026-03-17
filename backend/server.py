from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import base64
import asyncio
import io
import resend
import pandas as pd
from fpdf import FPDF
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'smartsafety_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# Initialize Twilio
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        logger.warning(f"Twilio initialization failed: {e}")

# Uploads directory for logos
UPLOADS_DIR = ROOT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SmartSafety+ API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================== MODELS ==================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "inspector"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    created_at: str
    is_active: bool = True
    phone: Optional[str] = None
    specialization: Optional[str] = None
    certifications: Optional[str] = None
    location: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ================== EPP LOGISTICS MODELS ==================

class CostCenter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category_id: str
    description: Optional[str] = None
    specifications: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    category_id: str
    type_id: str
    brand: str
    model: Optional[str] = None
    unit_cost: float = 0.0
    certification_number: Optional[str] = None
    certification_expiry: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPStock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    epp_item_id: str
    cost_center_id: str
    warehouse_location: str
    quantity: int = 0
    min_stock: int = 5
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    epp_item_id: str
    epp_item_name: Optional[str] = None  # Store item name for historical reference
    epp_item_code: Optional[str] = None  # Store item code for historical reference
    movement_type: str  # reception, distribution, dispatch, delivery, return
    quantity: int
    unit_cost: float
    total_cost: float
    from_cost_center_id: Optional[str] = None
    to_cost_center_id: Optional[str] = None
    warehouse_location: Optional[str] = None
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    document_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPDelivery(BaseModel):
    """Entrega de EPP a trabajador - Formato completo"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    delivery_number: Optional[str] = None  # N° manual para migración
    date: str
    time: Optional[str] = None
    group: Optional[str] = None
    user: Optional[str] = None
    status: str = "entregado"  # entregado, devuelto, perdido
    
    # Responsable de la entrega
    responsible_name: str
    responsible_rut: Optional[str] = None
    responsible_position: Optional[str] = None
    
    # Colaborador que recibe
    worker_name: str
    worker_rut: Optional[str] = None
    worker_position: Optional[str] = None
    
    # Faena / Centro de costo
    cost_center_id: Optional[str] = None
    cost_center_name: Optional[str] = None
    
    # Tipo de entrega
    delivery_type: str = "entrega"  # entrega, reposicion
    
    # EPP entregado
    epp_item_id: str
    epp_item_code: Optional[str] = None
    epp_item_name: str
    unit: str = "unidad"
    quantity: int
    unit_cost: float = 0.0
    total_cost: float = 0.0
    
    # Detalles opcionales
    details: Optional[str] = None
    
    # Firma del trabajador
    signature_data: Optional[str] = None
    signature_confirmed: bool = False
    
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EPPStockAdjustment(BaseModel):
    """Ajuste de inventario de EPP"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    epp_item_id: str
    epp_item_code: Optional[str] = None
    epp_item_name: str
    previous_stock: int
    new_stock: int
    adjustment_quantity: int
    reason: str
    adjusted_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ================== INCIDENT MODELS ==================

class Incident(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: str
    category: str
    location: str
    reported_by: str
    reported_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "open"
    corrective_action: Optional[str] = None
    closed_at: Optional[str] = None

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    category: str
    location: str

# ================== SCAN & FINDINGS MODELS ==================

class SafetyFinding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scan_id: str
    category: str
    description: str
    severity: str
    normative_reference: str
    corrective_action: str
    position: Optional[dict] = None
    confidence: float = 0.0
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Scan360(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str
    scanned_by: str
    scanned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    image_data: Optional[str] = None
    findings_count: int = 0
    critical_count: int = 0
    status: str = "completed"
    procedure_id: Optional[str] = None

# ================== PROCEDURES MODELS ==================

class Procedure(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: Optional[str] = None
    content: str
    version: str = "1.0"
    category: str
    risks_identified: Optional[List[str]] = []
    controls_required: Optional[List[str]] = []
    epp_required: Optional[List[str]] = []
    ai_analysis: Optional[str] = None
    is_active: bool = True
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ================== RISK MATRIX MODELS ==================

class RiskMatrix(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    area: str
    process: str
    risks: List[Dict[str, Any]] = []
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "draft"


# ================== INCIDENT INVESTIGATION ISO 45001 ==================

class AffectedWorker(BaseModel):
    """Datos del trabajador afectado"""
    name: str
    rut: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    position: str
    department: Optional[str] = None
    seniority_position: Optional[str] = None
    seniority_company: Optional[str] = None
    previous_incidents: Optional[str] = None
    worker_type: Optional[str] = None  # SPOT or Base


class IncidentInvestigation(BaseModel):
    """Investigación de Incidentes según ISO 45001:2018 y formato RG-35"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(default_factory=lambda: f"RG-35-{datetime.now().strftime('%Y%m%d%H%M')}")
    version: str = "08"
    incident_id: str
    status: str = "draft"  # draft, in_progress, review, approved, closed
    
    # Sección 1: Antecedentes del Incidente
    incident_description: str
    incident_date: str
    incident_time: Optional[str] = None
    incident_types: List[str] = []  # SEGURIDAD, OPERACIONAL, AMBIENTAL, DOCUMENTAL, VEHICULAR, SALUD
    shift_day: Optional[str] = None
    consequences: Optional[str] = None
    body_part_injured: Optional[str] = None
    incident_location: str
    work_site: Optional[str] = None
    witnesses: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_position: Optional[str] = None
    
    # Sección 2: Antecedentes del Trabajador
    affected_worker: Optional[Dict[str, Any]] = None
    
    # Sección 3: Repetitividad
    occurrence_number: int = 1
    previous_incident_date: Optional[str] = None
    previous_actions_taken: Optional[str] = None
    previous_incident_status: Optional[str] = None
    
    # Sección 4: Cronograma
    work_schedule: Optional[str] = None
    
    # Sección 5: Recopilación de Información
    # 5.1 Entrevistas
    interviewed_workers: Optional[str] = None
    declarations_obtained: bool = False
    interview_observations: Optional[str] = None
    
    # 5.2 Pauta de Observación (Preguntas ISO 45001)
    task_observation: Optional[Dict[str, Any]] = None
    
    # 5.3 Revisión Documental
    document_review: Optional[Dict[str, Any]] = None
    
    # Sección 6: Evidencia Fotográfica
    photos: List[Dict[str, Any]] = []
    
    # Sección 7: Construcción del Relato
    narrative: Optional[str] = None
    facts_list: Optional[str] = None
    
    # Sección 8: Revisión de Capas (Modelo Heinrich)
    layer_analysis: Optional[Dict[str, Any]] = None
    
    # Sección 9: Árbol de Causas
    cause_tree: Optional[Dict[str, Any]] = None
    root_causes: List[str] = []
    
    # Sección 10: Causas según ISO 45001
    immediate_causes: List[str] = []  # Actos y condiciones subestándar
    basic_causes: List[str] = []  # Factores personales y del trabajo
    organizational_causes: List[str] = []  # Deficiencias en el SG-SST
    
    # Sección 11: Acciones Correctivas
    corrective_actions: List[Dict[str, Any]] = []
    
    # Metadatos
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class CorrectiveAction(BaseModel):
    """Acción correctiva para investigación de incidentes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    action_type: str  # immediate, preventive, corrective
    responsible: str
    due_date: str
    priority: str = "medium"  # low, medium, high, critical
    status: str = "pending"  # pending, in_progress, completed, verified
    verification_date: Optional[str] = None
    verified_by: Optional[str] = None
    evidence: Optional[str] = None
    iso_clause: Optional[str] = None  # Referencia a cláusula ISO 45001

class Risk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hazard: str
    risk_description: str
    consequences: str
    probability: int  # 1-5
    severity: int  # 1-5
    risk_level: int  # probability * severity
    existing_controls: str
    additional_controls: str
    responsible: str
    deadline: Optional[str] = None
    status: str = "open"

# ================== CONFIGURATION MODELS ==================

class ConfigCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # epp_category, epp_type, incident_category, risk_category
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ================== AUTH HELPERS ==================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ================== AUTH ROUTES ==================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.email, user_data.role)
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        created_at=user_doc["created_at"],
        is_active=True
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"],
        is_active=user.get("is_active", True)
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ================== USERS MANAGEMENT ==================

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    users = await db.users.find({"role": {"$ne": "superadmin"}}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.users.update_one({"id": user_id}, {"$set": {"role": role}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

@api_router.put("/users/{user_id}/profile")
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

# ================== CONFIGURATION (CATEGORIES & TYPES) ==================

@api_router.get("/config/categories")
async def get_config_categories(config_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if config_type:
        query["type"] = config_type
    categories = await db.config_categories.find(query, {"_id": 0}).to_list(1000)
    return categories

@api_router.post("/config/categories")
async def create_config_category(category: ConfigCategory, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.config_categories.insert_one(category.model_dump())
    return category

@api_router.put("/config/categories/{category_id}")
async def update_config_category(category_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.config_categories.update_one({"id": category_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category updated"}

@api_router.delete("/config/categories/{category_id}")
async def delete_config_category(category_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.config_categories.delete_one({"id": category_id})
    return {"message": "Category deleted"}

# ================== COST CENTERS ==================

@api_router.get("/cost-centers")
async def get_cost_centers(current_user: dict = Depends(get_current_user)):
    centers = await db.cost_centers.find({}, {"_id": 0}).to_list(1000)
    return centers

@api_router.post("/cost-centers")
async def create_cost_center(center: CostCenter, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.cost_centers.insert_one(center.model_dump())
    return center

@api_router.put("/cost-centers/{center_id}")
async def update_cost_center(center_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.cost_centers.update_one({"id": center_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return {"message": "Cost center updated"}

@api_router.delete("/cost-centers/{center_id}")
async def delete_cost_center(center_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.cost_centers.delete_one({"id": center_id})
    return {"message": "Cost center deleted"}

# ================== EPP ITEMS ==================

@api_router.get("/epp/items")
async def get_epp_items(current_user: dict = Depends(get_current_user)):
    items = await db.epp_items.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/epp/items")
async def create_epp_item(item: EPPItem, current_user: dict = Depends(get_current_user)):
    await db.epp_items.insert_one(item.model_dump())
    return item

@api_router.put("/epp/items/{item_id}")
async def update_epp_item(item_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    result = await db.epp_items.update_one({"id": item_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item updated"}

@api_router.delete("/epp/items/{item_id}")
async def delete_epp_item(item_id: str, current_user: dict = Depends(get_current_user)):
    await db.epp_items.delete_one({"id": item_id})
    return {"message": "Item deleted"}

# ================== EPP STOCK ==================

@api_router.get("/epp/stock")
async def get_epp_stock(cost_center_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if cost_center_id:
        query["cost_center_id"] = cost_center_id
    stocks = await db.epp_stock.find(query, {"_id": 0}).to_list(1000)
    return stocks

@api_router.get("/epp/stock/summary")
async def get_stock_summary(current_user: dict = Depends(get_current_user)):
    """Get stock summary by cost center with total values"""
    pipeline = [
        {
            "$lookup": {
                "from": "epp_items",
                "localField": "epp_item_id",
                "foreignField": "id",
                "as": "item"
            }
        },
        {"$unwind": {"path": "$item", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "cost_centers",
                "localField": "cost_center_id",
                "foreignField": "id",
                "as": "cost_center"
            }
        },
        {"$unwind": {"path": "$cost_center", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": "$cost_center_id",
                "cost_center_name": {"$first": "$cost_center.name"},
                "total_items": {"$sum": "$quantity"},
                "total_value": {"$sum": {"$multiply": ["$quantity", {"$ifNull": ["$item.unit_cost", 0]}]}},
                "low_stock_count": {
                    "$sum": {"$cond": [{"$lt": ["$quantity", "$min_stock"]}, 1, 0]}
                }
            }
        }
    ]
    summary = await db.epp_stock.aggregate(pipeline).to_list(1000)
    return summary

# ================== EPP MOVEMENTS (LOGISTICS FLOW) ==================

@api_router.get("/epp/movements")
async def get_epp_movements(
    movement_type: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if movement_type:
        query["movement_type"] = movement_type
    if cost_center_id:
        query["$or"] = [
            {"from_cost_center_id": cost_center_id},
            {"to_cost_center_id": cost_center_id}
        ]
    movements = await db.epp_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich movements with item names if missing
    items_cache = {}
    for movement in movements:
        if not movement.get("epp_item_name"):
            item_id = movement.get("epp_item_id")
            if item_id not in items_cache:
                item = await db.epp_items.find_one({"id": item_id}, {"_id": 0})
                items_cache[item_id] = item
            item = items_cache.get(item_id)
            if item:
                movement["epp_item_name"] = item.get("name", "")
                movement["epp_item_code"] = item.get("code", "")
    
    return movements

@api_router.post("/epp/movements/reception")
async def create_reception(
    epp_item_id: str,
    quantity: int,
    unit_cost: float,
    cost_center_id: str,
    warehouse_location: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Reception of EPP into warehouse"""
    # Get item info for historical reference
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    item_name = item.get("name", "N/A") if item else "N/A"
    item_code = item.get("code", "") if item else ""
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        epp_item_name=item_name,
        epp_item_code=item_code,
        movement_type="reception",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        to_cost_center_id=cost_center_id,
        warehouse_location=warehouse_location,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update or create stock
    existing_stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": cost_center_id,
        "warehouse_location": warehouse_location
    })
    
    if existing_stock:
        await db.epp_stock.update_one(
            {"id": existing_stock["id"]},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        stock = EPPStock(
            epp_item_id=epp_item_id,
            cost_center_id=cost_center_id,
            warehouse_location=warehouse_location,
            quantity=quantity
        )
        await db.epp_stock.insert_one(stock.model_dump())
    
    return movement

@api_router.post("/epp/movements/distribution")
async def create_distribution(
    epp_item_id: str,
    quantity: int,
    from_cost_center_id: str,
    to_cost_center_id: str,
    from_location: str,
    to_location: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Distribution between warehouses/locations"""
    # Check stock availability
    from_stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": from_cost_center_id,
        "warehouse_location": from_location
    })
    
    if not from_stock or from_stock["quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Get item cost
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    unit_cost = item.get("unit_cost", 0) if item else 0
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        movement_type="distribution",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        from_cost_center_id=from_cost_center_id,
        to_cost_center_id=to_cost_center_id,
        warehouse_location=to_location,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update stocks
    await db.epp_stock.update_one(
        {"id": from_stock["id"]},
        {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
    )
    
    to_stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": to_cost_center_id,
        "warehouse_location": to_location
    })
    
    if to_stock:
        await db.epp_stock.update_one(
            {"id": to_stock["id"]},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        stock = EPPStock(
            epp_item_id=epp_item_id,
            cost_center_id=to_cost_center_id,
            warehouse_location=to_location,
            quantity=quantity
        )
        await db.epp_stock.insert_one(stock.model_dump())
    
    return movement

@api_router.post("/epp/movements/dispatch")
async def create_dispatch(
    epp_item_id: str,
    quantity: int,
    cost_center_id: str,
    warehouse_location: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Dispatch EPP for delivery"""
    # Check stock
    stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": cost_center_id,
        "warehouse_location": warehouse_location
    })
    
    if not stock or stock["quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    unit_cost = item.get("unit_cost", 0) if item else 0
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        movement_type="dispatch",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        from_cost_center_id=cost_center_id,
        warehouse_location=warehouse_location,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update stock
    await db.epp_stock.update_one(
        {"id": stock["id"]},
        {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
    )
    
    return movement

@api_router.post("/epp/movements/delivery")
async def create_delivery(
    epp_item_id: str,
    quantity: int,
    worker_id: str,
    worker_name: str,
    cost_center_id: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Deliver EPP to worker"""
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="EPP item not found")
    
    unit_cost = item.get("unit_cost", 0)
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        movement_type="delivery",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        to_cost_center_id=cost_center_id,
        worker_id=worker_id,
        worker_name=worker_name,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Create delivery record
    delivery = EPPDelivery(
        epp_item_id=epp_item_id,
        epp_item_name=item["name"],
        worker_id=worker_id,
        worker_name=worker_name,
        cost_center_id=cost_center_id,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        delivery_date=datetime.now(timezone.utc).isoformat(),
        delivered_by=current_user["name"]
    )
    await db.epp_deliveries.insert_one(delivery.model_dump())
    
    return {"movement": movement.model_dump(), "delivery": delivery.model_dump()}

@api_router.post("/epp/movements/return")
async def create_return(
    delivery_id: str,
    quantity: int,
    cost_center_id: str,
    warehouse_location: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Return EPP from worker"""
    delivery = await db.epp_deliveries.find_one({"id": delivery_id}, {"_id": 0})
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    movement = EPPMovement(
        epp_item_id=delivery["epp_item_id"],
        movement_type="return",
        quantity=quantity,
        unit_cost=delivery["unit_cost"],
        total_cost=quantity * delivery["unit_cost"],
        from_cost_center_id=delivery["cost_center_id"],
        to_cost_center_id=cost_center_id,
        warehouse_location=warehouse_location,
        worker_id=delivery["worker_id"],
        worker_name=delivery["worker_name"],
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update delivery status
    await db.epp_deliveries.update_one(
        {"id": delivery_id},
        {"$set": {"status": "returned", "return_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Add back to stock
    stock = await db.epp_stock.find_one({
        "epp_item_id": delivery["epp_item_id"],
        "cost_center_id": cost_center_id,
        "warehouse_location": warehouse_location
    })
    
    if stock:
        await db.epp_stock.update_one(
            {"id": stock["id"]},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        new_stock = EPPStock(
            epp_item_id=delivery["epp_item_id"],
            cost_center_id=cost_center_id,
            warehouse_location=warehouse_location,
            quantity=quantity
        )
        await db.epp_stock.insert_one(new_stock.model_dump())
    
    return movement

# ================== EPP DELIVERIES ==================

@api_router.get("/epp/deliveries")
async def get_deliveries(
    status: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if cost_center_id:
        query["cost_center_id"] = cost_center_id
    deliveries = await db.epp_deliveries.find(query, {"_id": 0}).sort("delivery_date", -1).to_list(1000)
    return deliveries

# ================== EPP COST REPORTS ==================

@api_router.get("/epp/reports/costs")
async def get_cost_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get cost report by cost center"""
    match_stage = {}
    if start_date:
        match_stage["created_at"] = {"$gte": start_date}
    if end_date:
        match_stage.setdefault("created_at", {})["$lte"] = end_date
    if cost_center_id:
        match_stage["$or"] = [
            {"from_cost_center_id": cost_center_id},
            {"to_cost_center_id": cost_center_id}
        ]
    
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": {
                    "movement_type": "$movement_type",
                    "cost_center": {"$ifNull": ["$to_cost_center_id", "$from_cost_center_id"]}
                },
                "total_quantity": {"$sum": "$quantity"},
                "total_cost": {"$sum": "$total_cost"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"total_cost": -1}}
    ]
    
    report = await db.epp_movements.aggregate(pipeline).to_list(1000)
    return report


# ================== EPP DELIVERIES (ENHANCED) ==================

@api_router.post("/epp/deliveries/create")
async def create_delivery_enhanced(
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create delivery with full format (including manual ID for migration)"""
    
    # Get EPP item info
    item = await db.epp_items.find_one({"id": data.get("epp_item_id")}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="EPP item not found")
    
    unit_cost = item.get("unit_cost", 0)
    quantity = data.get("quantity", 1)
    
    delivery = EPPDelivery(
        delivery_number=data.get("delivery_number"),  # Manual ID for migration
        date=data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        time=data.get("time", datetime.now(timezone.utc).strftime("%H:%M")),
        group=data.get("group"),
        user=current_user.get("name"),
        status=data.get("status", "entregado"),
        responsible_name=data.get("responsible_name", current_user.get("name")),
        responsible_rut=data.get("responsible_rut"),
        responsible_position=data.get("responsible_position"),
        worker_name=data.get("worker_name"),
        worker_rut=data.get("worker_rut"),
        worker_position=data.get("worker_position"),
        cost_center_id=data.get("cost_center_id"),
        cost_center_name=data.get("cost_center_name"),
        delivery_type=data.get("delivery_type", "entrega"),
        epp_item_id=data.get("epp_item_id"),
        epp_item_code=item.get("code"),
        epp_item_name=item.get("name"),
        unit=item.get("unit", "unidad"),
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        details=data.get("details"),
        signature_data=data.get("signature_data"),
        signature_confirmed=data.get("signature_confirmed", False),
        created_by=current_user.get("id")
    )
    
    delivery_dict = delivery.model_dump()
    await db.epp_deliveries.insert_one(delivery_dict)
    
    # Decrease stock
    stock = await db.epp_stock.find_one({"epp_item_id": data.get("epp_item_id")})
    if stock:
        await db.epp_stock.update_one(
            {"id": stock["id"]},
            {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    
    delivery_dict.pop("_id", None)
    return {"message": "Entrega registrada correctamente", "delivery": delivery_dict}


@api_router.get("/epp/deliveries/export-pdf")
async def export_deliveries_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export deliveries as PDF"""
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    if cost_center_id:
        query["cost_center_id"] = cost_center_id
    
    deliveries = await db.epp_deliveries.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    pdf = SafetyPDF(
        title="Reporte de Entregas de EPP",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Stats
    total_deliveries = len(deliveries)
    total_items = sum(d.get("quantity", 0) for d in deliveries)
    total_cost = sum(d.get("total_cost", 0) for d in deliveries)
    
    pdf.add_stat_box("Entregas", total_deliveries, 10, pdf.get_y())
    pdf.add_stat_box("Items", total_items, 60, pdf.get_y())
    pdf.add_stat_box(f"Costo Total", f"${total_cost:,.0f}", 110, pdf.get_y())
    pdf.ln(30)
    
    # Table
    pdf.add_section_title("Detalle de Entregas")
    headers = ["N°", "Fecha", "Trabajador", "EPP", "Cant.", "Tipo"]
    widths = [20, 25, 50, 45, 15, 25]
    pdf.add_table_header(headers, widths)
    
    for i, d in enumerate(deliveries[:50]):
        pdf.add_table_row([
            d.get('delivery_number', str(i+1))[:8],
            d.get('date', '')[:10],
            d.get('worker_name', 'N/A')[:22],
            d.get('epp_item_name', 'N/A')[:20],
            str(d.get('quantity', 0)),
            d.get('delivery_type', 'entrega')[:10]
        ], widths, fill=(i % 2 == 0))
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=entregas-epp-{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@api_router.get("/epp/delivery/{delivery_id}/pdf")
async def export_single_delivery_pdf(
    delivery_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export single delivery as PDF document"""
    
    delivery = await db.epp_deliveries.find_one({"id": delivery_id}, {"_id": 0})
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    
    pdf = SafetyPDF(
        title="Comprobante de Entrega de EPP",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Delivery info
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"N° Entrega: {delivery.get('delivery_number', delivery.get('id', '')[:8])}", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.ln(5)
    
    # Delivery details
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, pdf.get_y(), 190, 50, 'F')
    y = pdf.get_y() + 5
    
    pdf.set_xy(15, y)
    pdf.cell(90, 5, f"Fecha: {delivery.get('date', 'N/A')}")
    pdf.cell(90, 5, f"Hora: {delivery.get('time', 'N/A')}", ln=True)
    
    pdf.set_xy(15, pdf.get_y() + 2)
    pdf.cell(90, 5, f"Tipo: {delivery.get('delivery_type', 'Entrega').upper()}")
    pdf.cell(90, 5, f"Centro de Costo: {delivery.get('cost_center_name', 'N/A')}", ln=True)
    
    pdf.ln(15)
    
    # Responsible
    pdf.add_section_title("Responsable de la Entrega", (59, 130, 246))
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Nombre: {delivery.get('responsible_name', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"RUT: {delivery.get('responsible_rut', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"Cargo: {delivery.get('responsible_position', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # Worker
    pdf.add_section_title("Trabajador que Recibe", (16, 185, 129))
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Nombre: {delivery.get('worker_name', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"RUT: {delivery.get('worker_rut', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"Cargo: {delivery.get('worker_position', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # EPP Details
    pdf.add_section_title("EPP Entregado", (249, 115, 22))
    headers = ["Código", "Artículo", "Unidad", "Cantidad", "Costo Unit.", "Total"]
    widths = [25, 60, 25, 25, 25, 25]
    pdf.add_table_header(headers, widths)
    pdf.add_table_row([
        delivery.get('epp_item_code', 'N/A'),
        delivery.get('epp_item_name', 'N/A')[:25],
        delivery.get('unit', 'unidad'),
        str(delivery.get('quantity', 0)),
        f"${delivery.get('unit_cost', 0):,.0f}",
        f"${delivery.get('total_cost', 0):,.0f}"
    ], widths, fill=True)
    
    pdf.ln(10)
    
    # Details
    if delivery.get('details'):
        pdf.add_section_title("Observaciones")
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 5, delivery.get('details', ''))
        pdf.ln(5)
    
    # Signature
    pdf.ln(15)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 30, "Firma Responsable:", border=1, align='C')
    pdf.cell(95, 30, "Firma Trabajador (Recibe Conforme):", border=1, align='C')
    
    if delivery.get('signature_confirmed'):
        pdf.ln(35)
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 8, "  FIRMADO  ", fill=True, align='C')
        pdf.set_text_color(30, 41, 59)
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=entrega-{delivery.get('delivery_number', delivery_id[:8])}.pdf"}
    )


# ================== EPP STOCK ADJUSTMENTS ==================

@api_router.get("/epp/stock/inventory")
async def get_stock_inventory(current_user: dict = Depends(get_current_user)):
    """Get complete stock inventory with item details"""
    
    items = await db.epp_items.find({"is_active": True}, {"_id": 0}).to_list(1000)
    stocks = await db.epp_stock.find({}, {"_id": 0}).to_list(1000)
    
    # Aggregate stock by item
    stock_by_item = {}
    for stock in stocks:
        item_id = stock.get("epp_item_id")
        if item_id not in stock_by_item:
            stock_by_item[item_id] = 0
        stock_by_item[item_id] += stock.get("quantity", 0)
    
    inventory = []
    for item in items:
        inventory.append({
            "id": item.get("id"),
            "code": item.get("code"),
            "name": item.get("name"),
            "category_id": item.get("category_id"),
            "unit": item.get("unit", "unidad"),
            "unit_cost": item.get("unit_cost", 0),
            "current_stock": stock_by_item.get(item.get("id"), 0),
            "min_stock": item.get("min_stock", 5),
            "stock_value": stock_by_item.get(item.get("id"), 0) * item.get("unit_cost", 0)
        })
    
    return inventory


@api_router.post("/epp/stock/adjust")
async def adjust_stock(
    epp_item_id: str,
    new_stock: int,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Adjust stock for inventory corrections"""
    
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="EPP item not found")
    
    # Get current stock
    stocks = await db.epp_stock.find({"epp_item_id": epp_item_id}, {"_id": 0}).to_list(100)
    current_stock = sum(s.get("quantity", 0) for s in stocks)
    
    adjustment_qty = new_stock - current_stock
    
    # Create adjustment record
    adjustment = EPPStockAdjustment(
        epp_item_id=epp_item_id,
        epp_item_code=item.get("code"),
        epp_item_name=item.get("name"),
        previous_stock=current_stock,
        new_stock=new_stock,
        adjustment_quantity=adjustment_qty,
        reason=reason,
        adjusted_by=current_user.get("name")
    )
    
    await db.epp_adjustments.insert_one(adjustment.model_dump())
    
    # Update or create stock record
    if stocks:
        # Update first stock record
        await db.epp_stock.update_one(
            {"id": stocks[0]["id"]},
            {"$set": {"quantity": new_stock, "last_updated": datetime.now(timezone.utc).isoformat()}}
        )
        # Zero out others if multiple
        for s in stocks[1:]:
            await db.epp_stock.update_one({"id": s["id"]}, {"$set": {"quantity": 0}})
    else:
        new_stock_doc = EPPStock(
            epp_item_id=epp_item_id,
            cost_center_id="general",
            warehouse_location="bodega_principal",
            quantity=new_stock
        )
        await db.epp_stock.insert_one(new_stock_doc.model_dump())
    
    return {
        "message": f"Stock ajustado de {current_stock} a {new_stock}",
        "adjustment": {
            "previous": current_stock,
            "new": new_stock,
            "difference": adjustment_qty
        }
    }


@api_router.get("/epp/adjustments")
async def get_adjustments(current_user: dict = Depends(get_current_user)):
    """Get stock adjustment history"""
    adjustments = await db.epp_adjustments.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return adjustments


# ================== EPP EXCEL IMPORT ==================

@api_router.post("/epp/import/items")
async def import_items_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP items from Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            item = {
                "id": str(uuid.uuid4()),
                "code": str(row.get("codigo", row.get("Codigo", ""))),
                "name": str(row.get("nombre", row.get("Nombre", ""))),
                "category_id": str(row.get("categoria", row.get("Categoria", "general"))),
                "type_id": str(row.get("tipo", row.get("Tipo", "general"))),
                "brand": str(row.get("marca", row.get("Marca", ""))),
                "model": str(row.get("modelo", row.get("Modelo", ""))) if pd.notna(row.get("modelo", row.get("Modelo"))) else None,
                "unit_cost": float(row.get("costo", row.get("Costo", row.get("costo_unitario", 0)))) if pd.notna(row.get("costo", row.get("Costo", row.get("costo_unitario")))) else 0,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            if item["code"] and item["name"]:
                await db.epp_items.insert_one(item)
                imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors, "total_rows": len(df)}


@api_router.post("/epp/import/receptions")
async def import_receptions_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP receptions from Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Find item by code
            code = str(row.get("codigo_epp", row.get("codigo", "")))
            item = await db.epp_items.find_one({"code": code}, {"_id": 0})
            
            if not item:
                errors.append(f"Fila {idx + 2}: Código EPP '{code}' no encontrado")
                continue
            
            quantity = int(row.get("cantidad", 0))
            unit_cost = float(row.get("costo_unitario", item.get("unit_cost", 0)))
            
            movement = {
                "id": str(uuid.uuid4()),
                "epp_item_id": item["id"],
                "movement_type": "reception",
                "quantity": quantity,
                "unit_cost": unit_cost,
                "total_cost": quantity * unit_cost,
                "document_number": str(row.get("documento", "")) if pd.notna(row.get("documento")) else None,
                "notes": str(row.get("notas", "")) if pd.notna(row.get("notas")) else None,
                "created_by": current_user.get("name"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.epp_movements.insert_one(movement)
            
            # Update stock
            stock = await db.epp_stock.find_one({"epp_item_id": item["id"]})
            if stock:
                await db.epp_stock.update_one(
                    {"id": stock["id"]},
                    {"$inc": {"quantity": quantity}}
                )
            else:
                new_stock = {
                    "id": str(uuid.uuid4()),
                    "epp_item_id": item["id"],
                    "cost_center_id": "general",
                    "warehouse_location": "bodega_principal",
                    "quantity": quantity,
                    "min_stock": 5,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await db.epp_stock.insert_one(new_stock)
            
            imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors, "total_rows": len(df)}


@api_router.post("/epp/import/deliveries")
async def import_deliveries_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP deliveries from Excel file (for migration)"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Find item by code
            code = str(row.get("codigo_epp", row.get("codigo", "")))
            item = await db.epp_items.find_one({"code": code}, {"_id": 0})
            
            if not item:
                errors.append(f"Fila {idx + 2}: Código EPP '{code}' no encontrado")
                continue
            
            quantity = int(row.get("cantidad", 1))
            unit_cost = float(row.get("costo_unitario", item.get("unit_cost", 0)))
            
            # Convert date
            date_val = row.get("fecha", datetime.now())
            if isinstance(date_val, str):
                date_str = date_val
            else:
                date_str = date_val.strftime("%Y-%m-%d") if pd.notna(date_val) else datetime.now().strftime("%Y-%m-%d")
            
            delivery = EPPDelivery(
                delivery_number=str(row.get("numero", row.get("N°", ""))) if pd.notna(row.get("numero", row.get("N°"))) else None,
                date=date_str,
                time=str(row.get("hora", "")) if pd.notna(row.get("hora")) else None,
                group=str(row.get("grupo", "")) if pd.notna(row.get("grupo")) else None,
                user=current_user.get("name"),
                status="entregado",
                responsible_name=str(row.get("responsable", current_user.get("name"))),
                responsible_rut=str(row.get("rut_responsable", "")) if pd.notna(row.get("rut_responsable")) else None,
                responsible_position=str(row.get("cargo_responsable", "")) if pd.notna(row.get("cargo_responsable")) else None,
                worker_name=str(row.get("trabajador", row.get("nombre_trabajador", ""))),
                worker_rut=str(row.get("rut_trabajador", "")) if pd.notna(row.get("rut_trabajador")) else None,
                worker_position=str(row.get("cargo_trabajador", "")) if pd.notna(row.get("cargo_trabajador")) else None,
                cost_center_id=str(row.get("centro_costo_id", "")) if pd.notna(row.get("centro_costo_id")) else None,
                cost_center_name=str(row.get("centro_costo", row.get("faena", ""))) if pd.notna(row.get("centro_costo", row.get("faena"))) else None,
                delivery_type=str(row.get("tipo_entrega", "entrega")).lower(),
                epp_item_id=item["id"],
                epp_item_code=item.get("code"),
                epp_item_name=item.get("name"),
                unit=item.get("unit", "unidad"),
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost,
                details=str(row.get("detalles", "")) if pd.notna(row.get("detalles")) else None,
                signature_confirmed=bool(row.get("firmado", False)) if pd.notna(row.get("firmado")) else False,
                created_by=current_user.get("id")
            )
            
            await db.epp_deliveries.insert_one(delivery.model_dump())
            imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors, "total_rows": len(df)}


# ================== INCIDENTS ==================

@api_router.get("/incidents")
async def get_incidents(current_user: dict = Depends(get_current_user)):
    incidents = await db.incidents.find({}, {"_id": 0}).to_list(1000)
    return incidents

@api_router.post("/incidents")
async def create_incident(incident: IncidentCreate, current_user: dict = Depends(get_current_user)):
    incident_doc = Incident(
        **incident.model_dump(),
        reported_by=current_user["name"]
    )
    await db.incidents.insert_one(incident_doc.model_dump())
    return incident_doc

@api_router.put("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, status: str, corrective_action: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    update_data = {"status": status}
    if corrective_action:
        update_data["corrective_action"] = corrective_action
    if status == "closed":
        update_data["closed_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.incidents.update_one({"id": incident_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident updated"}

@api_router.get("/incidents/stats")
async def get_incident_stats(current_user: dict = Depends(get_current_user)):
    total = await db.incidents.count_documents({})
    open_count = await db.incidents.count_documents({"status": "open"})
    critical = await db.incidents.count_documents({"severity": {"$in": ["critical", "critico"]}})
    
    by_category = await db.incidents.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    by_severity = await db.incidents.aggregate([
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    return {
        "total": total,
        "open": open_count,
        "critical": critical,
        "by_category": {item["_id"]: item["count"] for item in by_category if item["_id"]},
        "by_severity": {item["_id"]: item["count"] for item in by_severity if item["_id"]}
    }


# ================== INCIDENT INVESTIGATION ISO 45001 ==================

@api_router.get("/investigations")
async def get_investigations(status: str = None, current_user: dict = Depends(get_current_user)):
    """Get all incident investigations"""
    query = {}
    if status:
        query["status"] = status
    investigations = await db.investigations.find(query, {"_id": 0}).to_list(1000)
    return investigations


@api_router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific investigation with full details"""
    investigation = await db.investigations.find_one({"id": investigation_id}, {"_id": 0})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Get related incident
    incident = await db.incidents.find_one({"id": investigation.get("incident_id")}, {"_id": 0})
    
    return {"investigation": investigation, "incident": incident}


@api_router.post("/investigations")
async def create_investigation(
    incident_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a new investigation from an incident (ISO 45001 format)"""
    
    # Get incident
    incident = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Check if investigation already exists
    existing = await db.investigations.find_one({"incident_id": incident_id})
    if existing:
        raise HTTPException(status_code=400, detail="Investigation already exists for this incident")
    
    investigation = IncidentInvestigation(
        incident_id=incident_id,
        incident_description=incident.get("description", ""),
        incident_date=incident.get("reported_at", datetime.now(timezone.utc).isoformat())[:10],
        incident_location=incident.get("location", ""),
        incident_types=[incident.get("category", "SEGURIDAD")],
        created_by=current_user.get("id")
    )
    
    inv_dict = investigation.model_dump()
    await db.investigations.insert_one(inv_dict)
    inv_dict.pop("_id", None)
    
    # Update incident status
    await db.incidents.update_one(
        {"id": incident_id},
        {"$set": {"status": "investigating", "investigation_id": investigation.id}}
    )
    
    return {"message": "Investigación iniciada según ISO 45001:2018", "investigation": inv_dict}


@api_router.put("/investigations/{investigation_id}")
async def update_investigation(
    investigation_id: str,
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Update investigation data"""
    
    investigation = await db.investigations.find_one({"id": investigation_id})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Update fields
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.investigations.update_one(
        {"id": investigation_id},
        {"$set": data}
    )
    
    updated = await db.investigations.find_one({"id": investigation_id}, {"_id": 0})
    return {"message": "Investigación actualizada", "investigation": updated}


@api_router.post("/investigations/{investigation_id}/corrective-action")
async def add_corrective_action(
    investigation_id: str,
    action: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Add a corrective action to an investigation"""
    
    investigation = await db.investigations.find_one({"id": investigation_id})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    corrective_action = {
        "id": str(uuid.uuid4()),
        "description": action.get("description", ""),
        "action_type": action.get("action_type", "corrective"),
        "responsible": action.get("responsible", ""),
        "due_date": action.get("due_date", ""),
        "priority": action.get("priority", "medium"),
        "status": "pending",
        "iso_clause": action.get("iso_clause", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.investigations.update_one(
        {"id": investigation_id},
        {"$push": {"corrective_actions": corrective_action}}
    )
    
    return {"message": "Acción correctiva agregada", "action": corrective_action}


@api_router.put("/investigations/{investigation_id}/status")
async def update_investigation_status(
    investigation_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Update investigation status"""
    valid_statuses = ["draft", "in_progress", "review", "approved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_data = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    
    if status == "approved":
        update_data["approved_by"] = current_user.get("id")
        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.investigations.update_one(
        {"id": investigation_id},
        {"$set": update_data}
    )
    
    # If closed, update incident status
    if status == "closed":
        investigation = await db.investigations.find_one({"id": investigation_id})
        if investigation:
            await db.incidents.update_one(
                {"id": investigation.get("incident_id")},
                {"$set": {"status": "closed"}}
            )
    
    return {"message": f"Estado actualizado a: {status}"}


@api_router.get("/investigations/{investigation_id}/export-pdf")
async def export_investigation_pdf(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export investigation as PDF report (ISO 45001 format)"""
    
    investigation = await db.investigations.find_one({"id": investigation_id}, {"_id": 0})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    incident = await db.incidents.find_one({"id": investigation.get("incident_id")}, {"_id": 0})
    
    pdf = SafetyPDF(
        title=f"Investigación de Incidente - {investigation.get('code', 'RG-35')}",
        org_name="SmartSafety+ | ISO 45001:2018"
    )
    pdf.add_page()
    
    # Header info
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Código: {investigation.get('code', 'N/A')} | Versión: {investigation.get('version', '08')}", ln=True)
    pdf.cell(0, 6, f"Estado: {investigation.get('status', 'draft').upper()}", ln=True)
    pdf.cell(0, 6, f"Fecha: {investigation.get('created_at', '')[:10]}", ln=True)
    pdf.ln(10)
    
    # Section 1: Incident Background
    pdf.add_section_title("1. ANTECEDENTES DEL INCIDENTE", (59, 130, 246))
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, f"Descripción: {investigation.get('incident_description', 'N/A')}")
    pdf.ln(3)
    pdf.cell(95, 5, f"Fecha: {investigation.get('incident_date', 'N/A')}")
    pdf.cell(95, 5, f"Hora: {investigation.get('incident_time', 'N/A')}", ln=True)
    pdf.cell(95, 5, f"Ubicación: {investigation.get('incident_location', 'N/A')}")
    pdf.cell(95, 5, f"Tipos: {', '.join(investigation.get('incident_types', []))}", ln=True)
    pdf.ln(5)
    
    # Section 2: Affected Worker
    worker = investigation.get('affected_worker', {})
    if worker:
        pdf.add_section_title("2. ANTECEDENTES DEL TRABAJADOR AFECTADO", (59, 130, 246))
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(95, 5, f"Nombre: {worker.get('name', 'N/A')}")
        pdf.cell(95, 5, f"RUT: {worker.get('rut', 'N/A')}", ln=True)
        pdf.cell(95, 5, f"Cargo: {worker.get('position', 'N/A')}")
        pdf.cell(95, 5, f"Antigüedad: {worker.get('seniority_company', 'N/A')}", ln=True)
        pdf.ln(5)
    
    # Section 7: Narrative
    if investigation.get('narrative'):
        pdf.add_section_title("7. CONSTRUCCIÓN DEL RELATO", (59, 130, 246))
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, investigation.get('narrative', ''))
        pdf.ln(5)
    
    # Section 10: Causes (ISO 45001)
    pdf.add_section_title("10. ANÁLISIS DE CAUSAS (ISO 45001:2018)", (239, 68, 68))
    
    immediate = investigation.get('immediate_causes', [])
    if immediate:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, "Causas Inmediatas (Actos/Condiciones Subestándar):", ln=True)
        pdf.set_font('Helvetica', '', 9)
        for cause in immediate:
            pdf.cell(5, 5, "•")
            pdf.multi_cell(0, 5, cause)
    
    basic = investigation.get('basic_causes', [])
    if basic:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, "Causas Básicas (Factores Personales/Trabajo):", ln=True)
        pdf.set_font('Helvetica', '', 9)
        for cause in basic:
            pdf.cell(5, 5, "•")
            pdf.multi_cell(0, 5, cause)
    
    root = investigation.get('root_causes', [])
    if root:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, "Causas Raíz:", ln=True)
        pdf.set_font('Helvetica', '', 9)
        for cause in root:
            pdf.cell(5, 5, "•")
            pdf.multi_cell(0, 5, cause)
    
    pdf.ln(5)
    
    # Section 11: Corrective Actions
    actions = investigation.get('corrective_actions', [])
    if actions:
        pdf.add_section_title("11. ACCIONES CORRECTIVAS", (16, 185, 129))
        headers = ["Acción", "Tipo", "Responsable", "Fecha", "Estado"]
        widths = [60, 25, 35, 30, 25]
        pdf.add_table_header(headers, widths)
        
        for i, action in enumerate(actions):
            pdf.add_table_row([
                action.get('description', '')[:28],
                action.get('action_type', 'N/A')[:10],
                action.get('responsible', 'N/A')[:15],
                action.get('due_date', '')[:10],
                action.get('status', 'N/A')
            ], widths, fill=(i % 2 == 0))
    
    # Digital Signature Section
    signature = investigation.get('approved_signature', {})
    if signature:
        pdf.ln(10)
        pdf.add_section_title("FIRMA DE APROBACIÓN", (59, 130, 246))
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Aprobado por: {signature.get('name', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Cargo: {signature.get('position', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Fecha de firma: {signature.get('date', 'N/A')[:19].replace('T', ' ')}", ln=True)
        pdf.ln(5)
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 8, "  APROBADO  ", fill=True, align='C')
        pdf.set_text_color(30, 41, 59)
    
    # Output PDF
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    filename = f"investigacion-{investigation.get('code', 'RG-35')}-{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ================== PROCEDURES ==================

@api_router.get("/procedures")
async def get_procedures(current_user: dict = Depends(get_current_user)):
    procedures = await db.procedures.find({}, {"_id": 0}).to_list(1000)
    return procedures

@api_router.get("/procedures/{procedure_id}")
async def get_procedure(procedure_id: str, current_user: dict = Depends(get_current_user)):
    procedure = await db.procedures.find_one({"id": procedure_id}, {"_id": 0})
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return procedure

@api_router.post("/procedures")
async def create_procedure(
    code: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and create a new procedure with AI analysis"""
    content = await file.read()
    content_text = content.decode('utf-8', errors='ignore')
    
    procedure = Procedure(
        code=code,
        name=name,
        description=description,
        content=content_text,
        category=category,
        created_by=current_user["name"]
    )
    
    # AI Analysis of procedure
    if EMERGENT_LLM_KEY:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"procedure-{procedure.id}",
                system_message="""Eres un experto en seguridad industrial. Analiza el procedimiento y extrae:
1. Riesgos identificados
2. Controles requeridos
3. EPP necesario
4. Puntos críticos de seguridad

Responde en formato JSON:
{
    "risks_identified": ["riesgo1", "riesgo2"],
    "controls_required": ["control1", "control2"],
    "epp_required": ["epp1", "epp2"],
    "critical_points": ["punto1", "punto2"],
    "summary": "resumen breve del análisis"
}"""
            ).with_model("openai", "gpt-4o")
            
            response = await chat.send_message(UserMessage(
                text=f"Analiza este procedimiento de seguridad:\n\n{content_text[:10000]}"
            ))
            
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group())
                procedure.risks_identified = analysis.get("risks_identified", [])
                procedure.controls_required = analysis.get("controls_required", [])
                procedure.epp_required = analysis.get("epp_required", [])
                procedure.ai_analysis = analysis.get("summary", "")
        except Exception as e:
            logger.error(f"Procedure AI analysis error: {str(e)}")
    
    await db.procedures.insert_one(procedure.model_dump())
    return procedure

@api_router.put("/procedures/{procedure_id}")
async def update_procedure(procedure_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.procedures.update_one({"id": procedure_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return {"message": "Procedure updated"}

@api_router.delete("/procedures/{procedure_id}")
async def delete_procedure(procedure_id: str, current_user: dict = Depends(get_current_user)):
    await db.procedures.delete_one({"id": procedure_id})
    return {"message": "Procedure deleted"}

# ================== RISK MATRIX ==================

@api_router.get("/risk-matrix")
async def get_risk_matrices(current_user: dict = Depends(get_current_user)):
    matrices = await db.risk_matrices.find({}, {"_id": 0}).to_list(1000)
    return matrices

@api_router.get("/risk-matrix/{matrix_id}")
async def get_risk_matrix(matrix_id: str, current_user: dict = Depends(get_current_user)):
    matrix = await db.risk_matrices.find_one({"id": matrix_id}, {"_id": 0})
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return matrix

@api_router.post("/risk-matrix")
async def create_risk_matrix(
    name: str,
    area: str,
    process: str,
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    matrix = RiskMatrix(
        name=name,
        description=description,
        area=area,
        process=process,
        created_by=current_user["name"]
    )
    await db.risk_matrices.insert_one(matrix.model_dump())
    return matrix

@api_router.post("/risk-matrix/{matrix_id}/risks")
async def add_risk_to_matrix(matrix_id: str, risk: Risk, current_user: dict = Depends(get_current_user)):
    risk_dict = risk.model_dump()
    risk_dict["risk_level"] = risk.probability * risk.severity
    
    result = await db.risk_matrices.update_one(
        {"id": matrix_id},
        {
            "$push": {"risks": risk_dict},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"message": "Risk added", "risk": risk_dict}

@api_router.put("/risk-matrix/{matrix_id}/risks/{risk_id}")
async def update_risk_in_matrix(matrix_id: str, risk_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if "probability" in updates and "severity" in updates:
        updates["risk_level"] = updates["probability"] * updates["severity"]
    
    result = await db.risk_matrices.update_one(
        {"id": matrix_id, "risks.id": risk_id},
        {
            "$set": {f"risks.$.{k}": v for k, v in updates.items()},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix or risk not found")
    return {"message": "Risk updated"}

@api_router.delete("/risk-matrix/{matrix_id}/risks/{risk_id}")
async def delete_risk_from_matrix(matrix_id: str, risk_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.risk_matrices.update_one(
        {"id": matrix_id},
        {
            "$pull": {"risks": {"id": risk_id}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"message": "Risk deleted"}

@api_router.put("/risk-matrix/{matrix_id}/status")
async def update_matrix_status(matrix_id: str, status: str, current_user: dict = Depends(get_current_user)):
    result = await db.risk_matrices.update_one(
        {"id": matrix_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"message": "Status updated"}

# ================== SCAN 360 ==================

SAFETY_SYSTEM_PROMPT = """Eres un Auditor Experto en Prevención de Riesgos (HSE/SSOMA) con visión computacional avanzada. Tu misión es analizar imágenes de entornos industriales para detectar condiciones inseguras, actos subestándar y brechas de cumplimiento normativo (basado en estándares OSHA y normativas locales de seguridad industrial).

{procedure_context}

Analiza la imagen y detecta:
1. Vías de Evacuación y Tránsito: pasillos, escaleras, salidas de emergencia obstruidas
2. Equipos de Emergencia: extintores, duchas de emergencia, señalética
3. Riesgos Eléctricos: tableros abiertos, cables expuestos
4. Sustancias Peligrosas: contenedores sin rotulación, materiales incompatibles
5. EPP: verificar uso correcto de casco, lentes, chaleco, guantes, calzado
6. Trabajo en Altura: arnés, línea de vida si aplica
7. Orden y Aseo: materiales mal estibados, obstrucciones

Por cada riesgo detectado, genera un hallazgo con:
- categoria: (Seguridad Eléctrica, Orden y Aseo, EPP, Evacuación, Sustancias Peligrosas, Trabajo en Altura)
- descripcion: explicación breve del riesgo
- severidad: (bajo, medio, alto, critico)
- referencia_normativa: estándar de seguridad incumplido
- accion_correctiva: qué hacer para mitigar el riesgo
- confianza: porcentaje de confianza (0-100)

Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
{{
  "hallazgos": [
    {{
      "categoria": "string",
      "descripcion": "string",
      "severidad": "string",
      "referencia_normativa": "string",
      "accion_correctiva": "string",
      "confianza": number
    }}
  ],
  "resumen": "string con resumen general del análisis",
  "nivel_riesgo_general": "bajo|medio|alto|critico"
}}"""

@api_router.get("/scans")
async def get_scans(current_user: dict = Depends(get_current_user)):
    scans = await db.scans.find({}, {"_id": 0, "image_data": 0}).to_list(1000)
    return scans

@api_router.get("/scans/{scan_id}")
async def get_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    scan = await db.scans.find_one({"id": scan_id}, {"_id": 0})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    findings = await db.findings.find({"scan_id": scan_id}, {"_id": 0}).to_list(1000)
    return {"scan": scan, "findings": findings}

@api_router.delete("/scans/{scan_id}")
async def delete_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scan and its associated findings"""
    scan = await db.scans.find_one({"id": scan_id}, {"_id": 0})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete associated findings
    await db.findings.delete_many({"scan_id": scan_id})
    
    # Delete the scan
    await db.scans.delete_one({"id": scan_id})
    
    return {"message": "Scan eliminado correctamente", "deleted_findings": True}

@api_router.post("/scans/analyze")
async def analyze_scan(
    name: str = Form(...),
    location: str = Form(...),
    procedure_id: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        image_content = await image.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        scan_id = str(uuid.uuid4())
        scan_doc = {
            "id": scan_id,
            "name": name,
            "location": location,
            "scanned_by": current_user["name"],
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "image_data": image_base64,
            "findings_count": 0,
            "critical_count": 0,
            "status": "processing",
            "procedure_id": procedure_id
        }
        await db.scans.insert_one(scan_doc)
        
        # Get procedure context if provided
        procedure_context = ""
        if procedure_id:
            procedure = await db.procedures.find_one({"id": procedure_id}, {"_id": 0})
            if procedure:
                procedure_context = f"""
CONTEXTO DEL PROCEDIMIENTO:
Nombre: {procedure.get('name', '')}
Descripción: {procedure.get('description', '')}
Riesgos identificados en el procedimiento: {', '.join(procedure.get('risks_identified', []))}
Controles requeridos: {', '.join(procedure.get('controls_required', []))}
EPP requerido: {', '.join(procedure.get('epp_required', []))}

IMPORTANTE: Además de los riesgos generales, presta especial atención a verificar el cumplimiento de los controles y EPP del procedimiento.
"""
        
        if EMERGENT_LLM_KEY:
            try:
                system_prompt = SAFETY_SYSTEM_PROMPT.format(procedure_context=procedure_context)
                
                chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"scan-{scan_id}",
                    system_message=system_prompt
                ).with_model("openai", "gpt-4o")
                
                image_obj = ImageContent(image_base64=image_base64)
                user_message = UserMessage(
                    text="Analiza esta imagen de un entorno industrial y detecta todos los riesgos de seguridad presentes. Responde en formato JSON.",
                    file_contents=[image_obj]
                )
                
                response = await chat.send_message(user_message)
                
                import json
                import re
                
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    analysis = json.loads(json_match.group())
                    
                    findings = []
                    findings_for_db = []
                    critical_count = 0
                    
                    for hallazgo in analysis.get("hallazgos", []):
                        finding = SafetyFinding(
                            scan_id=scan_id,
                            category=hallazgo.get("categoria", "General"),
                            description=hallazgo.get("descripcion", ""),
                            severity=hallazgo.get("severidad", "medio"),
                            normative_reference=hallazgo.get("referencia_normativa", ""),
                            corrective_action=hallazgo.get("accion_correctiva", ""),
                            confidence=hallazgo.get("confianza", 85.0)
                        )
                        finding_dict = finding.model_dump()
                        findings.append(finding_dict.copy())  # Clean copy for response
                        findings_for_db.append(finding_dict)  # For MongoDB insert
                        if hallazgo.get("severidad") == "critico":
                            critical_count += 1
                    
                    if findings_for_db:
                        await db.findings.insert_many(findings_for_db)
                    
                    await db.scans.update_one(
                        {"id": scan_id},
                        {"$set": {
                            "status": "completed",
                            "findings_count": len(findings),
                            "critical_count": critical_count,
                            "summary": analysis.get("resumen", ""),
                            "risk_level": analysis.get("nivel_riesgo_general", "medio")
                        }}
                    )
                    
                    return {
                        "scan_id": scan_id,
                        "findings_count": len(findings),
                        "critical_count": critical_count,
                        "summary": analysis.get("resumen", ""),
                        "risk_level": analysis.get("nivel_riesgo_general", "medio"),
                        "findings": findings
                    }
            except Exception as e:
                logger.error(f"AI Analysis error: {str(e)}")
                await db.scans.update_one({"id": scan_id}, {"$set": {"status": "error", "error": str(e)}})
                raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        else:
            await db.scans.update_one({"id": scan_id}, {"$set": {"status": "completed", "findings_count": 0}})
            return {"scan_id": scan_id, "findings_count": 0, "message": "No AI key configured"}
            
    except Exception as e:
        logger.error(f"Scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/findings")
async def get_findings(current_user: dict = Depends(get_current_user)):
    findings = await db.findings.find({}, {"_id": 0}).to_list(1000)
    return findings

@api_router.put("/findings/{finding_id}/status")
async def update_finding_status(finding_id: str, status: str, current_user: dict = Depends(get_current_user)):
    result = await db.findings.update_one({"id": finding_id}, {"$set": {"status": status}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"message": "Finding updated"}

# ================== DASHBOARD ==================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    total_incidents = await db.incidents.count_documents({})
    open_incidents = await db.incidents.count_documents({"status": "open"})
    critical_findings = await db.findings.count_documents({"severity": {"$in": ["critico", "critical"]}})
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    scans_today = await db.scans.count_documents({
        "scanned_at": {"$gte": today.isoformat()}
    })
    
    pending_actions = await db.findings.count_documents({"status": "pending"})
    total_scans = await db.scans.count_documents({})
    
    # EPP costs summary
    epp_costs = await db.epp_movements.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_cost"}}}
    ]).to_list(1)
    total_epp_cost = epp_costs[0]["total"] if epp_costs else 0
    
    return {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "critical_findings": critical_findings,
        "scans_today": scans_today,
        "total_scans": total_scans,
        "pending_actions": pending_actions,
        "total_epp_cost": total_epp_cost
    }

@api_router.get("/dashboard/recent-activity")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    recent_incidents = await db.incidents.find({}, {"_id": 0}).sort("reported_at", -1).limit(5).to_list(5)
    recent_scans = await db.scans.find({}, {"_id": 0, "image_data": 0}).sort("scanned_at", -1).limit(5).to_list(5)
    recent_findings = await db.findings.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "incidents": recent_incidents,
        "scans": recent_scans,
        "findings": recent_findings
    }

@api_router.get("/dashboard/charts")
async def get_dashboard_charts(current_user: dict = Depends(get_current_user)):
    severity_data = await db.incidents.aggregate([
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    category_data = await db.findings.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    # EPP costs by cost center
    epp_by_center = await db.epp_movements.aggregate([
        {
            "$group": {
                "_id": {"$ifNull": ["$to_cost_center_id", "$from_cost_center_id"]},
                "total_cost": {"$sum": "$total_cost"}
            }
        }
    ]).to_list(100)
    
    return {
        "incidents_by_severity": [{"name": item["_id"] or "Sin clasificar", "value": item["count"]} for item in severity_data],
        "findings_by_category": [{"name": item["_id"] or "General", "value": item["count"]} for item in category_data],
        "epp_costs_by_center": [{"center": item["_id"] or "Sin asignar", "cost": item["total_cost"]} for item in epp_by_center]
    }

# ================== NOTIFICATIONS ==================

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    critical_findings = await db.findings.find(
        {"severity": {"$in": ["critico", "critical"]}, "status": "pending"},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    open_incidents = await db.incidents.find(
        {"status": "open", "severity": {"$in": ["critical", "high", "critico", "alto"]}},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    notifications = []
    for finding in critical_findings:
        notifications.append({
            "id": finding["id"],
            "type": "finding",
            "title": f"Hallazgo Crítico: {finding['category']}",
            "message": finding["description"][:100],
            "severity": "critical",
            "created_at": finding["created_at"]
        })
    
    for incident in open_incidents:
        notifications.append({
            "id": incident["id"],
            "type": "incident",
            "title": f"Incidente: {incident['title']}",
            "message": incident["description"][:100],
            "severity": incident["severity"],
            "created_at": incident["reported_at"]
        })
    
    return sorted(notifications, key=lambda x: x["created_at"], reverse=True)

# ================== PDF EXPORT ==================

class SafetyPDF(FPDF):
    """Custom PDF class for SmartSafety+ reports"""
    
    def __init__(self, title="Reporte de Seguridad", org_name="SmartSafety+"):
        super().__init__()
        self.title_text = title
        self.org_name = org_name
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Logo placeholder (blue rectangle)
        self.set_fill_color(59, 130, 246)  # Blue
        self.rect(10, 8, 25, 12, 'F')
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 11)
        self.cell(0, 0, 'SS+')
        
        # Title
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 16)
        self.set_xy(40, 10)
        self.cell(0, 10, self.title_text)
        
        # Organization name
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 116, 139)
        self.set_xy(40, 18)
        self.cell(0, 5, self.org_name)
        
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f'SmartSafety+ Enterprise 2026 | Pagina {self.page_no()}', align='C')
        
    def add_section_title(self, title, color=(59, 130, 246)):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*color)
        self.cell(0, 10, title, ln=True)
        self.set_text_color(30, 41, 59)
        
    def add_stat_box(self, label, value, x, y, width=45):
        self.set_xy(x, y)
        self.set_fill_color(248, 250, 252)
        self.rect(x, y, width, 20, 'F')
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 116, 139)
        self.set_xy(x + 3, y + 3)
        self.cell(0, 5, label)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 41, 59)
        self.set_xy(x + 3, y + 10)
        self.cell(0, 5, str(value))
        
    def add_table_header(self, headers, widths):
        self.set_fill_color(59, 130, 246)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 9)
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, border=1, fill=True, align='C')
        self.ln()
        self.set_text_color(30, 41, 59)
        
    def add_table_row(self, cells, widths, fill=False):
        if fill:
            self.set_fill_color(248, 250, 252)
        self.set_font('Helvetica', '', 8)
        for i, cell in enumerate(cells):
            text = str(cell)[:30] if len(str(cell)) > 30 else str(cell)
            self.cell(widths[i], 7, text, border=1, fill=fill, align='L')
        self.ln()
        
    def add_severity_badge(self, severity):
        colors = {
            'critico': (239, 68, 68),
            'critical': (239, 68, 68),
            'alto': (249, 115, 22),
            'high': (249, 115, 22),
            'medio': (245, 158, 11),
            'medium': (245, 158, 11),
            'bajo': (16, 185, 129),
            'low': (16, 185, 129)
        }
        color = colors.get(severity.lower(), (100, 116, 139))
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 7)
        self.cell(20, 5, severity.upper(), fill=True, align='C')
        self.set_text_color(30, 41, 59)


@api_router.get("/reports/export-pdf")
async def export_report_pdf(report_type: str = "incidents", current_user: dict = Depends(get_current_user)):
    """Generate professional PDF report"""
    
    pdf = SafetyPDF(
        title=f"Reporte de {report_type.replace('-', ' ').title()}",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Report info
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.cell(0, 6, f"Generado por: {current_user.get('name', 'Admin')}", ln=True)
    pdf.ln(10)
    
    if report_type == "incidents":
        incidents = await db.incidents.find({}, {"_id": 0}).to_list(100)
        
        # Stats boxes
        total = len(incidents)
        open_count = len([i for i in incidents if i.get('status') == 'open'])
        critical = len([i for i in incidents if i.get('severity') in ['critico', 'critical']])
        
        pdf.add_stat_box("Total Incidentes", total, 10, pdf.get_y())
        pdf.add_stat_box("Abiertos", open_count, 60, pdf.get_y())
        pdf.add_stat_box("Criticos", critical, 110, pdf.get_y())
        pdf.ln(30)
        
        # Table
        pdf.add_section_title("Listado de Incidentes")
        headers = ["Titulo", "Severidad", "Estado", "Fecha"]
        widths = [70, 30, 30, 40]
        pdf.add_table_header(headers, widths)
        
        for i, inc in enumerate(incidents[:30]):
            pdf.add_table_row([
                inc.get('title', 'Sin titulo')[:25],
                inc.get('severity', 'N/A'),
                inc.get('status', 'N/A'),
                inc.get('reported_at', '')[:10]
            ], widths, fill=(i % 2 == 0))
    
    elif report_type == "findings":
        findings = await db.findings.find({}, {"_id": 0}).to_list(100)
        
        total = len(findings)
        critical = len([f for f in findings if f.get('severity') in ['critico', 'critical']])
        pending = len([f for f in findings if f.get('status') == 'pending'])
        
        pdf.add_stat_box("Total Hallazgos", total, 10, pdf.get_y())
        pdf.add_stat_box("Criticos", critical, 60, pdf.get_y())
        pdf.add_stat_box("Pendientes", pending, 110, pdf.get_y())
        pdf.ln(30)
        
        pdf.add_section_title("Hallazgos de Seguridad")
        headers = ["Categoria", "Descripcion", "Severidad", "Estado"]
        widths = [35, 80, 25, 25]
        pdf.add_table_header(headers, widths)
        
        for i, f in enumerate(findings[:30]):
            pdf.add_table_row([
                f.get('category', 'General')[:15],
                f.get('description', 'N/A')[:35],
                f.get('severity', 'N/A'),
                f.get('status', 'N/A')
            ], widths, fill=(i % 2 == 0))
    
    elif report_type == "epp":
        movements = await db.epp_movements.find({}, {"_id": 0}).to_list(100)
        
        total = len(movements)
        total_cost = sum(m.get('total_cost', 0) for m in movements)
        total_qty = sum(m.get('quantity', 0) for m in movements)
        
        pdf.add_stat_box("Movimientos", total, 10, pdf.get_y())
        pdf.add_stat_box("Unidades", total_qty, 60, pdf.get_y())
        pdf.add_stat_box(f"Costo Total", f"${total_cost:,.0f}", 110, pdf.get_y())
        pdf.ln(30)
        
        pdf.add_section_title("Movimientos de EPP")
        headers = ["Tipo", "Cantidad", "Costo Unit.", "Total", "Fecha"]
        widths = [35, 25, 30, 35, 35]
        pdf.add_table_header(headers, widths)
        
        for i, m in enumerate(movements[:30]):
            pdf.add_table_row([
                m.get('movement_type', 'N/A'),
                str(m.get('quantity', 0)),
                f"${m.get('unit_cost', 0):,.0f}",
                f"${m.get('total_cost', 0):,.0f}",
                m.get('created_at', '')[:10]
            ], widths, fill=(i % 2 == 0))
    
    elif report_type == "risk-matrix":
        matrices = await db.risk_matrices.find({}, {"_id": 0}).to_list(100)
        
        total_matrices = len(matrices)
        total_risks = sum(len(m.get('risks', [])) for m in matrices)
        critical_risks = sum(
            len([r for r in m.get('risks', []) if r.get('risk_level') in ['Critico', 'Alto']])
            for m in matrices
        )
        
        pdf.add_stat_box("Matrices", total_matrices, 10, pdf.get_y())
        pdf.add_stat_box("Riesgos", total_risks, 60, pdf.get_y())
        pdf.add_stat_box("Criticos/Altos", critical_risks, 110, pdf.get_y())
        pdf.ln(30)
        
        for matrix in matrices[:5]:
            pdf.add_section_title(f"Matriz: {matrix.get('name', 'Sin nombre')}")
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 6, f"Area: {matrix.get('area', 'N/A')} | Proceso: {matrix.get('process', 'N/A')}", ln=True)
            pdf.ln(3)
            
            risks = matrix.get('risks', [])
            if risks:
                headers = ["Peligro", "Riesgo", "P", "S", "Nivel", "Estado"]
                widths = [40, 50, 15, 15, 25, 25]
                pdf.add_table_header(headers, widths)
                
                for i, r in enumerate(risks[:15]):
                    pdf.add_table_row([
                        r.get('hazard', 'N/A')[:18],
                        r.get('risk_description', 'N/A')[:22],
                        str(r.get('probability', '-')),
                        str(r.get('severity', '-')),
                        r.get('risk_level', 'N/A'),
                        r.get('status', 'N/A')
                    ], widths, fill=(i % 2 == 0))
            pdf.ln(10)
    
    # Output PDF
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    filename = f"reporte-{report_type}-{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ================== EMAIL NOTIFICATIONS ==================

class EmailNotificationRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    finding_id: Optional[str] = None
    incident_id: Optional[str] = None
    custom_message: Optional[str] = None


def generate_alert_html(finding: dict = None, incident: dict = None, custom_message: str = None) -> str:
    """Generate HTML email template for safety alerts"""
    
    severity_colors = {
        'critico': '#EF4444', 'critical': '#EF4444',
        'alto': '#F97316', 'high': '#F97316',
        'medio': '#F59E0B', 'medium': '#F59E0B',
        'bajo': '#10B981', 'low': '#10B981'
    }
    
    if finding:
        severity = finding.get('severity', 'medio')
        color = severity_colors.get(severity.lower(), '#64748B')
        content = f"""
        <div style="background-color: {color}; color: white; padding: 12px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 18px;">⚠️ Hallazgo de Seguridad - {severity.upper()}</h2>
        </div>
        <div style="padding: 20px; background: #f8fafc; border-radius: 0 0 8px 8px;">
            <p style="margin: 0 0 10px;"><strong>Categoria:</strong> {finding.get('category', 'General')}</p>
            <p style="margin: 0 0 10px;"><strong>Descripcion:</strong> {finding.get('description', 'Sin descripcion')}</p>
            <p style="margin: 0 0 10px;"><strong>Referencia Normativa:</strong> {finding.get('normative_reference', 'N/A')}</p>
            <p style="margin: 0;"><strong>Accion Correctiva:</strong> {finding.get('corrective_action', 'Pendiente')}</p>
        </div>
        """
    elif incident:
        severity = incident.get('severity', 'medio')
        color = severity_colors.get(severity.lower(), '#64748B')
        content = f"""
        <div style="background-color: {color}; color: white; padding: 12px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 18px;">🚨 Incidente Reportado - {severity.upper()}</h2>
        </div>
        <div style="padding: 20px; background: #f8fafc; border-radius: 0 0 8px 8px;">
            <p style="margin: 0 0 10px;"><strong>Titulo:</strong> {incident.get('title', 'Sin titulo')}</p>
            <p style="margin: 0 0 10px;"><strong>Descripcion:</strong> {incident.get('description', 'Sin descripcion')}</p>
            <p style="margin: 0 0 10px;"><strong>Ubicacion:</strong> {incident.get('location', 'N/A')}</p>
            <p style="margin: 0;"><strong>Estado:</strong> {incident.get('status', 'Abierto')}</p>
        </div>
        """
    else:
        content = f"""
        <div style="padding: 20px; background: #f8fafc; border-radius: 8px;">
            <p style="margin: 0;">{custom_message or 'Notificacion del sistema SmartSafety+'}</p>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; margin: 0; padding: 20px; background-color: #f1f5f9;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3B82F6 0%, #1d4ed8 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    <span style="color: white;">Smart</span><span style="color: #F97316;">Safety+</span>
                </h1>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0; font-size: 12px;">Sistema de Gestion de Seguridad</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 20px;">
                {content}
            </div>
            
            <!-- Footer -->
            <div style="background: #f8fafc; padding: 15px 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; font-size: 12px; color: #64748b;">
                    Este es un mensaje automatico de SmartSafety+ Enterprise 2026
                </p>
                <p style="margin: 5px 0 0; font-size: 11px; color: #94a3b8;">
                    No responda a este correo
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


@api_router.post("/notifications/send-alert")
async def send_notification_alert(request: EmailNotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send email notification for safety alerts"""
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    finding = None
    incident = None
    
    if request.finding_id:
        finding = await db.findings.find_one({"id": request.finding_id}, {"_id": 0})
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
    
    if request.incident_id:
        incident = await db.incidents.find_one({"id": request.incident_id}, {"_id": 0})
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    
    html_content = generate_alert_html(finding, incident, request.custom_message)
    
    params = {
        "from": SENDER_EMAIL,
        "to": [request.recipient_email],
        "subject": request.subject,
        "html": html_content
    }
    
    try:
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        # Log notification
        notification_log = {
            "id": str(uuid.uuid4()),
            "type": "email",
            "recipient": request.recipient_email,
            "subject": request.subject,
            "finding_id": request.finding_id,
            "incident_id": request.incident_id,
            "sent_by": current_user.get("id"),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "email_id": email_result.get("id") if email_result else None
        }
        await db.notification_logs.insert_one(notification_log)
        
        return {
            "status": "success",
            "message": f"Email enviado a {request.recipient_email}",
            "email_id": email_result.get("id") if email_result else None
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar email: {str(e)}")


@api_router.post("/notifications/send-critical-alert")
async def send_critical_finding_alert(finding_id: str, current_user: dict = Depends(get_current_user)):
    """Send automatic alert for critical findings to all admins"""
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    finding = await db.findings.find_one({"id": finding_id}, {"_id": 0})
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Get all admin users
    admins = await db.users.find({"role": {"$in": ["admin", "superadmin"]}}, {"_id": 0}).to_list(100)
    
    if not admins:
        return {"status": "warning", "message": "No hay administradores para notificar"}
    
    html_content = generate_alert_html(finding=finding)
    sent_count = 0
    
    for admin in admins:
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [admin["email"]],
                "subject": f"🚨 ALERTA CRITICA: {finding.get('category', 'Hallazgo de Seguridad')}",
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {admin['email']}: {str(e)}")
    
    return {
        "status": "success",
        "message": f"Alertas enviadas a {sent_count} administradores",
        "recipients": sent_count
    }


# ================== ORGANIZATION LOGOS ==================

@api_router.get("/organization/current")
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


@api_router.put("/organization/current")
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


@api_router.post("/organization/current/logo")
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


@api_router.delete("/organization/current/logo")
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


@api_router.post("/organizations/{org_id}/logo")
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


@api_router.get("/uploads/{filename}")
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


# ================== SMS NOTIFICATIONS (TWILIO) ==================

class SMSNotificationRequest(BaseModel):
    phone_number: str
    message: str
    finding_id: Optional[str] = None
    incident_id: Optional[str] = None


@api_router.post("/notifications/send-sms")
async def send_sms_notification(request: SMSNotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send SMS notification for safety alerts"""
    
    if not twilio_client:
        raise HTTPException(status_code=500, detail="SMS service not configured. Please add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to .env")
    
    if not TWILIO_PHONE_NUMBER:
        raise HTTPException(status_code=500, detail="Twilio phone number not configured")
    
    # Format phone number (ensure E.164 format)
    phone = request.phone_number
    if not phone.startswith('+'):
        phone = f"+{phone}"
    
    # Build message
    message_body = request.message
    
    if request.finding_id:
        finding = await db.findings.find_one({"id": request.finding_id}, {"_id": 0})
        if finding:
            message_body = f"🚨 ALERTA SmartSafety+\nHallazgo: {finding.get('category', 'N/A')}\nSeveridad: {finding.get('severity', 'N/A')}\n{finding.get('description', '')[:100]}"
    
    if request.incident_id:
        incident = await db.incidents.find_one({"id": request.incident_id}, {"_id": 0})
        if incident:
            message_body = f"🚨 INCIDENTE SmartSafety+\n{incident.get('title', 'N/A')}\nSeveridad: {incident.get('severity', 'N/A')}\nUbicacion: {incident.get('location', 'N/A')}"
    
    try:
        sms = await asyncio.to_thread(
            twilio_client.messages.create,
            body=message_body[:1600],  # Twilio limit
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        # Log SMS
        sms_log = {
            "id": str(uuid.uuid4()),
            "type": "sms",
            "recipient": phone,
            "message": message_body[:200],
            "finding_id": request.finding_id,
            "incident_id": request.incident_id,
            "sent_by": current_user.get("id"),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "sms_sid": sms.sid
        }
        await db.notification_logs.insert_one(sms_log)
        
        return {
            "status": "success",
            "message": f"SMS enviado a {phone}",
            "sms_sid": sms.sid
        }
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar SMS: {str(e)}")


@api_router.get("/notifications/config-status")
async def get_notification_config_status(current_user: dict = Depends(get_current_user)):
    """Check which notification services are configured"""
    return {
        "email": {
            "configured": bool(RESEND_API_KEY),
            "provider": "Resend"
        },
        "sms": {
            "configured": bool(twilio_client),
            "provider": "Twilio"
        }
    }


# ================== SMART+ ECOSYSTEM INTEGRATION ==================

class EcosystemApp(BaseModel):
    """Represents an app in the Smart+ ecosystem"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # SmartPlan+, SmartForms+, SmartSafety+
    code: str  # smartplan, smartforms, smartsafety
    url: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[str] = None


class IntegrationTask(BaseModel):
    """Task created from SmartSafety+ finding for SmartPlan+"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_app: str = "smartsafety"
    target_app: str = "smartplan"
    source_id: str  # finding_id or incident_id
    source_type: str  # "finding" or "incident"
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = "pending"  # pending, synced, completed, failed
    external_task_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    synced_at: Optional[str] = None


class DynamicFormTemplate(BaseModel):
    """Form template from SmartForms+ for inspections"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    form_type: str = "inspection"  # inspection, checklist, audit, survey
    fields: List[Dict[str, Any]] = []
    organization_id: Optional[str] = None
    is_active: bool = True
    source_app: str = "smartforms"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None


class FormSubmission(BaseModel):
    """Submitted form data"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    form_template_id: str
    submitted_by: str
    location: Optional[str] = None
    data: Dict[str, Any] = {}
    scan_id: Optional[str] = None
    status: str = "submitted"  # submitted, reviewed, approved, rejected
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Ecosystem Apps Configuration
@api_router.get("/ecosystem/apps")
async def get_ecosystem_apps(current_user: dict = Depends(get_current_user)):
    """Get available apps in the Smart+ ecosystem"""
    apps = await db.ecosystem_apps.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    if not apps:
        # Return default ecosystem apps
        default_apps = [
            {
                "id": "smartsafety",
                "name": "SmartSafety+",
                "code": "smartsafety",
                "url": "",  # Current app
                "description": "Gestión de seguridad operativa y prevención de riesgos",
                "icon": "shield",
                "is_active": True,
                "is_current": True
            },
            {
                "id": "smartplan",
                "name": "SmartPlan+",
                "code": "smartplan",
                "url": "",  # To be configured
                "description": "Planificación y gestión de tareas y proyectos",
                "icon": "calendar",
                "is_active": False,
                "is_current": False
            },
            {
                "id": "smartforms",
                "name": "SmartForms+",
                "code": "smartforms",
                "url": "",  # To be configured
                "description": "Creación de formularios dinámicos e inspecciones",
                "icon": "clipboard",
                "is_active": False,
                "is_current": False
            }
        ]
        return default_apps
    
    # Mark current app
    for app in apps:
        app["is_current"] = app.get("code") == "smartsafety"
    
    return apps


@api_router.post("/ecosystem/apps")
async def configure_ecosystem_app(app: EcosystemApp, current_user: dict = Depends(get_current_user)):
    """Configure an ecosystem app connection"""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    app_dict = app.model_dump()
    
    # Update or insert
    await db.ecosystem_apps.update_one(
        {"code": app.code},
        {"$set": app_dict},
        upsert=True
    )
    
    return {"message": f"App {app.name} configurada correctamente", "app": app_dict}


# Integration with SmartPlan+ - Create tasks from findings
@api_router.post("/ecosystem/smartplan/create-task")
async def create_task_from_finding(
    finding_id: str = None,
    incident_id: str = None,
    assigned_to: str = None,
    due_date: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a task in SmartPlan+ from a finding or incident"""
    
    if not finding_id and not incident_id:
        raise HTTPException(status_code=400, detail="Debe proporcionar finding_id o incident_id")
    
    source_type = "finding" if finding_id else "incident"
    source_id = finding_id or incident_id
    
    # Get source data
    if finding_id:
        source = await db.findings.find_one({"id": finding_id}, {"_id": 0})
        if not source:
            raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
        title = f"Corregir: {source.get('category', 'Hallazgo de seguridad')}"
        description = f"{source.get('description', '')}\n\nAcción correctiva: {source.get('corrective_action', 'Pendiente de definir')}\n\nReferencia: {source.get('normative_reference', 'N/A')}"
        priority = "critical" if source.get("severity") == "critico" else "high" if source.get("severity") == "alto" else "medium"
    else:
        source = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
        if not source:
            raise HTTPException(status_code=404, detail="Incidente no encontrado")
        title = f"Investigar: {source.get('title', 'Incidente')}"
        description = source.get("description", "")
        priority = "critical" if source.get("severity") == "critico" else "high" if source.get("severity") == "alto" else "medium"
    
    # Create integration task
    task = IntegrationTask(
        source_id=source_id,
        source_type=source_type,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        assigned_to=assigned_to,
        status="pending"
    )
    
    task_dict = task.model_dump()
    await db.integration_tasks.insert_one(task_dict)
    
    # Remove _id for response
    task_dict.pop("_id", None)
    
    return {
        "message": "Tarea creada para sincronización con SmartPlan+",
        "task": task_dict
    }


@api_router.get("/ecosystem/smartplan/tasks")
async def get_integration_tasks(status: str = None, current_user: dict = Depends(get_current_user)):
    """Get tasks pending sync with SmartPlan+"""
    query = {"target_app": "smartplan"}
    if status:
        query["status"] = status
    
    tasks = await db.integration_tasks.find(query, {"_id": 0}).to_list(1000)
    return tasks


@api_router.put("/ecosystem/smartplan/tasks/{task_id}/sync")
async def mark_task_synced(task_id: str, external_task_id: str = None, current_user: dict = Depends(get_current_user)):
    """Mark a task as synced with SmartPlan+"""
    result = await db.integration_tasks.update_one(
        {"id": task_id},
        {"$set": {
            "status": "synced",
            "external_task_id": external_task_id,
            "synced_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Tarea marcada como sincronizada"}


# Integration with SmartForms+ - Dynamic forms
@api_router.get("/ecosystem/smartforms/templates")
async def get_form_templates(form_type: str = None, current_user: dict = Depends(get_current_user)):
    """Get available form templates from SmartForms+"""
    query = {"is_active": True}
    if form_type:
        query["form_type"] = form_type
    
    templates = await db.form_templates.find(query, {"_id": 0}).to_list(100)
    
    if not templates:
        # Return default inspection templates
        default_templates = [
            {
                "id": "default-inspection",
                "name": "Inspección General de Seguridad",
                "description": "Formulario estándar para inspecciones de seguridad",
                "form_type": "inspection",
                "source_app": "smartsafety",
                "is_active": True,
                "fields": [
                    {"id": "area", "type": "text", "label": "Área Inspeccionada", "required": True},
                    {"id": "inspector", "type": "text", "label": "Inspector", "required": True},
                    {"id": "date", "type": "date", "label": "Fecha de Inspección", "required": True},
                    {"id": "epp_completo", "type": "checkbox", "label": "EPP Completo", "required": False},
                    {"id": "orden_limpieza", "type": "select", "label": "Orden y Limpieza", "options": ["Bueno", "Regular", "Deficiente"], "required": True},
                    {"id": "senalizacion", "type": "select", "label": "Señalización", "options": ["Adecuada", "Incompleta", "Faltante"], "required": True},
                    {"id": "extintores", "type": "checkbox", "label": "Extintores Vigentes", "required": False},
                    {"id": "rutas_evacuacion", "type": "checkbox", "label": "Rutas de Evacuación Despejadas", "required": False},
                    {"id": "observaciones", "type": "textarea", "label": "Observaciones", "required": False},
                    {"id": "fotos", "type": "file", "label": "Fotografías", "accept": "image/*", "multiple": True, "required": False}
                ]
            },
            {
                "id": "checklist-epp",
                "name": "Checklist de EPP",
                "description": "Verificación de equipos de protección personal",
                "form_type": "checklist",
                "source_app": "smartsafety",
                "is_active": True,
                "fields": [
                    {"id": "trabajador", "type": "text", "label": "Nombre del Trabajador", "required": True},
                    {"id": "cargo", "type": "text", "label": "Cargo", "required": True},
                    {"id": "casco", "type": "select", "label": "Casco de Seguridad", "options": ["Correcto", "Dañado", "No usa"], "required": True},
                    {"id": "lentes", "type": "select", "label": "Lentes de Seguridad", "options": ["Correcto", "Dañado", "No usa"], "required": True},
                    {"id": "guantes", "type": "select", "label": "Guantes", "options": ["Correcto", "Dañado", "No usa"], "required": True},
                    {"id": "calzado", "type": "select", "label": "Calzado de Seguridad", "options": ["Correcto", "Dañado", "No usa"], "required": True},
                    {"id": "chaleco", "type": "select", "label": "Chaleco Reflectante", "options": ["Correcto", "Dañado", "No usa"], "required": True},
                    {"id": "observaciones", "type": "textarea", "label": "Observaciones", "required": False}
                ]
            },
            {
                "id": "audit-5s",
                "name": "Auditoría 5S",
                "description": "Evaluación de metodología 5S",
                "form_type": "audit",
                "source_app": "smartsafety",
                "is_active": True,
                "fields": [
                    {"id": "area", "type": "text", "label": "Área Auditada", "required": True},
                    {"id": "seiri", "type": "range", "label": "Seiri (Clasificar)", "min": 1, "max": 5, "required": True},
                    {"id": "seiton", "type": "range", "label": "Seiton (Ordenar)", "min": 1, "max": 5, "required": True},
                    {"id": "seiso", "type": "range", "label": "Seiso (Limpiar)", "min": 1, "max": 5, "required": True},
                    {"id": "seiketsu", "type": "range", "label": "Seiketsu (Estandarizar)", "min": 1, "max": 5, "required": True},
                    {"id": "shitsuke", "type": "range", "label": "Shitsuke (Disciplina)", "min": 1, "max": 5, "required": True},
                    {"id": "acciones", "type": "textarea", "label": "Acciones de Mejora", "required": False}
                ]
            }
        ]
        return default_templates
    
    return templates


@api_router.post("/ecosystem/smartforms/templates")
async def create_form_template(template: DynamicFormTemplate, current_user: dict = Depends(get_current_user)):
    """Create or import a form template"""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    template_dict = template.model_dump()
    await db.form_templates.insert_one(template_dict)
    template_dict.pop("_id", None)
    
    return {"message": "Plantilla creada correctamente", "template": template_dict}


@api_router.post("/ecosystem/smartforms/submit")
async def submit_form(
    template_id: str,
    data: Dict[str, Any],
    location: str = None,
    scan_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Submit a form response"""
    
    # Verify template exists
    template = await db.form_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        # Check default templates
        templates = await get_form_templates(current_user=current_user)
        template = next((t for t in templates if t["id"] == template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    submission = FormSubmission(
        form_template_id=template_id,
        submitted_by=current_user.get("id"),
        location=location,
        data=data,
        scan_id=scan_id
    )
    
    submission_dict = submission.model_dump()
    await db.form_submissions.insert_one(submission_dict)
    submission_dict.pop("_id", None)
    
    return {"message": "Formulario enviado correctamente", "submission": submission_dict}


@api_router.get("/ecosystem/smartforms/submissions")
async def get_form_submissions(template_id: str = None, current_user: dict = Depends(get_current_user)):
    """Get form submissions"""
    query = {}
    if template_id:
        query["form_template_id"] = template_id
    
    submissions = await db.form_submissions.find(query, {"_id": 0}).to_list(1000)
    return submissions


# Shared data - Collaborators/Workers
@api_router.get("/ecosystem/shared/collaborators")
async def get_shared_collaborators(current_user: dict = Depends(get_current_user)):
    """Get collaborators shared across ecosystem"""
    # Get users with their profiles
    users = await db.users.find(
        {"role": {"$ne": "superadmin"}},
        {"_id": 0, "password": 0}
    ).to_list(1000)
    
    # Get profiles
    profiles = await db.profiles.find({}, {"_id": 0}).to_list(1000)
    profiles_map = {p.get("user_id"): p for p in profiles}
    
    collaborators = []
    for user in users:
        profile = profiles_map.get(user.get("id"), {})
        collaborators.append({
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "position": profile.get("position"),
            "department": profile.get("department"),
            "cost_center": profile.get("cost_center"),
            "is_active": user.get("is_active", True)
        })
    
    return collaborators


# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
