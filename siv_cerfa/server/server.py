"""
SIV → CERFA — Service local Flask v2.0
Utilise les templates PDF personnalisés Dreux Carte Grise
avec les coordonnées calibrées.
"""
import os, sys, json, tempfile, subprocess
from datetime import date, datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file

BASE_DIR    = Path(__file__).parent.parent
TEMPLATES   = BASE_DIR / "templates"
OUTPUT_DIR  = BASE_DIR / "output"
SKILL_FILL  = Path("/mnt/skills/public/pdf/scripts/fill_pdf_form_with_annotations.py")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return r

@app.route("/generer", methods=["OPTIONS"])
def gen_opt(): return "", 200

# ── Coordonnées calibrées sur grille pixel ────────────────────────────────

def field(desc, x0, y0, x1, y1, text, fs=9):
    return {"page_number":1,"description":desc,"field_label":"l",
            "label_bounding_box":[x0-1,y0-2,x0,y0-1],
            "entry_bounding_box":[x0,y0,x1,y1],
            "entry_text":{"text":str(text),"font_size":fs}}

def build_fields_13757(d):
    """Construit le JSON de champs pour le CERFA 13757 (Mandat)."""
    t = d.get("titulaire", {})
    v = d.get("vehicule", {})

    nom_prenom = f'{t.get("nom","").upper()} {t.get("prenom","").upper()}'.strip()
    adr = t

    return {
      "pages":[{"page_number":1,"image_width":1240,"image_height":1755}],
      "form_fields":[
        field("Nom Prénom mandant", 174,338,728,358, nom_prenom),
        field("N° voie",            214,420,270,440, adr.get("num_voie",""),  8),
        field("Type voie",          400,420,512,440, adr.get("type_voie",""), 8),
        field("Libellé voie",       518,420,728,440, adr.get("libelle_voie",""),8),
        field("Code postal",         92,490,165,510, adr.get("code_postal",""),8),
        field("Commune",            168,490,458,510, adr.get("commune",""),   8),
        field("Marque",             207,812,638,832, v.get("marque","").upper()),
        field("VIN",                162,898,625,918, v.get("vin","").upper(),  8),
        field("Immatriculation",    304,1002,740,1022,d.get("immatriculation","").upper()),
        field("Jour",               578,1192,632,1212,_jour(d),  8),
        field("Mois",               638,1192,672,1212,_mois(d),  8),
        field("Annee",              682,1192,738,1212,_annee(d), 8),
      ]
    }

def build_fields_13750(d):
    """Construit le JSON de champs pour le CERFA 13750 (Demande CI)."""
    t = d.get("titulaire", {})
    v = d.get("vehicule", {})
    adr = t

    nom_prenom = f'{t.get("nom","").upper()} {t.get("prenom","").upper()}'.strip()
    naiss_j, naiss_m, naiss_a = _parse_date(t.get("date_naissance",""))

    return {
      "pages":[{"page_number":1,"image_width":1241,"image_height":1754}],
      "form_fields":[
        field("Immat A",    15,240,267,260, d.get("immatriculation","").upper(),8),
        field("Date B",    941,240,1235,260,v.get("date_premiere_immat",""),    8),
        field("Marque",     15,378,466,398, v.get("marque","").upper(),          8),
        field("VIN",        15,462,420,482, v.get("vin","").upper(),             8),
        field("Genre",     432,462,657,482, v.get("genre","").upper(),           8),
        field("NomPrenom", 115,650,879,670, nom_prenom),
        field("Naiss J",    18,697, 62,717, naiss_j, 8),
        field("Naiss M",    65,697,110,717, naiss_m, 8),
        field("Naiss A",   116,697,175,717, naiss_a, 8),
        field("Naiss Com", 222,697,652,717, t.get("commune_naissance","").upper(),8),
        field("Naiss Dep", 833,697,930,717, t.get("departement_naissance",""),   8),
        field("N° voie",   115,752,183,772, adr.get("num_voie",""),              8),
        field("Type voie", 254,752,424,772, adr.get("type_voie",""),             8),
        field("Libelle",   432,752,935,772, adr.get("libelle_voie",""),          8),
        field("CP",         18,812,100,832, adr.get("code_postal",""),           8),
        field("Commune",   115,812,690,832, adr.get("commune",""),               8),
      ]
    }

