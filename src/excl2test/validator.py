"""Prévalidation : règles appliquées à chaque cas de test, avant toute génération.

Principe : aucune interprétation silencieuse. Une valeur ambiguë (par exemple un
nombre saisi comme du texte) est signalée, jamais corrigée en douce.
Une ligne peut produire plusieurs anomalies, mais sans effet de cascade :
si le signal est inconnu, on ne juge pas son unité ni sa plage.
"""

import re

from openpyxl.utils import get_column_letter

from . import schema
from .models import Issue

ID_PATTERN = re.compile(r"^TC-\d{3}$")
REQ_PATTERN = re.compile(r"^REQ-[A-Z0-9]+-\d{3}$")


def _is_blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cell(column, row):
    return f"{get_column_letter(schema.CASES_COLUMNS.index(column) + 1)}{row}"


def validate(cases, dictionary):
    """Renvoie la liste des anomalies (vide = fichier valide)."""
    issues = []
    first_row_of_id = {}

    for case in cases:
        v, row = case.values, case.row
        case_id = v["ID"] if not _is_blank(v["ID"]) else None

        def add(code, column, message):
            issues.append(
                Issue(
                    code=code,
                    sheet=schema.SHEET_CASES,
                    cell=_cell(column, row),
                    message=message,
                    case_id=str(case_id) if case_id is not None else None,
                )
            )

        # --- Identifiant : présent, bien formé, unique
        if _is_blank(v["ID"]):
            add("FIELD_EMPTY", "ID", "identifiant vide")
        elif not ID_PATTERN.match(str(v["ID"])):
            add("ID_FORMAT", "ID", f"identifiant '{v['ID']}' invalide (format attendu : TC-001)")
        elif v["ID"] in first_row_of_id:
            add(
                "ID_DUPLICATE",
                "ID",
                f"identifiant '{v['ID']}' déjà utilisé ligne {first_row_of_id[v['ID']]}",
            )
        else:
            first_row_of_id[v["ID"]] = row

        # --- Exigence : présente et bien formée
        if _is_blank(v["Exigence"]):
            add("REQ_EMPTY", "Exigence", "exigence de rattachement vide (traçabilité impossible)")
        elif not REQ_PATTERN.match(str(v["Exigence"])):
            add("REQ_FORMAT", "Exigence", f"exigence '{v['Exigence']}' invalide (ex. REQ-DCDC-001)")

        # --- Entrée puis sortie : signal, unité, valeur
        for side, sig_col, val_col, unit_col in (
            ("entrée", "Signal_entree", "Valeur_entree", "Unite_entree"),
            ("sortie", "Signal_sortie", "Valeur_attendue", "Unite_sortie"),
        ):
            signal = v[sig_col]
            known = None
            if _is_blank(signal):
                add("FIELD_EMPTY", sig_col, f"signal de {side} vide")
            elif signal not in dictionary:
                add("SIGNAL_UNKNOWN", sig_col, f"signal '{signal}' absent du dictionnaire de données")
            else:
                known = dictionary[signal]

            if known is not None:
                unit = v[unit_col]
                if _is_blank(unit):
                    add("FIELD_EMPTY", unit_col, f"unité de {side} vide")
                elif unit != known.unit:
                    add(
                        "UNIT_MISMATCH",
                        unit_col,
                        f"unité '{unit}' incohérente avec '{signal}' (attendu : '{known.unit}')",
                    )

            value = v[val_col]
            if _is_blank(value):
                add("FIELD_EMPTY", val_col, f"valeur de {side} vide")
            elif not _is_number(value):
                add(
                    "VALUE_NOT_NUMERIC",
                    val_col,
                    f"valeur {value!r} non numérique (saisir un nombre, pas du texte)",
                )
            elif known is not None and not (known.min <= value <= known.max):
                add(
                    "OUT_OF_RANGE",
                    val_col,
                    f"valeur {value} hors plage [{known.min} ; {known.max}] pour '{signal}'",
                )

        # --- Tolérance
        tol = v["Tolerance_pct"]
        if _is_blank(tol):
            add("FIELD_EMPTY", "Tolerance_pct", "tolérance vide")
        elif not _is_number(tol):
            add("VALUE_NOT_NUMERIC", "Tolerance_pct", f"tolérance {tol!r} non numérique")
        elif not (0 <= tol <= 100):
            add("TOLERANCE_RANGE", "Tolerance_pct", f"tolérance {tol} % hors de l'intervalle [0 ; 100]")

    return issues
