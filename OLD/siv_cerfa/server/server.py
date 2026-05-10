"""
SIV → CERFA — Service local Flask v4.0
Avec mode édition visuelle des coordonnées.
"""
import os, sys, json, tempfile
from datetime import datetime
from pathlib import Path

SERVER_DIR  = Path(__file__).parent
sys.path.insert(0, str(SERVER_DIR))

from fill_pdf import fill_pdf_form
from flask import Flask, request, jsonify, send_file, send_from_directory

BASE_DIR    = Path(__file__).parent.parent
TEMPLATES   = BASE_DIR / "templates"
OUTPUT_DIR  = BASE_DIR / "output"
COORDS_FILE = SERVER_DIR / "coords.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

# ── Coordonnées par défaut (calibrées sur grille pixel) ────────────────────

DEFAULT_COORDS = {
  "13757": {
    "image_width": 1240, "image_height": 1755,
    "fields": [
      {"key":"nom_prenom",  "x":220, "y":348, "w":508, "fs":9, "label":"Nom Prénom mandant"},
      {"key":"num_voie",    "x":180, "y":432, "w":60,  "fs":8, "label":"N° voie"},
      {"key":"type_voie",   "x":360, "y":432, "w":100, "fs":8, "label":"Type voie"},
      {"key":"libelle_voie","x":475, "y":432, "w":255, "fs":8, "label":"Libellé voie"},
      {"key":"code_postal", "x":120, "y":506, "w":75,  "fs":8, "label":"Code postal"},
      {"key":"commune",     "x":220, "y":506, "w":260, "fs":8, "label":"Commune"},
      {"key":"marque",      "x":225, "y":830, "w":413, "fs":9, "label":"Marque"},
      {"key":"vin",         "x":180, "y":910, "w":445, "fs":8, "label":"VIN"},
      {"key":"immat",       "x":485, "y":1014,"w":255, "fs":9, "label":"Immatriculation"},
      {"key":"jour",        "x":595, "y":1218,"w":45,  "fs":8, "label":"Date Jour"},
      {"key":"mois",        "x":660, "y":1218,"w":40,  "fs":8, "label":"Date Mois"},
      {"key":"annee",       "x":725, "y":1218,"w":55,  "fs":8, "label":"Date Année"},
    ]
  },
  "13750": {
    "image_width": 1241, "image_height": 1754,
    "fields": [
      {"key":"immat",       "x":50,  "y":295, "w":230, "fs":8, "label":"(A) Immatriculation"},
      {"key":"date_immat",  "x":980, "y":295, "w":250, "fs":8, "label":"(B) Date 1re immat"},
      {"key":"marque",      "x":115, "y":402, "w":365, "fs":8, "label":"Marque (D.1)"},
      {"key":"vin",         "x":115, "y":491, "w":305, "fs":8, "label":"VIN (E)"},
      {"key":"genre",       "x":575, "y":491, "w":145, "fs":8, "label":"Genre (J.1)"},
      {"key":"nom_prenom",  "x":175, "y":670, "w":704, "fs":9, "label":"Nom Prénom"},
      {"key":"naiss_jour",  "x":22,  "y":709, "w":38,  "fs":8, "label":"Naiss Jour"},
      {"key":"naiss_mois",  "x":67,  "y":709, "w":43,  "fs":8, "label":"Naiss Mois"},
      {"key":"naiss_annee", "x":118, "y":709, "w":57,  "fs":8, "label":"Naiss Année"},
      {"key":"naiss_com",   "x":240, "y":709, "w":410, "fs":8, "label":"Commune naissance"},
      {"key":"naiss_dep",   "x":835, "y":709, "w":85,  "fs":8, "label":"Département naiss"},
      {"key":"num_voie",    "x":130, "y":782, "w":50,  "fs":8, "label":"N° voie"},
      {"key":"type_voie",   "x":275, "y":782, "w":135, "fs":8, "label":"Type voie"},
      {"key":"libelle_voie","x":450, "y":782, "w":475, "fs":8, "label":"Libellé voie"},
      {"key":"code_postal", "x":22,  "y":848, "w":76,  "fs":8, "label":"Code postal"},
      {"key":"commune",     "x":170, "y":848, "w":515, "fs":8, "label":"Commune"},
    ]
  }
}

def load_coords():
    if COORDS_FILE.exists():
        try:
            return json.loads(COORDS_FILE.read_text(encoding='utf-8'))
        except: pass
    return DEFAULT_COORDS

def save_coords(c):
    COORDS_FILE.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding='utf-8')

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return r

@app.route("/generer", methods=["OPTIONS"])
def gen_opt(): return "", 200

# ── Construction des champs depuis les coords ──────────────────────────────

def build_field(spec, text):
    return {
        "page_number": 1,
        "description": spec["label"],
        "field_label": "l",
        "label_bounding_box": [spec["x"]-1, spec["y"]-2, spec["x"], spec["y"]-1],
        "entry_bounding_box": [spec["x"], spec["y"]-15,
                               spec["x"]+spec["w"], spec["y"]],
        "entry_text": {"text": str(text), "font_size": spec.get("fs", 9)}
    }

