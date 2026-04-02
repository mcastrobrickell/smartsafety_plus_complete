"""SmartSafety+ - Scan 360 & Findings Router
Improvements:
  - Images saved to filesystem instead of base64 in MongoDB
  - Paginated list endpoints
  - Rate limiting on AI analysis
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, Request
from typing import Optional
from config import db, EMERGENT_LLM_KEY, UPLOADS_DIR, logger
from models.schemas import SafetyFinding
from utils.auth import get_current_user
from utils.pagination import paginated_find
from utils.rate_limit import limiter
from openai import AsyncOpenAI
from datetime import datetime, timezone
import uuid
import base64
import json
import re
from pathlib import Path

router = APIRouter(tags=["scans"])

# Directory for scan images
SCANS_DIR = UPLOADS_DIR / "scans"
SCANS_DIR.mkdir(exist_ok=True)

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


@router.get("/scans")
async def get_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """List scans with pagination. Images excluded from listing."""
    return await paginated_find(
        db.scans,
        projection={"_id": 0, "image_data": 0},
        sort_field="scanned_at",
        page=page,
        page_size=page_size,
    )


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    scan = await db.scans.find_one({"id": scan_id}, {"_id": 0, "image_data": 0})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Build image URL if file exists
    image_path = SCANS_DIR / f"{scan_id}.jpg"
    if image_path.exists():
        scan["image_url"] = f"/api/uploads/scans/{scan_id}.jpg"

    findings = await db.findings.find({"scan_id": scan_id}, {"_id": 0}).to_list(500)
    return {"scan": scan, "findings": findings}


@router.delete("/scans/{scan_id}")
async def delete_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scan, its associated findings, and its image file."""
    scan = await db.scans.find_one({"id": scan_id}, {"_id": 0})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    await db.findings.delete_many({"scan_id": scan_id})
    await db.scans.delete_one({"id": scan_id})

    # Delete image file
    image_path = SCANS_DIR / f"{scan_id}.jpg"
    if image_path.exists():
        image_path.unlink()

    return {"message": "Scan eliminado correctamente", "deleted_findings": True}


@router.post("/scans/analyze")
@limiter.limit("20/minute")
async def analyze_scan(
    request: Request,
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

        # ── Save image to filesystem instead of MongoDB ──
        image_path = SCANS_DIR / f"{scan_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_content)

        scan_doc = {
            "id": scan_id,
            "name": name,
            "location": location,
            "scanned_by": current_user["name"],
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "image_url": f"/api/uploads/scans/{scan_id}.jpg",
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

                client = AsyncOpenAI(api_key=EMERGENT_LLM_KEY)

                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [
                            {"type": "text", "text": "Analiza esta imagen de un entorno industrial y detecta todos los riesgos de seguridad presentes. Responde en formato JSON."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]}
                    ],
                    max_tokens=4000
                )

                response_text = response.choices[0].message.content
                json_match = re.search(r'\{[\s\S]*\}', response_text)
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
                        findings.append(finding_dict.copy())
                        findings_for_db.append(finding_dict)
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


# ================== FINDINGS ==================

@router.get("/findings")
async def get_findings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List findings with pagination and optional filters."""
    query = {}
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status

    return await paginated_find(
        db.findings,
        query=query,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )


@router.put("/findings/{finding_id}/status")
async def update_finding_status(finding_id: str, status: str, current_user: dict = Depends(get_current_user)):
    result = await db.findings.update_one({"id": finding_id}, {"$set": {"status": status}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"message": "Finding updated"}
