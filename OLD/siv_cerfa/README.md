# SIV CERFA — Générateur automatique de formulaires CERFA

Application métier pour la génération automatique des formulaires CERFA 13750 et 13757 à partir d'une démarche SIV (Système d'Immatriculation des Véhicules), à la manière d'AutoCerfa ou MISIV TMS.

---

## Fonctionnement

```
Démarche SIV saisie
       │
       ▼
CerfaGeneratorService.process(demarche)
       │
       ├─ changement_proprietaire ──▶ CERFA 13750 + CERFA 13757
       └─ declaration_cession ──────▶ CERFA 13757 uniquement
```

---

## Structure du projet

```
siv_cerfa/
├── main.py                          ← Point d'entrée CLI
├── src/
│   ├── models/
│   │   └── siv.py                   ← Modèles de données (Titulaire, Véhicule, Démarche...)
│   ├── services/
│   │   └── cerfa_service.py         ← Logique métier + orchestration
│   ├── mappings/
│   │   ├── cerfa_13757.py           ← Coordonnées des champs CERFA 13757
│   │   └── cerfa_13750.py           ← Coordonnées des champs CERFA 13750
│   └── generators/
│       └── pdf_generator.py         ← Génération PDF (Pillow + ReportLab)
├── templates/
│   ├── cerfa_13757_template.jpeg    ← Image CERFA 13757 (fond)
│   └── cerfa_13750_template.jpeg    ← Image CERFA 13750 (fond)
├── examples/
│   ├── exemple_changement_proprietaire.py
│   └── exemple_declaration_cession.py
├── tools/
│   └── calibrate.py                 ← Outil de calibration des coordonnées
├── tests/
│   └── test_cerfa.py               ← Tests unitaires
└── output/                         ← PDFs générés
```

---

## Installation

```bash
pip install pillow reportlab
```

---

## Lancement rapide

```bash
# Exemple changement de propriétaire → génère CERFA 13750 + 13757
python main.py --exemple changement

# Exemple déclaration de cession → génère CERFA 13757 uniquement
python main.py --exemple cession

# Calibration des coordonnées
python main.py --calibrer 13757
python main.py --calibrer 13750
```

---

## Utilisation programmatique

```python
from datetime import date
from src.models.siv import (
    DemarcheChangementProprietaire, PersonnePhysique,
    Vehicule, Mandataire, AdressePostale, Civilite, TypeCertificat
)
from src.services.cerfa_service import CerfaGeneratorService
from pathlib import Path

# 1. Créer le nouveau titulaire
titulaire = PersonnePhysique(
    civilite=Civilite.M,
    nom_naissance="DUPONT",
    prenom="Pierre",
    date_naissance=date(1985, 3, 12),
    adresse=AdressePostale(
        numero_voie="5", type_voie="Rue", libelle_voie="des Lilas",
        code_postal="75001", commune="Paris",
    ),
    telephone="0612345678",
    email="p.dupont@email.com",
)

# 2. Renseigner le véhicule
vehicule = Vehicule(
    numero_immatriculation="AB-123-CD",
    marque="RENAULT",
    denomination_commerciale="CLIO",
    numero_vin="VF1RFB00060123456",
    genre_national="VP",
    date_premiere_immatriculation=date(2019, 3, 20),
    date_achat=date(2024, 11, 15),
)

# 3. Renseigner le mandataire (garage)
mandataire = Mandataire(
    nom_raison_sociale="GARAGE DUPONT SAS",
    siret="12345678900012",
)

# 4. Créer la démarche
demarche = DemarcheChangementProprietaire(
    nouveau_titulaire=titulaire,
    vehicule=vehicule,
    mandataire=mandataire,
    type_certificat=TypeCertificat.CERTIFICAT,
    fait_a="Paris",
    date_signature=date(2024, 11, 15),
)

# 5. Générer les CERFA
service = CerfaGeneratorService(output_dir=Path("output"))
results = service.process(demarche)
# → results = {"13757": Path("output/cerfa_13757.pdf"), "13750": Path("output/cerfa_13750.pdf")}
```

---

## Calibration des coordonnées

Si le texte n'est pas positionné au bon endroit sur le formulaire :

```bash
python main.py --calibrer 13757
```

Ouvrez `output/calibration_13757.jpeg` — chaque champ est marqué d'un point rouge avec son nom. Ajustez les valeurs `x` et `y` dans `src/mappings/cerfa_13757.py`.

---

## Types de démarches supportées

| Démarche | CERFA générés |
|----------|--------------|
| `changement_proprietaire` | 13750 + 13757 |
| `declaration_cession` | 13757 uniquement |

---

## Ajouter un nouveau CERFA

1. Ajouter le template JPEG dans `templates/cerfa_XXXXX_template.jpeg`
2. Créer `src/mappings/cerfa_XXXXX.py` avec la liste des champs
3. Ajouter la logique dans `CerfaGeneratorService`

---

## Tests

```bash
# Avec pytest (si disponible)
python -m pytest tests/ -v

# Avec unittest (standard)
python -m unittest discover tests/
```

---

## Architecture

```
Couche              Fichier                    Responsabilité
──────────────────────────────────────────────────────────────
Modèles de données  src/models/siv.py          Entités métier (Titulaire, Véhicule, Démarche)
Logique métier      src/services/cerfa_service  Orchestration + règles de génération
Mapping champs      src/mappings/cerfa_XXXXX    Coordonnées pixel par CERFA
Génération PDF      src/generators/pdf_generator Pillow (texte) + ReportLab (PDF)
Interface           main.py + examples/         CLI et exemples
```
