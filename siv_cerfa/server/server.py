"""
SIV → CERFA — Service local Flask
===================================
Reçoit les données JSON depuis l'extension Edge/Chrome
et génère les PDFs CERFA 13750 et 13757.

Démarrage : python server/server.py
URL       : http://localhost:5000
"""

import os
import sys
import json
import webbrowser
from datetime import date, datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file


# ── Chemin vers le projet siv_cerfa ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.siv import (
    DemarcheChangementProprietaire,
    DemarcheDeclarationCession,
    PersonnePhysique, PersonneMorale,
    Vehicule, Mandataire, AdressePostale,
    Civilite, TypeCertificat,
)
from src.services.cerfa_service import CerfaGeneratorService

# ── Configuration ────────────────────────────────────────────────────────────
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/generer', methods=['OPTIONS'])
def generer_options():
    from flask import Response
    return Response('', 200)




# ── Utilitaires ──────────────────────────────────────────────────────────────

def parse_date(s: str | None) -> date | None:
    """Parse une date JJ/MM/AAAA ou AAAA-MM-JJ."""
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def build_adresse(d: dict) -> AdressePostale:
    return AdressePostale(
        numero_voie        = d.get("num_voie", ""),
        extension          = d.get("extension_voie", ""),
        type_voie          = d.get("type_voie", ""),
        libelle_voie       = d.get("libelle_voie", ""),
        lieu_dit           = d.get("lieu_dit", ""),
        code_postal        = d.get("code_postal", ""),
        commune            = d.get("commune", ""),
        pays               = d.get("pays", "France"),
        etage_appartement  = d.get("etage", ""),
        immeuble_residence = d.get("immeuble", ""),
    )


def build_titulaire(t: dict):
    """Construit un objet PersonnePhysique ou PersonneMorale depuis le JSON reçu."""
    if t.get("type") == "personne_morale":
        return PersonneMorale(
            raison_sociale    = t.get("raison_sociale", t.get("nom", "")),
            siret             = t.get("siret", ""),
            siren             = t.get("siren", ""),
            representant_legal= t.get("representant_legal", ""),
            adresse           = build_adresse(t),
            telephone         = t.get("telephone", ""),
            email             = t.get("email", ""),
        )
    # Personne physique (défaut)
    sexe_val = t.get("sexe", "M").strip().upper()
    civilite = Civilite.MME if sexe_val in ("F", "MME", "FEMININ") else Civilite.M
    return PersonnePhysique(
        civilite              = civilite,
        nom_naissance         = t.get("nom", ""),
        prenom                = t.get("prenom", ""),
        nom_usage             = t.get("nom_usage", ""),
        date_naissance        = parse_date(t.get("date_naissance")),
        commune_naissance     = t.get("commune_naissance", ""),
        departement_naissance = t.get("departement_naissance", ""),
        pays_naissance        = t.get("pays_naissance", "France"),
        adresse               = build_adresse(t),
        telephone             = t.get("telephone", ""),
        email                 = t.get("email", ""),
    )


def build_vehicule(v: dict, immatriculation: str = "", numero_formule: str = "") -> Vehicule:
    return Vehicule(
        numero_immatriculation        = immatriculation or v.get("immatriculation", ""),
        marque                        = v.get("marque", ""),
        denomination_commerciale      = v.get("denomination", ""),
        type_variante_version         = v.get("tvv", ""),
        numero_vin                    = v.get("vin", ""),
        genre_national                = v.get("genre", ""),
        carrosserie                   = v.get("carrosserie", ""),
        energie                       = v.get("energie", ""),
        puissance_fiscale             = str(v.get("puissance_fiscale", "")),
        date_premiere_immatriculation = parse_date(v.get("date_premiere_immat")),
        numero_formule                = numero_formule or v.get("numero_formule", ""),
    )


