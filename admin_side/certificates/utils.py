from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

def generate_single_certificate(name, template_path, x, y, font_size, course_name=None, institution_name=None, logo_path=None, **kwargs):
    """
    Generates a single PDF certificate in memory with student name and optional course/institution details.
    
    Args:
        name: Student's full name
        template_path: Path to the certificate template image
        x: X coordinate for name placement (from left)
        y: Y coordinate for name placement (from bottom - ReportLab coordinate system)
        font_size: Font size for the student name
        course_name: Optional course name to display
        institution_name: Optional institution name to display
        logo_path: Optional path to company logo image
    """
    buffer = BytesIO()
    
    # A4 Landscape dimensions in points (1 inch = 72 points)
    page_width, page_height = landscape(A4)  # 842 x 595 points
    
    # Initialize Canvas
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    # SAFETY CHECK: Ensure Y is within page boundaries
    if y > page_height - 50:
        y = page_height / 2
    elif y < 50:
        y = page_height / 2
    
    # 1. Draw the Background Image FIRST
    try:
        bg = ImageReader(template_path)
        c.drawImage(bg, 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"Error loading certificate template image: {e}")
        c.setStrokeColorRGB(0.2, 0.4, 0.7)
        c.setLineWidth(3)
        c.rect(20, 20, page_width-40, page_height-40)

    # 2. Draw Company Logo if provided (Top Right)
    if logo_path:
        try:
            logo = ImageReader(logo_path)
            # Define logo size and position
            logo_w = 80
            logo_h = 80
            logo_x = page_width - logo_w - 50
            logo_y = page_height - logo_h - 50
            c.drawImage(logo, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error loading logo image: {e}")

    # 3. Draw the Student Name
    actual_font_size = max(font_size, 40)
    c.setFont("Helvetica-Bold", actual_font_size)
    c.setFillColorRGB(0, 0, 0)
    
    text_width = c.stringWidth(name, "Helvetica-Bold", actual_font_size)
    x_centered = (page_width - text_width) / 2
    
    # Draw an opaque white background band behind the name to cover template placeholders
    padding = 20
    cover_width = page_width * 0.85
    cover_x = (page_width - cover_width) / 2
    cover_height = actual_font_size + (4 * padding)
    cover_y = y - (2 * padding)
    c.setFillColorRGB(1, 1, 1)
    c.rect(cover_x, cover_y, cover_width, cover_height, fill=1, stroke=0)

    # Draw the student name on top
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x_centered, y, name)
    
    # 4. Add course name if provided
    if course_name:
        c.setFont("Helvetica", 20)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        success_text = "has successfully completed the program in"
        c.drawString((page_width - c.stringWidth(success_text, "Helvetica", 20)) / 2, y - 50, success_text)
        
        c.setFont("Helvetica-Bold", 32)
        c.setFillColorRGB(0, 0.4, 0.8)
        c.drawString((page_width - c.stringWidth(course_name, "Helvetica-Bold", 32)) / 2, y - 100, course_name)
    
    # 5. Add institution details (Issue date removed per request)
    info_y = y - 160
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    
    if institution_name:
        line = f"Organized by: {institution_name}"
        c.drawString((page_width - c.stringWidth(line, "Helvetica", 16)) / 2, info_y, line)


    
    # 6. Finalize
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer 