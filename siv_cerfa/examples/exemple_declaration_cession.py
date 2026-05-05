"""
Exemple : Déclaration de cession
Génère uniquement le CERFA 13757
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.siv import (
    DemarcheDeclarationCession,
    PersonnePhysique,
    Vehicule,
    Mandataire,
    AdressePostale,
    Civilite,
)
from src.services.cerfa_service import CerfaGeneratorService


def main():
    # ── Vendeur ────────────────────────────────────────────────────────────
    vendeur = PersonnePhysique(
        civilite=Civilite.MME,
        nom_naissance="BERNARD",
        prenom="Sophie",
        date_naissance=date(1972, 9, 3),
        commune_naissance="Bordeaux",
        departement_naissance="33",
        adresse=AdressePostale(
            numero_voie="8",
            type_voie="Allée",
            libelle_voie="des Roses",
            code_postal="33000",
            commune="Bordeaux",
            pays="France",
        ),
        telephone="0698765432",
        email="sophie.bernard@email.com",
    )

    vehicule = Vehicule(
        numero_immatriculation="EF-456-GH",
        marque="PEUGEOT",
        denomination_commerciale="308",
        numero_vin="VF3LBBHYB6S012345",
        genre_national="VP",
        date_premiere_immatriculation=date(2021, 7, 1),
    )

    mandataire = Mandataire(
        nom_raison_sociale="AUTO SERVICES 33 SAS",
        siret="98765432100045",
    )

    demarche = DemarcheDeclarationCession(
        vendeur=vendeur,
        vehicule=vehicule,
        mandataire=mandataire,
        fait_a="Bordeaux",
        date_signature=date(2024, 11, 20),
    )

    output_dir = Path(__file__).parent.parent / "output"
    service = CerfaGeneratorService(output_dir=output_dir)
    results = service.process(demarche, prefix="cession_")

    print("\n✅ CERFA générés avec succès :")
    for cerfa_id, path in results.items():
        print(f"   CERFA {cerfa_id} → {path}")
    print("\n📋 Note : La déclaration de cession génère uniquement le CERFA 13757.")


if __name__ == "__main__":
    main()
