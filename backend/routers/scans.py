"""
SmartSafety+ - Scans 360 Router
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

from config import db, EMERGENT_LLM_KEY
from models.schemas import Scan360
from utils.auth import get_current_user

router = APIRouter(prefix="/scans", tags=["Scans 360"])


@router.get("")
async def get_scans(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    scans = await db.scans.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return scans


@router.post("")
async def create_scan(scan: Scan360, current_user: dict = Depends(get_current_user)):
    scan.created_by = current_user["name"]
    await db.scans.insert_one(scan.model_dump())
    return scan


@router.get("/{scan_id}")
async def get_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    scan = await db.scans.find_one({"id": scan_id}, {"_id": 0})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.scans.delete_one({"id": scan_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"status": "deleted"}


@router.post("/{scan_id}/analyze")
async def analyze_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    """Analyze scan image with AI"""
    scan = await db.scans.find_one({"id": scan_id}, {"_id": 0})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, model="gpt-4o")
        
        prompt = """Analiza esta imagen de un entorno de trabajo desde la perspectiva de seguridad industrial.
        
        Identifica:
        1. Riesgos potenciales visibles
        2. Condiciones inseguras
        3. Uso correcto/incorrecto de EPP
        4. Condiciones del area de trabajo
        5. Recomendaciones de mejora
        
        Responde en formato JSON con la siguiente estructura:
        {
            "risk_level": "alto/medio/bajo",
            "findings": [
                {"type": "riesgo/condicion/epp/area", "description": "descripcion", "severity": "alta/media/baja", "location": "ubicacion en imagen"}
            ],
            "recommendations": ["recomendacion1", "recomendacion2"],
            "summary": "resumen general del analisis"
        }"""
        
        image_content = ImageContent(image_url=scan["image_url"])
        response = await chat.send_async([
            UserMessage(content=[prompt, image_content])
        ])
        
        import json
        try:
            response_text = response.content if hasattr(response, 'content') else str(response)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {
                "risk_level": "medio",
                "findings": [],
                "recommendations": [],
                "summary": response_text
            }
        
        # Update scan with analysis
        await db.scans.update_one(
            {"id": scan_id},
            {"$set": {
                "status": "analyzed",
                "ai_analysis": analysis.get("summary", ""),
                "risk_level": analysis.get("risk_level", "medio"),
                "findings": analysis.get("findings", []),
                "recommendations": analysis.get("recommendations", []),
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "status": "analyzed",
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
