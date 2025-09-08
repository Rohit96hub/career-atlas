# resume_generator.py

from fpdf import FPDF
import os

# --- Design Constants ---
SIDEBAR_WIDTH = 65
MARGIN = 10
PRIMARY_COLOR = (30, 30, 30)       # Near Black for text
SECONDARY_COLOR = (100, 100, 100) # Gray for subtitles
ACCENT_COLOR = (79, 70, 229)    # Indigo
SIDEBAR_BG_COLOR = (243, 244, 246) # Light Gray

FONT_FAMILY = "DejaVu"

class ResumePDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font_path = os.path.join(os.path.dirname(__file__), 'fonts')
        self.add_font(FONT_FAMILY, '', os.path.join(font_path, 'DejaVuSans.ttf'))
        self.add_font(FONT_FAMILY, 'B', os.path.join(font_path, 'DejaVuSans-Bold.ttf'))
        self.add_font(FONT_FAMILY, 'I', os.path.join(font_path, 'DejaVuSans-Oblique.ttf'))
        self.left_col_x = MARGIN
        self.right_col_x = MARGIN + SIDEBAR_WIDTH + 10

    def header(self): pass
    def footer(self): pass

    def draw_sidebar(self):
        self.set_fill_color(*SIDEBAR_BG_COLOR)
        self.rect(0, 0, SIDEBAR_WIDTH + MARGIN, self.h, 'F')
        self.set_x(self.left_col_x)

    def add_profile_picture(self, image_path):
        if image_path and os.path.exists(image_path):
            self.image(image_path, x=self.left_col_x, y=MARGIN + 10, w=SIDEBAR_WIDTH, h=SIDEBAR_WIDTH)

    def add_sidebar_section(self, title, items):
        self.set_x(self.left_col_x)
        self.set_font(FONT_FAMILY, 'B', 12)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, title.upper(), 0, 1)
        self.set_draw_color(*ACCENT_COLOR)
        self.line(self.get_x(), self.get_y(), self.get_x() + SIDEBAR_WIDTH - MARGIN, self.get_y())
        self.ln(4)

        self.set_font(FONT_FAMILY, '', 10)
        self.set_text_color(*SECONDARY_COLOR)
        for item in items:
            self.set_x(self.left_col_x)
            self.multi_cell(SIDEBAR_WIDTH - MARGIN, 5, f"• {item}", split_only=True)
        self.ln(8)

    def add_main_header(self, name):
        self.set_y(MARGIN + 15)
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, 'B', 32)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 12, name, 0, 1)
        self.set_x(self.right_col_x)

    def add_main_section_title(self, title):
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, 'B', 14)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, title.upper(), 0, 1)
        self.set_draw_color(*ACCENT_COLOR)
        self.line(self.get_x(), self.get_y(), self.get_x() + (self.w - SIDEBAR_WIDTH - 3 * MARGIN), self.get_y())
        self.ln(4)

    def add_job(self, title, company, dates, description_points):
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, 'B', 11)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 6, title, 0, 0, 'L')
        self.set_font(FONT_FAMILY, '', 11)
        self.set_text_color(*SECONDARY_COLOR)
        self.cell(0, 6, dates, 0, 1, 'R')
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, 'I', 11)
        self.cell(0, 6, company, 0, 1, 'L')
        self.ln(2)

        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, '', 10)
        self.set_text_color(50, 50, 50)
        for point in description_points:
            self.set_x(self.right_col_x)
            self.multi_cell(self.w - SIDEBAR_WIDTH - 3 * MARGIN, 5, f'• {point}', split_only=True)
        self.ln(5)

    def add_text_block(self, text):
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(self.w - SIDEBAR_WIDTH - 3 * MARGIN, 5, text, split_only=True)
        self.ln(5)

def create_resume_pdf(content, image_path, output_path):
    """Generates the newly designed two-column resume PDF."""
    pdf = ResumePDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=MARGIN)
    pdf.add_page()
    
    # --- LEFT SIDEBAR ---
    pdf.draw_sidebar()
    pdf.add_profile_picture(image_path)
    
    # Contact Info
    pdf.set_y(MARGIN + 10 + SIDEBAR_WIDTH + 10)
    contact_info = [f"📧 {content.email}", f"📞 {content.phone}"]
    pdf.add_sidebar_section("Contact", contact_info)

    # Skills
    pdf.add_sidebar_section("Skills", content.skills)

    # --- RIGHT MAIN COLUMN ---
    pdf.add_main_header(content.full_name)
    
    # Professional Summary
    pdf.add_main_section_title("Professional Summary")
    pdf.add_text_block(content.summary)

    # Work Experience
    pdf.add_main_section_title("Work Experience")
    for job in content.experiences:
        pdf.add_job(job.title, job.company, job.dates, job.description)

    # Education
    pdf.add_main_section_title("Education")
    pdf.add_text_block(content.education)

    pdf.output(output_path)
    print(f"--- Elite Resume PDF generated at {output_path} ---")

