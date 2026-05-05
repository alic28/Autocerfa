"""
Mapping CERFA 13750*05 — coordonnées v3 calibrées sur grille pixel
Image : 924 x 1316 px

Lectures grille :
  VÉHICULE :
    y≈212 : immat / date achat / date 1re immat
    y≈248 : numéro formule
    y≈302 : marque / dénomination
    y≈328 : TVV
    y≈355 : VIN / genre national
  TITULAIRE :
    y≈462 : cases personne physique/morale/sexe
    y≈496 : nom/prénom / nom usage
    y≈520 : naissance (jour/mois/an/commune/dpt/pays)
    y≈550 : étage / immeuble
    y≈572 : n° voie / extension / type / libellé
    y≈595 : lieu-dit / téléphone
    y≈618 : code postal / commune / email
  SIGNATURE :
    y≈1128 : Fait à / date
"""

CERFA_13750_FIELDS: list[dict] = [

    # ── Cases type de demande ──────────────────────────────────────────────
    {
        "key": "case_certificat",
        "x": 133, "y": 120,
        "max_width": 12, "font_size": 8,
        "description": "Case Certificat", "is_checkbox": True,
    },
    {
        "key": "case_duplicata",
        "x": 212, "y": 118,
        "max_width": 12, "font_size": 8,
        "description": "Case Duplicata", "is_checkbox": True,
    },
    {
        "key": "case_correction",
        "x": 311, "y": 118,
        "max_width": 12, "font_size": 8,
        "description": "Case Correction", "is_checkbox": True,
    },
    {
        "key": "case_changement_domicile",
        "x": 408, "y": 118,
        "max_width": 12, "font_size": 8,
        "description": "Case Changement domicile", "is_checkbox": True,
    },

    # ── VÉHICULE — ligne 1 ─────────────────────────────────────────────────
    {
        "key": "vehicule_immatriculation",
        "x": 25, "y": 212,
        "max_width": 155, "font_size": 8,
        "description": "(A) N° immatriculation",
    },
    {
        "key": "vehicule_date_achat",
        "x": 222, "y": 212,
        "max_width": 140, "font_size": 8,
        "description": "Date d'achat",
    },
    {
        "key": "vehicule_date_premiere_immat",
        "x": 698, "y": 212,
        "max_width": 218, "font_size": 8,
        "description": "(B) Date 1re immatriculation",
    },

    # ── VÉHICULE — ligne 2 : numéro formule ───────────────────────────────
    {
        "key": "vehicule_numero_formule",
        "x": 25, "y": 248,
        "max_width": 380, "font_size": 8,
        "description": "Numéro de formule CI",
    },

    # ── VÉHICULE — ligne 3 : marque / dénomination ────────────────────────
    {
        "key": "vehicule_marque",
        "x": 25, "y": 302,
        "max_width": 230, "font_size": 8,
        "description": "Marque (D.1)",
    },
    {
        "key": "vehicule_denomination",
        "x": 295, "y": 302,
        "max_width": 270, "font_size": 8,
        "description": "Dénomination commerciale (D.3)",
    },

    # ── VÉHICULE — ligne 4 : TVV ───────────────────────────────────────────
    {
        "key": "vehicule_tvv",
        "x": 25, "y": 328,
        "max_width": 440, "font_size": 8,
        "description": "Type variante version (D.2)",
    },

    # ── VÉHICULE — ligne 5 : VIN / genre ──────────────────────────────────
    {
        "key": "vehicule_vin",
        "x": 25, "y": 355,
        "max_width": 280, "font_size": 8,
        "description": "N° identification véhicule (E)",
    },
    {
        "key": "vehicule_genre",
        "x": 355, "y": 355,
        "max_width": 200, "font_size": 8,
        "description": "Genre national (J.1)",
    },

    # ── TITULAIRE — cases ─────────────────────────────────────────────────
    {
        "key": "titulaire_personne_physique",
        "x": 183, "y": 462,
        "max_width": 12, "font_size": 8,
        "description": "Case Personne physique", "is_checkbox": True,
    },
    {
        "key": "titulaire_sexe_m",
        "x": 264, "y": 462,
        "max_width": 12, "font_size": 8,
        "description": "Case Sexe M", "is_checkbox": True,
    },
    {
        "key": "titulaire_sexe_f",
        "x": 291, "y": 462,
        "max_width": 12, "font_size": 8,
        "description": "Case Sexe F", "is_checkbox": True,
    },
    {
        "key": "titulaire_personne_morale",
        "x": 384, "y": 462,
        "max_width": 12, "font_size": 8,
        "description": "Case Personne morale", "is_checkbox": True,
    },
    {
        "key": "titulaire_siren",
        "x": 530, "y": 462,
        "max_width": 180, "font_size": 8,
        "description": "N° SIREN",
    },

    # ── TITULAIRE — nom / prénom ───────────────────────────────────────────
    {
        "key": "titulaire_nom_prenom",
        "x": 25, "y": 496,
        "max_width": 500, "font_size": 9,
        "description": "NOM DE NAISSANCE et PRÉNOM",
    },
    {
        "key": "titulaire_nom_usage",
        "x": 558, "y": 496,
        "max_width": 358, "font_size": 8,
        "description": "NOM D'USAGE",
    },

    # ── TITULAIRE — naissance ──────────────────────────────────────────────
    {
        "key": "titulaire_naissance_jour",
        "x": 25, "y": 520,
        "max_width": 36, "font_size": 8,
        "description": "Jour naissance",
    },
    {
        "key": "titulaire_naissance_mois",
        "x": 68, "y": 520,
        "max_width": 36, "font_size": 8,
        "description": "Mois naissance",
    },
    {
        "key": "titulaire_naissance_annee",
        "x": 114, "y": 520,
        "max_width": 50, "font_size": 8,
        "description": "Année naissance",
    },
    {
        "key": "titulaire_commune_naissance",
        "x": 200, "y": 520,
        "max_width": 270, "font_size": 8,
        "description": "Commune de naissance",
    },
    {
        "key": "titulaire_departement_naissance",
        "x": 500, "y": 520,
        "max_width": 118, "font_size": 8,
        "description": "Département de naissance",
    },
    {
        "key": "titulaire_pays_naissance",
        "x": 638, "y": 520,
        "max_width": 278, "font_size": 8,
        "description": "Pays de naissance",
    },

    # ── TITULAIRE — domicile : étage / immeuble ───────────────────────────
    {
        "key": "titulaire_etage",
        "x": 25, "y": 550,
        "max_width": 215, "font_size": 8,
        "description": "Étage / Appartement",
    },
    {
        "key": "titulaire_immeuble",
        "x": 442, "y": 550,
        "max_width": 474, "font_size": 8,
        "description": "Immeuble / Résidence",
    },

    # ── TITULAIRE — domicile : ligne voie ─────────────────────────────────
    {
        "key": "titulaire_num_voie",
        "x": 25, "y": 572,
        "max_width": 55, "font_size": 8,
        "description": "N° de la voie",
    },
    {
        "key": "titulaire_extension",
        "x": 90, "y": 572,
        "max_width": 55, "font_size": 8,
        "description": "Extension",
    },
    {
        "key": "titulaire_type_voie",
        "x": 157, "y": 572,
        "max_width": 128, "font_size": 8,
        "description": "Type de voie",
    },
    {
        "key": "titulaire_libelle_voie",
        "x": 298, "y": 572,
        "max_width": 618, "font_size": 8,
        "description": "Libellé de voie",
    },

    # ── TITULAIRE — domicile : lieu-dit / téléphone ───────────────────────
    {
        "key": "titulaire_lieu_dit",
        "x": 25, "y": 595,
        "max_width": 415, "font_size": 8,
        "description": "Lieu-dit / BP",
    },
    {
        "key": "titulaire_telephone",
        "x": 555, "y": 595,
        "max_width": 358, "font_size": 8,
        "description": "Téléphone",
    },

    # ── TITULAIRE — domicile : CP / commune / email ───────────────────────
    {
        "key": "titulaire_code_postal",
        "x": 25, "y": 618,
        "max_width": 75, "font_size": 8,
        "description": "Code postal",
    },
    {
        "key": "titulaire_commune",
        "x": 113, "y": 618,
        "max_width": 415, "font_size": 8,
        "description": "Commune",
    },
    {
        "key": "titulaire_email",
        "x": 555, "y": 618,
        "max_width": 358, "font_size": 8,
        "description": "Email",
    },

    # ── Signature ─────────────────────────────────────────────────────────
    {
        "key": "titulaire_fait_a",
        "x": 78, "y": 1128,
        "max_width": 150, "font_size": 8,
        "description": "Fait à",
    },
    {
        "key": "titulaire_date_signature",
        "x": 148, "y": 1142,
        "max_width": 115, "font_size": 8,
        "description": "Date signature",
    },
]
