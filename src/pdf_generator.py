import re
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def get_ordinal_suffix(day: int) -> str:
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

def generate_cover_letter_pdf(
    cover_letter_text: str,
    output_path: Path,
    name: str = "ANTONIO GALASSO",
    phone: str = "+39 3780840950",
    email: str = "antogalassozerotre@gmail.com",
    github_handle: str = "AntGalasso",
    location: str = "Milano"
) -> Path:
    """
    Genera un PDF formattato identico al modello MotivationLetterGalasso.pdf.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch
    )
    
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        name="HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor="#1a1a1a"
    )
    
    meta_style = ParagraphStyle(
        name="MetaStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor="#333333"
    )
    
    body_style = ParagraphStyle(
        name="BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14.5,
        textColor="#222222",
        spaceAfter=10
    )
    
    story = []
    
    # Intestazione anagrafica
    story.append(Paragraph(name.upper(), header_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(phone, meta_style))
    story.append(Paragraph(email, meta_style))
    story.append(Paragraph(github_handle, meta_style))
    story.append(Paragraph(location, meta_style))
    story.append(Spacer(1, 8))
    
    # Data giornaliera dinamica (es. 05th Oct 2026)
    today = datetime.now()
    day_str = f"{today.day:02d}{get_ordinal_suffix(today.day)}"
    date_str = f"{day_str} {today.strftime('%b %Y')}"
    story.append(Paragraph(date_str, meta_style))
    story.append(Spacer(1, 14))
    
    # Pulizia corpo del testo
    paragraphs = [p.strip() for p in cover_letter_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in cover_letter_text.split("\n") if p.strip()]
        
    for p_text in paragraphs:
        clean_text = p_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(clean_text, body_style))
        
    doc.build(story)
    return output_path