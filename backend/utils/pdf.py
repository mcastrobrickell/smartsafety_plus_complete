"""SmartSafety+ - PDF utilities"""
from fpdf import FPDF

class SafetyPDF(FPDF):
    """Custom PDF class for SmartSafety+ reports"""
    
    def __init__(self, title="Reporte de Seguridad", org_name="SmartSafety+"):
        super().__init__()
        self.title_text = title
        self.org_name = org_name
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Logo placeholder (blue rectangle)
        self.set_fill_color(59, 130, 246)  # Blue
        self.rect(10, 8, 25, 12, 'F')
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 11)
        self.cell(0, 0, 'SS+')
        
        # Title
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 16)
        self.set_xy(40, 10)
        self.cell(0, 10, self.title_text)
        
        # Organization name
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 116, 139)
        self.set_xy(40, 18)
        self.cell(0, 5, self.org_name)
        
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f'SmartSafety+ Enterprise 2026 | Pagina {self.page_no()}', align='C')
        
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
        self.set_fill_color(59, 130, 246)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 9)
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, border=1, fill=True, align='C')
        self.ln()
        self.set_text_color(30, 41, 59)
        
    def add_table_row(self, cells, widths, fill=False):
        if fill:
            self.set_fill_color(248, 250, 252)
        self.set_font('Helvetica', '', 8)
        for i, cell in enumerate(cells):
            text = str(cell)[:30] if len(str(cell)) > 30 else str(cell)
            self.cell(widths[i], 7, text, border=1, fill=fill, align='L')
        self.ln()
        
    def add_severity_badge(self, severity):
        colors = {
            'critico': (239, 68, 68),
            'critical': (239, 68, 68),
            'alto': (249, 115, 22),
            'high': (249, 115, 22),
            'medio': (245, 158, 11),
            'medium': (245, 158, 11),
            'bajo': (16, 185, 129),
            'low': (16, 185, 129)
        }
        color = colors.get(severity.lower(), (100, 116, 139))
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 7)
        self.cell(20, 5, severity.upper(), fill=True, align='C')
        self.set_text_color(30, 41, 59)


