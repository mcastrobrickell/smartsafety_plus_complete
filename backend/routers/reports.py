"""
SmartSafety+ - Enhanced PDF Reports Router
Professional reports with cover page, executive summary, and charts.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from config import db
from utils.auth import get_current_user
from utils.pdf import SafetyPDF
from datetime import datetime, timezone
import io

router = APIRouter(tags=["reports"])


async def _get_global_stats():
    """Get global stats for executive summary."""
    total_incidents = await db.incidents.count_documents({})
    open_incidents = await db.incidents.count_documents({"status": "open"})
    critical_findings = await db.findings.count_documents({"severity": {"$in": ["critico", "critical"]}})
    total_findings = await db.findings.count_documents({})
    resolved_findings = await db.findings.count_documents({"status": {"$in": ["resolved", "closed"]}})
    pending_actions = await db.findings.count_documents({"status": "pending"})
    total_scans = await db.scans.count_documents({})
    resolution_rate = (resolved_findings / total_findings * 100) if total_findings > 0 else 0

    return {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "critical_findings": critical_findings,
        "total_findings": total_findings,
        "resolved_findings": resolved_findings,
        "pending_actions": pending_actions,
        "total_scans": total_scans,
        "resolution_rate": resolution_rate,
    }


@router.get("/reports/executive")
async def export_executive_report(
    current_user: dict = Depends(get_current_user)
):
    """
    Generate comprehensive executive report with cover page,
    summary, incidents, findings, and EPP data.
    """
    # Get organization
    org = await db.organizations.find_one({}, {"_id": 0})
    org_name = org.get("name", "SmartSafety+") if org else "SmartSafety+"

    stats = await _get_global_stats()

    pdf = SafetyPDF(
        title="Reporte Ejecutivo de Seguridad",
        org_name=org_name,
        subtitle="Resumen integral de gestión de seguridad operativa"
    )

    # ── Cover Page ──
    pdf.add_cover_page(
        generated_by=current_user.get("name", "Admin"),
        period=f"Al {datetime.now().strftime('%d/%m/%Y')}"
    )

    # ── Executive Summary ──
    pdf.add_executive_summary(stats)

    # ── Incidents Section ──
    pdf.add_page()
    pdf.add_section_title("1. INCIDENTES DE SEGURIDAD", (239, 68, 68))
    pdf.ln(3)

    incidents = await db.incidents.find({}, {"_id": 0}).sort("reported_at", -1).limit(30).to_list(30)

    if incidents:
        # Summary text
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Total: {stats['total_incidents']} incidentes | Abiertos: {stats['open_incidents']} | Últimos 30 registros:", ln=True)
        pdf.ln(3)

        headers = ["Título", "Severidad", "Categoría", "Ubicación", "Estado", "Fecha"]
        widths = [45, 20, 25, 30, 20, 25]
        pdf.add_table_header(headers, widths)

        for i, inc in enumerate(incidents):
            pdf.add_table_row([
                inc.get('title', 'N/A')[:20],
                inc.get('severity', 'N/A'),
                inc.get('category', 'N/A')[:12],
                inc.get('location', 'N/A')[:14],
                inc.get('status', 'N/A'),
                inc.get('reported_at', '')[:10]
            ], widths, fill=(i % 2 == 0))
    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.cell(0, 10, "No hay incidentes registrados.", ln=True)

    # ── Findings Section ──
    pdf.add_page()
    pdf.add_section_title("2. HALLAZGOS DE SEGURIDAD", (249, 115, 22))
    pdf.ln(3)

    findings = await db.findings.find({}, {"_id": 0}).sort("created_at", -1).limit(30).to_list(30)

    if findings:
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Total: {stats['total_findings']} | Críticos: {stats['critical_findings']} | Pendientes: {stats['pending_actions']}", ln=True)
        pdf.ln(3)

        headers = ["Categoría", "Descripción", "Severidad", "Referencia", "Estado"]
        widths = [30, 55, 20, 40, 20]
        pdf.add_table_header(headers, widths)

        for i, f in enumerate(findings):
            pdf.add_table_row([
                f.get('category', 'N/A')[:14],
                f.get('description', 'N/A')[:25],
                f.get('severity', 'N/A'),
                f.get('normative_reference', 'N/A')[:18],
                f.get('status', 'N/A')
            ], widths, fill=(i % 2 == 0))

    # ── EPP Section ──
    pdf.add_page()
    pdf.add_section_title("3. GESTIÓN DE EPP", (0, 229, 255))
    pdf.ln(3)

    movements = await db.epp_movements.find({}, {"_id": 0}).sort("created_at", -1).limit(30).to_list(30)
    epp_total_cost = sum(m.get('total_cost', 0) for m in movements)
    epp_total_qty = sum(m.get('quantity', 0) for m in movements)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Movimientos: {len(movements)} | Unidades: {epp_total_qty} | Costo: ${epp_total_cost:,.0f}", ln=True)
    pdf.ln(3)

    if movements:
        headers = ["Tipo", "Item", "Cantidad", "Costo Unit.", "Total", "Fecha"]
        widths = [28, 42, 20, 25, 25, 25]
        pdf.add_table_header(headers, widths)

        for i, m in enumerate(movements):
            pdf.add_table_row([
                m.get('movement_type', 'N/A')[:12],
                m.get('epp_item_name', 'N/A')[:18] if m.get('epp_item_name') else 'N/A',
                str(m.get('quantity', 0)),
                f"${m.get('unit_cost', 0):,.0f}",
                f"${m.get('total_cost', 0):,.0f}",
                m.get('created_at', '')[:10]
            ], widths, fill=(i % 2 == 0))

    # ── Risk Matrices Section ──
    matrices = await db.risk_matrices.find({}, {"_id": 0}).limit(5).to_list(5)
    if matrices:
        pdf.add_page()
        pdf.add_section_title("4. MATRICES DE RIESGO", (168, 85, 247))
        pdf.ln(3)

        for matrix in matrices:
            pdf.add_info_block(
                f"Matriz: {matrix.get('name', 'N/A')}",
                f"Área: {matrix.get('area', 'N/A')} | Proceso: {matrix.get('process', 'N/A')} | "
                f"Riesgos: {len(matrix.get('risks', []))} | Estado: {matrix.get('status', 'N/A')}",
                (168, 85, 247)
            )

    # Output
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    filename = f"reporte-ejecutivo-{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/export-pdf")
async def export_report_pdf(
    report_type: str = "incidents",
    current_user: dict = Depends(get_current_user)
):
    """Generate PDF report by type (incidents, findings, epp, risk-matrix)."""
    org = await db.organizations.find_one({}, {"_id": 0})
    org_name = org.get("name", "SmartSafety+") if org else "SmartSafety+"

    pdf = SafetyPDF(
        title=f"Reporte de {report_type.replace('-', ' ').title()}",
        org_name=org_name
    )
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.cell(0, 6, f"Generado por: {current_user.get('name', 'Admin')}", ln=True)
    pdf.ln(10)

    if report_type == "incidents":
        incidents = await db.incidents.find({}, {"_id": 0}).to_list(100)
        total = len(incidents)
        open_c = len([i for i in incidents if i.get('status') == 'open'])
        critical = len([i for i in incidents if i.get('severity') in ['critico', 'critical']])

        pdf.add_stat_box("Total", total, 10, pdf.get_y())
        pdf.add_stat_box("Abiertos", open_c, 60, pdf.get_y())
        pdf.add_stat_box("Críticos", critical, 110, pdf.get_y())
        pdf.ln(30)

        pdf.add_section_title("Listado de Incidentes")
        headers = ["Título", "Severidad", "Estado", "Fecha"]
        widths = [70, 30, 30, 40]
        pdf.add_table_header(headers, widths)
        for i, inc in enumerate(incidents[:50]):
            pdf.add_table_row([
                inc.get('title', 'N/A')[:25], inc.get('severity', 'N/A'),
                inc.get('status', 'N/A'), inc.get('reported_at', '')[:10]
            ], widths, fill=(i % 2 == 0))

    elif report_type == "findings":
        findings = await db.findings.find({}, {"_id": 0}).to_list(100)
        total = len(findings)
        critical = len([f for f in findings if f.get('severity') in ['critico', 'critical']])
        pending = len([f for f in findings if f.get('status') == 'pending'])

        pdf.add_stat_box("Total", total, 10, pdf.get_y())
        pdf.add_stat_box("Críticos", critical, 60, pdf.get_y())
        pdf.add_stat_box("Pendientes", pending, 110, pdf.get_y())
        pdf.ln(30)

        pdf.add_section_title("Hallazgos de Seguridad")
        headers = ["Categoría", "Descripción", "Severidad", "Estado"]
        widths = [35, 80, 25, 25]
        pdf.add_table_header(headers, widths)
        for i, f in enumerate(findings[:50]):
            pdf.add_table_row([
                f.get('category', 'N/A')[:15], f.get('description', 'N/A')[:35],
                f.get('severity', 'N/A'), f.get('status', 'N/A')
            ], widths, fill=(i % 2 == 0))

    elif report_type == "epp":
        movements = await db.epp_movements.find({}, {"_id": 0}).to_list(100)
        total = len(movements)
        total_cost = sum(m.get('total_cost', 0) for m in movements)
        total_qty = sum(m.get('quantity', 0) for m in movements)

        pdf.add_stat_box("Movimientos", total, 10, pdf.get_y())
        pdf.add_stat_box("Unidades", total_qty, 60, pdf.get_y())
        pdf.add_stat_box(f"Costo", f"${total_cost:,.0f}", 110, pdf.get_y())
        pdf.ln(30)

        pdf.add_section_title("Movimientos de EPP")
        headers = ["Tipo", "Cantidad", "Costo Unit.", "Total", "Fecha"]
        widths = [35, 25, 30, 35, 35]
        pdf.add_table_header(headers, widths)
        for i, m in enumerate(movements[:50]):
            pdf.add_table_row([
                m.get('movement_type', 'N/A'), str(m.get('quantity', 0)),
                f"${m.get('unit_cost', 0):,.0f}", f"${m.get('total_cost', 0):,.0f}",
                m.get('created_at', '')[:10]
            ], widths, fill=(i % 2 == 0))

    elif report_type == "risk-matrix":
        matrices = await db.risk_matrices.find({}, {"_id": 0}).to_list(100)
        total_matrices = len(matrices)
        total_risks = sum(len(m.get('risks', [])) for m in matrices)

        pdf.add_stat_box("Matrices", total_matrices, 10, pdf.get_y())
        pdf.add_stat_box("Riesgos", total_risks, 60, pdf.get_y())
        pdf.ln(30)

        for matrix in matrices[:5]:
            pdf.add_section_title(f"Matriz: {matrix.get('name', 'N/A')}")
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 6, f"Área: {matrix.get('area', 'N/A')} | Proceso: {matrix.get('process', 'N/A')}", ln=True)
            pdf.ln(3)
            risks = matrix.get('risks', [])
            if risks:
                headers = ["Peligro", "Riesgo", "P", "S", "Nivel", "Estado"]
                widths = [40, 50, 15, 15, 25, 25]
                pdf.add_table_header(headers, widths)
                for i, r in enumerate(risks[:15]):
                    pdf.add_table_row([
                        r.get('hazard', 'N/A')[:18], r.get('risk_description', 'N/A')[:22],
                        str(r.get('probability', '-')), str(r.get('severity', '-')),
                        str(r.get('risk_level', 'N/A')), r.get('status', 'N/A')
                    ], widths, fill=(i % 2 == 0))
            pdf.ln(10)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    filename = f"reporte-{report_type}-{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
