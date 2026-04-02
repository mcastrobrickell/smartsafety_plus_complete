"""SmartSafety+ - Dashboard & Audit Router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from config import db
from utils.auth import get_current_user
from utils.pagination import paginated_find
from datetime import datetime, timezone

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    total_incidents = await db.incidents.count_documents({})
    open_incidents = await db.incidents.count_documents({"status": "open"})
    critical_findings = await db.findings.count_documents({"severity": {"$in": ["critico", "critical"]}})
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    scans_today = await db.scans.count_documents({
        "scanned_at": {"$gte": today.isoformat()}
    })
    
    pending_actions = await db.findings.count_documents({"status": "pending"})
    total_scans = await db.scans.count_documents({})
    
    # EPP costs summary
    epp_costs = await db.epp_movements.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_cost"}}}
    ]).to_list(1)
    total_epp_cost = epp_costs[0]["total"] if epp_costs else 0
    
    return {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "critical_findings": critical_findings,
        "scans_today": scans_today,
        "total_scans": total_scans,
        "pending_actions": pending_actions,
        "total_epp_cost": total_epp_cost
    }

@router.get("/dashboard/recent-activity")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    recent_incidents = await db.incidents.find({}, {"_id": 0}).sort("reported_at", -1).limit(5).to_list(5)
    recent_scans = await db.scans.find({}, {"_id": 0, "image_data": 0}).sort("scanned_at", -1).limit(5).to_list(5)
    recent_findings = await db.findings.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "incidents": recent_incidents,
        "scans": recent_scans,
        "findings": recent_findings
    }

@router.get("/dashboard/charts")
async def get_dashboard_charts(current_user: dict = Depends(get_current_user)):
    severity_data = await db.incidents.aggregate([
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    category_data = await db.findings.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    # EPP costs by cost center
    epp_by_center = await db.epp_movements.aggregate([
        {
            "$group": {
                "_id": {"$ifNull": ["$to_cost_center_id", "$from_cost_center_id"]},
                "total_cost": {"$sum": "$total_cost"}
            }
        }
    ]).to_list(100)
    
    return {
        "incidents_by_severity": [{"name": item["_id"] or "Sin clasificar", "value": item["count"]} for item in severity_data],
        "findings_by_category": [{"name": item["_id"] or "General", "value": item["count"]} for item in category_data],
        "epp_costs_by_center": [{"center": item["_id"] or "Sin asignar", "cost": item["total_cost"]} for item in epp_by_center]
    }


# ================== DASHBOARD ADVANCED ==================

@router.get("/dashboard/trends")
async def get_dashboard_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Advanced trends: daily counts for incidents, findings, scans over N days.
    Includes risk heatmap by location and compliance KPIs.
    """
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # ── Daily incidents trend ──
    incidents_trend = await db.incidents.aggregate([
        {"$match": {"reported_at": {"$gte": cutoff}}},
        {"$addFields": {"date": {"$substr": ["$reported_at", 0, 10]}}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(365)

    # ── Daily findings trend ──
    findings_trend = await db.findings.aggregate([
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$addFields": {"date": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(365)

    # ── Daily scans trend ──
    scans_trend = await db.scans.aggregate([
        {"$match": {"scanned_at": {"$gte": cutoff}}},
        {"$addFields": {"date": {"$substr": ["$scanned_at", 0, 10]}}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(365)

    # ── Risk heatmap by location ──
    location_risk = await db.findings.aggregate([
        {"$lookup": {"from": "scans", "localField": "scan_id", "foreignField": "id", "as": "scan"}},
        {"$unwind": {"path": "$scan", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$scan.location",
            "total_findings": {"$sum": 1},
            "critical": {"$sum": {"$cond": [{"$in": ["$severity", ["critico", "critical"]]}, 1, 0]}},
            "high": {"$sum": {"$cond": [{"$in": ["$severity", ["alto", "high"]]}, 1, 0]}},
            "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
        }},
        {"$sort": {"total_findings": -1}},
        {"$limit": 15}
    ]).to_list(15)

    # ── Compliance KPIs ──
    total_findings = await db.findings.count_documents({})
    resolved_findings = await db.findings.count_documents({"status": {"$in": ["resolved", "closed"]}})
    total_incidents = await db.incidents.count_documents({})
    closed_incidents = await db.incidents.count_documents({"status": "closed"})

    resolution_rate = (resolved_findings / total_findings * 100) if total_findings > 0 else 0
    incident_closure_rate = (closed_incidents / total_incidents * 100) if total_incidents > 0 else 0

    # Average resolution time (findings)
    resolution_pipeline = await db.findings.aggregate([
        {"$match": {"status": {"$in": ["resolved", "closed"]}}},
        {"$limit": 100}
    ]).to_list(100)

    # Severity distribution (current pending)
    severity_dist = await db.findings.aggregate([
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]).to_list(10)

    return {
        "period_days": days,
        "trends": {
            "incidents": [{"date": d["_id"], "count": d["count"]} for d in incidents_trend],
            "findings": [{"date": d["_id"], "count": d["count"]} for d in findings_trend],
            "scans": [{"date": d["_id"], "count": d["count"]} for d in scans_trend],
        },
        "heatmap": [
            {
                "location": d["_id"] or "Sin ubicación",
                "total": d["total_findings"],
                "critical": d["critical"],
                "high": d["high"],
                "pending": d["pending"],
                "risk_score": d["critical"] * 4 + d["high"] * 2 + d["pending"],
            }
            for d in location_risk
        ],
        "kpis": {
            "finding_resolution_rate": round(resolution_rate, 1),
            "incident_closure_rate": round(incident_closure_rate, 1),
            "total_findings": total_findings,
            "resolved_findings": resolved_findings,
            "total_incidents": total_incidents,
            "closed_incidents": closed_incidents,
            "pending_severity": {d["_id"]: d["count"] for d in severity_dist if d["_id"]},
        }
    }


# ================== AUDIT LOG ==================

@router.get("/audit-log")
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    method: Optional[str] = None,
    user_email: Optional[str] = None,
    path_contains: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get audit trail. Admin/SuperAdmin only."""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {}
    if method:
        query["method"] = method.upper()
    if user_email:
        query["user_email"] = {"$regex": user_email, "$options": "i"}
    if path_contains:
        query["path"] = {"$regex": path_contains, "$options": "i"}

    return await paginated_find(
        db.audit_log,
        query=query,
        sort_field="timestamp",
        page=page,
        page_size=page_size,
    )


@router.get("/audit-log/stats")
async def get_audit_stats(current_user: dict = Depends(get_current_user)):
    """Get audit summary stats. Admin/SuperAdmin only."""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    total = await db.audit_log.count_documents({})

    # Actions by method
    by_method = await db.audit_log.aggregate([
        {"$group": {"_id": "$method", "count": {"$sum": 1}}}
    ]).to_list(10)

    # Actions by user (top 10)
    by_user = await db.audit_log.aggregate([
        {"$match": {"user_email": {"$ne": None}}},
        {"$group": {"_id": "$user_email", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]).to_list(10)

    # Failed requests (4xx/5xx)
    errors = await db.audit_log.count_documents({"status_code": {"$gte": 400}})

    # Last 24h activity
    from datetime import timedelta
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    last_24h = await db.audit_log.count_documents({"timestamp": {"$gte": yesterday}})

    return {
        "total_actions": total,
        "last_24h": last_24h,
        "errors": errors,
        "by_method": {item["_id"]: item["count"] for item in by_method if item["_id"]},
        "top_users": [{"email": item["_id"], "actions": item["count"]} for item in by_user],
    }
