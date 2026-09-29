"""Vérification du parseur et des règles de prévalidation.

Chaque défaut de cas_invalides.xlsx doit produire exactement l'anomalie attendue,
sur la bonne cellule, et rien d'autre : c'est la stratégie « pas d'interprétation
silencieuse, erreurs explicites et reproductibles ».
"""

import pytest
from openpyxl import Workbook

from excl2test import schema
from excl2test.cli import main
from excl2test.parser import TemplateError, load
from excl2test.sample_data import generate
from excl2test.validator import validate


@pytest.fixture
def files(tmp_path):
    return generate(tmp_path)


def _issues(path):
    cases, dictionary = load(path)
    return validate(cases, dictionary)


# --- Cas nominal -----------------------------------------------------------

def test_valid_file_has_no_issue(files):
    valid_path, _ = files
    assert _issues(valid_path) == []


# --- Un défaut = une anomalie précise --------------------------------------

# (cellule Excel, code attendu) pour chacune des 10 lignes de cas_invalides.xlsx
EXPECTED_DEFECTS = [
    ("C2", "SIGNAL_UNKNOWN"),
    ("B3", "REQ_EMPTY"),
    ("D4", "VALUE_NOT_NUMERIC"),
    ("E5", "UNIT_MISMATCH"),
    ("D6", "OUT_OF_RANGE"),
    ("I7", "TOLERANCE_RANGE"),
    ("G8", "FIELD_EMPTY"),
    ("A9", "ID_FORMAT"),
    ("H10", "UNIT_MISMATCH"),
    ("A11", "ID_DUPLICATE"),
]


def test_invalid_file_gives_exactly_the_expected_issues(files):
    _, invalid_path = files
    found = [(i.cell, i.code) for i in _issues(invalid_path)]
    assert found == EXPECTED_DEFECTS


def test_issues_are_reproducible(files):
    _, invalid_path = files
    assert _issues(invalid_path) == _issues(invalid_path)


def test_duplicate_message_points_to_first_occurrence(files):
    _, invalid_path = files
    duplicate = [i for i in _issues(invalid_path) if i.code == "ID_DUPLICATE"][0]
    assert "ligne 2" in duplicate.message


# --- Robustesse : entrées ambiguës ou cassées ------------------------------

def _make_workbook(tmp_path, cases_rows, header=None):
    wb = Workbook()
    ws = wb.active
    ws.title = schema.SHEET_CASES
    ws.append(header or schema.CASES_COLUMNS)
    for row in cases_rows:
        ws.append(row)
    wd = wb.create_sheet(schema.SHEET_DICT)
    wd.append(schema.DICT_COLUMNS)
    for row in schema.DICTIONARY:
        wd.append(list(row))
    path = tmp_path / "custom.xlsx"
    wb.save(path)
    return path


def test_number_typed_as_text_is_reported_not_converted(tmp_path):
    path = _make_workbook(
        tmp_path, [("TC-001", "REQ-DCDC-001", "Vin", "48", "V", "Vout", 12.0, "V", 2)]
    )
    assert [(i.cell, i.code) for i in _issues(path)] == [("D2", "VALUE_NOT_NUMERIC")]


def test_boundary_values_are_accepted(tmp_path):
    path = _make_workbook(
        tmp_path,
        [
            ("TC-001", "REQ-DCDC-001", "Vin", 8, "V", "Vout", 0, "V", 0),
            ("TC-002", "REQ-DCDC-001", "Vin", 60, "V", "Vout", 30, "V", 100),
        ],
    )
    assert _issues(path) == []


def test_just_outside_boundary_is_rejected(tmp_path):
    path = _make_workbook(
        tmp_path, [("TC-001", "REQ-DCDC-001", "Vin", 60.01, "V", "Vout", 12.0, "V", 2)]
    )
    assert [i.code for i in _issues(path)] == ["OUT_OF_RANGE"]


def test_blank_rows_are_ignored(tmp_path):
    path = _make_workbook(
        tmp_path,
        [
            ("TC-001", "REQ-DCDC-001", "Vin", 48, "V", "Vout", 12.0, "V", 2),
            (None,) * 9,
        ],
    )
    cases, _ = load(path)
    assert len(cases) == 1


def test_wrong_header_raises_template_error(tmp_path):
    bad_header = list(schema.CASES_COLUMNS)
    bad_header[3] = "Valeur"
    path = _make_workbook(tmp_path, [], header=bad_header)
    with pytest.raises(TemplateError, match="D1"):
        load(path)


def test_missing_file_raises_template_error(tmp_path):
    with pytest.raises(TemplateError, match="introuvable"):
        load(tmp_path / "absent.xlsx")


def test_not_an_excel_file_raises_template_error(tmp_path):
    fake = tmp_path / "faux.xlsx"
    fake.write_text("ceci n'est pas un classeur")
    with pytest.raises(TemplateError):
        load(fake)


# --- Ligne de commande : codes de retour -----------------------------------

def test_cli_exit_codes(files, tmp_path, capsys):
    valid_path, invalid_path = files
    out_dir = str(tmp_path / "sorties")
    assert main([str(valid_path), "--sortie", out_dir]) == 0
    assert main([str(invalid_path), "--sortie", out_dir]) == 1
    assert main([str(tmp_path / "absent.xlsx"), "--sortie", out_dir]) == 2
    out = capsys.readouterr().out
    assert "VALIDE" in out and "ECHEC" in out and "INEXPLOITABLE" in out
