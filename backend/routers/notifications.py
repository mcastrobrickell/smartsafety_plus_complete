"""SmartSafety+ - Notifications Router (Email, SMS, In-App)"""
from fastapi import APIRouter, HTTPException, Depends
from config import db, RESEND_API_KEY, SENDER_EMAIL, TWILIO_PHONE_NUMBER, twilio_client, resend, logger
from models.schemas import EmailNotificationRequest, SMSNotificationRequest
from utils.auth import get_current_user
from utils.email import generate_alert_html
from datetime import datetime, timezone
import uuid
import asyncio

router = APIRouter(tags=["notifications"])

@router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    critical_findings = await db.findings.find(
        {"severity": {"$in": ["critico", "critical"]}, "status": "pending"},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    open_incidents = await db.incidents.find(
        {"status": "open", "severity": {"$in": ["critical", "high", "critico", "alto"]}},
        {"_id": 0}
    ).limit(10).to_list(10)
    
    notifications = []
    for finding in critical_findings:
        notifications.append({
            "id": finding["id"],
            "type": "finding",
            "title": f"Hallazgo Crítico: {finding['category']}",
            "message": finding["description"][:100],
            "severity": "critical",
            "created_at": finding["created_at"]
        })
    
    for incident in open_incidents:
        notifications.append({
            "id": incident["id"],
            "type": "incident",
            "title": f"Incidente: {incident['title']}",
            "message": incident["description"][:100],
            "severity": incident["severity"],
            "created_at": incident["reported_at"]
        })
    
    return sorted(notifications, key=lambda x: x["created_at"], reverse=True)


@router.post("/notifications/send-alert")
async def send_notification_alert(request: EmailNotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send email notification for safety alerts"""
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    finding = None
    incident = None
    
    if request.finding_id:
        finding = await db.findings.find_one({"id": request.finding_id}, {"_id": 0})
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
    
    if request.incident_id:
        incident = await db.incidents.find_one({"id": request.incident_id}, {"_id": 0})
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
    
    html_content = generate_alert_html(finding, incident, request.custom_message)
    
    params = {
        "from": SENDER_EMAIL,
        "to": [request.recipient_email],
        "subject": request.subject,
        "html": html_content
    }
    
    try:
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        # Log notification
        notification_log = {
            "id": str(uuid.uuid4()),
            "type": "email",
            "recipient": request.recipient_email,
            "subject": request.subject,
            "finding_id": request.finding_id,
            "incident_id": request.incident_id,
            "sent_by": current_user.get("id"),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "email_id": email_result.get("id") if email_result else None
        }
        await db.notification_logs.insert_one(notification_log)
        
        return {
            "status": "success",
            "message": f"Email enviado a {request.recipient_email}",
            "email_id": email_result.get("id") if email_result else None
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar email: {str(e)}")


@router.post("/notifications/send-critical-alert")
async def send_critical_finding_alert(finding_id: str, current_user: dict = Depends(get_current_user)):
    """Send automatic alert for critical findings to all admins"""
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    finding = await db.findings.find_one({"id": finding_id}, {"_id": 0})
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Get all admin users
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
    
    return {
        "status": "success",
        "message": f"Alertas enviadas a {sent_count} administradores",
        "recipients": sent_count
    }


@router.post("/notifications/send-sms")
async def send_sms_notification(request: SMSNotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send SMS notification for safety alerts"""
    
    if not twilio_client:
        raise HTTPException(status_code=500, detail="SMS service not configured. Please add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to .env")
    
    if not TWILIO_PHONE_NUMBER:
        raise HTTPException(status_code=500, detail="Twilio phone number not configured")
    
    # Format phone number (ensure E.164 format)
    phone = request.phone_number
    if not phone.startswith('+'):
        phone = f"+{phone}"
    
    # Build message
    message_body = request.message
    
    if request.finding_id:
        finding = await db.findings.find_one({"id": request.finding_id}, {"_id": 0})
        if finding:
            message_body = f"🚨 ALERTA SmartSafety+\nHallazgo: {finding.get('category', 'N/A')}\nSeveridad: {finding.get('severity', 'N/A')}\n{finding.get('description', '')[:100]}"
    
    if request.incident_id:
        incident = await db.incidents.find_one({"id": request.incident_id}, {"_id": 0})
        if incident:
            message_body = f"🚨 INCIDENTE SmartSafety+\n{incident.get('title', 'N/A')}\nSeveridad: {incident.get('severity', 'N/A')}\nUbicacion: {incident.get('location', 'N/A')}"
    
    try:
        sms = await asyncio.to_thread(
            twilio_client.messages.create,
            body=message_body[:1600],  # Twilio limit
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        # Log SMS
        sms_log = {
            "id": str(uuid.uuid4()),
            "type": "sms",
            "recipient": phone,
            "message": message_body[:200],
            "finding_id": request.finding_id,
            "incident_id": request.incident_id,
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


@router.get("/notifications/config-status")
async def get_notification_config_status(current_user: dict = Depends(get_current_user)):
    """Check which notification services are configured"""
    return {
        "email": {
            "configured": bool(RESEND_API_KEY),
            "provider": "Resend"
        },
        "sms": {
            "configured": bool(twilio_client),
            "provider": "Twilio"
        }
    }

