"""
SmartSafety+ - Notifications Router (Complete)
  - In-app notification center (read/unread, badge, filters)
  - WebSocket for real-time push
  - Email notifications (Resend)
  - SMS notifications (Twilio)
  - Escalation integration
"""
from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from config import db, RESEND_API_KEY, SENDER_EMAIL, TWILIO_PHONE_NUMBER, twilio_client, resend, logger
from models.schemas import EmailNotificationRequest, SMSNotificationRequest
from utils.auth import get_current_user
from utils.email import generate_alert_html
from utils.rate_limit import limiter
from utils.websocket import ws_manager
from utils.pagination import paginated_find
from utils.escalation import create_notification
from datetime import datetime, timezone
import uuid
import asyncio
import jwt as pyjwt
from config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter(tags=["notifications"])


# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET - Real-time connection
# ═══════════════════════════════════════════════════════════════════════

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket for real-time notifications.
    Connect with: ws://host/api/ws/notifications?token=JWT_TOKEN
    """
    user_id = "anonymous"
    try:
        if token:
            payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub", "anonymous")
    except Exception:
        pass

    await ws_manager.connect(websocket, user_id)
    try:
        # Send unread count on connect
        unread = await db.in_app_notifications.count_documents({
            "read_by": {"$nin": [user_id]},
            "$or": [
                {"target_roles": {"$exists": False}},
                {"target_roles": {"$size": 0}},
                {"target_roles": {"$in": ["all"]}}
            ]
        })
        await websocket.send_json({"event": "connected", "unread_count": unread})

        # Keep alive - listen for pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception:
        ws_manager.disconnect(websocket, user_id)


# ═══════════════════════════════════════════════════════════════════════
# IN-APP NOTIFICATION CENTER
# ═══════════════════════════════════════════════════════════════════════

@router.get("/notifications")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    unread_only: bool = False,
    severity: Optional[str] = None,
    notif_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated notifications for the current user.
    Filters: unread_only, severity (critical/high/medium/low), type (escalation/finding/incident/system).
    """
    user_id = current_user.get("id")
    user_role = current_user.get("role")

    query = {
        "$or": [
            {"target_roles": {"$in": [user_role, "all"]}},
            {"target_roles": {"$exists": False}},
            {"target_roles": {"$size": 0}},
        ]
    }

    if unread_only:
        query["read_by"] = {"$nin": [user_id]}
    if severity:
        query["severity"] = severity
    if notif_type:
        query["type"] = notif_type

    result = await paginated_find(
        db.in_app_notifications,
        query=query,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )

    # Mark which ones are read by this user
    for item in result["items"]:
        item["is_read"] = user_id in item.get("read_by", [])
        item.pop("read_by", None)  # Don't send full list to client

    return result


@router.get("/notifications/badge")
async def get_notification_badge(current_user: dict = Depends(get_current_user)):
    """Get unread notification count for badge display."""
    user_id = current_user.get("id")
    user_role = current_user.get("role")

    count = await db.in_app_notifications.count_documents({
        "read_by": {"$nin": [user_id]},
        "$or": [
            {"target_roles": {"$in": [user_role, "all"]}},
            {"target_roles": {"$exists": False}},
            {"target_roles": {"$size": 0}},
        ]
    })
    return {"unread_count": count}


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a single notification as read."""
    user_id = current_user.get("id")
    result = await db.in_app_notifications.update_one(
        {"id": notification_id},
        {"$addToSet": {"read_by": user_id}}
    )
    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marcada como leída"}


@router.put("/notifications/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current user."""
    user_id = current_user.get("id")
    result = await db.in_app_notifications.update_many(
        {"read_by": {"$nin": [user_id]}},
        {"$addToSet": {"read_by": user_id}}
    )
    return {"message": f"{result.modified_count} notificaciones marcadas como leídas"}


@router.post("/notifications/create")
async def create_custom_notification(
    title: str,
    message: str,
    severity: str = "medium",
    target_roles: str = "all",
    current_user: dict = Depends(get_current_user)
):
    """Create a custom notification (admin only)."""
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    roles = [r.strip() for r in target_roles.split(",")]
    notif = await create_notification(
        title=title,
        message=message,
        severity=severity,
        notif_type="system",
        target_roles=roles,
    )
    notif.pop("_id", None)
    return {"message": "Notificación creada", "notification": notif}


# ═══════════════════════════════════════════════════════════════════════
# LEGACY ENDPOINTS (generated notifications from findings/incidents)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/notifications/alerts")
async def get_alert_notifications(current_user: dict = Depends(get_current_user)):
    """Get active alerts from critical findings and open incidents (legacy)."""
    critical_findings = await db.findings.find(
        {"severity": {"$in": ["critico", "critical"]}, "status": "pending"},
        {"_id": 0}
    ).limit(10).to_list(10)

    open_incidents = await db.incidents.find(
        {"status": "open", "severity": {"$in": ["critical", "high", "critico", "alto"]}},
        {"_id": 0}
    ).limit(10).to_list(10)

    alerts = []
    for finding in critical_findings:
        alerts.append({
            "id": finding["id"],
            "type": "finding",
            "title": f"Hallazgo Crítico: {finding['category']}",
            "message": finding["description"][:100],
            "severity": "critical",
            "created_at": finding["created_at"]
        })

    for incident in open_incidents:
        alerts.append({
            "id": incident["id"],
            "type": "incident",
            "title": f"Incidente: {incident['title']}",
            "message": incident["description"][:100],
            "severity": incident["severity"],
            "created_at": incident["reported_at"]
        })

    return sorted(alerts, key=lambda x: x["created_at"], reverse=True)


