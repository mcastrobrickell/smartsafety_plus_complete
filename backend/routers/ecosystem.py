"""SmartSafety+ - Smart+ Ecosystem Integration Router"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from config import db, logger
from models.schemas import EcosystemApp, IntegrationTask, DynamicFormTemplate, FormSubmission
from utils.auth import get_current_user
from utils.pagination import paginated_find
from datetime import datetime, timezone
import uuid

router = APIRouter(tags=["ecosystem"])

@router.get("/ecosystem/apps")
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


@router.post("/ecosystem/apps")
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
@router.post("/ecosystem/smartplan/create-task")
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


@router.get("/ecosystem/smartplan/tasks")
async def get_integration_tasks(status: str = None, current_user: dict = Depends(get_current_user)):
    """Get tasks pending sync with SmartPlan+"""
    query = {"target_app": "smartplan"}
    if status:
        query["status"] = status
    
    tasks = await db.integration_tasks.find(query, {"_id": 0}).to_list(1000)
    return tasks


@router.put("/ecosystem/smartplan/tasks/{task_id}/sync")
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
@router.get("/ecosystem/smartforms/templates")
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


@router.post("/ecosystem/smartforms/templates")
async def create_form_template(template: DynamicFormTemplate, current_user: dict = Depends(get_current_user)):
    """Create or import a form template"""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    template_dict = template.model_dump()
    await db.form_templates.insert_one(template_dict)
    template_dict.pop("_id", None)
    
    return {"message": "Plantilla creada correctamente", "template": template_dict}


@router.post("/ecosystem/smartforms/submit")
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


@router.get("/ecosystem/smartforms/submissions")
async def get_form_submissions(template_id: str = None, current_user: dict = Depends(get_current_user)):
    """Get form submissions"""
    query = {}
    if template_id:
        query["form_template_id"] = template_id
    
    submissions = await db.form_submissions.find(query, {"_id": 0}).to_list(1000)
    return submissions


# Shared data - Collaborators/Workers
@router.get("/ecosystem/shared/collaborators")
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

