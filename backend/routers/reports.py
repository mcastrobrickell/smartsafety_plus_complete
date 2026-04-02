"""SmartSafety+ - PDF Reports Router"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from config import db
from utils.auth import get_current_user
from utils.pdf import SafetyPDF
from datetime import datetime, timezone
import io

router = APIRouter(tags=["reports"])

@router.get("/reports/export-pdf")
async def export_report_pdf(report_type: str = "incidents", current_user: dict = Depends(get_current_user)):
    """Generate professional PDF report"""
    
    pdf = SafetyPDF(
        title=f"Reporte de {report_type.replace('-', ' ').title()}",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Report info
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.cell(0, 6, f"Generado por: {current_user.get('name', 'Admin')}", ln=True)
    pdf.ln(10)
    
    if report_type == "incidents":
        incidents = await db.incidents.find({}, {"_id": 0}).to_list(100)
        
        # Stats boxes
        total = len(incidents)
        open_count = len([i for i in incidents if i.get('status') == 'open'])
        critical = len([i for i in incidents if i.get('severity') in ['critico', 'critical']])
        
        pdf.add_stat_box("Total Incidentes", total, 10, pdf.get_y())
        pdf.add_stat_box("Abiertos", open_count, 60, pdf.get_y())
        pdf.add_stat_box("Criticos", critical, 110, pdf.get_y())
        pdf.ln(30)
        
        # Table
        pdf.add_section_title("Listado de Incidentes")
        headers = ["Titulo", "Severidad", "Estado", "Fecha"]
        widths = [70, 30, 30, 40]
        pdf.add_table_header(headers, widths)
        
        for i, inc in enumerate(incidents[:30]):
            pdf.add_table_row([
                inc.get('title', 'Sin titulo')[:25],
                inc.get('severity', 'N/A'),
                inc.get('status', 'N/A'),
                inc.get('reported_at', '')[:10]
            ], widths, fill=(i % 2 == 0))
    
    elif report_type == "findings":
        findings = await db.findings.find({}, {"_id": 0}).to_list(100)
        
        total = len(findings)
        critical = len([f for f in findings if f.get('severity') in ['critico', 'critical']])
        pending = len([f for f in findings if f.get('status') == 'pending'])
        
        pdf.add_stat_box("Total Hallazgos", total, 10, pdf.get_y())
        pdf.add_stat_box("Criticos", critical, 60, pdf.get_y())
        pdf.add_stat_box("Pendientes", pending, 110, pdf.get_y())
        pdf.ln(30)
        
        pdf.add_section_title("Hallazgos de Seguridad")
        headers = ["Categoria", "Descripcion", "Severidad", "Estado"]
        widths = [35, 80, 25, 25]
        pdf.add_table_header(headers, widths)
        
        for i, f in enumerate(findings[:30]):
            pdf.add_table_row([
                f.get('category', 'General')[:15],
                f.get('description', 'N/A')[:35],
                f.get('severity', 'N/A'),
                f.get('status', 'N/A')
            ], widths, fill=(i % 2 == 0))
    
    elif report_type == "epp":
        movements = await db.epp_movements.find({}, {"_id": 0}).to_list(100)
        
        total = len(movements)
        total_cost = sum(m.get('total_cost', 0) for m in movements)
        total_qty = sum(m.get('quantity', 0) for m in movements)
        
        pdf.add_stat_box("Movimientos", total, 10, pdf.get_y())
        pdf.add_stat_box("Unidades", total_qty, 60, pdf.get_y())
        pdf.add_stat_box(f"Costo Total", f"${total_cost:,.0f}", 110, pdf.get_y())
        pdf.ln(30)
        
        pdf.add_section_title("Movimientos de EPP")
        headers = ["Tipo", "Cantidad", "Costo Unit.", "Total", "Fecha"]
        widths = [35, 25, 30, 35, 35]
        pdf.add_table_header(headers, widths)
        
        for i, m in enumerate(movements[:30]):
            pdf.add_table_row([
                m.get('movement_type', 'N/A'),
                str(m.get('quantity', 0)),
                f"${m.get('unit_cost', 0):,.0f}",
                f"${m.get('total_cost', 0):,.0f}",
                m.get('created_at', '')[:10]
            ], widths, fill=(i % 2 == 0))
    
    elif report_type == "risk-matrix":
        matrices = await db.risk_matrices.find({}, {"_id": 0}).to_list(100)
        
        total_matrices = len(matrices)
        total_risks = sum(len(m.get('risks', [])) for m in matrices)
        critical_risks = sum(
            len([r for r in m.get('risks', []) if r.get('risk_level') in ['Critico', 'Alto']])
            for m in matrices
        )
        
        pdf.add_stat_box("Matrices", total_matrices, 10, pdf.get_y())
        pdf.add_stat_box("Riesgos", total_risks, 60, pdf.get_y())
        pdf.add_stat_box("Criticos/Altos", critical_risks, 110, pdf.get_y())
        pdf.ln(30)
        
        for matrix in matrices[:5]:
            pdf.add_section_title(f"Matriz: {matrix.get('name', 'Sin nombre')}")
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 6, f"Area: {matrix.get('area', 'N/A')} | Proceso: {matrix.get('process', 'N/A')}", ln=True)
            pdf.ln(3)
            
            risks = matrix.get('risks', [])
            if risks:
                headers = ["Peligro", "Riesgo", "P", "S", "Nivel", "Estado"]
                widths = [40, 50, 15, 15, 25, 25]
                pdf.add_table_header(headers, widths)
                
                for i, r in enumerate(risks[:15]):
                    pdf.add_table_row([
                        r.get('hazard', 'N/A')[:18],
                        r.get('risk_description', 'N/A')[:22],
                        str(r.get('probability', '-')),
                        str(r.get('severity', '-')),
                        r.get('risk_level', 'N/A'),
                        r.get('status', 'N/A')
                    ], widths, fill=(i % 2 == 0))
            pdf.ln(10)
    
    # Output PDF
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    filename = f"reporte-{report_type}-{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


