"""
SmartSafety+ - PDF Generation Utilities
"""
from fpdf import FPDF
from datetime import datetime


class SafetyPDF(FPDF):
    """Custom PDF class for SmartSafety+ reports"""
    
    def __init__(self, title="SmartSafety+ Report", org_name="SmartSafety+ Enterprise"):
        super().__init__()
        self.title = title
        self.org_name = org_name
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 8, self.org_name, ln=True, align='C')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, self.title, ln=True, align='C')
        self.set_draw_color(59, 130, 246)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'SmartSafety+ - Pagina {self.page_no()}', align='C')
    
    def section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(59, 130, 246)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f'  {title}', ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def add_field(self, label, value, width=95):
        self.set_font('Helvetica', 'B', 9)
        self.cell(width/2, 6, f'{label}:', align='L')
        self.set_font('Helvetica', '', 9)
        self.cell(width/2, 6, str(value) if value else 'N/A', ln=True)
    
    def add_table_row(self, cells, widths, header=False):
        if header:
            self.set_font('Helvetica', 'B', 9)
            self.set_fill_color(240, 240, 240)
        else:
            self.set_font('Helvetica', '', 9)
        
        for i, (cell, width) in enumerate(zip(cells, widths)):
            self.cell(width, 7, str(cell)[:30] if cell else '', border=1, fill=header)
        self.ln()
