"""
Outil de calibration des coordonnées CERFA.

Usage :
    python tools/calibrate.py 13757   → génère une image avec dots + labels
    python tools/calibrate.py 13750   → idem pour le CERFA 13750

Permet d'ajuster visuellement les coordonnées dans les fichiers
src/mappings/cerfa_13757.py et src/mappings/cerfa_13750.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from src.generators.pdf_generator import TEMPLATES_DIR, _get_font


def generate_calibration_image(cerfa_id: str) -> None:
    """Génère une image annotée avec les positions des champs."""
    if cerfa_id == "13757":
        from src.mappings.cerfa_13757 import CERFA_13757_FIELDS as fields
    elif cerfa_id == "13750":
        from src.mappings.cerfa_13750 import CERFA_13750_FIELDS as fields
    else:
        print(f"CERFA inconnu : {cerfa_id}. Utilisez 13757 ou 13750.")
        sys.exit(1)

    template = TEMPLATES_DIR / f"cerfa_{cerfa_id}_template.jpeg"
    img = Image.open(template).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _get_font(7)
    bold_font = _get_font(8)

    colors = {
        "text": (220, 50, 50),     # rouge
        "checkbox": (50, 150, 220), # bleu
    }

    for field in fields:
        x, y = field["x"], field["y"]
        is_cb = field.get("is_checkbox", False)
        color = colors["checkbox"] if is_cb else colors["text"]
        key = field["key"]

        # Croix rouge/bleue au point d'ancrage
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=color)
        # Ligne horizontale courte
        draw.line([x, y, x + min(field.get("max_width", 50), 60), y], fill=color, width=1)
        # Label
        draw.text((x, y - 9), key, fill=color, font=font)

    # Légende
    draw.rectangle([10, 5, 300, 30], fill=(255, 255, 255, 200))
    draw.text((15, 8), "● Rouge = champ texte   ● Bleu = checkbox", fill=(0, 0, 0), font=font)

    out_path = Path(__file__).parent.parent / "output" / f"calibration_{cerfa_id}.jpeg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), quality=95)
    print(f"✅ Image de calibration générée : {out_path}")
    print("   Ouvrez l'image et ajustez les coordonnées x/y dans le fichier de mapping.")


if __name__ == "__main__":
    cerfa_id = sys.argv[1] if len(sys.argv) > 1 else "13757"
    generate_calibration_image(cerfa_id)
