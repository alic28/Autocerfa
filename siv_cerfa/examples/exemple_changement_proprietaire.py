"""
Exemple : Changement de propriétaire
Génère CERFA 13750 + CERFA 13757
"""
import sys
from datetime import date
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.siv import (
    DemarcheChangementProprietaire,
    PersonnePhysique,
    Vehicule,
    Mandataire,
    AdressePostale,
    Civilite,
    TypeCertificat,
)
from src.services.cerfa_service import CerfaGeneratorService


def main():
    # ── Nouveau propriétaire ───────────────────────────────────────────────
    nouveau_titulaire = PersonnePhysique(
        civilite=Civilite.M,
        nom_naissance="MARTIN",
        prenom="Jean",
        nom_usage="",
        date_naissance=date(1985, 6, 15),
        commune_naissance="Lyon",
        departement_naissance="69",
        pays_naissance="France",
        adresse=AdressePostale(
            numero_voie="12",
            extension="",
            type_voie="Rue",
            libelle_voie="de la Paix",
            code_postal="75001",
            commune="Paris",
            pays="France",
        ),
        telephone="0612345678",
        email="jean.martin@email.com",
    )

    # ── Véhicule ───────────────────────────────────────────────────────────
    vehicule = Vehicule(
        numero_immatriculation="AB-123-CD",
        marque="RENAULT",
        denomination_commerciale="CLIO",
        type_variante_version="ZEN",
        numero_vin="VF1RFB00060123456",
        genre_national="VP",
        energie="ES",
        puissance_fiscale="6",
        date_premiere_immatriculation=date(2019, 3, 20),
        date_achat=date(2024, 11, 15),
    )

    # ── Mandataire (garage) ────────────────────────────────────────────────
    mandataire = Mandataire(
        nom_raison_sociale="GARAGE DUPONT SAS",
        siret="12345678900012",
        adresse=AdressePostale(
            numero_voie="45",
            type_voie="Avenue",
            libelle_voie="des Champs",
            code_postal="75008",
            commune="Paris",
        ),
    )

    # ── Démarche ───────────────────────────────────────────────────────────
    demarche = DemarcheChangementProprietaire(
        nouveau_titulaire=nouveau_titulaire,
        vehicule=vehicule,
        mandataire=mandataire,
        type_certificat=TypeCertificat.CERTIFICAT,
        fait_a="Paris",
        date_signature=date(2024, 11, 15),
    )

    # ── Génération ─────────────────────────────────────────────────────────
    output_dir = Path(__file__).parent.parent / "output"
    service = CerfaGeneratorService(output_dir=output_dir)
    results = service.process(demarche, prefix="changement_proprietaire_")

    print("\n✅ CERFA générés avec succès :")
    for cerfa_id, path in results.items():
        print(f"   CERFA {cerfa_id} → {path}")


if __name__ == "__main__":
    main()