def get_value(d, key):
    """Map d'un key 'nom_prenom'... vers la bonne valeur du payload."""
    t = d.get("titulaire", {})
    v = d.get("vehicule",  {})
    nom = f'{t.get("nom","").upper()} {t.get("prenom","").upper()}'.strip()
    j, m, a = _date_sig(d)
    nj, nm, na = _parse_date(t.get("date_naissance",""))

    return {
        "nom_prenom":   nom,
        "num_voie":     t.get("num_voie",""),
        "type_voie":    t.get("type_voie",""),
        "libelle_voie": t.get("libelle_voie",""),
        "code_postal":  t.get("code_postal",""),
        "commune":      t.get("commune",""),
        "marque":       v.get("marque","").upper(),
        "vin":          v.get("vin","").upper(),
        "genre":        v.get("genre","").upper(),
        "immat":        d.get("immatriculation","").upper(),
        "date_immat":   v.get("date_premiere_immat",""),
        "jour":         j, "mois": m, "annee": a,
        "naiss_jour":   nj, "naiss_mois": nm, "naiss_annee": na,
        "naiss_com":    t.get("commune_naissance","").upper(),
        "naiss_dep":    t.get("departement_naissance",""),
    }.get(key, "")

def build_fields(form_id, d):
    coords = load_coords()
    cfg    = coords.get(form_id, DEFAULT_COORDS[form_id])
    return {
        "pages": [{"page_number":1, "image_width": cfg["image_width"],
                   "image_height": cfg["image_height"]}],
        "form_fields": [build_field(spec, get_value(d, spec["key"]))
                        for spec in cfg["fields"]]
    }

def _parse_date(s):
    if not s: return "", "", ""
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            from datetime import datetime as dt
            d = dt.strptime(s, fmt)
            return f"{d.day:02d}", f"{d.month:02d}", str(d.year)
        except ValueError: pass
    return "", "", ""

def _date_sig(d):
    ds = d.get("date_signature","") or datetime.now().strftime("%d/%m/%Y")
    return _parse_date(ds)

def fill_cerfa(template_path, fields_data, output_path):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False, encoding='utf-8') as f:
            json.dump(fields_data, f, ensure_ascii=False)
            tmp = f.name
        fill_pdf_form(str(template_path), tmp, str(output_path))
        return output_path
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/health")
def health(): return jsonify({"status":"ok","version":"4.0"})

@app.route("/generer", methods=["POST"])
def generer():
    try:
        data = request.get_json(force=True) or {}
        print("\n" + "="*60)
        print("PAYLOAD RECU :")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("="*60)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        immat = data.get("immatriculation","XX").replace("-","").upper()
        prefix = f"{ts}_{immat}_"
        result = {}

        out757 = OUTPUT_DIR / f"{prefix}cerfa_13757.pdf"
        fill_cerfa(TEMPLATES / "cerfa_13757_template.pdf",
                   build_fields("13757", data), out757)
        result["cerfa_13757_url"] = f"http://localhost:5000/cerfa/{out757.name}"

        if data.get("type_demarche") == "changement_proprietaire":
            out750 = OUTPUT_DIR / f"{prefix}cerfa_13750.pdf"
            fill_cerfa(TEMPLATES / "cerfa_13750_template.pdf",
                       build_fields("13750", data), out750)
            result["cerfa_13750_url"] = f"http://localhost:5000/cerfa/{out750.name}"

        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/cerfa/<filename>")
def serve_cerfa(filename):
    if ".." in filename or "/" in filename or "\\" in filename: return "Interdit", 400
    p = OUTPUT_DIR / filename
    if not p.exists(): return "Introuvable", 404
    return send_file(str(p), mimetype="application/pdf", as_attachment=False)

@app.route("/list")
def list_cerfa():
    files = sorted(OUTPUT_DIR.glob("*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonify([{"name": f.name, "url": f"http://localhost:5000/cerfa/{f.name}"}
                    for f in files[:20]])

# ── Mode édition visuelle ──────────────────────────────────────────────────

@app.route("/editor")
def editor():
    """Page web d'édition visuelle des coordonnées."""
    return send_from_directory(str(SERVER_DIR), "editor.html")

@app.route("/template/<form_id>.png")
def template_png(form_id):
    """Sert le PNG du template (pré-généré dans templates/)."""
    if form_id not in ("13750", "13757"): return "Inconnu", 404
    p = TEMPLATES / f"cerfa_{form_id}_template.png"
    if not p.exists(): return f"Image template manquante: {p}", 500
    return send_file(str(p), mimetype="image/png")

@app.route("/coords", methods=["GET"])
def get_coords():
    return jsonify(load_coords())

@app.route("/coords", methods=["POST"])
def set_coords():
    save_coords(request.get_json(force=True))
    print("[COORDS] sauvegardés dans coords.json")
    return jsonify({"ok": True})

@app.route("/preview/<form_id>", methods=["POST"])
def preview(form_id):
    """Génère un aperçu PDF à partir de coordonnées temporaires."""
    try:
        if form_id not in ("13750", "13757"):
            return "Inconnu", 404
        body = request.get_json(force=True)
        # Sauvegarde temporaire des coords
        all_coords = load_coords()
        all_coords[form_id] = body["coords"]
        save_coords(all_coords)
        # Génération
        sample = body.get("sample", {})
        out = OUTPUT_DIR / f"_preview_{form_id}.pdf"
        fill_cerfa(TEMPLATES / f"cerfa_{form_id}_template.pdf",
                   build_fields(form_id, sample), out)
        return jsonify({"url": f"http://localhost:5000/cerfa/{out.name}?_t={datetime.now().timestamp()}"})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 55)
    print("  SIV -> CERFA -- Serveur local v4.0")
    print(f"  URL    : http://localhost:5000")
    print(f"  Editor : http://localhost:5000/editor   <-- NOUVEAU")
    print(f"  Output : {OUTPUT_DIR}")
    print("=" * 55)
    app.run(host="127.0.0.1", port=5000, debug=False)
