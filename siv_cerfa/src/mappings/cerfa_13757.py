"""
Mapping CERFA 13757 — coordonnées v3 calibrées sur grille pixel
Image : 924 x 1316 px

Lectures grille (lignes bleues tous les 100px, subdivisions 20px) :
  y≈240 : ligne "Je soussigné(e)" → nom mandant
  y≈320 : ligne adresse voie
  y≈395 : ligne CP / commune / pays
  y≈455 : ligne "donne mandat à" → mandataire
  y≈540 : ligne opération
  y≈655 : intérieur boîte Marque
  y≈730 : ligne Numéro VIN
  y≈812 : ligne N° immatriculation
  y≈963 : ligne Fait à / date signature
"""

CERFA_13757_FIELDS: list[dict] = [

    # ── Mandant (Je soussigné) ─────────────────────────────────────────────
    {
        "key": "mandant_nom_prenom",
        "x": 170, "y": 240,
        "max_width": 440, "font_size": 9,
        "description": "NOM PRÉNOM ou RAISON SOCIALE du mandant",
    },
    {
        "key": "mandant_siret",
        "x": 680, "y": 240,
        "max_width": 215, "font_size": 8,
        "description": "N° SIRET du mandant",
    },

    # ── Adresse mandant — ligne voie ───────────────────────────────────────
    {
        "key": "mandant_num_voie",
        "x": 135, "y": 320,
        "max_width": 44, "font_size": 8,
        "description": "N° de la voie",
    },
    {
        "key": "mandant_extension",
        "x": 185, "y": 320,
        "max_width": 52, "font_size": 8,
        "description": "Extension (bis, ter...)",
    },
    {
        "key": "mandant_type_voie",
        "x": 245, "y": 320,
        "max_width": 90, "font_size": 8,
        "description": "Type de voie",
    },
    {
        "key": "mandant_nom_voie",
        "x": 345, "y": 320,
        "max_width": 568, "font_size": 8,
        "description": "Nom de la voie",
    },

    # ── Code postal / Commune / Pays ───────────────────────────────────────
    {
        "key": "mandant_code_postal",
        "x": 100, "y": 395,
        "max_width": 78, "font_size": 8,
        "description": "Code postal",
    },
    {
        "key": "mandant_commune",
        "x": 205, "y": 395,
        "max_width": 365, "font_size": 8,
        "description": "Nom de la commune",
    },
    {
        "key": "mandant_pays",
        "x": 595, "y": 395,
        "max_width": 260, "font_size": 8,
        "description": "Pays",
    },

    # ── Mandataire (donne mandat à) ────────────────────────────────────────
    {
        "key": "mandataire_nom_raison",
        "x": 170, "y": 455,
        "max_width": 440, "font_size": 9,
        "description": "NOM/RAISON SOCIALE du mandataire",
    },
    {
        "key": "mandataire_siret",
        "x": 680, "y": 455,
        "max_width": 215, "font_size": 8,
        "description": "N° SIRET du mandataire",
    },

    # ── Opération d'immatriculation ────────────────────────────────────────
    {
        "key": "operation_immatriculation",
        "x": 100, "y": 565,
        "max_width": 800, "font_size": 8,
        "description": "Description de l'opération",
    },

    # ── Marque (dans la boîte) ─────────────────────────────────────────────
    {
        "key": "vehicule_marque",
        "x": 185, "y": 655,
        "max_width": 430, "font_size": 9,
        "description": "Marque du véhicule",
    },

    # ── VIN (dans les cases) ───────────────────────────────────────────────
    {
        "key": "vehicule_vin",
        "x": 200, "y": 730,
        "max_width": 440, "font_size": 9,
        "description": "Numéro VIN",
    },

    # ── N° d'immatriculation ───────────────────────────────────────────────
    {
        "key": "vehicule_immatriculation",
        "x": 375, "y": 812,
        "max_width": 310, "font_size": 9,
        "description": "Numéro d'immatriculation",
    },

    # ── Signature — Fait à / Date ──────────────────────────────────────────
    {
        "key": "fait_a",
        "x": 95, "y": 963,
        "max_width": 435, "font_size": 9,
        "description": "Fait à (lieu)",
    },
    {
        "key": "date_jour",
        "x": 555, "y": 963,
        "max_width": 44, "font_size": 9,
        "description": "Jour",
    },
    {
        "key": "date_mois",
        "x": 614, "y": 963,
        "max_width": 44, "font_size": 9,
        "description": "Mois",
    },
    {
        "key": "date_annee",
        "x": 675, "y": 963,
        "max_width": 70, "font_size": 9,
        "description": "Année",
    },
]
