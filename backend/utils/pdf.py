"""
SmartSafety+ - Enhanced PDF Utilities
Professional PDF generation with cover page, executive summary, and modern styling.
"""
from fpdf import FPDF
from datetime import datetime
from pathlib import Path

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


class SafetyPDF(FPDF):
    """Professional PDF generator for SmartSafety+ reports."""

    def __init__(self, title="Reporte de Seguridad", org_name="SmartSafety+", subtitle=None):
        super().__init__()
        self.title_text = title
        self.org_name = org_name
        self.subtitle = subtitle
        self.set_auto_page_break(auto=True, margin=15)

    # ── Header / Footer ──────────────────────────────────────────

    def header(self):
        if self.page_no() == 1 and hasattr(self, '_has_cover') and self._has_cover:
            return  # Skip header on cover page

        # Logo or brand badge
        self.set_fill_color(0, 229, 255)  # Cyan
        self.rect(10, 8, 28, 12, 'F')
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(5, 7, 10)
        self.set_xy(12, 11)
        self.cell(0, 0, 'SS+')

        # Try to load org logo
        logo_path = None
        for ext in ['png', 'jpg', 'jpeg', 'webp']:
            candidates = list(UPLOADS_DIR.glob(f"logo_*.{ext}"))
            if candidates:
                logo_path = candidates[0]
                break
        if logo_path and logo_path.exists():
            try:
                self.image(str(logo_path), 42, 6, 18)
            except Exception:
                pass

        # Title
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 14)
        self.set_xy(logo_path and 64 or 42, 10)
        self.cell(0, 10, self.title_text)

        # Org name
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 116, 139)
        self.set_xy(logo_path and 64 or 42, 18)
        self.cell(0, 5, self.org_name)

        # Separator line
        self.set_draw_color(0, 229, 255)
        self.set_line_width(0.5)
        self.line(10, 26, 200, 26)
        self.ln(22)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100, 116, 139)
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.cell(0, 10, f'SmartSafety+ | {self.org_name} | {date_str} | Pag {self.page_no()}/{{nb}}', align='C')

    # ── Cover Page ───────────────────────────────────────────────

    def add_cover_page(self, generated_by="Admin", period=None):
        """Add a professional cover page."""
        self._has_cover = True
        self.alias_nb_pages()
        self.add_page()

        # Background gradient (dark area)
        self.set_fill_color(5, 7, 10)
        self.rect(0, 0, 210, 120, 'F')

        # Cyan accent bar
        self.set_fill_color(0, 229, 255)
        self.rect(0, 118, 210, 3, 'F')

        # Brand
        self.set_text_color(248, 250, 252)
        self.set_font('Helvetica', 'B', 32)
        self.set_xy(20, 35)
        self.cell(0, 15, 'SmartSafety+')

        # Title
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(0, 229, 255)
        self.set_xy(20, 55)
        self.multi_cell(170, 10, self.title_text)

        # Subtitle
        if self.subtitle:
            self.set_font('Helvetica', '', 12)
            self.set_text_color(148, 163, 184)
            self.set_xy(20, self.get_y() + 5)
            self.cell(0, 8, self.subtitle)

        # Org name
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(248, 250, 252)
        self.set_xy(20, 95)
        self.cell(0, 8, self.org_name)

        # Metadata box
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', '', 11)
        y_start = 135

        meta = [
            ("Generado por", generated_by),
            ("Fecha", datetime.now().strftime('%d de %B de %Y')),
        ]
        if period:
            meta.append(("Período", period))
        meta.append(("Sistema", "SmartSafety+ v2.1"))

        for label, value in meta:
            self.set_xy(20, y_start)
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(100, 116, 139)
            self.cell(45, 8, f"{label}:")
            self.set_font('Helvetica', '', 10)
            self.set_text_color(30, 41, 59)
            self.cell(0, 8, value)
            y_start += 10

        # Confidential notice
        self.set_xy(20, 260)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, "CONFIDENCIAL - Este documento contiene información reservada de seguridad operativa.")

    # ── Executive Summary ────────────────────────────────────────

    def add_executive_summary(self, stats: dict):
        """Add executive summary page with key metrics."""
        self.add_page()
        self.add_section_title("RESUMEN EJECUTIVO", (0, 229, 255))
        self.ln(5)

        # Stats grid (2 rows of 3)
        metrics = [
            ("Incidentes Totales", stats.get("total_incidents", 0), (37, 99, 235)),
            ("Incidentes Abiertos", stats.get("open_incidents", 0), (239, 68, 68)),
            ("Hallazgos Críticos", stats.get("critical_findings", 0), (239, 68, 68)),
            ("Scans Realizados", stats.get("total_scans", 0), (0, 229, 255)),
            ("Acciones Pendientes", stats.get("pending_actions", 0), (249, 115, 22)),
            ("Tasa Resolución", f"{stats.get('resolution_rate', 0):.0f}%", (34, 197, 94)),
        ]

        x_start = 10
        y_start = self.get_y() + 5
        box_w = 60
        box_h = 28
        gap = 3

        for i, (label, value, color) in enumerate(metrics):
            col = i % 3
            row = i // 3
            x = x_start + col * (box_w + gap)
            y = y_start + row * (box_h + gap)

            # Box background
            self.set_fill_color(248, 250, 252)
            self.rect(x, y, box_w, box_h, 'F')

            # Color accent bar
            self.set_fill_color(*color)
            self.rect(x, y, 3, box_h, 'F')

            # Value
            self.set_font('Helvetica', 'B', 18)
            self.set_text_color(30, 41, 59)
            self.set_xy(x + 8, y + 4)
            self.cell(box_w - 10, 10, str(value))

            # Label
            self.set_font('Helvetica', '', 8)
            self.set_text_color(100, 116, 139)
            self.set_xy(x + 8, y + 16)
            self.cell(box_w - 10, 6, label)

        self.set_y(y_start + 2 * (box_h + gap) + 10)

    # ── Components ───────────────────────────────────────────────

    def add_section_title(self, title, color=(59, 130, 246)):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*color)
        self.cell(0, 10, title, ln=True)
        self.set_text_color(30, 41, 59)

    def add_stat_box(self, label, value, x, y, width=45):
        self.set_xy(x, y)
        self.set_fill_color(248, 250, 252)
        self.rect(x, y, width, 20, 'F')
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 116, 139)
        self.set_xy(x + 3, y + 3)
        self.cell(0, 5, label)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 41, 59)
        self.set_xy(x + 3, y + 10)
        self.cell(0, 5, str(value))

    def add_table_header(self, headers, widths):
        self.set_fill_color(5, 7, 10)
        self.set_text_color(0, 229, 255)
        self.set_font('Helvetica', 'B', 8)
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, border=0, fill=True, align='C')
        self.ln()
        self.set_text_color(30, 41, 59)

    def add_table_row(self, cells, widths, fill=False):
        if fill:
            self.set_fill_color(248, 250, 252)
        else:
            self.set_fill_color(255, 255, 255)
        self.set_font('Helvetica', '', 8)
        for i, cell in enumerate(cells):
            text = str(cell)[:30] if len(str(cell)) > 30 else str(cell)
            self.cell(widths[i], 7, text, border=0, fill=True, align='L')
        self.ln()
        # Subtle separator
        self.set_draw_color(230, 230, 230)
        self.line(10, self.get_y(), 200, self.get_y())

    def add_severity_badge(self, severity):
        colors = {
            'critico': (239, 68, 68), 'critical': (239, 68, 68),
            'alto': (249, 115, 22), 'high': (249, 115, 22),
            'medio': (245, 158, 11), 'medium': (245, 158, 11),
            'bajo': (16, 185, 129), 'low': (16, 185, 129)
        }
        color = colors.get(severity.lower(), (100, 116, 139))
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 7)
        self.cell(20, 5, severity.upper(), fill=True, align='C')
        self.set_text_color(30, 41, 59)

    def add_info_block(self, title, text, color=(59, 130, 246)):
        """Add a highlighted info block with border."""
        self.set_fill_color(color[0], color[1], color[2])
        self.rect(10, self.get_y(), 3, 20, 'F')
        self.set_xy(16, self.get_y() + 2)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*color)
        self.cell(0, 6, title, ln=True)
        self.set_xy(16, self.get_y())
        self.set_font('Helvetica', '', 9)
        self.set_text_color(30, 41, 59)
        self.multi_cell(180, 5, text[:500])
        self.ln(5)
