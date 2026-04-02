"""SmartSafety+ - Incidents & Investigations Router"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from config import db, logger
from models.schemas import Incident, IncidentCreate, IncidentInvestigation
from utils.auth import get_current_user
from utils.pagination import paginated_find
from utils.websocket import ws_manager
from utils.pdf import SafetyPDF
from datetime import datetime, timezone
import uuid
import io

router = APIRouter(tags=["incidents"])
investigations_router = APIRouter(tags=["investigations"])

@router.get("/incidents")
async def get_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if severity:
        query["severity"] = severity
    return await paginated_find(
        db.incidents,
        query=query,
        sort_field="reported_at",
        page=page,
        page_size=page_size,
    )

@router.post("/incidents")
async def create_incident(incident: IncidentCreate, current_user: dict = Depends(get_current_user)):
    incident_doc = Incident(
        **incident.model_dump(),
        reported_by=current_user["name"]
    )
    await db.incidents.insert_one(incident_doc.model_dump())

    # Broadcast via WebSocket
    await ws_manager.broadcast({
        "event": "new_incident",
        "data": {
            "id": incident_doc.id,
            "title": incident_doc.title,
            "severity": incident_doc.severity,
            "location": incident_doc.location,
            "reported_by": incident_doc.reported_by,
        }
    })

    return incident_doc

@router.put("/incidents/{incident_id}/status")
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

@router.get("/incidents/stats")
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


@investigations_router.get("/investigations")
async def get_investigations(
    status: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get all incident investigations with pagination"""
    query = {}
    if status:
        query["status"] = status
    return await paginated_find(
        db.investigations,
        query=query,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )


@investigations_router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific investigation with full details"""
    investigation = await db.investigations.find_one({"id": investigation_id}, {"_id": 0})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Get related incident
    incident = await db.incidents.find_one({"id": investigation.get("incident_id")}, {"_id": 0})
    
    return {"investigation": investigation, "incident": incident}


@investigations_router.post("/investigations")
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


@investigations_router.put("/investigations/{investigation_id}")
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


@investigations_router.post("/investigations/{investigation_id}/corrective-action")
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


@investigations_router.put("/investigations/{investigation_id}/status")
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


@investigations_router.get("/investigations/{investigation_id}/export-pdf")
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

