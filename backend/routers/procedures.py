"""SmartSafety+ - Procedures Router"""
# Paginated
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from config import db, EMERGENT_LLM_KEY, logger
from models.schemas import Procedure
from utils.auth import get_current_user
from utils.pagination import paginated_find
from fastapi import Query as Q
from openai import AsyncOpenAI
from datetime import datetime, timezone
import uuid
import json
import re

router = APIRouter(tags=["procedures"])

@router.get("/procedures")
async def get_procedures(
    page: int = Q(1, ge=1),
    page_size: int = Q(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    return await paginated_find(db.procedures, sort_field="created_at", page=page, page_size=page_size)

@router.get("/procedures/{procedure_id}")
async def get_procedure(procedure_id: str, current_user: dict = Depends(get_current_user)):
    procedure = await db.procedures.find_one({"id": procedure_id}, {"_id": 0})
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return procedure

@router.post("/procedures")
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
            client = AsyncOpenAI(api_key=EMERGENT_LLM_KEY)
            
            system_prompt = """Eres un experto en seguridad industrial. Analiza el procedimiento y extrae:
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
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analiza este procedimiento de seguridad:\n\n{content_text[:10000]}"}
                ],
                max_tokens=2000
            )
            
            import json
            import re
            response_text = response.choices[0].message.content
            json_match = re.search(r'\{[\s\S]*\}', response_text)
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

@router.put("/procedures/{procedure_id}")
async def update_procedure(procedure_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.procedures.update_one({"id": procedure_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return {"message": "Procedure updated"}

@router.delete("/procedures/{procedure_id}")
async def delete_procedure(procedure_id: str, current_user: dict = Depends(get_current_user)):
    await db.procedures.delete_one({"id": procedure_id})
    return {"message": "Procedure deleted"}