def slug_date() -> str:
    """Timestamp pour nommer les fichiers."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Ping — vérifié par l'extension pour savoir si le service tourne."""
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.route("/generer", methods=["POST"])
def generer():
    """
    Reçoit les données SIV et génère les CERFA correspondants.

    Body JSON attendu :
    {
      "type_demarche": "changement_proprietaire" | "declaration_cession",
      "immatriculation": "GP-910-RT",
      "numero_formule": "2023CP97184",
      "dossier": "GP-910-RT",
      "mandataire_nom": "DREUX CARTE GRISE",
      "mandataire_siret": "",
      "vehicule": { "vin": "...", "marque": "FIAT", "genre": "VP", ... },
      "titulaire": {
        "type": "personne_physique",
        "nom": "OMONT", "prenom": "INES LEA", "sexe": "F",
        "date_naissance": "21/01/2006",
        "commune_naissance": "LA TESTE DE BUCH",
        "departement_naissance": "33",
        "num_voie": "5", "type_voie": "RUE", "libelle_voie": "PASTEUR",
        "code_postal": "59300", "commune": "VALENCIENNES"
      },
      "fait_a": "Dreux",
      "date_signature": "15/11/2024"
    }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Body JSON vide ou invalide"}), 400

        print(f"\n[SERVER] Requête reçue — dossier : {data.get('dossier', '?')}")
        print(f"[SERVER] Type de démarche : {data.get('type_demarche', '?')}")

        type_demarche  = data.get("type_demarche", "changement_proprietaire")
        immatriculation = data.get("immatriculation", "")
        numero_formule  = data.get("numero_formule", "")
        fait_a          = data.get("fait_a", "")
        date_signature  = parse_date(data.get("date_signature")) or date.today()

        vehicule_data   = data.get("vehicule", {})
        titulaire_data  = data.get("titulaire", {})

        # Construire les objets métier
        vehicule   = build_vehicule(vehicule_data, immatriculation, numero_formule)
        titulaire  = build_titulaire(titulaire_data)
        mandataire = Mandataire(
            nom_raison_sociale = data.get("mandataire_nom", ""),
            siret              = data.get("mandataire_siret", ""),
        )

        # Prefix unique pour éviter les collisions de fichiers
        ts = slug_date()
        prefix = f"{ts}_{immatriculation.replace('-','')}_"

        # Construire la démarche et générer
        service = CerfaGeneratorService(output_dir=OUTPUT_DIR)

        if type_demarche == "declaration_cession":
            demarche = DemarcheDeclarationCession(
                vendeur        = titulaire,
                vehicule       = vehicule,
                mandataire     = mandataire,
                fait_a         = fait_a,
                date_signature = date_signature,
            )
        else:
            # Par défaut : changement de propriétaire
            demarche = DemarcheChangementProprietaire(
                nouveau_titulaire = titulaire,
                vehicule          = vehicule,
                mandataire        = mandataire,
                type_certificat   = TypeCertificat.CERTIFICAT,
                fait_a            = fait_a,
                date_signature    = date_signature,
            )

        results = service.process(demarche, prefix=prefix)
        print(f"[SERVER] CERFA générés : {list(results.keys())}")

        # Construire les URLs de téléchargement
        response = {}
        for cerfa_id, path in results.items():
            filename = path.name
            url = f"http://localhost:5000/cerfa/{filename}"
            response[f"cerfa_{cerfa_id}_url"] = url
            print(f"[SERVER]   CERFA {cerfa_id} → {url}")

        return jsonify(response)

    except Exception as e:
        import traceback
        print(f"[SERVER] ❌ Erreur : {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/cerfa/<filename>", methods=["GET"])
def serve_cerfa(filename: str):
    """Sert un PDF généré pour affichage dans le navigateur."""
    # Sécurité : interdire les chemins relatifs
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"error": "Nom de fichier invalide"}), 400

    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        return jsonify({"error": f"Fichier introuvable : {filename}"}), 404

    return send_file(
        str(filepath),
        mimetype="application/pdf",
        as_attachment=False,         # Ouvrir dans le navigateur (pas télécharger)
        download_name=filename,
    )


@app.route("/list", methods=["GET"])
def list_cerfas():
    """Liste les CERFA générés (pour debug)."""
    files = sorted(OUTPUT_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    return jsonify([
        {"name": f.name, "url": f"http://localhost:5000/cerfa/{f.name}",
         "size_kb": round(f.stat().st_size / 1024, 1)}
        for f in files[:20]
    ])


# ── Démarrage ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  SIV → CERFA — Service local")
    print("=" * 60)
    print(f"  URL    : http://localhost:5000")
    print(f"  Output : {OUTPUT_DIR}")
    print("  Appuyez sur Ctrl+C pour arrêter.")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
