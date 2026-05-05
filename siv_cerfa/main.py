#!/usr/bin/env python3
"""
Point d'entrée principal de l'application SIV CERFA.

Usage :
    python main.py --exemple changement    → génère exemple changement propriétaire
    python main.py --exemple cession       → génère exemple déclaration de cession
    python main.py --calibrer 13757        → génère image de calibration CERFA 13757
    python main.py --calibrer 13750        → génère image de calibration CERFA 13750
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description="Générateur automatique de CERFA SIV (13750 / 13757)"
    )
    parser.add_argument(
        "--exemple",
        choices=["changement", "cession"],
        help="Lancer un exemple de génération"
    )
    parser.add_argument(
        "--calibrer",
        choices=["13757", "13750"],
        help="Générer une image de calibration pour un CERFA"
    )

    args = parser.parse_args()

    if args.calibrer:
        from tools.calibrate import generate_calibration_image
        generate_calibration_image(args.calibrer)

    elif args.exemple == "changement":
        from examples.exemple_changement_proprietaire import main as run
        run()

    elif args.exemple == "cession":
        from examples.exemple_declaration_cession import main as run
        run()

    else:
        parser.print_help()
        print("\nExemples d'utilisation :")
        print("  python main.py --exemple changement")
        print("  python main.py --exemple cession")
        print("  python main.py --calibrer 13757")


if __name__ == "__main__":
    main()
