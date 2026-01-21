# generate_certificate_pillow_simple.py
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# ----- placeholders (easy to tweak) -----
TEMPLATE_PATH = "path/to/testttted.jpg"             # <-- your template image
OUTPUT_DIR = "output"
OUTPUT_FILENAME = "certificate_output.jpg"

# Default: center the student name horizontally under the template's green box area
NAME_COORDS = (100, 380)     # (x, y) for student name; X will be adjusted if center_name=True
BODY_COORDS = (100, 460)     # (x, y) where wrapped paragraph starts (moved up under name)
WRAP_WIDTH = 60              # characters per line for textwrap (adjust for layout)

NAME_FONT_PATH = "path/to/your-bold.ttf"  # e.g. Arial Bold
BODY_FONT_PATH = "path/to/your-regular.ttf"
NAME_FONT_SIZE = 80       # enlarged name font
BODY_FONT_SIZE = 22       # larger body text
LINE_SPACING = 8          # extra pixels between body lines
NAME_FILL = (0, 0, 0)     # color for name (black)
BODY_FILL = (40, 40, 40)  # darker body text color
# Option to center name horizontally (useful to keep it under the green box)
CENTER_NAME_BY_DEFAULT = True
# ----------------------------------------

# New: bounding boxes for auto-fitting text
NAME_BOX = (60, 320, 520, 140)   # (x, y, width, height) - area for student name
BODY_BOX = (60, 460, 520, 220)   # (x, y, width, height) - area for description paragraph


def _fit_font_size_for_text(draw, text, font_path, max_width, max_height, max_size=200, min_size=10):
    """Find the largest font size where `text` (single line) fits within max_width and max_height."""
    for size in range(max_size, min_size - 1, -1):
        try:
            f = ImageFont.truetype(font_path, size)
        except Exception:
            f = ImageFont.load_default()
        try:
            w = draw.textlength(text, font=f)
            h = f.getsize(text)[1]
        except Exception:
            bbox = draw.textbbox((0, 0), text, font=f)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        if w <= max_width and h <= max_height:
            return size
    return min_size


def _wrap_text_by_pixels(draw, text, font, max_width):
    """Wrap text by measuring pixel width per line."""
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for w in words[1:]:
        test = current + ' ' + w
        try:
            width = draw.textlength(test, font=font)
        except Exception:
            bbox = draw.textbbox((0,0), test, font=font)
            width = bbox[2] - bbox[0]
        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


def _fit_font_size_for_paragraph(draw, paragraph, font_path, box_width, box_height, max_size=80, min_size=10, line_spacing=6):
    """Choose the largest font size where wrapped paragraph fits within box_height."""
    for size in range(max_size, min_size - 1, -1):
        try:
            f = ImageFont.truetype(font_path, size)
        except Exception:
            f = ImageFont.load_default()
        lines = _wrap_text_by_pixels(draw, paragraph, f, box_width)
        total_h = 0
        for line in lines:
            try:
                h = f.getsize(line)[1]
            except Exception:
                bbox = draw.textbbox((0,0), line, font=f)
                h = bbox[3] - bbox[1]
            total_h += h + line_spacing
        if total_h <= box_height:
            return size, lines
    # fallback: return minimal size and its wrapped lines
    try:
        f = ImageFont.truetype(font_path, min_size)
    except Exception:
        f = ImageFont.load_default()
    return min_size, _wrap_text_by_pixels(draw, paragraph, f, box_width)


