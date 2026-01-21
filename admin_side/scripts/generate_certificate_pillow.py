"""
Simple certificate generator using Pillow (PIL).
Usage example:
    python generate_certificate_pillow.py \
        --template "path/to/template.png" \
        --student "Jane Doe" \
        --course "Mern stack" \
        --out "output/certificate_jane.png"

Customize fonts, coordinates and sizes via CLI options or by editing the placeholders below.
"""
import argparse
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont


def _wrap_text_by_pixels(draw, text, font, max_width):
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
            bbox = draw.textbbox((0, 0), test, font=font)
            width = bbox[2] - bbox[0]
        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


def generate_certificate(
    student_name,
    course_name,
    template_path,
    output_path,
    # --- placeholders you can tweak ---
    name_coords=(100, 380),
    body_coords=(100, 550),
    name_font_path='path/to/bold.ttf',
    body_font_path='path/to/regular.ttf',
    name_font_size=48,
    body_font_size=18,
    max_text_width=None,
    body_line_spacing=6,
    name_fill=(0, 0, 0),
    body_fill=(60, 60, 60),
    center_name=False,
):
    # Load image
    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Load fonts (fallback to default)
    try:
        name_font = ImageFont.truetype(name_font_path, name_font_size)
    except Exception:
        name_font = ImageFont.load_default()
    try:
        body_font = ImageFont.truetype(body_font_path, body_font_size)
    except Exception:
        body_font = ImageFont.load_default()

    # Optionally center the student name horizontally
    if center_name:
        try:
            name_w = draw.textlength(student_name, font=name_font)
        except Exception:
            bbox = draw.textbbox((0, 0), student_name, font=name_font)
            name_w = bbox[2] - bbox[0]
        x = (img.width - name_w) / 2
        name_coords = (int(x), name_coords[1])

    # Draw student name
    draw.text(name_coords, student_name, font=name_font, fill=name_fill)

    # Build body paragraph
    body_text = (
        f"This certificate is awarded to {student_name} for completing {course_name}. "
        "They have demonstrated a thorough understanding of the curriculum and met all the "
        "necessary requirements with dedication and excellence."
    )

    img_width = img.width
    margin = 100
    if max_text_width is None:
        max_w = img_width - body_coords[0] - margin
    else:
        max_w = max_text_width

    lines = _wrap_text_by_pixels(draw, body_text, body_font, max_w)

    # Draw wrapped body
    x, y = body_coords
    for line in lines:
        draw.text((x, y), line, font=body_font, fill=body_fill)
        try:
            h = body_font.getsize(line)[1]
        except Exception:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            h = bbox[3] - bbox[1]
        y += h + body_line_spacing

    # Save output (ensure directory exists)
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    img.convert("RGB").save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate a certificate image using a template")
    parser.add_argument('--template', required=True, help='Path to certificate template image')
    parser.add_argument('--student', required=True, help='Student full name')
    parser.add_argument('--course', required=True, help='Course name')
    parser.add_argument('--out', required=True, help='Output file path (png/jpg)')
    parser.add_argument('--center-name', action='store_true', help='Center the student name horizontally')
    parser.add_argument('--name-x', type=int, help='Override name X coordinate')
    parser.add_argument('--name-y', type=int, help='Override name Y coordinate')
    args = parser.parse_args()

    name_coords = (100, 380)
    body_coords = (100, 550)

    if args.name_x is not None:
        name_coords = (args.name_x, name_coords[1])
    if args.name_y is not None:
        name_coords = (name_coords[0], args.name_y)

    out = generate_certificate(
        args.student,
        args.course,
        args.template,
        args.out,
        name_coords=name_coords,
        body_coords=body_coords,
        name_font_path='C:/Windows/Fonts/arialbd.ttf',  # adjust on your system
        body_font_path='C:/Windows/Fonts/arial.ttf',
        name_font_size=72,
        body_font_size=18,
        center_name=args.center_name
    )
    print('Saved:', out)


if __name__ == '__main__':
    main()
