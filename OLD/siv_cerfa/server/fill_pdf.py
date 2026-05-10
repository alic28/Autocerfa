"""
Remplissage PDF par superposition de texte (reportlab + pypdf merge).
La baseline du texte est placée à bbox.y1 (bas de la boîte = ligne du formulaire).
"""
import json
import sys
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black


def fill_pdf_form(template_pdf, fields_json, output_pdf):
    with open(fields_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    reader   = PdfReader(template_pdf)
    page     = reader.pages[0]
    mediabox = page.mediabox
    pdf_w    = float(mediabox.width)
    pdf_h    = float(mediabox.height)

    page_info = next(p for p in data["pages"] if p["page_number"] == 1)
    img_w = page_info.get("image_width",  pdf_w)
    img_h = page_info.get("image_height", pdf_h)

    buf = BytesIO()
    c   = canvas.Canvas(buf, pagesize=(pdf_w, pdf_h))
    c.setFillColor(black)

    x_scale = pdf_w / img_w
    y_scale = pdf_h / img_h

    nb_filled = 0
    for field in data["form_fields"]:
        text_obj = field.get("entry_text", {})
        text     = str(text_obj.get("text", "")).strip()
        if not text:
            continue

        font_size = int(text_obj.get("font_size", 9))
        bbox      = field["entry_bounding_box"]   # [x0, y0_top, x1, y1_bottom]

        # On place la baseline du texte à 2px AU-DESSUS du bas de la bbox
        # (bbox y1 = ligne du formulaire en image)
        x_image_left   = bbox[0]
        y_image_bottom = bbox[3]

        pdf_x        = x_image_left * x_scale + 1
        pdf_baseline = pdf_h - (y_image_bottom - 2) * y_scale

        c.setFont("Helvetica", font_size)
        c.drawString(pdf_x, pdf_baseline, text)
        nb_filled += 1

    c.save()
    buf.seek(0)

    overlay_reader = PdfReader(buf)
    page.merge_page(overlay_reader.pages[0])

    writer = PdfWriter()
    writer.add_page(page)
    for p in reader.pages[1:]:
        writer.add_page(p)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print(f"Successfully filled PDF form and saved to {output_pdf}")
    print(f"Added {nb_filled} text overlays")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: fill_pdf.py [input pdf] [fields.json] [output pdf]")
        sys.exit(1)
    fill_pdf_form(sys.argv[1], sys.argv[2], sys.argv[3])
