"""
Tests unitaires pour la logique métier SIV CERFA.
Exécution : python -m unittest discover tests/ -v  (depuis siv_cerfa/)
"""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.siv import (
    AdressePostale, Civilite, DemarcheChangementProprietaire,
    DemarcheDeclarationCession, Mandataire, PersonneMorale,
    PersonnePhysique, TypeCertificat, TypeDemarche, Vehicule,
)
from src.services.cerfa_service import (
    CerfaGeneratorService, _build_13757_values, _build_13750_values,
    _titulaire_nom_complet, _fmt_date,
)


def make_pp():
    return PersonnePhysique(
        civilite=Civilite.M, nom_naissance="DUPONT", prenom="Pierre",
        date_naissance=date(1990, 4, 12), commune_naissance="Nantes",
        departement_naissance="44",
        adresse=AdressePostale(numero_voie="3", type_voie="Rue",
                               libelle_voie="des Lilas", code_postal="44000", commune="Nantes"),
        telephone="0611223344", email="pierre.dupont@test.fr",
    )

def make_pm():
    return PersonneMorale(
        raison_sociale="TRANSPORT DU SUD SARL", siret="11122233300011",
        siren="111222333", representant_legal="Paul Leroy",
        adresse=AdressePostale(numero_voie="100", type_voie="Boulevard",
                               libelle_voie="de la Mer", code_postal="13000", commune="Marseille"),
    )

def make_vehicule():
    return Vehicule(
        numero_immatriculation="XY-789-ZA", marque="CITROEN",
        denomination_commerciale="C3", type_variante_version="FEEL",
        numero_vin="VF7SC9HZ0GJ123456", genre_national="VP",
        date_premiere_immatriculation=date(2020, 5, 10), date_achat=date(2024, 10, 1),
    )

def make_mandataire():
    return Mandataire(nom_raison_sociale="GARAGE LEBRUN", siret="55566677700099")


class TestModeles(unittest.TestCase):

    def test_nom_complet_physique(self):
        pp = make_pp()
        self.assertEqual(pp.nom_complet, "DUPONT Pierre")

    def test_adresse_ligne_voie_complete(self):
        a = AdressePostale(numero_voie="12", extension="bis",
                           type_voie="Avenue", libelle_voie="Victor Hugo")
        self.assertEqual(a.ligne_voie(), "12 bis Avenue Victor Hugo")

    def test_adresse_ligne_voie_sans_extension(self):
        a = AdressePostale(numero_voie="5", type_voie="Rue", libelle_voie="de la Gare")
        self.assertEqual(a.ligne_voie(), "5 Rue de la Gare")

    def test_nom_complet_personne_morale(self):
        self.assertEqual(_titulaire_nom_complet(make_pm()), "TRANSPORT DU SUD SARL")

    def test_fmt_date(self):
        self.assertEqual(_fmt_date(date(2024, 1, 5)), "05/01/2024")
        self.assertEqual(_fmt_date(None), "")


class TestDemarches(unittest.TestCase):

    def test_type_changement_proprietaire(self):
        d = DemarcheChangementProprietaire(
            nouveau_titulaire=make_pp(), vehicule=make_vehicule(), mandataire=make_mandataire()
        )
        self.assertEqual(d.type_demarche, TypeDemarche.CHANGEMENT_PROPRIETAIRE)

    def test_type_declaration_cession(self):
        d = DemarcheDeclarationCession(
            vendeur=make_pp(), vehicule=make_vehicule(), mandataire=make_mandataire()
        )
        self.assertEqual(d.type_demarche, TypeDemarche.DECLARATION_CESSION)


