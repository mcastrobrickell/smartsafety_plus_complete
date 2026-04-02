"""SmartSafety+ - Email utilities"""

def generate_alert_html(finding: dict = None, incident: dict = None, custom_message: str = None) -> str:
    """Generate HTML email template for safety alerts"""
    
    severity_colors = {
        'critico': '#EF4444', 'critical': '#EF4444',
        'alto': '#F97316', 'high': '#F97316',
        'medio': '#F59E0B', 'medium': '#F59E0B',
        'bajo': '#10B981', 'low': '#10B981'
    }
    
    if finding:
        severity = finding.get('severity', 'medio')
        color = severity_colors.get(severity.lower(), '#64748B')
        content = f"""
        <div style="background-color: {color}; color: white; padding: 12px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 18px;">⚠️ Hallazgo de Seguridad - {severity.upper()}</h2>
        </div>
        <div style="padding: 20px; background: #f8fafc; border-radius: 0 0 8px 8px;">
            <p style="margin: 0 0 10px;"><strong>Categoria:</strong> {finding.get('category', 'General')}</p>
            <p style="margin: 0 0 10px;"><strong>Descripcion:</strong> {finding.get('description', 'Sin descripcion')}</p>
            <p style="margin: 0 0 10px;"><strong>Referencia Normativa:</strong> {finding.get('normative_reference', 'N/A')}</p>
            <p style="margin: 0;"><strong>Accion Correctiva:</strong> {finding.get('corrective_action', 'Pendiente')}</p>
        </div>
        """
    elif incident:
        severity = incident.get('severity', 'medio')
        color = severity_colors.get(severity.lower(), '#64748B')
        content = f"""
        <div style="background-color: {color}; color: white; padding: 12px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 18px;">🚨 Incidente Reportado - {severity.upper()}</h2>
        </div>
        <div style="padding: 20px; background: #f8fafc; border-radius: 0 0 8px 8px;">
            <p style="margin: 0 0 10px;"><strong>Titulo:</strong> {incident.get('title', 'Sin titulo')}</p>
            <p style="margin: 0 0 10px;"><strong>Descripcion:</strong> {incident.get('description', 'Sin descripcion')}</p>
            <p style="margin: 0 0 10px;"><strong>Ubicacion:</strong> {incident.get('location', 'N/A')}</p>
            <p style="margin: 0;"><strong>Estado:</strong> {incident.get('status', 'Abierto')}</p>
        </div>
        """
    else:
        content = f"""
        <div style="padding: 20px; background: #f8fafc; border-radius: 8px;">
            <p style="margin: 0;">{custom_message or 'Notificacion del sistema SmartSafety+'}</p>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; margin: 0; padding: 20px; background-color: #f1f5f9;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3B82F6 0%, #1d4ed8 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    <span style="color: white;">Smart</span><span style="color: #F97316;">Safety+</span>
                </h1>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0; font-size: 12px;">Sistema de Gestion de Seguridad</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 20px;">
                {content}
            </div>
            
            <!-- Footer -->
            <div style="background: #f8fafc; padding: 15px 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; font-size: 12px; color: #64748b;">
                    Este es un mensaje automatico de SmartSafety+ Enterprise 2026
                </p>
                <p style="margin: 5px 0 0; font-size: 11px; color: #94a3b8;">
                    No responda a este correo
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


