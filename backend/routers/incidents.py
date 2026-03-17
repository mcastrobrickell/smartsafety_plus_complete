"""
SmartSafety+ - Incidents and Investigations Router
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone
import io

from config import db
from models.schemas import Incident, IncidentInvestigation
from utils.auth import get_current_user
from utils.pdf import SafetyPDF

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("")
async def get_incidents(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    incidents = await db.incidents.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return incidents


@router.post("")
async def create_incident(incident: Incident, current_user: dict = Depends(get_current_user)):
    incident.reported_by = current_user["name"]
    await db.incidents.insert_one(incident.model_dump())
    return incident


@router.get("/{incident_id}")
async def get_incident(incident_id: str, current_user: dict = Depends(get_current_user)):
    incident = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/{incident_id}")
async def update_incident(
    incident_id: str,
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.incidents.update_one(
        {"id": incident_id},
        {"$set": updates}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return await db.incidents.find_one({"id": incident_id}, {"_id": 0})


@router.delete("/{incident_id}")
async def delete_incident(incident_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.incidents.delete_one({"id": incident_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "deleted"}


# ================== INVESTIGATIONS ==================

investigations_router = APIRouter(prefix="/investigations", tags=["Investigations"])


@investigations_router.get("")
async def get_investigations(current_user: dict = Depends(get_current_user)):
    investigations = await db.investigations.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return investigations


@investigations_router.get("/{investigation_id}")
async def get_investigation(investigation_id: str, current_user: dict = Depends(get_current_user)):
    investigation = await db.investigations.find_one({"id": investigation_id}, {"_id": 0})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@investigations_router.get("/incident/{incident_id}")
async def get_investigation_by_incident(incident_id: str, current_user: dict = Depends(get_current_user)):
    investigation = await db.investigations.find_one({"incident_id": incident_id}, {"_id": 0})
    return investigation


@investigations_router.post("")
async def create_investigation(
    investigation: IncidentInvestigation,
    current_user: dict = Depends(get_current_user)
):
    existing = await db.investigations.find_one({"incident_id": investigation.incident_id})
    if existing:
        raise HTTPException(status_code=400, detail="Investigation already exists for this incident")
    
    investigation.investigator_name = current_user["name"]
    await db.investigations.insert_one(investigation.model_dump())
    
    # Update incident status
    await db.incidents.update_one(
        {"id": investigation.incident_id},
        {"$set": {"status": "investigating", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return investigation


@investigations_router.put("/{investigation_id}")
async def update_investigation(
    investigation_id: str,
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.investigations.update_one(
        {"id": investigation_id},
        {"$set": updates}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return await db.investigations.find_one({"id": investigation_id}, {"_id": 0})


@investigations_router.get("/{investigation_id}/pdf")
async def export_investigation_pdf(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export investigation as PDF report (ISO 45001 format)"""
    investigation = await db.investigations.find_one({"id": investigation_id}, {"_id": 0})
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    pdf = SafetyPDF(
        title="Informe de Investigacion de Incidente - ISO 45001",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Basic info
    pdf.section_title("1. Datos del Incidente")
    pdf.add_field("Fecha", investigation.get('incident_date'))
    pdf.add_field("Hora", investigation.get('incident_time'))
    pdf.add_field("Ubicacion", investigation.get('incident_location'))
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 5, "Descripcion:", ln=True)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, investigation.get('incident_description', 'N/A')[:500])
    pdf.ln(5)
    
    # Worker info
    pdf.section_title("2. Datos del Trabajador")
    pdf.add_field("Nombre", investigation.get('worker_name'))
    pdf.add_field("RUT", investigation.get('worker_rut'))
    pdf.add_field("Cargo", investigation.get('worker_position'))
    pdf.add_field("Antiguedad", investigation.get('worker_seniority'))
    pdf.ln(5)
    
    # Injury info
    pdf.section_title("3. Lesion")
    pdf.add_field("Tipo", investigation.get('injury_type'))
    pdf.add_field("Ubicacion", investigation.get('injury_location'))
    pdf.add_field("Severidad", investigation.get('injury_severity'))
    pdf.add_field("Dias perdidos", investigation.get('days_lost'))
    pdf.ln(5)
    
    # Causes
    pdf.section_title("4. Analisis de Causas")
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 5, "Causas Inmediatas:", ln=True)
    pdf.set_font('Helvetica', '', 9)
    for cause in investigation.get('immediate_causes', []):
        pdf.cell(0, 5, f"  - {cause}", ln=True)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 5, "Causas Basicas:", ln=True)
    pdf.set_font('Helvetica', '', 9)
    for cause in investigation.get('basic_causes', []):
        pdf.cell(0, 5, f"  - {cause}", ln=True)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 5, "Causas Raiz:", ln=True)
    pdf.set_font('Helvetica', '', 9)
    for cause in investigation.get('root_causes', []):
        pdf.cell(0, 5, f"  - {cause}", ln=True)
    pdf.ln(5)
    
    # Corrective actions
    pdf.section_title("5. Acciones Correctivas")
    for action in investigation.get('corrective_actions', []):
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, f"- {action.get('description', 'N/A')}", ln=True)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(0, 4, f"  Responsable: {action.get('responsible', 'N/A')} | Fecha limite: {action.get('due_date', 'N/A')}", ln=True)
    
    # Output PDF
    pdf_output = io.BytesIO()
    pdf_content = pdf.output()
    pdf_output.write(pdf_content)
    pdf_output.seek(0)
    
    return StreamingResponse(
        pdf_output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=investigacion-{investigation_id[:8]}.pdf"}
    )