class TestBuildValues(unittest.TestCase):

    def test_13757_champs_cles(self):
        v = _build_13757_values(make_pp(), make_mandataire(), make_vehicule(),
                                "Nantes", date(2024, 11, 1))
        self.assertEqual(v["mandant_nom_prenom"], "DUPONT Pierre")
        self.assertEqual(v["mandant_code_postal"], "44000")
        self.assertEqual(v["vehicule_marque"], "CITROEN")
        self.assertEqual(v["vehicule_vin"], "VF7SC9HZ0GJ123456")
        self.assertEqual(v["fait_a"], "Nantes")
        self.assertEqual(v["date_jour"], "01")
        self.assertEqual(v["date_mois"], "11")
        self.assertEqual(v["date_annee"], "2024")

    def test_13750_personne_physique(self):
        v = _build_13750_values(make_pp(), make_vehicule(), TypeCertificat.CERTIFICAT,
                                "Nantes", date(2024, 11, 1))
        self.assertEqual(v["titulaire_personne_physique"], "X")
        self.assertEqual(v["titulaire_sexe_m"], "X")
        self.assertEqual(v["titulaire_sexe_f"], "")
        self.assertEqual(v["case_certificat"], "X")
        self.assertEqual(v["titulaire_nom_prenom"], "DUPONT Pierre")

    def test_13750_personne_morale(self):
        v = _build_13750_values(make_pm(), make_vehicule(), TypeCertificat.CERTIFICAT,
                                "Marseille", None)
        self.assertEqual(v["titulaire_personne_morale"], "X")
        self.assertEqual(v["titulaire_nom_prenom"], "TRANSPORT DU SUD SARL")
        self.assertEqual(v["titulaire_siren"], "111222333")

    def test_mandataire_dans_13757(self):
        v = _build_13757_values(make_pp(), make_mandataire(), make_vehicule(), "Lyon", None)
        self.assertEqual(v["mandataire_nom_raison"], "GARAGE LEBRUN")
        self.assertEqual(v["mandataire_siret"], "55566677700099")


class TestCerfaService(unittest.TestCase):

    @patch("src.services.cerfa_service.generate_cerfa_pdf")
    def test_changement_proprietaire_genere_2_cerfa(self, mock_gen):
        mock_gen.return_value = Path("/tmp/test.pdf")
        demarche = DemarcheChangementProprietaire(
            nouveau_titulaire=make_pp(), vehicule=make_vehicule(), mandataire=make_mandataire()
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            service = CerfaGeneratorService(output_dir=Path(tmpdir))
            results = service.process(demarche)

        self.assertIn("13757", results)
        self.assertIn("13750", results)
        self.assertEqual(mock_gen.call_count, 2)

    @patch("src.services.cerfa_service.generate_cerfa_pdf")
    def test_declaration_cession_genere_1_cerfa(self, mock_gen):
        mock_gen.return_value = Path("/tmp/test.pdf")
        demarche = DemarcheDeclarationCession(
            vendeur=make_pp(), vehicule=make_vehicule(), mandataire=make_mandataire()
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            service = CerfaGeneratorService(output_dir=Path(tmpdir))
            results = service.process(demarche)

        self.assertIn("13757", results)
        self.assertNotIn("13750", results)
        self.assertEqual(mock_gen.call_count, 1)

    @patch("src.services.cerfa_service.generate_cerfa_pdf")
    def test_cerfa_13757_appelé_avec_bons_params(self, mock_gen):
        mock_gen.return_value = Path("/tmp/test.pdf")
        demarche = DemarcheDeclarationCession(
            vendeur=make_pp(), vehicule=make_vehicule(), mandataire=make_mandataire(),
            fait_a="Paris", date_signature=date(2024, 12, 1),
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            service = CerfaGeneratorService(output_dir=Path(tmpdir))
            service.process(demarche)

        call_args = mock_gen.call_args
        self.assertEqual(call_args[0][0], "13757")
        field_values = call_args[0][1]
        self.assertEqual(field_values["vehicule_marque"], "CITROEN")
        self.assertEqual(field_values["fait_a"], "Paris")


if __name__ == "__main__":
    unittest.main(verbosity=2)
