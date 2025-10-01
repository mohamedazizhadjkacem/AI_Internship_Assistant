"""
PDF Generation Utilities
Handles PDF creation for cover letters and other documents
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
import io
import re
from datetime import datetime

def create_cover_letter_pdf(content: str, applicant_name: str = "", job_title: str = "", company_name: str = "") -> bytes:
    """
    Create a professional PDF from cover letter content
    
    Args:
        content: The cover letter text content
        applicant_name: Name of the applicant (for filename purposes)
        job_title: Job title being applied for
        company_name: Company name
        
    Returns:
        PDF bytes that can be downloaded
    """
    
    # Create a BytesIO buffer to hold PDF data
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=14
    )
    
    signature_style = ParagraphStyle(
        'CustomSignature',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    # Build the document content
    story = []
    
    # Split content into lines
    lines = content.split('\n')
    
    current_paragraph = []
    in_header = True
    
    for line in lines:
        line = line.strip()
        
        if not line:  # Empty line
            if current_paragraph:
                # End current paragraph
                paragraph_text = ' '.join(current_paragraph)
                if in_header and any(keyword in line.lower() for keyword in ['dear', 'hiring manager', 'to whom']):
                    in_header = False
                
                style = header_style if in_header else body_style
                
                # Handle special formatting
                if paragraph_text.startswith('Dear '):
                    style = date_style
                elif paragraph_text.startswith('Sincerely') or paragraph_text.startswith('Best regards'):
                    style = signature_style
                
                story.append(Paragraph(paragraph_text, style))
                story.append(Spacer(1, 6))
                current_paragraph = []
        else:
            # Check if this looks like a date
            if re.match(r'^\w+\s+\d+,\s+\d{4}$', line):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    story.append(Paragraph(paragraph_text, header_style))
                    current_paragraph = []
                story.append(Paragraph(line, date_style))
                story.append(Spacer(1, 12))
                in_header = False
            # Check if this looks like an address or contact info
            elif any(keyword in line.lower() for keyword in ['@', 'phone:', 'email:', '|']) or line.startswith('Hiring Manager'):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    style = header_style if in_header else body_style
                    story.append(Paragraph(paragraph_text, style))
                    current_paragraph = []
                story.append(Paragraph(line, header_style))
                story.append(Spacer(1, 6))
            # Check for signature lines
            elif line.startswith('Sincerely') or line.startswith('Best regards'):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    story.append(Paragraph(paragraph_text, body_style))
                    current_paragraph = []
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, signature_style))
                story.append(Spacer(1, 24))  # Space for signature
            else:
                current_paragraph.append(line)
    
    # Handle any remaining content
    if current_paragraph:
        paragraph_text = ' '.join(current_paragraph)
        story.append(Paragraph(paragraph_text, signature_style))
    
    # Build the PDF
    doc.build(story)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def generate_pdf_filename(applicant_name: str = "", job_title: str = "", company_name: str = "") -> str:
    """
    Generate a professional filename for the cover letter PDF
    
    Args:
        applicant_name: Name of the applicant
        job_title: Job title being applied for
        company_name: Company name
        
    Returns:
        Formatted filename (safe for HTTP headers)
    """
    
    # Helper function to clean and truncate text
    def clean_and_truncate(text: str, max_length: int = 30) -> str:
        if not text:
            return ""
        # Remove newlines and extra spaces first
        text = ' '.join(text.split())
        # Remove special characters except alphanumeric, spaces, and hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        # Truncate if too long
        text = text[:max_length] if len(text) > max_length else text
        # Replace spaces with underscores
        return text.strip().replace(' ', '_')
    
    # Clean and format components with length limits
    name_part = clean_and_truncate(applicant_name, 25) if applicant_name else "Applicant"
    job_part = clean_and_truncate(job_title, 40) if job_title else "Position"
    company_part = clean_and_truncate(company_name, 25) if company_name else "Company"
    
    # Create filename with length safety
    if applicant_name and job_title and company_name:
        filename = f"{name_part}_{job_part}_{company_part}_Cover_Letter.pdf"
    elif job_title and company_name:
        filename = f"Cover_Letter_{job_part}_{company_part}.pdf"
    else:
        filename = f"Cover_Letter_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Final safety check - ensure total filename is reasonable
    if len(filename) > 150:  # Reasonable limit for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{name_part}_Cover_Letter_{timestamp}.pdf"
    
    return filename