def generate_certificate(student_name, course_name,
                         template_path=TEMPLATE_PATH,
                         output_dir=OUTPUT_DIR,
                         output_filename=OUTPUT_FILENAME,
                         name_coords=NAME_COORDS,
                         body_coords=BODY_COORDS,
                         wrap_width=WRAP_WIDTH,
                         name_font_path=NAME_FONT_PATH,
                         body_font_path=BODY_FONT_PATH,
                         name_font_size=NAME_FONT_SIZE,
                         body_font_size=BODY_FONT_SIZE,
                         line_spacing=LINE_SPACING,
                         name_fill=NAME_FILL,
                         body_fill=BODY_FILL,
                         center_name=CENTER_NAME_BY_DEFAULT):
    """Generate certificate image with student name and wrapped paragraph."""
    # Load template
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Load fonts (fallback to default if not found)
    try:
        name_font = ImageFont.truetype(name_font_path, name_font_size)
    except Exception:
        name_font = ImageFont.load_default()

    try:
        body_font = ImageFont.truetype(body_font_path, body_font_size)
    except Exception:
        body_font = ImageFont.load_default()

    # If using a TrueType font and we want to ensure bold look, try to simulate bold by drawing text twice with slight offset
    use_bold_sim = False
    if hasattr(name_font, 'path') and name_font_size >= 60:
        use_bold_sim = True

    # Auto-fit the student name into NAME_BOX if available
    nb_x, nb_y, nb_w, nb_h = NAME_BOX
    # Use the fitting helper to get the biggest font size
    chosen_name_size = _fit_font_size_for_text(draw, student_name, name_font_path, nb_w, nb_h, max_size=170, min_size=24)
    chosen_name_size += 10  # small boost +10px to match visual sample
    try:
        name_font = ImageFont.truetype(name_font_path, chosen_name_size)
    except Exception:
        name_font = ImageFont.load_default()

    # Center name inside the name box horizontally and vertically
    try:
        name_w = draw.textlength(student_name, font=name_font)
        name_h = name_font.getsize(student_name)[1]
    except Exception:
        bbox = draw.textbbox((0, 0), student_name, font=name_font)
        name_w = bbox[2] - bbox[0]
        name_h = bbox[3] - bbox[1]

    name_x = nb_x + (nb_w - name_w) / 2
    name_y = nb_y + (nb_h - name_h) / 2
    name_coords = (int(name_x), int(name_y))

    # Simulate bold by slight offset if using big TrueType font
    if use_bold_sim:
        draw.text((name_coords[0]+1, name_coords[1]+1), student_name, font=name_font, fill=(0,0,0))
    draw.text(name_coords, student_name, font=name_font, fill=name_fill)

    # Subtitle: 'has successfully completed the program in' centered below name
    subtitle_text = 'has successfully completed the program in'
    subtitle_size = 28
    try:
        subtitle_font = ImageFont.truetype(body_font_path, subtitle_size)
    except Exception:
        subtitle_font = ImageFont.load_default()
    try:
        sub_w = draw.textlength(subtitle_text, font=subtitle_font)
    except Exception:
        bbox = draw.textbbox((0,0), subtitle_text, font=subtitle_font)
        sub_w = bbox[2] - bbox[0]
    sub_x = NAME_BOX[0] + (NAME_BOX[2] - sub_w) / 2
    sub_y = NAME_BOX[1] + NAME_BOX[3] + 10
    draw.text((int(sub_x), int(sub_y)), subtitle_text, font=subtitle_font, fill=(60,60,60))

    # Draw course name centered and prominent in blue
    course_box_x = NAME_BOX[0]
    course_box_w = NAME_BOX[2]
    course_size = _fit_font_size_for_text(draw, course_name, name_font_path, course_box_w, 80, max_size=80, min_size=20)
    try:
        course_font = ImageFont.truetype(name_font_path, course_size)
    except Exception:
        course_font = ImageFont.load_default()
    try:
        course_w = draw.textlength(course_name, font=course_font)
        course_h = course_font.getsize(course_name)[1]
    except Exception:
        bbox = draw.textbbox((0,0), course_name, font=course_font)
        course_w = bbox[2] - bbox[0]
        course_h = bbox[3] - bbox[1]
    course_x = course_box_x + (course_box_w - course_w) / 2
    course_y = sub_y + 40
    draw.text((int(course_x), int(course_y)), course_name, font=course_font, fill=(10, 100, 220))

    # Auto-fit paragraph into BODY_BOX
    bx, by, bw, bh = BODY_BOX
    # nudge the body down slightly to sit beneath the course
    by = course_y + course_h + 20
    paragraph = (f"This certificate is awarded to {student_name} for completing {course_name}. "
                 "They have demonstrated a thorough understanding of the curriculum and met all the "
                 "necessary requirements with dedication and excellence.")

    chosen_body_size, wrapped_lines = _fit_font_size_for_paragraph(draw, paragraph, body_font_path, bw, bh, max_size=36, min_size=12, line_spacing=line_spacing)
    try:
        body_font = ImageFont.truetype(body_font_path, chosen_body_size)
    except Exception:
        body_font = ImageFont.load_default()

    # Draw white band behind body for readability
    band_x = bx - 10
    band_y = by - 10
    band_w = bw + 20
    band_h = bh + 20
    draw.rectangle([band_x, band_y, band_x + band_w, band_y + band_h], fill=(255,255,255,230))

    # Draw wrapped lines centered in the body box
    x = bx
    y = by
    for line in wrapped_lines:
        try:
            line_w = draw.textlength(line, font=body_font)
        except Exception:
            bbox = draw.textbbox((0,0), line, font=body_font)
            line_w = bbox[2] - bbox[0]
        line_x = bx + (bw - line_w) / 2
        draw.text((int(line_x), y), line, font=body_font, fill=body_fill)
        try:
            h = body_font.getsize(line)[1]
        except Exception:
            bbox = draw.textbbox((0,0), line, font=body_font)
            h = bbox[3] - bbox[1]
        y += h + line_spacing

    # Footer: Organized by text centered
    org_text = 'Organized by: Royal College'
    org_size = 18
    try:
        org_font = ImageFont.truetype(body_font_path, org_size)
    except Exception:
        org_font = ImageFont.load_default()
    try:
        org_w = draw.textlength(org_text, font=org_font)
    except Exception:
        bbox = draw.textbbox((0,0), org_text, font=org_font)
        org_w = bbox[2] - bbox[0]
    org_x = bx + (bw - org_w) / 2
    org_y = by + bh + 20
    draw.text((int(org_x), int(org_y)), org_text, font=org_font, fill=(90,90,90))

    # Build and wrap body paragraph
    body_text = (f"This certificate is awarded to {student_name} for completing {course_name}. "
                 "They have demonstrated a thorough understanding of the curriculum and "
                 "met all the necessary requirements with dedication and excellence.")
    wrapped_lines = textwrap.wrap(body_text, width=wrap_width)

    # Option: increase body font size slightly for visibility on the template
    # (body_font_size already increased in defaults)

    # Draw a subtle white band behind the body text to improve readability
    try:
        _, first_line_height = body_font.getsize(wrapped_lines[0])
    except Exception:
        bbox = draw.textbbox((0,0), wrapped_lines[0], font=body_font)
        first_line_height = bbox[3] - bbox[1]
    band_height = (first_line_height + line_spacing) * max(4, len(wrapped_lines))
    band_x = body_coords[0] - 10
    band_y = body_coords[1] - 10
    band_w = img.width - body_coords[0] - 100
    draw.rectangle([band_x, band_y, band_x + band_w, band_y + band_height], fill=(255,255,255,230))

    # Draw wrapped lines starting at body_coords (bigger text)
    x, y = body_coords
    for line in wrapped_lines:
        draw.text((x, y), line, font=body_font, fill=body_fill)
        # compute line height
        try:
            line_height = body_font.getsize(line)[1]
        except Exception:
            bbox = draw.textbbox((0,0), line, font=body_font)
            line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing

    # Save output
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    img.save(output_path)
    return output_path


# Example / quick test
if __name__ == "__main__":
    out = generate_certificate("tester tester", "Mern stack",
                               template_path="testttted.jpg",
                               output_dir=".",
                               output_filename="testttted_result.jpg",
                               wrap_width=70)  # tweak width as needed
    print("Saved:", out)