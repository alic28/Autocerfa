"""
Générateur PDF pour les formulaires CERFA.
"""
from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def _get_font(size: int) -> ImageFont.ImageFont:
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def fill_cerfa_image(
    template_path: Path,
    field_values: dict[str, str],
    field_definitions: list[dict],
) -> Image.Image:
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    for field_def in field_definitions:
        key = field_def["key"]
        value = field_values.get(key, "")
        if not value:
            continue

        x = field_def["x"]
        y = field_def["y"]
        font_size = field_def.get("font_size", 9)
        max_width = field_def.get("max_width", 200)

        font = _get_font(font_size)
        text = str(value)
        while text:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width <= max_width:
                break
            text = text[:-1]

        draw.text((x, y), text, fill=(0, 0, 0), font=font)

    return img


def image_to_pdf(img: Image.Image, output_path: Path) -> None:
    a4_w, a4_h = A4

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    img.save(tmp_path, format="JPEG", quality=92)

    try:
        c = canvas.Canvas(str(output_path), pagesize=A4)
        c.drawImage(
            tmp_path,
            x=0, y=0,
            width=a4_w, height=a4_h,
            preserveAspectRatio=True,
            anchor="sw",
        )
        c.save()
    finally:
        os.unlink(tmp_path)


def generate_cerfa_pdf(
    cerfa_id: str,
    field_values: dict[str, str],
    field_definitions: list[dict],
    output_path: Path,
) -> Path:
    template_path = TEMPLATES_DIR / f"cerfa_{cerfa_id}_template.jpeg"
    if not template_path.exists():
        raise FileNotFoundError(f"Template introuvable : {template_path}")

    img = fill_cerfa_image(template_path, field_values, field_definitions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_to_pdf(img, output_path)
    return output_path
