"""
SmartSafety+ - AI Engine Router
Advanced AI-powered features:
  1. Scan comparativo temporal (antes/después)
  2. IA predictiva de riesgos
  3. Plan de acción automático
  4. Chat IA sobre datos de seguridad
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from config import db, EMERGENT_LLM_KEY, logger
from utils.auth import get_current_user
from utils.rate_limit import limiter
from openai import AsyncOpenAI
from datetime import datetime, timezone, timedelta
import json
import re

router = APIRouter(prefix="/ai", tags=["ai-engine"])


def _get_ai_client():
    """Get OpenAI client or raise if not configured."""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="Servicio de IA no configurado. Configure EMERGENT_LLM_KEY en .env")
    return AsyncOpenAI(api_key=EMERGENT_LLM_KEY)


async def _call_ai(system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> str:
    """Common AI call helper. Returns raw text response."""
    client = _get_ai_client()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content


def _parse_json(text: str) -> dict:
    """Extract JSON from AI response text."""
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group())
    raise ValueError("No se encontró JSON válido en la respuesta de IA")


# ═══════════════════════════════════════════════════════════════════════
# 1. SCAN COMPARATIVO TEMPORAL
# ═══════════════════════════════════════════════════════════════════════

class CompareRequest(BaseModel):
    scan_id_before: str
    scan_id_after: str


@router.post("/compare-scans")
@limiter.limit("15/minute")
async def compare_scans(
    request: Request,
    body: CompareRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Compara dos scans del mismo lugar en fechas distintas.
    La IA analiza la evolución: qué se resolvió, qué empeoró, qué es nuevo.
    """
    scan_before = await db.scans.find_one({"id": body.scan_id_before}, {"_id": 0, "image_data": 0})
    scan_after = await db.scans.find_one({"id": body.scan_id_after}, {"_id": 0, "image_data": 0})

    if not scan_before or not scan_after:
        raise HTTPException(status_code=404, detail="Uno o ambos scans no encontrados")

    findings_before = await db.findings.find({"scan_id": body.scan_id_before}, {"_id": 0}).to_list(100)
    findings_after = await db.findings.find({"scan_id": body.scan_id_after}, {"_id": 0}).to_list(100)

    system_prompt = """Eres un experto en seguridad industrial. Compara dos inspecciones del mismo lugar realizadas en fechas distintas.

Analiza:
1. Hallazgos RESUELTOS: estaban en la primera inspección pero ya no aparecen en la segunda
2. Hallazgos PERSISTENTES: siguen presentes en ambas inspecciones
3. Hallazgos NUEVOS: aparecen solo en la segunda inspección
4. Hallazgos que EMPEORARON: subieron de severidad
5. Tendencia general: ¿mejoró o empeoró la seguridad?

Responde ÚNICAMENTE en JSON:
{
  "resueltos": [{"descripcion": "...", "categoria": "...", "severidad_original": "..."}],
  "persistentes": [{"descripcion": "...", "categoria": "...", "severidad": "..."}],
  "nuevos": [{"descripcion": "...", "categoria": "...", "severidad": "..."}],
  "empeoraron": [{"descripcion": "...", "severidad_antes": "...", "severidad_despues": "..."}],
  "tendencia": "mejora|estable|deterioro",
  "score_mejora": number,
  "resumen": "análisis ejecutivo de la evolución",
  "recomendaciones": ["recomendación 1", "recomendación 2"]
}"""

    user_prompt = f"""INSPECCIÓN ANTERIOR ({scan_before.get('scanned_at', '')[:10]}):
Lugar: {scan_before.get('location', 'N/A')}
Hallazgos ({len(findings_before)}):
{json.dumps([{"cat": f.get("category"), "desc": f.get("description"), "sev": f.get("severity")} for f in findings_before], ensure_ascii=False, indent=1)}

INSPECCIÓN POSTERIOR ({scan_after.get('scanned_at', '')[:10]}):
Lugar: {scan_after.get('location', 'N/A')}
Hallazgos ({len(findings_after)}):
{json.dumps([{"cat": f.get("category"), "desc": f.get("description"), "sev": f.get("severity")} for f in findings_after], ensure_ascii=False, indent=1)}"""

    try:
        response_text = await _call_ai(system_prompt, user_prompt)
        analysis = _parse_json(response_text)

        # Save comparison to DB
        comparison = {
            "id": f"cmp-{body.scan_id_before[:8]}-{body.scan_id_after[:8]}",
            "scan_before_id": body.scan_id_before,
            "scan_after_id": body.scan_id_after,
            "location": scan_before.get("location", scan_after.get("location")),
            "date_before": scan_before.get("scanned_at"),
            "date_after": scan_after.get("scanned_at"),
            "analysis": analysis,
            "created_by": current_user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.scan_comparisons.insert_one(comparison)

        return {
            "comparison_id": comparison["id"],
            "location": comparison["location"],
            "period": f"{scan_before.get('scanned_at', '')[:10]} → {scan_after.get('scanned_at', '')[:10]}",
            "findings_before": len(findings_before),
            "findings_after": len(findings_after),
            **analysis
        }
    except Exception as e:
        logger.error(f"Compare scans error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis comparativo: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
# 2. IA PREDICTIVA DE RIESGOS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/risk-prediction")
@limiter.limit("10/minute")
async def predict_risks(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Analiza patrones históricos de hallazgos e incidentes para predecir
    las zonas, categorías y tipos de riesgo más probables a corto plazo.
    """
    # Gather historical data
    recent_findings = await db.findings.find(
        {}, {"_id": 0, "scan_id": 0}
    ).sort("created_at", -1).limit(200).to_list(200)

    recent_incidents = await db.incidents.find(
        {}, {"_id": 0}
    ).sort("reported_at", -1).limit(100).to_list(100)

    recent_scans = await db.scans.find(
        {}, {"_id": 0, "image_data": 0, "image_url": 0}
    ).sort("scanned_at", -1).limit(50).to_list(50)

    if len(recent_findings) < 3 and len(recent_incidents) < 2:
        return {
            "status": "insufficient_data",
            "message": "Se necesitan al menos 3 hallazgos y 2 incidentes para generar predicciones",
            "predictions": []
        }

    system_prompt = """Eres un analista predictivo de seguridad industrial. Con base en los datos históricos de hallazgos, incidentes y scans, identifica patrones y genera predicciones.

Analiza:
- Frecuencia de hallazgos por categoría y severidad
- Tendencia temporal (¿están aumentando o disminuyendo?)
- Ubicaciones con más riesgo recurrente
- Correlación entre hallazgos no resueltos y incidentes posteriores
- Patrones estacionales o por turno si es posible

Responde ÚNICAMENTE en JSON:
{
  "risk_score_global": number (1-100, donde 100 = riesgo máximo),
  "tendencia": "mejorando|estable|empeorando",
  "predicciones": [
    {
      "categoria": "string",
      "probabilidad": "alta|media|baja",
      "ubicacion_probable": "string",
      "razon": "string",
      "accion_preventiva": "string"
    }
  ],
  "zonas_criticas": [
    {"ubicacion": "string", "risk_score": number, "hallazgos_pendientes": number}
  ],
  "patrones_detectados": ["patrón 1", "patrón 2"],
  "resumen_ejecutivo": "string con resumen para gerencia"
}"""

    user_prompt = f"""DATOS HISTÓRICOS PARA ANÁLISIS PREDICTIVO:

HALLAZGOS RECIENTES ({len(recent_findings)} registros):
{json.dumps([{
    "cat": f.get("category"), "sev": f.get("severity"),
    "status": f.get("status"), "fecha": f.get("created_at", "")[:10]
} for f in recent_findings[:80]], ensure_ascii=False)}

INCIDENTES ({len(recent_incidents)} registros):
{json.dumps([{
    "titulo": i.get("title"), "cat": i.get("category"),
    "sev": i.get("severity"), "status": i.get("status"),
    "ubicacion": i.get("location"), "fecha": i.get("reported_at", "")[:10]
} for i in recent_incidents[:40]], ensure_ascii=False)}

SCANS ({len(recent_scans)} registros):
{json.dumps([{
    "ubicacion": s.get("location"), "hallazgos": s.get("findings_count"),
    "criticos": s.get("critical_count"), "fecha": s.get("scanned_at", "")[:10]
} for s in recent_scans[:30]], ensure_ascii=False)}"""

    try:
        response_text = await _call_ai(system_prompt, user_prompt, max_tokens=3000)
        prediction = _parse_json(response_text)

        # Save prediction
        prediction_record = {
            "id": f"pred-{datetime.now().strftime('%Y%m%d%H%M')}",
            "prediction": prediction,
            "data_points": {
                "findings": len(recent_findings),
                "incidents": len(recent_incidents),
                "scans": len(recent_scans),
            },
            "created_by": current_user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.ai_predictions.insert_one(prediction_record)

        return {
            "prediction_id": prediction_record["id"],
            "generated_at": prediction_record["created_at"],
            "data_analyzed": prediction_record["data_points"],
            **prediction
        }
    except Exception as e:
        logger.error(f"Risk prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
# 3. PLAN DE ACCIÓN AUTOMÁTICO
# ═══════════════════════════════════════════════════════════════════════

class ActionPlanRequest(BaseModel):
    scan_id: Optional[str] = None
    finding_ids: Optional[List[str]] = None
    incident_id: Optional[str] = None


@router.post("/action-plan")
@limiter.limit("15/minute")
async def generate_action_plan(
    request: Request,
    body: ActionPlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Genera un plan de acción correctiva priorizado por riesgo y costo.
    Puede basarse en un scan, una lista de hallazgos, o un incidente.
    """
    findings = []
    incident = None
    source_type = "manual"

    if body.scan_id:
        source_type = "scan"
        findings = await db.findings.find(
            {"scan_id": body.scan_id}, {"_id": 0}
        ).to_list(100)
        if not findings:
            raise HTTPException(status_code=404, detail="No se encontraron hallazgos para este scan")

    elif body.finding_ids:
        source_type = "findings"
        findings = await db.findings.find(
            {"id": {"$in": body.finding_ids}}, {"_id": 0}
        ).to_list(100)

    elif body.incident_id:
        source_type = "incident"
        incident = await db.incidents.find_one({"id": body.incident_id}, {"_id": 0})
        if not incident:
            raise HTTPException(status_code=404, detail="Incidente no encontrado")
        # Also get related findings
        findings = await db.findings.find(
            {"status": "pending"}, {"_id": 0}
        ).sort("created_at", -1).limit(20).to_list(20)

    if not findings and not incident:
        raise HTTPException(status_code=400, detail="Debe proporcionar scan_id, finding_ids, o incident_id")

    system_prompt = """Eres un Jefe de Prevención de Riesgos con 20 años de experiencia. Genera un Plan de Acción Correctiva profesional y priorizado.

Para cada acción, indica:
- Prioridad basada en: severidad del riesgo × probabilidad de recurrencia
- Plazo realista de implementación
- Responsable sugerido (cargo, no nombre)
- Costo estimado (bajo/medio/alto)
- Indicador de verificación

Responde ÚNICAMENTE en JSON:
{
  "plan_name": "string",
  "nivel_urgencia": "inmediato|corto_plazo|mediano_plazo",
  "acciones": [
    {
      "prioridad": 1,
      "accion": "string descriptivo",
      "tipo": "inmediata|correctiva|preventiva",
      "hallazgo_relacionado": "descripción breve del hallazgo",
      "severidad_riesgo": "critico|alto|medio|bajo",
      "responsable_sugerido": "cargo",
      "plazo_dias": number,
      "costo_estimado": "bajo|medio|alto",
      "indicador_verificacion": "cómo verificar que se cumplió",
      "referencia_normativa": "norma aplicable"
    }
  ],
  "recursos_necesarios": ["recurso 1", "recurso 2"],
  "resumen_ejecutivo": "párrafo resumen para gerencia",
  "costo_estimado_total": "bajo|medio|alto",
  "tiempo_implementacion_total": "X días/semanas"
}"""

    data_for_ai = ""
    if findings:
        data_for_ai += f"HALLAZGOS ({len(findings)}):\n"
        data_for_ai += json.dumps([{
            "cat": f.get("category"), "desc": f.get("description"),
            "sev": f.get("severity"), "ref": f.get("normative_reference"),
            "correctiva_sugerida": f.get("corrective_action")
        } for f in findings], ensure_ascii=False, indent=1)

    if incident:
        data_for_ai += f"\n\nINCIDENTE:\n"
        data_for_ai += json.dumps({
            "titulo": incident.get("title"), "desc": incident.get("description"),
            "sev": incident.get("severity"), "cat": incident.get("category"),
            "ubicacion": incident.get("location"), "status": incident.get("status")
        }, ensure_ascii=False)

    try:
        response_text = await _call_ai(system_prompt, f"Genera un plan de acción para:\n\n{data_for_ai}")
        plan = _parse_json(response_text)

        # Save plan to DB
        plan_record = {
            "id": f"plan-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "source_type": source_type,
            "scan_id": body.scan_id,
            "finding_ids": body.finding_ids or [f.get("id") for f in findings],
            "incident_id": body.incident_id,
            "plan": plan,
            "status": "draft",
            "created_by": current_user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.action_plans.insert_one(plan_record)

        return {
            "plan_id": plan_record["id"],
            "source_type": source_type,
            "generated_at": plan_record["created_at"],
            **plan
        }
    except Exception as e:
        logger.error(f"Action plan error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando plan: {str(e)}")


@router.get("/action-plans")
async def list_action_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Listar planes de acción generados."""
    from utils.pagination import paginated_find
    return await paginated_find(
        db.action_plans,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )


# ═══════════════════════════════════════════════════════════════════════
# 4. CHAT IA SOBRE DATOS DE SEGURIDAD
# ═══════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


@router.post("/chat")
@limiter.limit("30/minute")
async def chat_with_data(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Asistente IA que responde preguntas sobre los datos de seguridad de la empresa.
    Consulta la DB en tiempo real y responde en lenguaje natural.
    """
    # Gather context data based on the question
    context = await _build_chat_context(body.question)

    system_prompt = f"""Eres el Asistente de Seguridad de SmartSafety+. Respondes preguntas sobre los datos de seguridad operativa de la empresa.

REGLAS:
- Responde siempre en español
- Sé conciso y directo
- Cita datos específicos cuando los tengas
- Si no tienes datos suficientes, dilo honestamente
- Sugiere acciones cuando sea relevante
- Usa formato claro con números y porcentajes cuando aplique

DATOS ACTUALES DEL SISTEMA:
{context}

El usuario que pregunta es: {current_user.get('name')} ({current_user.get('role')})"""

    try:
        response_text = await _call_ai(system_prompt, body.question, max_tokens=2000)

        # Save chat to DB
        chat_entry = {
            "id": f"chat-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "conversation_id": body.conversation_id or f"conv-{datetime.now().strftime('%Y%m%d%H%M')}",
            "question": body.question,
            "answer": response_text,
            "user_id": current_user.get("id"),
            "user_name": current_user.get("name"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.ai_chat_history.insert_one(chat_entry)

        return {
            "chat_id": chat_entry["id"],
            "conversation_id": chat_entry["conversation_id"],
            "answer": response_text,
        }
    except Exception as e:
        logger.error(f"AI Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en chat IA: {str(e)}")


async def _build_chat_context(question: str) -> str:
    """Build relevant context from DB based on the question keywords."""
    context_parts = []
    q_lower = question.lower()

    # Always include summary stats
    total_incidents = await db.incidents.count_documents({})
    open_incidents = await db.incidents.count_documents({"status": "open"})
    total_findings = await db.findings.count_documents({})
    pending_findings = await db.findings.count_documents({"status": "pending"})
    critical_findings = await db.findings.count_documents({"severity": {"$in": ["critico", "critical"]}})
    total_scans = await db.scans.count_documents({})

    context_parts.append(f"""RESUMEN GENERAL:
- Incidentes: {total_incidents} total, {open_incidents} abiertos
- Hallazgos: {total_findings} total, {pending_findings} pendientes, {critical_findings} críticos
- Scans realizados: {total_scans}""")

    # If asking about incidents
    if any(w in q_lower for w in ["incidente", "accidente", "reporte", "reportado"]):
        incidents = await db.incidents.find({}, {"_id": 0}).sort("reported_at", -1).limit(15).to_list(15)
        if incidents:
            context_parts.append(f"\nÚLTIMOS INCIDENTES ({len(incidents)}):")
            for i in incidents:
                context_parts.append(
                    f"  - [{i.get('severity','?')}] {i.get('title','?')} | {i.get('location','?')} | {i.get('status','?')} | {i.get('reported_at','')[:10]}"
                )

    # If asking about findings/hallazgos
    if any(w in q_lower for w in ["hallazgo", "finding", "riesgo", "detectado", "pendiente"]):
        findings = await db.findings.find({}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
        if findings:
            context_parts.append(f"\nÚLTIMOS HALLAZGOS ({len(findings)}):")
            for f in findings:
                context_parts.append(
                    f"  - [{f.get('severity','?')}] {f.get('category','?')}: {f.get('description','?')[:80]} | {f.get('status','?')}"
                )

    # If asking about EPP
    if any(w in q_lower for w in ["epp", "equipo", "protección", "casco", "guante", "entrega", "stock"]):
        epp_stats = await db.epp_movements.aggregate([
            {"$group": {"_id": "$movement_type", "total": {"$sum": "$quantity"}, "costo": {"$sum": "$total_cost"}}}
        ]).to_list(10)
        if epp_stats:
            context_parts.append("\nESTADÍSTICAS EPP:")
            for s in epp_stats:
                context_parts.append(f"  - {s['_id']}: {s['total']} unidades, ${s['costo']:,.0f}")

    # If asking about scans
    if any(w in q_lower for w in ["scan", "inspección", "foto", "imagen", "360"]):
        scans = await db.scans.find({}, {"_id": 0, "image_data": 0, "image_url": 0}).sort("scanned_at", -1).limit(10).to_list(10)
        if scans:
            context_parts.append(f"\nÚLTIMOS SCANS ({len(scans)}):")
            for s in scans:
                context_parts.append(
                    f"  - {s.get('name','?')} | {s.get('location','?')} | {s.get('findings_count',0)} hallazgos | {s.get('scanned_at','')[:10]}"
                )

    # If asking about procedures
    if any(w in q_lower for w in ["procedimiento", "protocolo", "normativa", "documento"]):
        procs = await db.procedures.find({}, {"_id": 0, "content": 0}).limit(10).to_list(10)
        if procs:
            context_parts.append(f"\nPROCEDIMIENTOS ({len(procs)}):")
            for p in procs:
                context_parts.append(f"  - [{p.get('code','?')}] {p.get('name','?')} | {p.get('category','?')}")

    # If asking about risk matrix
    if any(w in q_lower for w in ["matriz", "riesgo", "probabilidad", "consecuencia"]):
        matrices = await db.risk_matrices.find({}, {"_id": 0}).limit(5).to_list(5)
        if matrices:
            context_parts.append(f"\nMATRICES DE RIESGO ({len(matrices)}):")
            for m in matrices:
                n_risks = len(m.get("risks", []))
                context_parts.append(f"  - {m.get('name','?')} | {m.get('area','?')} | {n_risks} riesgos | {m.get('status','?')}")

    return "\n".join(context_parts)


# ═══════════════════════════════════════════════════════════════════════
# HISTORIAL
# ═══════════════════════════════════════════════════════════════════════

@router.get("/predictions")
async def list_predictions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Listar predicciones históricas."""
    from utils.pagination import paginated_find
    return await paginated_find(
        db.ai_predictions,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )


@router.get("/chat-history")
async def get_chat_history(
    conversation_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Obtener historial de chat IA."""
    from utils.pagination import paginated_find
    query = {"user_id": current_user.get("id")}
    if conversation_id:
        query["conversation_id"] = conversation_id
    return await paginated_find(
        db.ai_chat_history,
        query=query,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )


@router.get("/comparisons")
async def list_comparisons(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Listar comparaciones de scans."""
    from utils.pagination import paginated_find
    return await paginated_find(
        db.scan_comparisons,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )
