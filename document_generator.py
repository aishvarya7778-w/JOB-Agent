import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem

def _add_bottom_border(paragraph):
    """Adds a subtle bottom border to a Word paragraph for clean section headers."""
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '333333')
    pBdr.append(bottom)
    pPr.append(pBdr)

# ==========================================
# DOCX BUILDERS
# ==========================================

def build_cv_docx(cv_data: dict, filepath: str):
    doc = Document()
    
    # Set standard ATS margins (0.6 inches)
    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.65)
        section.right_margin = Inches(0.65)
        
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    # Name Header
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_p.add_run(cv_data.get("name", "Aishvarya Sahu"))
    name_run.font.size = Pt(20)
    name_run.font.bold = True
    name_p.paragraph_format.space_after = Pt(2)
    name_p.paragraph_format.space_before = Pt(0)

    # Contact Info
    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_info = cv_data.get("contact_info", {})
    contact_parts = [
        contact_info.get("location", "Bhopal, India"),
        contact_info.get("phone", "+91 89824 22652"),
        contact_info.get("email", "sahuaishvarya.8786@gmail.com"),
        contact_info.get("linkedin", "linkedin.com/in/aishvarya-sahu"),
        contact_info.get("github", "github.com/aishvarya7778-w"),
        contact_info.get("portfolio", "sites.google.com/view/aishvarya7778")
    ]
    contact_text = "  |  ".join([p for p in contact_parts if p])
    c_run = contact_p.add_run(contact_text)
    c_run.font.size = Pt(9)
    c_run.font.color.rgb = RGBColor(80, 80, 80)
    contact_p.paragraph_format.space_after = Pt(8)

    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title.upper())
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(20, 50, 90)
        _add_bottom_border(p)
        return p

    # Summary
    if cv_data.get("summary"):
        add_section_header("Professional Summary")
        sp = doc.add_paragraph(cv_data["summary"])
        sp.paragraph_format.space_after = Pt(6)
        sp.paragraph_format.line_spacing = 1.15

    # Skills
    if cv_data.get("skills"):
        add_section_header("Technical Skills")
        for category, skill_list in cv_data["skills"].items():
            sp = doc.add_paragraph()
            sp.paragraph_format.space_after = Pt(2)
            c_run = sp.add_run(f"• {category}: ")
            c_run.bold = True
            if isinstance(skill_list, list):
                sp.add_run(", ".join(skill_list))
            else:
                sp.add_run(str(skill_list))

    # Projects
    if cv_data.get("projects"):
        add_section_header("Key Technical Projects")
        for proj in cv_data["projects"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(1)
            t_run = p.add_run(proj.get("title", ""))
            t_run.bold = True
            t_run.font.size = Pt(10.5)
            if proj.get("tech_stack"):
                stack_run = p.add_run(f"  |  Tech Stack: {proj['tech_stack']}")
                stack_run.italic = True
                stack_run.font.size = Pt(9.5)
                stack_run.font.color.rgb = RGBColor(70, 70, 70)
                
            for bullet in proj.get("bullets", []):
                bp = doc.add_paragraph(style='List Bullet')
                bp.paragraph_format.space_after = Pt(1)
                bp.paragraph_format.space_before = Pt(0)
                bp.paragraph_format.line_spacing = 1.1
                bp.add_run(bullet)

    # Education
    if cv_data.get("education"):
        add_section_header("Education")
        for edu in cv_data["education"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(1)
            deg_run = p.add_run(edu.get("degree", ""))
            deg_run.bold = True
            if edu.get("institution"):
                p.add_run(f" — {edu['institution']}")
            if edu.get("details"):
                dp = doc.add_paragraph(edu["details"])
                dp.paragraph_format.space_after = Pt(2)
                dp.paragraph_format.space_before = Pt(0)
                dp.runs[0].font.size = Pt(9)
                dp.runs[0].font.color.rgb = RGBColor(80, 80, 80)

    # Certifications
    if cv_data.get("certifications"):
        add_section_header("Certifications")
        for cert in cv_data["certifications"]:
            cp = doc.add_paragraph(style='List Bullet')
            cp.paragraph_format.space_after = Pt(1)
            cp.add_run(cert)

    # Achievements
    if cv_data.get("achievements"):
        add_section_header("Honors & Hackathon Achievements")
        for ach in cv_data["achievements"]:
            ap = doc.add_paragraph(style='List Bullet')
            ap.paragraph_format.space_after = Pt(1)
            ap.add_run(ach)

    # Leadership
    if cv_data.get("leadership"):
        add_section_header("Leadership & Activities")
        for lead in cv_data["leadership"]:
            lp = doc.add_paragraph(style='List Bullet')
            lp.paragraph_format.space_after = Pt(1)
            lp.add_run(lead)

    doc.save(filepath)


def build_cover_letter_docx(letter_data: dict, filepath: str):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(40, 40, 40)

    # Header
    name_p = doc.add_paragraph()
    n_run = name_p.add_run(letter_data.get("candidate_name", "Aishvarya Sahu"))
    n_run.font.size = Pt(18)
    n_run.font.bold = True
    name_p.paragraph_format.space_after = Pt(2)

    contact_p = doc.add_paragraph()
    contact_parts = [
        letter_data.get("location", "Bhopal, India"),
        letter_data.get("phone", "+91 89824 22652"),
        letter_data.get("email", "sahuaishvarya.8786@gmail.com"),
        letter_data.get("linkedin", "linkedin.com/in/aishvarya-sahu")
    ]
    c_run = contact_p.add_run(" | ".join(contact_parts))
    c_run.font.size = Pt(9.5)
    c_run.font.color.rgb = RGBColor(90, 90, 90)
    contact_p.paragraph_format.space_after = Pt(16)
    _add_bottom_border(contact_p)

    # Date
    date_p = doc.add_paragraph(letter_data.get("date", "September 2026"))
    date_p.paragraph_format.space_after = Pt(12)

    # Recipient
    recip_p = doc.add_paragraph()
    recip_p.paragraph_format.space_after = Pt(12)
    recip_p.paragraph_format.line_spacing = 1.15
    recip_p.add_run(f"Hiring Team / Recruitment\n{letter_data.get('company_name', 'Company')}\n{letter_data.get('job_location', 'Hyderabad, India')}")

    # Subject line
    subj_p = doc.add_paragraph()
    subj_p.paragraph_format.space_after = Pt(14)
    s_run = subj_p.add_run(f"Subject: Application for {letter_data.get('job_title', 'AI Engineer')} Role")
    s_run.bold = True
    s_run.font.color.rgb = RGBColor(20, 50, 90)

    # Salutation
    sal_p = doc.add_paragraph(letter_data.get("salutation", f"Dear Hiring Team at {letter_data.get('company_name', 'the Company')},"))
    sal_p.paragraph_format.space_after = Pt(10)

    # Body Paragraphs
    for para in letter_data.get("paragraphs", []):
        p = doc.add_paragraph(para)
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.line_spacing = 1.18

    # Sign-off
    close_p = doc.add_paragraph("Sincerely,\n\n")
    close_p.paragraph_format.space_before = Pt(8)
    close_p.paragraph_format.space_after = Pt(0)
    
    sig_p = doc.add_paragraph(letter_data.get("candidate_name", "Aishvarya Sahu"))
    sig_p.runs[0].bold = True

    doc.save(filepath)


# ==========================================
# REPORTLAB PDF BUILDERS
# ==========================================

def build_cv_pdf(cv_data: dict, filepath: str):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CVTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#112233')
    )
    contact_style = ParagraphStyle(
        'CVContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor('#445566')
    )
    header_style = ParagraphStyle(
        'CVHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#103366'),
        spaceBefore=7,
        spaceAfter=3
    )
    subhead_style = ParagraphStyle(
        'CVSubhead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#222222')
    )
    body_style = ParagraphStyle(
        'CVBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#222222')
    )
    bullet_style = ParagraphStyle(
        'CVBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=11.5,
        leftIndent=12,
        firstLineIndent=-8,
        textColor=colors.HexColor('#222222')
    )

    story = []

    # Title & Contact
    story.append(Paragraph(cv_data.get("name", "Aishvarya Sahu"), title_style))
    story.append(Spacer(1, 2))
    
    contact_info = cv_data.get("contact_info", {})
    contact_parts = [
        contact_info.get("location", "Bhopal, India"),
        contact_info.get("phone", "+91 89824 22652"),
        contact_info.get("email", "sahuaishvarya.8786@gmail.com"),
        contact_info.get("linkedin", "linkedin.com/in/aishvarya-sahu"),
        contact_info.get("github", "github.com/aishvarya7778-w"),
        contact_info.get("portfolio", "sites.google.com/view/aishvarya7778")
    ]
    contact_text = "  |  ".join([p for p in contact_parts if p])
    story.append(Paragraph(contact_text, contact_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#103366'), spaceBefore=2, spaceAfter=4))

    def add_pdf_header(heading):
        story.append(Paragraph(heading.upper(), header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceBefore=1, spaceAfter=4))

    # Summary
    if cv_data.get("summary"):
        add_pdf_header("Professional Summary")
        story.append(Paragraph(cv_data["summary"], body_style))
        story.append(Spacer(1, 3))

    # Skills
    if cv_data.get("skills"):
        add_pdf_header("Technical Skills")
        for category, skill_list in cv_data["skills"].items():
            if isinstance(skill_list, list):
                skills_str = ", ".join(skill_list)
            else:
                skills_str = str(skill_list)
            p_text = f"<b>&bull; {category}:</b> {skills_str}"
            story.append(Paragraph(p_text, body_style))
            story.append(Spacer(1, 2))

    # Projects
    if cv_data.get("projects"):
        add_pdf_header("Key Technical Projects")
        for proj in cv_data["projects"]:
            t = proj.get("title", "")
            s = proj.get("tech_stack", "")
            heading_text = f"<b>{t}</b>" + (f" <font size=8.5 color='#555555'>| Tech Stack: {s}</font>" if s else "")
            story.append(Paragraph(heading_text, subhead_style))
            story.append(Spacer(1, 1))
            for b in proj.get("bullets", []):
                story.append(Paragraph(f"&bull; {b}", bullet_style))
                story.append(Spacer(1, 1))
            story.append(Spacer(1, 3))

    # Education
    if cv_data.get("education"):
        add_pdf_header("Education")
        for edu in cv_data["education"]:
            d = edu.get("degree", "")
            inst = edu.get("institution", "")
            details = edu.get("details", "")
            story.append(Paragraph(f"<b>{d}</b> — {inst}", subhead_style))
            if details:
                story.append(Paragraph(f"<font size=8.5 color='#555555'>{details}</font>", body_style))
            story.append(Spacer(1, 2))

    # Certifications
    if cv_data.get("certifications"):
        add_pdf_header("Certifications")
        for cert in cv_data["certifications"]:
            story.append(Paragraph(f"&bull; {cert}", bullet_style))
            story.append(Spacer(1, 1))

    # Achievements
    if cv_data.get("achievements"):
        add_pdf_header("Honors & Hackathon Achievements")
        for ach in cv_data["achievements"]:
            story.append(Paragraph(f"&bull; {ach}", bullet_style))
            story.append(Spacer(1, 1))

    # Leadership
    if cv_data.get("leadership"):
        add_pdf_header("Leadership & Activities")
        for lead in cv_data["leadership"]:
            story.append(Paragraph(f"&bull; {lead}", bullet_style))
            story.append(Spacer(1, 1))

    doc.build(story)


def build_cover_letter_pdf(letter_data: dict, filepath: str):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CLTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#112233')
    )
    contact_style = ParagraphStyle(
        'CLContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#556677')
    )
    date_style = ParagraphStyle(
        'CLDate',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#333333'),
        spaceBefore=8,
        spaceAfter=8
    )
    recipient_style = ParagraphStyle(
        'CLRecipient',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#222222'),
        spaceAfter=10
    )
    subject_style = ParagraphStyle(
        'CLSubject',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#103366'),
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'CLBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#222222'),
        spaceAfter=10
    )

    story = []

    # Header
    story.append(Paragraph(letter_data.get("candidate_name", "Aishvarya Sahu"), title_style))
    contact_parts = [
        letter_data.get("location", "Bhopal, India"),
        letter_data.get("phone", "+91 89824 22652"),
        letter_data.get("email", "sahuaishvarya.8786@gmail.com"),
        letter_data.get("linkedin", "linkedin.com/in/aishvarya-sahu")
    ]
    story.append(Spacer(1, 2))
    story.append(Paragraph(" | ".join(contact_parts), contact_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#103366'), spaceBefore=2, spaceAfter=8))

    # Date
    story.append(Paragraph(letter_data.get("date", "September 2026"), date_style))

    # Recipient
    recip_text = f"Hiring Team / Recruitment<br/>{letter_data.get('company_name', 'Company')}<br/>{letter_data.get('job_location', 'Hyderabad, India')}"
    story.append(Paragraph(recip_text, recipient_style))

    # Subject
    story.append(Paragraph(f"<b>Subject: Application for {letter_data.get('job_title', 'AI Engineer')} Role</b>", subject_style))

    # Salutation
    story.append(Paragraph(letter_data.get("salutation", f"Dear Hiring Team,"), body_style))

    # Paragraphs
    for p_text in letter_data.get("paragraphs", []):
        story.append(Paragraph(p_text, body_style))

    # Sign-off
    story.append(Spacer(1, 8))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>{letter_data.get('candidate_name', 'Aishvarya Sahu')}</b>", body_style))

    doc.build(story)
