# resume_generator.py

from fpdf import FPDF
import os

# --- Design Constants ---
SIDEBAR_WIDTH = 65
MARGIN = 10
PRIMARY_COLOR = (30, 30, 30)
SECONDARY_COLOR = (100, 100, 100)
ACCENT_COLOR = (79, 70, 229)
SIDEBAR_BG_COLOR = (243, 244, 246)
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
            try:
                self.image(image_path, x=self.left_col_x + (SIDEBAR_WIDTH - 40) / 2, y=MARGIN + 10, w=40, h=40)
                self.set_line_width(1)
                self.set_draw_color(*ACCENT_COLOR)
                self.ellipse(self.left_col_x + (SIDEBAR_WIDTH - 40) / 2, MARGIN + 10, 40, 40)
            except Exception as e:
                print(f"Could not process profile picture: {e}")
        self.set_y(MARGIN + 10 + 40 + 10)

    def add_sidebar_section(self, title, items):
        self.set_x(self.left_col_x)
        self.set_font(FONT_FAMILY, 'B', 11)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, title.upper(), 0, 1)
        self.set_draw_color(220, 220, 220)
        self.line(self.get_x(), self.get_y(), self.get_x() + SIDEBAR_WIDTH - MARGIN, self.get_y())
        self.ln(4)

        self.set_font(FONT_FAMILY, '', 9)
        self.set_text_color(*SECONDARY_COLOR)
        for item in items:
            self.set_x(self.left_col_x)
            self.multi_cell(SIDEBAR_WIDTH - MARGIN, 5, item, split_only=True)
            self.ln(1)
        self.ln(6)

    def add_main_header(self, name, title):
        self.set_y(MARGIN + 15)
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, 'B', 32)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 12, name, 0, 1)
        self.set_x(self.right_col_x)
        self.set_font(FONT_FAMILY, '', 14)
        self.set_text_color(*ACCENT_COLOR)
        self.cell(0, 8, title, 0, 1)

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

def create_resume_pdf(content, image_path, output_path, chosen_career):
    """Generates the newly designed two-column resume PDF."""
    if not content:
        print("--- ERROR: No content provided to PDF generator. ---")
        return
        
    pdf = ResumePDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=MARGIN)
    pdf.add_page()
    
    # --- LEFT SIDEBAR ---
    pdf.draw_sidebar()
    pdf.add_profile_picture(image_path)
    contact_info = [f"📧 {content.email}", f"📞 {content.phone}"]
    pdf.add_sidebar_section("Contact", contact_info)
    pdf.add_sidebar_section("Skills", content.skills)
    
    # --- RIGHT MAIN COLUMN ---
    pdf.add_main_header(content.full_name, chosen_career)
    
    pdf.add_main_section_title("Professional Summary")
    pdf.add_text_block(content.summary)

    pdf.add_main_section_title("Work Experience")
    for job in content.experiences:
        pdf.add_job(job.title, job.company, job.dates, job.description)

    pdf.add_main_section_title("Education")
    pdf.add_text_block(content.education)

    pdf.output(output_path)
    print(f"--- Elite Resume PDF generated at {output_path} ---")
