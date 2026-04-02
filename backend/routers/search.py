"""
SmartSafety+ - Global Search Router
Full-text search across incidents, findings, scans, procedures, EPP, and investigations.
Supports Cmd+K / Ctrl+K style instant search from the frontend.
"""
from fastapi import APIRouter, Depends, Query
from config import db, logger
from utils.auth import get_current_user
from datetime import datetime, timezone
import re

router = APIRouter(tags=["search"])


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2, max_length=200, description="Término de búsqueda"),
    types: str = Query("all", description="Filtrar por tipo: all, incidents, findings, scans, procedures, epp, investigations"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    Búsqueda global full-text en todas las colecciones.
    Retorna resultados agrupados por tipo con relevancia.
    """
    # Build regex for case-insensitive partial match
    pattern = {"$regex": re.escape(q), "$options": "i"}
    requested_types = types.split(",") if types != "all" else [
        "incidents", "findings", "scans", "procedures", "epp", "investigations"
    ]

    results = []
    per_type_limit = max(3, limit // len(requested_types))

    # ── Incidents ──
    if "incidents" in requested_types:
        items = await db.incidents.find(
            {"$or": [
                {"title": pattern},
                {"description": pattern},
                {"location": pattern},
                {"category": pattern},
            ]},
            {"_id": 0}
        ).sort("reported_at", -1).limit(per_type_limit).to_list(per_type_limit)

        for item in items:
            results.append({
                "type": "incident",
                "id": item.get("id"),
                "title": item.get("title", ""),
                "subtitle": f"{item.get('severity', '')} · {item.get('location', '')}",
                "description": item.get("description", "")[:150],
                "severity": item.get("severity"),
                "status": item.get("status"),
                "date": item.get("reported_at", "")[:10],
                "url": f"/incidents",
            })

    # ── Findings ──
    if "findings" in requested_types:
        items = await db.findings.find(
            {"$or": [
                {"description": pattern},
                {"category": pattern},
                {"corrective_action": pattern},
                {"normative_reference": pattern},
            ]},
            {"_id": 0}
        ).sort("created_at", -1).limit(per_type_limit).to_list(per_type_limit)

        for item in items:
            results.append({
                "type": "finding",
                "id": item.get("id"),
                "title": item.get("category", "Hallazgo"),
                "subtitle": f"{item.get('severity', '')} · {item.get('status', '')}",
                "description": item.get("description", "")[:150],
                "severity": item.get("severity"),
                "status": item.get("status"),
                "date": item.get("created_at", "")[:10],
                "url": f"/findings",
            })

    # ── Scans ──
    if "scans" in requested_types:
        items = await db.scans.find(
            {"$or": [
                {"name": pattern},
                {"location": pattern},
                {"summary": pattern},
                {"scanned_by": pattern},
            ]},
            {"_id": 0, "image_data": 0, "image_url": 0}
        ).sort("scanned_at", -1).limit(per_type_limit).to_list(per_type_limit)

        for item in items:
            results.append({
                "type": "scan",
                "id": item.get("id"),
                "title": item.get("name", "Scan"),
                "subtitle": f"{item.get('location', '')} · {item.get('findings_count', 0)} hallazgos",
                "description": item.get("summary", "")[:150],
                "severity": item.get("risk_level"),
                "status": item.get("status"),
                "date": item.get("scanned_at", "")[:10],
                "url": f"/scan360",
            })

    # ── Procedures ──
    if "procedures" in requested_types:
        items = await db.procedures.find(
            {"$or": [
                {"name": pattern},
                {"code": pattern},
                {"description": pattern},
                {"category": pattern},
                {"content": pattern},
            ]},
            {"_id": 0, "content": 0}
        ).limit(per_type_limit).to_list(per_type_limit)

        for item in items:
            results.append({
                "type": "procedure",
                "id": item.get("id"),
                "title": f"[{item.get('code', '')}] {item.get('name', '')}",
                "subtitle": item.get("category", ""),
                "description": item.get("description", "")[:150],
                "status": "active" if item.get("is_active") else "inactive",
                "date": item.get("created_at", "")[:10],
                "url": f"/procedures",
            })

    # ── EPP Items ──
    if "epp" in requested_types:
        items = await db.epp_items.find(
            {"$or": [
                {"name": pattern},
                {"code": pattern},
                {"brand": pattern},
            ]},
            {"_id": 0}
        ).limit(per_type_limit).to_list(per_type_limit)

        for item in items:
            results.append({
                "type": "epp",
                "id": item.get("id"),
                "title": item.get("name", ""),
                "subtitle": f"{item.get('code', '')} · {item.get('brand', '')}",
                "description": f"Costo: ${item.get('unit_cost', 0):,.0f}",
                "status": "active" if item.get("is_active") else "inactive",
                "date": item.get("created_at", "")[:10],
                "url": f"/epp",
            })

    # ── Investigations ──
    if "investigations" in requested_types:
        items = await db.investigations.find(
            {"$or": [
                {"code": pattern},
                {"incident_description": pattern},
                {"incident_location": pattern},
                {"narrative": pattern},
            ]},
            {"_id": 0, "photos": 0}
        ).sort("created_at", -1).limit(per_type_limit).to_list(per_type_limit)

        for item in items:
            results.append({
                "type": "investigation",
                "id": item.get("id"),
                "title": f"Investigación {item.get('code', '')}",
                "subtitle": f"{item.get('status', '')} · {item.get('incident_location', '')}",
                "description": item.get("incident_description", "")[:150],
                "status": item.get("status"),
                "date": item.get("created_at", "")[:10],
                "url": f"/investigation/{item.get('id', '')}",
            })

    # Sort by date descending
    results.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Group by type for summary
    type_counts = {}
    for r in results:
        t = r["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "query": q,
        "total": len(results),
        "by_type": type_counts,
        "results": results[:limit],
    }
