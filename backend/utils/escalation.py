"""
SmartSafety+ - Auto-Escalation Engine
Background task that checks for unresolved critical items and escalates them.

Escalation rules:
  - Critical finding pending > 24h → notify supervisor
  - Critical finding pending > 48h → notify admin + mark as escalated
  - High-severity incident open > 48h → notify admin
  - Any escalation creates an in-app notification
"""
from config import db, RESEND_API_KEY, SENDER_EMAIL, logger
from utils.websocket import ws_manager
from datetime import datetime, timezone, timedelta
import uuid
import asyncio


async def create_notification(
    title: str,
    message: str,
    severity: str = "high",
    notif_type: str = "escalation",
    reference_id: str = None,
    reference_type: str = None,
    target_roles: list = None,
):
    """Create an in-app notification and broadcast via WebSocket."""
    notif = {
        "id": str(uuid.uuid4()),
        "title": title,
        "message": message,
        "severity": severity,
        "type": notif_type,
        "reference_id": reference_id,
        "reference_type": reference_type,
        "target_roles": target_roles or ["admin", "superadmin"],
        "read_by": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.in_app_notifications.insert_one(notif)

    # Broadcast to connected clients
    await ws_manager.broadcast({
        "event": "notification",
        "data": {k: v for k, v in notif.items() if k != "_id"}
    })

    return notif


async def run_escalation_check():
    """Run a single escalation check cycle."""
    now = datetime.now(timezone.utc)
    escalated_count = 0

    # ── 1. Critical findings pending > 24h ──
    threshold_24h = (now - timedelta(hours=24)).isoformat()
    threshold_48h = (now - timedelta(hours=48)).isoformat()

    stale_critical_findings = await db.findings.find({
        "severity": {"$in": ["critico", "critical"]},
        "status": "pending",
        "created_at": {"$lte": threshold_24h},
        "escalated": {"$ne": True},
    }, {"_id": 0}).to_list(50)

    for finding in stale_critical_findings:
        hours_old = (now - datetime.fromisoformat(finding["created_at"].replace("Z", "+00:00"))).total_seconds() / 3600

        if hours_old >= 48:
            # Level 2: Escalate to admin
            await db.findings.update_one(
                {"id": finding["id"]},
                {"$set": {"escalated": True, "escalation_level": 2, "escalated_at": now.isoformat()}}
            )
            await create_notification(
                title=f"⚠️ ESCALAMIENTO L2: {finding.get('category', 'Hallazgo')}",
                message=f"Hallazgo crítico sin resolver hace {int(hours_old)}h: {finding.get('description', '')[:120]}",
                severity="critical",
                reference_id=finding["id"],
                reference_type="finding",
                target_roles=["admin", "superadmin"],
            )
            escalated_count += 1

        elif hours_old >= 24:
            # Level 1: Notify supervisor
            await db.findings.update_one(
                {"id": finding["id"]},
                {"$set": {"escalation_level": 1, "escalation_warned_at": now.isoformat()}}
            )
            await create_notification(
                title=f"⏰ Hallazgo crítico sin resolver ({int(hours_old)}h)",
                message=f"{finding.get('category', '')}: {finding.get('description', '')[:120]}",
                severity="high",
                reference_id=finding["id"],
                reference_type="finding",
                target_roles=["admin", "superadmin"],
            )
            escalated_count += 1

    # ── 2. High/Critical incidents open > 48h ──
    stale_incidents = await db.incidents.find({
        "severity": {"$in": ["critical", "high", "critico", "alto"]},
        "status": "open",
        "reported_at": {"$lte": threshold_48h},
        "escalated": {"$ne": True},
    }, {"_id": 0}).to_list(50)

    for incident in stale_incidents:
        hours_old = (now - datetime.fromisoformat(incident["reported_at"].replace("Z", "+00:00"))).total_seconds() / 3600
        await db.incidents.update_one(
            {"id": incident["id"]},
            {"$set": {"escalated": True, "escalated_at": now.isoformat()}}
        )
        await create_notification(
            title=f"🚨 Incidente escalado: {incident.get('title', 'Sin título')}",
            message=f"Incidente {incident.get('severity', '')} abierto hace {int(hours_old)}h en {incident.get('location', 'N/A')}",
            severity="critical",
            reference_id=incident["id"],
            reference_type="incident",
            target_roles=["admin", "superadmin"],
        )
        escalated_count += 1

    if escalated_count > 0:
        logger.info(f"🔔 Escalamiento: {escalated_count} items escalados")

    return escalated_count


async def escalation_loop(interval_minutes: int = 30):
    """Background loop that runs escalation checks periodically."""
    logger.info(f"🔔 Escalation engine started (interval: {interval_minutes}min)")
    while True:
        try:
            await run_escalation_check()
        except Exception as e:
            logger.error(f"Escalation check error: {e}")
        await asyncio.sleep(interval_minutes * 60)