# ═══════════════════════════════════════════════════════════════════════
# EMAIL NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/notifications/send-alert")
@limiter.limit("15/minute")
async def send_notification_alert(request: Request, body: EmailNotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send email notification for safety alerts."""
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")

    finding = None
    incident = None

    if body.finding_id:
        finding = await db.findings.find_one({"id": body.finding_id}, {"_id": 0})
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")

    if body.incident_id:
        incident = await db.incidents.find_one({"id": body.incident_id}, {"_id": 0})
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

    html_content = generate_alert_html(finding, incident, body.custom_message)

    params = {
        "from": SENDER_EMAIL,
        "to": [body.recipient_email],
        "subject": body.subject,
        "html": html_content
    }

    try:
        email_result = await asyncio.to_thread(resend.Emails.send, params)

        notification_log = {
            "id": str(uuid.uuid4()),
            "type": "email",
            "recipient": body.recipient_email,
            "subject": body.subject,
            "finding_id": body.finding_id,
            "incident_id": body.incident_id,
            "sent_by": current_user.get("id"),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "email_id": email_result.get("id") if email_result else None
        }
        await db.notification_logs.insert_one(notification_log)

        # Also create in-app notification
        await create_notification(
            title=f"Email enviado: {body.subject}",
            message=f"Destinatario: {body.recipient_email}",
            severity="low",
            notif_type="email_sent",
            target_roles=[current_user.get("role", "admin")],
        )

        return {
            "status": "success",
            "message": f"Email enviado a {body.recipient_email}",
            "email_id": email_result.get("id") if email_result else None
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar email: {str(e)}")


@router.post("/notifications/send-critical-alert")
async def send_critical_finding_alert(finding_id: str, current_user: dict = Depends(get_current_user)):
    """Send automatic alert for critical findings to all admins."""
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")

    finding = await db.findings.find_one({"id": finding_id}, {"_id": 0})
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    admins = await db.users.find({"role": {"$in": ["admin", "superadmin"]}}, {"_id": 0}).to_list(100)

    if not admins:
        return {"status": "warning", "message": "No hay administradores para notificar"}

    html_content = generate_alert_html(finding=finding)
    sent_count = 0

    for admin in admins:
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [admin["email"]],
                "subject": f"🚨 ALERTA CRITICA: {finding.get('category', 'Hallazgo de Seguridad')}",
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {admin['email']}: {str(e)}")

    # Create in-app notification too
    await create_notification(
        title=f"🚨 Hallazgo Crítico: {finding.get('category', 'Seguridad')}",
        message=finding.get("description", "")[:150],
        severity="critical",
        notif_type="critical_alert",
        reference_id=finding_id,
        reference_type="finding",
        target_roles=["admin", "superadmin"],
    )

    # Broadcast via WebSocket
    await ws_manager.broadcast({
        "event": "critical_finding",
        "data": {
            "finding_id": finding_id,
            "category": finding.get("category"),
            "severity": "critical",
            "description": finding.get("description", "")[:100],
        }
    })

    return {
        "status": "success",
        "message": f"Alertas enviadas a {sent_count} administradores",
        "recipients": sent_count
    }


# ═══════════════════════════════════════════════════════════════════════
# SMS NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/notifications/send-sms")
@limiter.limit("10/minute")
async def send_sms_notification(request: Request, body: SMSNotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send SMS notification for safety alerts."""
    if not twilio_client:
        raise HTTPException(status_code=500, detail="SMS service not configured")

    if not TWILIO_PHONE_NUMBER:
        raise HTTPException(status_code=500, detail="Twilio phone number not configured")

    phone = body.phone_number
    if not phone.startswith('+'):
        phone = f"+{phone}"

    message_body = body.message

    if body.finding_id:
        finding = await db.findings.find_one({"id": body.finding_id}, {"_id": 0})
        if finding:
            message_body = f"🚨 ALERTA SmartSafety+\nHallazgo: {finding.get('category', 'N/A')}\nSeveridad: {finding.get('severity', 'N/A')}\n{finding.get('description', '')[:100]}"

    if body.incident_id:
        incident = await db.incidents.find_one({"id": body.incident_id}, {"_id": 0})
        if incident:
            message_body = f"🚨 INCIDENTE SmartSafety+\n{incident.get('title', 'N/A')}\nSeveridad: {incident.get('severity', 'N/A')}\nUbicacion: {incident.get('location', 'N/A')}"

    try:
        sms = await asyncio.to_thread(
            twilio_client.messages.create,
            body=message_body[:1600],
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )

        sms_log = {
            "id": str(uuid.uuid4()),
            "type": "sms",
            "recipient": phone,
            "message": message_body[:200],
            "finding_id": body.finding_id,
            "incident_id": body.incident_id,
            "sent_by": current_user.get("id"),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "sms_sid": sms.sid
        }
        await db.notification_logs.insert_one(sms_log)

        return {
            "status": "success",
            "message": f"SMS enviado a {phone}",
            "sms_sid": sms.sid
        }
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar SMS: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
# CONFIG STATUS & WEBSOCKET INFO
# ═══════════════════════════════════════════════════════════════════════

@router.get("/notifications/config-status")
async def get_notification_config_status(current_user: dict = Depends(get_current_user)):
    """Check which notification services are configured."""
    return {
        "email": {"configured": bool(RESEND_API_KEY), "provider": "Resend"},
        "sms": {"configured": bool(twilio_client), "provider": "Twilio"},
        "websocket": {
            "active_connections": ws_manager.connection_count,
            "connected_users": len(ws_manager.connected_users),
        },
        "escalation": {"enabled": True, "interval_minutes": 30},
    }
