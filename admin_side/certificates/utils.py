from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

def generate_single_certificate(name, template_path, x, y, font_size, course_name=None, institution_name=None):
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
    """
    buffer = BytesIO()
    
    # A4 Landscape dimensions in points (1 inch = 72 points)
    page_width, page_height = landscape(A4)  # 842 x 595 points
    
    # Initialize Canvas
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    # SAFETY CHECK: Ensure Y is within page boundaries
    # Page height is 595. If Y is > 595 or < 0, text won't show.
    # We'll clamp it to a safe range (e.g., 50 to 550)
    if y > page_height - 50:
        print(f"Warning: Y coordinate {y} is too high. Resetting to center.")
        y = page_height / 2
    elif y < 50:
        print(f"Warning: Y coordinate {y} is too low. Resetting to center.")
        y = page_height / 2
    
    # 1. Draw the Background Image FIRST
    try:
        bg = ImageReader(template_path)
        c.drawImage(bg, 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"Error loading certificate template image: {e}")
        # Draw a simple border if image fails
        c.setStrokeColorRGB(0.2, 0.4, 0.7)
        c.setLineWidth(3)
        c.rect(20, 20, page_width-40, page_height-40)

    # 2. Draw the Student Name ON TOP of the image
    # Use a larger font size to ensure visibility
    actual_font_size = max(font_size, 40)  # Minimum 40pt
    c.setFont("Helvetica-Bold", actual_font_size)
    c.setFillColorRGB(0, 0, 0)  # Pure black color
    
    # Calculate text width for centering
    text_width = c.stringWidth(name, "Helvetica-Bold", actual_font_size)
    
    # Always center the text horizontally
    x_centered = (page_width - text_width) / 2
    
    # Draw a semi-transparent white background behind the text for better visibility
    padding = 10
    c.setFillColorRGB(1, 1, 1, alpha=0.8)  # White with 80% opacity
    c.rect(x_centered - padding, y - padding, text_width + (2 * padding), actual_font_size + (2 * padding), fill=1, stroke=0)
    
    # Draw the student name in BLACK
    c.setFillColorRGB(0, 0, 0)  # Black
    c.drawString(x_centered, y, name)
    
    # 3. Add course name if provided (below the student name)
    if course_name:
        course_font_size = max(actual_font_size - 20, 20)  # Smaller than name but readable
        c.setFont("Helvetica", course_font_size)
        c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark gray
        course_text = f"{course_name}"
        course_width = c.stringWidth(course_text, "Helvetica", course_font_size)
        c.drawString((page_width - course_width) / 2, y - 50, course_text)
    
    # 4. Add institution name if provided (at bottom)
    if institution_name:
        inst_font_size = 16
        c.setFont("Helvetica-Oblique", inst_font_size)
        c.setFillColorRGB(0.3, 0.3, 0.3)  # Medium gray
        inst_width = c.stringWidth(institution_name, "Helvetica-Oblique", inst_font_size)
        c.drawString((page_width - inst_width) / 2, 60, institution_name)
    
    # 5. Finalize
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer 