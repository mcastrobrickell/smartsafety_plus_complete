"""
SmartSafety+ - All Pydantic models/schemas
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

# ================== AUTH MODELS ==================

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
    epp_item_name: Optional[str] = None
    epp_item_code: Optional[str] = None
    movement_type: str
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
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    delivery_number: Optional[str] = None
    date: str
    time: Optional[str] = None
    group: Optional[str] = None
    user: Optional[str] = None
    status: str = "entregado"
    responsible_name: str
    responsible_rut: Optional[str] = None
    responsible_position: Optional[str] = None
    worker_name: str
    worker_rut: Optional[str] = None
    worker_position: Optional[str] = None
    cost_center_id: Optional[str] = None
    cost_center_name: Optional[str] = None
    delivery_type: str = "entrega"
    epp_item_id: str
    epp_item_code: Optional[str] = None
    epp_item_name: str
    unit: str = "unidad"
    quantity: int
    unit_cost: float = 0.0
    total_cost: float = 0.0
    details: Optional[str] = None
    signature_data: Optional[str] = None
    signature_confirmed: bool = False
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EPPStockAdjustment(BaseModel):
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

class Risk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hazard: str
    risk_description: str
    consequences: str
    probability: int
    severity: int
    risk_level: int
    existing_controls: str
    additional_controls: str
    responsible: str
    deadline: Optional[str] = None
    status: str = "open"

# ================== INCIDENT INVESTIGATION ISO 45001 ==================

class AffectedWorker(BaseModel):
    name: str
    rut: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    position: str
    department: Optional[str] = None
    seniority_position: Optional[str] = None
    seniority_company: Optional[str] = None
    previous_incidents: Optional[str] = None
    worker_type: Optional[str] = None

class IncidentInvestigation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(default_factory=lambda: f"RG-35-{datetime.now().strftime('%Y%m%d%H%M')}")
    version: str = "08"
    incident_id: str
    status: str = "draft"
    incident_description: str
    incident_date: str
    incident_time: Optional[str] = None
    incident_types: List[str] = []
    shift_day: Optional[str] = None
    consequences: Optional[str] = None
    body_part_injured: Optional[str] = None
    incident_location: str
    work_site: Optional[str] = None
    witnesses: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_position: Optional[str] = None
    affected_worker: Optional[Dict[str, Any]] = None
    occurrence_number: int = 1
    previous_incident_date: Optional[str] = None
    previous_actions_taken: Optional[str] = None
    previous_incident_status: Optional[str] = None
    work_schedule: Optional[str] = None
    interviewed_workers: Optional[str] = None
    declarations_obtained: bool = False
    interview_observations: Optional[str] = None
    task_observation: Optional[Dict[str, Any]] = None
    document_review: Optional[Dict[str, Any]] = None
    photos: List[Dict[str, Any]] = []
    narrative: Optional[str] = None
    facts_list: Optional[str] = None
    layer_analysis: Optional[Dict[str, Any]] = None
    cause_tree: Optional[Dict[str, Any]] = None
    root_causes: List[str] = []
    immediate_causes: List[str] = []
    basic_causes: List[str] = []
    organizational_causes: List[str] = []
    corrective_actions: List[Dict[str, Any]] = []
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

class CorrectiveAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    action_type: str
    responsible: str
    due_date: str
    priority: str = "medium"
    status: str = "pending"
    verification_date: Optional[str] = None
    verified_by: Optional[str] = None
    evidence: Optional[str] = None
    iso_clause: Optional[str] = None

# ================== CONFIGURATION MODELS ==================

class ConfigCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ================== NOTIFICATION MODELS ==================

class EmailNotificationRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    finding_id: Optional[str] = None
    incident_id: Optional[str] = None
    custom_message: Optional[str] = None

class SMSNotificationRequest(BaseModel):
    phone_number: str
    message: str
    finding_id: Optional[str] = None
    incident_id: Optional[str] = None

# ================== ECOSYSTEM MODELS ==================

class EcosystemApp(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    description: Optional[str] = None
    url: Optional[str] = None
    icon: str = "shield"
    is_active: bool = True
    is_current: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class IntegrationTask(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_app: str
    target_app: str
    task_type: str
    finding_id: Optional[str] = None
    incident_id: Optional[str] = None
    title: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    external_task_id: Optional[str] = None
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    synced_at: Optional[str] = None

class DynamicFormTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    description: Optional[str] = None
    form_type: str
    fields: List[Dict[str, Any]] = []
    is_active: bool = True
    version: str = "1.0"
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FormSubmission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    template_name: str
    data: Dict[str, Any] = {}
    submitted_by: str
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "submitted"
    location: Optional[str] = None
    photos: List[str] = []
