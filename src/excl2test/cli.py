"""Ligne de commande : py -m excl2test <fichier.xlsx>

Codes de retour : 0 = fichier valide, 1 = anomalies détectées, 2 = fichier inexploitable.
"""

import argparse
import sys

from .parser import TemplateError, load
from .validator import validate


def format_issue(issue):
    ident = f" ({issue.case_id})" if issue.case_id else ""
    return f"{issue.severity} [{issue.code}] {issue.sheet}!{issue.cell}{ident} : {issue.message}"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="excl2test", description="Prévalidation d'un fichier Excel de cas de test."
    )
    parser.add_argument("fichier", help="chemin du fichier .xlsx à valider")
    args = parser.parse_args(argv)

    print(f"Fichier : {args.fichier}")
    try:
        cases, dictionary = load(args.fichier)
    except TemplateError as exc:
        print(f"ERREUR DE STRUCTURE : {exc}")
        print("Résultat : fichier inexploitable, analyse interrompue.")
        return 2

    issues = validate(cases, dictionary)
    for issue in issues:
        print(format_issue(issue))

    if issues:
        lines = len({i.cell[1:] for i in issues})
        print(f"Résultat : ÉCHEC - {len(issues)} anomalie(s) sur {lines} ligne(s), {len(cases)} cas lus.")
        return 1
    print(f"Résultat : VALIDE - {len(cases)} cas lus, aucune anomalie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
