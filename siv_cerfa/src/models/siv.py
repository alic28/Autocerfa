"""
Modèles de données pour les démarches SIV (Système d'Immatriculation des Véhicules).
Chaque modèle représente une entité métier utilisée lors de la génération des CERFA.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Énumérations
# ---------------------------------------------------------------------------

class TypeDemarche(str, Enum):
    """Types de démarches SIV supportées."""
    CHANGEMENT_PROPRIETAIRE = "changement_proprietaire"
    DECLARATION_CESSION = "declaration_cession"


class Civilite(str, Enum):
    M = "M"
    MME = "Mme"


class TypeTitulaire(str, Enum):
    PERSONNE_PHYSIQUE = "personne_physique"
    PERSONNE_MORALE = "personne_morale"


class TypeCertificat(str, Enum):
    """Cases à cocher sur le CERFA 13750."""
    CERTIFICAT = "certificat"
    DUPLICATA = "duplicata"
    CORRECTION = "correction"
    CHANGEMENT_DOMICILE = "changement_domicile"
    CHANGEMENT_ETAT_CIVIL = "changement_etat_civil"
    CHANGEMENT_CARACTERISTIQUES = "changement_caracteristiques"


# ---------------------------------------------------------------------------
# Entités métier
# ---------------------------------------------------------------------------

@dataclass
class AdressePostale:
    """Adresse postale complète."""
    numero_voie: str = ""
    extension: str = ""          # bis, ter, etc.
    type_voie: str = ""          # avenue, rue, boulevard, etc.
    libelle_voie: str = ""
    lieu_dit: str = ""
    code_postal: str = ""
    commune: str = ""
    pays: str = "France"
    etage_appartement: str = ""
    immeuble_residence: str = ""

    def ligne_voie(self) -> str:
        """Retourne la ligne d'adresse formatée."""
        parts = [p for p in [
            self.numero_voie, self.extension,
            self.type_voie, self.libelle_voie
        ] if p]
        return " ".join(parts)


@dataclass
class PersonnePhysique:
    """Représente une personne physique (titulaire ou vendeur)."""
    civilite: Civilite = Civilite.M
    nom_naissance: str = ""
    prenom: str = ""
    nom_usage: str = ""           # Nom d'époux(se)
    date_naissance: Optional[date] = None
    commune_naissance: str = ""
    departement_naissance: str = ""
    pays_naissance: str = "France"
    adresse: AdressePostale = field(default_factory=AdressePostale)
    telephone: str = ""
    email: str = ""

    @property
    def nom_complet(self) -> str:
        return f"{self.nom_naissance} {self.prenom}".strip()

    @property
    def type_titulaire(self) -> TypeTitulaire:
        return TypeTitulaire.PERSONNE_PHYSIQUE


@dataclass
class PersonneMorale:
    """Représente une personne morale (société)."""
    raison_sociale: str = ""
    siret: str = ""
    siren: str = ""
    representant_legal: str = ""
    adresse: AdressePostale = field(default_factory=AdressePostale)
    telephone: str = ""
    email: str = ""

    @property
    def type_titulaire(self) -> TypeTitulaire:
        return TypeTitulaire.PERSONNE_MORALE


# Type union pour un titulaire (personne physique ou morale)
Titulaire = PersonnePhysique | PersonneMorale


@dataclass
class Vehicule:
    """Informations du véhicule pour le CERFA 13750."""
    numero_immatriculation: str = ""
    marque: str = ""                        # D.1
    denomination_commerciale: str = ""      # D.3
    type_variante_version: str = ""         # D.2
    numero_vin: str = ""                    # E
    genre_national: str = ""               # J.1
    carrosserie: str = ""
    energie: str = ""
    puissance_fiscale: str = ""
    date_premiere_immatriculation: Optional[date] = None  # B
    date_achat: Optional[date] = None
    numero_formule: str = ""
    couleur: str = ""
    kilometrage: Optional[int] = None


@dataclass
class Mandataire:
    """Le professionnel qui reçoit le mandat (garage, concessionnaire)."""
    nom_raison_sociale: str = ""
    siret: str = ""
    adresse: AdressePostale = field(default_factory=AdressePostale)


# ---------------------------------------------------------------------------
# Démarches SIV
# ---------------------------------------------------------------------------

@dataclass
class DemarcheChangementProprietaire:
    """
    Démarche : Changement de propriétaire.
    Génère : CERFA 13750 + CERFA 13757
    """
    type_demarche: TypeDemarche = field(default=TypeDemarche.CHANGEMENT_PROPRIETAIRE, init=False)
    nouveau_titulaire: Titulaire = field(default_factory=PersonnePhysique)
    vehicule: Vehicule = field(default_factory=Vehicule)
    mandataire: Mandataire = field(default_factory=Mandataire)
    type_certificat: TypeCertificat = TypeCertificat.CERTIFICAT
    fait_a: str = ""
    date_signature: Optional[date] = None


@dataclass
class DemarcheDeclarationCession:
    """
    Démarche : Déclaration de cession.
    Génère : CERFA 13757 uniquement
    """
    type_demarche: TypeDemarche = field(default=TypeDemarche.DECLARATION_CESSION, init=False)
    vendeur: Titulaire = field(default_factory=PersonnePhysique)
    vehicule: Vehicule = field(default_factory=Vehicule)
    mandataire: Mandataire = field(default_factory=Mandataire)
    fait_a: str = ""
    date_signature: Optional[date] = None


# Type union pour toutes les démarches supportées
Demarche = DemarcheChangementProprietaire | DemarcheDeclarationCession
