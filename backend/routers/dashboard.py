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
