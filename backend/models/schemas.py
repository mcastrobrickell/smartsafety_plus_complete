"""
SmartSafety+ - Pydantic Models
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "inspector"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: str
    name: str
    role: str = "inspector"
    organization_id: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Incident(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: str
    location: str
    category: str
    reported_by: str
    status: str = "pending"
    photos: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RiskCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    color: str = "#ff0000"
    icon: str = "alert-triangle"
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Scan360(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    image_url: str
    status: str = "pending"
    findings: List[Dict[str, Any]] = []
    ai_analysis: Optional[str] = None
    risk_level: Optional[str] = None
    recommendations: List[str] = []
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    analyzed_at: Optional[str] = None


class Procedure(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str
    version: str = "1.0"
    status: str = "draft"
    ai_analysis: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RiskMatrix(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    risks: List[Dict[str, Any]] = []
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConfigCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CostCenter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EPPItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    type_id: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    unit: str = "unidad"
    unit_cost: float = 0
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
    min_stock: int = 10
    max_stock: int = 100
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
    delivery_type: str = "entrega"
    responsible_name: str
    responsible_rut: Optional[str] = None
    responsible_position: Optional[str] = None
    worker_name: str
    worker_rut: Optional[str] = None
    worker_position: Optional[str] = None
    cost_center_id: Optional[str] = None
    cost_center_name: Optional[str] = None
    items: List[Dict[str, Any]] = []
    observations: Optional[str] = None
    signature_confirmed: bool = False
    signature_date: Optional[str] = None
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IncidentInvestigation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    investigation_status: str = "draft"
    incident_date: Optional[str] = None
    incident_time: Optional[str] = None
    incident_location: Optional[str] = None
    incident_description: Optional[str] = None
    worker_name: Optional[str] = None
    worker_rut: Optional[str] = None
    worker_position: Optional[str] = None
    worker_age: Optional[int] = None
    worker_seniority: Optional[str] = None
    worker_contract_type: Optional[str] = None
    worker_shift: Optional[str] = None
    worker_experience_months: Optional[int] = None
    injury_type: Optional[str] = None
    injury_location: Optional[str] = None
    injury_severity: Optional[str] = None
    days_lost: Optional[int] = None
    task_performed: Optional[str] = None
    witnesses: List[str] = []
    witness_statements: List[Dict[str, str]] = []
    immediate_causes: List[str] = []
    basic_causes: List[str] = []
    root_causes: List[str] = []
    human_factors: List[str] = []
    organizational_causes: List[str] = []
    corrective_actions: List[Dict[str, Any]] = []
    preventive_actions: List[Dict[str, Any]] = []
    photos: List[str] = []
    documents: List[str] = []
    conclusions: Optional[str] = None
    investigator_name: Optional[str] = None
    investigator_position: Optional[str] = None
    investigation_date: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    supervisor_signature: Optional[str] = None
    hse_signature: Optional[str] = None
    management_signature: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
