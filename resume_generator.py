# resume_generator.py

from fpdf import FPDF

# Define constants for colors and fonts for a professional look
PRIMARY_COLOR = (22, 27, 34) # Dark Charcoal
ACCENT_COLOR = (99, 102, 241) # Indigo
SECONDARY_COLOR = (74, 85, 104) # Cool Gray
FONT_FAMILY = "Arial"

class ResumePDF(FPDF):
    def header(self):
        # No header needed for a resume
        pass

    def footer(self):
        # No footer needed for a resume
        pass

    def add_profile_picture(self, image_path):
        if image_path:
            self.image(image_path, x=15, y=20, w=40, h=40)
            # Create a circular mask (advanced technique not directly supported, so we use a circular frame as an effect)
            self.set_line_width(1)
            self.set_draw_color(*ACCENT_COLOR)
            self.ellipse(15, 20, 40, 40)

    def add_personal_info(self, name, email, phone):
        self.set_xy(65, 25)
        self.set_font(FONT_FAMILY, 'B', 24)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, name, 0, 1, 'L')
        self.set_x(65)
        self.set_font(FONT_FAMILY, '', 11)
        self.set_text_color(*SECONDARY_COLOR)
        self.cell(0, 8, f"Email: {email} | Phone: {phone}", 0, 1, 'L')

    def add_section_title(self, title):
        self.set_font(FONT_FAMILY, 'B', 14)
        self.set_text_color(*ACCENT_COLOR)
        self.cell(0, 12, title.upper(), 0, 1, 'L')
        self.set_line_width(0.5)
        self.set_draw_color(*ACCENT_COLOR)
        self.line(self.get_x(), self.get_y(), self.get_x() + 180, self.get_y())
        self.ln(5)

    def add_job(self, title, company, dates, description_points):
        self.set_font(FONT_FAMILY, 'B', 11)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 6, title, 0, 0, 'L')
        self.set_font(FONT_FAMILY, '', 11)
        self.cell(0, 6, dates, 0, 1, 'R')
        self.set_font(FONT_FAMILY, 'I', 11)
        self.set_text_color(*SECONDARY_COLOR)
        self.cell(0, 6, company, 0, 1, 'L')
        self.ln(2)
        
        self.set_font(FONT_FAMILY, '', 10)
        self.set_text_color(*PRIMARY_COLOR)
        for point in description_points:
            self.multi_cell(0, 5, f'• {point}')
        self.ln(5)

    def add_text_block(self, text):
        self.set_font(FONT_FAMILY, '', 10)
        self.set_text_color(*PRIMARY_COLOR)
        self.multi_cell(0, 5, text)
        self.ln(5)
        
    def add_skills(self, skills):
        self.set_font(FONT_FAMILY, '', 10)
        self.set_text_color(*PRIMARY_COLOR)
        skills_text = " | ".join(skills)
        self.multi_cell(0, 5, skills_text)
        self.ln(5)

def create_resume_pdf(content, image_path, output_path):
    """Generates a complete resume PDF from structured content."""
    pdf = ResumePDF('P', 'mm', 'A4')
    pdf.add_page()
    
    # Header Section
    pdf.add_profile_picture(image_path)
    pdf.add_personal_info(content.full_name, content.email, content.phone)
    pdf.ln(20) # Space after header

    # Professional Summary
    pdf.add_section_title("Professional Summary")
    pdf.add_text_block(content.summary)

    # Work Experience
    pdf.add_section_title("Work Experience")
    for job in content.experiences:
        pdf.add_job(job.title, job.company, job.dates, job.description)

    # Education
    pdf.add_section_title("Education")
    pdf.add_text_block(content.education)
    
    # Skills
    pdf.add_section_title("Skills")
    pdf.add_skills(content.skills)

    pdf.output(output_path)
    print(f"--- Resume PDF generated at {output_path} ---")
