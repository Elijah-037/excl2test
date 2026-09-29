"""Ligne de commande : py -m excl2test <fichier.xlsx> [--sortie DOSSIER]

Codes de retour : 0 = fichier valide, 1 = anomalies détectées, 2 = fichier inexploitable.
Chaque exécution écrit un journal .log et un manifeste .json dans le dossier de sortie.
"""

import argparse
import sys

from .runner import check


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="excl2test", description="Prévalidation d'un fichier Excel de cas de test."
    )
    parser.add_argument("fichier", help="chemin du fichier .xlsx à valider")
    parser.add_argument(
        "--sortie",
        default="sorties",
        help="dossier où écrire le journal et le manifeste (défaut : sorties)",
    )
    args = parser.parse_args(argv)

    result = check(args.fichier, args.sortie)
    for line in result.lines:
        print(line)
    print(f"Journal   : {result.log_path}")
    print(f"Manifeste : {result.manifest_path}")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
