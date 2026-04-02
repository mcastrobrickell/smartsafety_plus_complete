"""SmartSafety+ - Dashboard Router"""
from fastapi import APIRouter, Depends
from config import db
from utils.auth import get_current_user
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