# ── Utilitaires date ──────────────────────────────────────────────────────

def _parse_date(s):
    """Parse JJ/MM/AAAA → (JJ, MM, AAAA)"""
    if not s: return "", "", ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s.strip(), fmt)
            return f"{d.day:02d}", f"{d.month:02d}", str(d.year)
        except ValueError: pass
    return "", "", ""

def _date_sig(d):
    ds = d.get("date_signature","")
    if not ds: ds = datetime.now().strftime("%d/%m/%Y")
    return _parse_date(ds)

def _jour(d): return _date_sig(d)[0]
def _mois(d): return _date_sig(d)[1]
def _annee(d): return _date_sig(d)[2]

# ── Remplissage PDF ───────────────────────────────────────────────────────

def fill_pdf(template_path: Path, fields_data: dict, output_path: Path) -> Path:
    """Remplit un PDF avec les annotations de texte."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(fields_data, f, ensure_ascii=False)
        json_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, str(SKILL_FILL),
             str(template_path), json_path, str(output_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"fill_pdf error: {result.stderr}")
        return output_path
    finally:
        os.unlink(json_path)

# ── Routes ────────────────────────────────────────────────────────────────

@app.route("/health")
def health(): return jsonify({"status":"ok","version":"2.0"})

@app.route("/generer", methods=["POST"])
def generer():
    try:
        data = request.get_json(force=True) or {}
        print(f"[SERVER] Dossier: {data.get('dossier','?')} | Démarche: {data.get('type_demarche','?')}")

        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        immat   = data.get("immatriculation","").replace("-","").upper()
        prefix  = f"{ts}_{immat}_"
        results = {}

        # ── CERFA 13757 toujours ─────────────────────────────────────────
        t13757  = TEMPLATES / "cerfa_13757_template.pdf"
        out757  = OUTPUT_DIR / f"{prefix}cerfa_13757.pdf"
        fill_pdf(t13757, build_fields_13757(data), out757)
        results["cerfa_13757_url"] = f"http://localhost:5000/cerfa/{out757.name}"

        # ── CERFA 13750 uniquement pour changement_proprietaire ──────────
        if data.get("type_demarche") == "changement_proprietaire":
            t13750 = TEMPLATES / "cerfa_13750_template.pdf"
            out750 = OUTPUT_DIR / f"{prefix}cerfa_13750.pdf"
            fill_pdf(t13750, build_fields_13750(data), out750)
            results["cerfa_13750_url"] = f"http://localhost:5000/cerfa/{out750.name}"

        print(f"[SERVER] ✅ CERFA générés : {list(results.keys())}")
        return jsonify(results)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/cerfa/<filename>")
def serve(filename):
    if ".." in filename or "/" in filename: return "Interdit", 400
    p = OUTPUT_DIR / filename
    if not p.exists(): return "Introuvable", 404
    return send_file(str(p), mimetype="application/pdf", as_attachment=False)

@app.route("/list")
def lst():
    files = sorted(OUTPUT_DIR.glob("*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonify([{"name":f.name,"url":f"http://localhost:5000/cerfa/{f.name}"}
                    for f in files[:20]])

if __name__ == "__main__":
    print("=" * 55)
    print("  SIV → CERFA — Service local v2.0")
    print(f"  URL    : http://localhost:5000")
    print(f"  Output : {OUTPUT_DIR}")
    print("=" * 55)
    app.run(host="127.0.0.1", port=5000, debug=False)
