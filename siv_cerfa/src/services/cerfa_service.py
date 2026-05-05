"""
Service métier principal : décide quels CERFA générer selon la démarche SIV,
prépare les données, et orchestre la génération PDF.

Règles métier :
  - changement_proprietaire → CERFA 13750 + CERFA 13757
  - declaration_cession     → CERFA 13757 uniquement
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from ..models.siv import (
    Demarche,
    DemarcheChangementProprietaire,
    DemarcheDeclarationCession,
    PersonnePhysique,
    PersonneMorale,
    Titulaire,
    TypeCertificat,
    Vehicule,
    Mandataire,
)
from ..mappings.cerfa_13757 import CERFA_13757_FIELDS
from ..mappings.cerfa_13750 import CERFA_13750_FIELDS
from ..generators.pdf_generator import generate_cerfa_pdf


# ---------------------------------------------------------------------------
# Helpers de formatage
# ---------------------------------------------------------------------------

def _fmt_date(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def _fmt_date_parts(d: date | None) -> tuple[str, str, str]:
    if d is None:
        return "", "", ""
    return f"{d.day:02d}", f"{d.month:02d}", str(d.year)


def _titulaire_nom_complet(t: Titulaire) -> str:
    if isinstance(t, PersonnePhysique):
        return f"{t.nom_naissance} {t.prenom}".strip()
    return t.raison_sociale


def _titulaire_siret(t: Titulaire) -> str:
    if isinstance(t, PersonneMorale):
        return t.siret or t.siren
    return ""


def _titulaire_siren(t: Titulaire) -> str:
    if isinstance(t, PersonneMorale):
        return t.siren
    return ""


# ---------------------------------------------------------------------------
# Préparation des valeurs pour CERFA 13757
# ---------------------------------------------------------------------------

def _build_13757_values(
    mandant: Titulaire,
    mandataire: Mandataire,
    vehicule: Vehicule,
    fait_a: str,
    date_signature: date | None,
) -> dict[str, str]:
    """Construit le dictionnaire de valeurs pour le CERFA 13757."""

    adresse = mandant.adresse
    jour, mois, annee = _fmt_date_parts(date_signature)

    return {
        # Mandant
        "mandant_nom_prenom": _titulaire_nom_complet(mandant),
        "mandant_siret": _titulaire_siret(mandant),
        "mandant_num_voie": adresse.numero_voie,
        "mandant_extension": adresse.extension,
        "mandant_type_voie": adresse.type_voie,
        "mandant_nom_voie": adresse.libelle_voie,
        "mandant_code_postal": adresse.code_postal,
        "mandant_commune": adresse.commune,
        "mandant_pays": adresse.pays,

        # Mandataire
        "mandataire_nom_raison": mandataire.nom_raison_sociale,
        "mandataire_siret": mandataire.siret,

        # Description de l'opération
        "operation_immatriculation": "Immatriculation du véhicule",

        # Véhicule
        "vehicule_marque": vehicule.marque,
        "vehicule_vin": vehicule.numero_vin,
        "vehicule_immatriculation": vehicule.numero_immatriculation,

        # Date / Lieu de signature
        "fait_a": fait_a,
        "date_jour": jour,
        "date_mois": mois,
        "date_annee": annee,
    }


# ---------------------------------------------------------------------------
# Préparation des valeurs pour CERFA 13750
# ---------------------------------------------------------------------------

_TYPE_CERTIFICAT_KEY_MAP = {
    TypeCertificat.CERTIFICAT: "case_certificat",
    TypeCertificat.DUPLICATA: "case_duplicata",
    TypeCertificat.CORRECTION: "case_correction",
    TypeCertificat.CHANGEMENT_DOMICILE: "case_changement_domicile",
}


def _build_13750_values(
    titulaire: Titulaire,
    vehicule: Vehicule,
    type_certificat: TypeCertificat,
    fait_a: str,
    date_signature: date | None,
) -> dict[str, str]:
    """Construit le dictionnaire de valeurs pour le CERFA 13750."""

    adresse = titulaire.adresse
    jour_s, mois_s, annee_s = _fmt_date_parts(date_signature)

    values: dict[str, str] = {
        # Véhicule
        "vehicule_immatriculation": vehicule.numero_immatriculation,
        "vehicule_date_achat": _fmt_date(vehicule.date_achat),
        "vehicule_date_premiere_immat": _fmt_date(vehicule.date_premiere_immatriculation),
        "vehicule_numero_formule": vehicule.numero_formule,
        "vehicule_marque": vehicule.marque,
        "vehicule_denomination": vehicule.denomination_commerciale,
        "vehicule_tvv": vehicule.type_variante_version,
        "vehicule_vin": vehicule.numero_vin,
        "vehicule_genre": vehicule.genre_national,

        # Titulaire – identité
        "titulaire_nom_prenom": _titulaire_nom_complet(titulaire),
        "titulaire_siren": _titulaire_siren(titulaire),

        # Adresse
        "titulaire_etage": adresse.etage_appartement,
        "titulaire_immeuble": adresse.immeuble_residence,
        "titulaire_num_voie": adresse.numero_voie,
        "titulaire_extension": adresse.extension,
        "titulaire_type_voie": adresse.type_voie,
        "titulaire_libelle_voie": adresse.libelle_voie,
        "titulaire_lieu_dit": adresse.lieu_dit,
        "titulaire_code_postal": adresse.code_postal,
        "titulaire_commune": adresse.commune,

        # Signature
        "titulaire_fait_a": fait_a,
        "titulaire_date_signature": _fmt_date(date_signature),
    }

    # Données spécifiques aux personnes physiques
    if isinstance(titulaire, PersonnePhysique):
        j, m, a = _fmt_date_parts(titulaire.date_naissance)
        values.update({
            "titulaire_personne_physique": "X",
            "titulaire_sexe_m": "X" if titulaire.civilite.value == "M" else "",
            "titulaire_sexe_f": "X" if titulaire.civilite.value == "Mme" else "",
            "titulaire_nom_usage": titulaire.nom_usage,
            "titulaire_naissance_jour": j,
            "titulaire_naissance_mois": m,
            "titulaire_naissance_annee": a,
            "titulaire_commune_naissance": titulaire.commune_naissance,
            "titulaire_departement_naissance": titulaire.departement_naissance,
            "titulaire_pays_naissance": titulaire.pays_naissance,
            "titulaire_telephone": titulaire.telephone,
            "titulaire_email": titulaire.email,
        })
    else:
        values["titulaire_personne_morale"] = "X"

    # Case type de certificat
    checkbox_key = _TYPE_CERTIFICAT_KEY_MAP.get(type_certificat)
    if checkbox_key:
        values[checkbox_key] = "X"

    return values


# ---------------------------------------------------------------------------
# Service principal
# ---------------------------------------------------------------------------

class CerfaGeneratorService:
    """
    Service de haut niveau pour la génération des CERFA SIV.

    Usage :
        service = CerfaGeneratorService(output_dir=Path("output"))
        results = service.process(demarche)
        # results = {"13757": Path("output/cerfa_13757.pdf"), ...}
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process(self, demarche: Demarche, prefix: str = "") -> dict[str, Path]:
        """
        Point d'entrée principal : analyse la démarche et génère les CERFA adaptés.

        Returns:
            Dictionnaire {cerfa_id: chemin_pdf}
        """
        if isinstance(demarche, DemarcheChangementProprietaire):
            return self._process_changement_proprietaire(demarche, prefix)
        elif isinstance(demarche, DemarcheDeclarationCession):
            return self._process_declaration_cession(demarche, prefix)
        else:
            raise ValueError(f"Type de démarche non supporté : {type(demarche)}")

    def _process_changement_proprietaire(
        self, demarche: DemarcheChangementProprietaire, prefix: str
    ) -> dict[str, Path]:
        """Génère CERFA 13750 + CERFA 13757 pour un changement de propriétaire."""
        results: dict[str, Path] = {}

        # ── CERFA 13757 ────────────────────────────────────────────────────
        values_13757 = _build_13757_values(
            mandant=demarche.nouveau_titulaire,
            mandataire=demarche.mandataire,
            vehicule=demarche.vehicule,
            fait_a=demarche.fait_a,
            date_signature=demarche.date_signature,
        )
        out_13757 = self.output_dir / f"{prefix}cerfa_13757.pdf"
        generate_cerfa_pdf("13757", values_13757, CERFA_13757_FIELDS, out_13757)
        results["13757"] = out_13757

        # ── CERFA 13750 ────────────────────────────────────────────────────
        values_13750 = _build_13750_values(
            titulaire=demarche.nouveau_titulaire,
            vehicule=demarche.vehicule,
            type_certificat=demarche.type_certificat,
            fait_a=demarche.fait_a,
            date_signature=demarche.date_signature,
        )
        out_13750 = self.output_dir / f"{prefix}cerfa_13750.pdf"
        generate_cerfa_pdf("13750", values_13750, CERFA_13750_FIELDS, out_13750)
        results["13750"] = out_13750

        return results

    def _process_declaration_cession(
        self, demarche: DemarcheDeclarationCession, prefix: str
    ) -> dict[str, Path]:
        """Génère uniquement le CERFA 13757 pour une déclaration de cession."""
        values_13757 = _build_13757_values(
            mandant=demarche.vendeur,
            mandataire=demarche.mandataire,
            vehicule=demarche.vehicule,
            fait_a=demarche.fait_a,
            date_signature=demarche.date_signature,
        )
        out_13757 = self.output_dir / f"{prefix}cerfa_13757.pdf"
        generate_cerfa_pdf("13757", values_13757, CERFA_13757_FIELDS, out_13757)
        return {"13757": out_13757}
