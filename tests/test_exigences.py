"""Contrôle du catalogue d'exigences et du générateur de matrice.

Le contrôle de couverture lit le code source des tests (et non l'exécution) :
il ne dépend donc pas des tests sélectionnés avec -k ou d'un lancement partiel.
"""

import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from excl2test.exigences import EXIGENCES
from excl2test.traceability import (
    STATUS_FAILED,
    STATUS_NOT_COVERED,
    STATUS_NOT_RUN,
    STATUS_VERIFIED,
    TestResult,
    build_matrix,
    orphan_tests,
    render_markdown,
    write_csv,
)

TESTS_DIR = Path(__file__).parent
NOW = datetime(2026, 10, 3, 9, 0, 0, tzinfo=timezone.utc)


def _referenced_ids():
    """Identifiants cités dans les marqueurs @pytest.mark.exigence(...) des fichiers de test."""
    found = set()
    for path in TESTS_DIR.glob("test_*.py"):
        if path.name == Path(__file__).name:
            continue
        for call in re.findall(r"pytest\.mark\.exigence\(([^)]*)\)", path.read_text(encoding="utf-8")):
            found.update(re.findall(r"EXG-\d+", call))
    return found


# --- Cohérence du catalogue ------------------------------------------------

@pytest.mark.exigence("EXG-04")
def test_catalog_ids_are_unique():
    ids = [e.id for e in EXIGENCES]
    assert len(ids) == len(set(ids))


def test_every_exigence_is_covered_by_at_least_one_test():
    missing = {e.id for e in EXIGENCES} - _referenced_ids()
    assert not missing, f"exigences sans test : {sorted(missing)}"


def test_every_marker_points_to_an_existing_exigence():
    unknown = _referenced_ids() - {e.id for e in EXIGENCES}
    assert not unknown, f"marqueurs vers des exigences inconnues (faute de frappe ?) : {sorted(unknown)}"


# --- Générateur de matrice -------------------------------------------------

def _results():
    return [
        TestResult("tests/a.py::t1", ("EXG-01",), "passed"),
        TestResult("tests/a.py::t2", ("EXG-01", "EXG-02"), "passed"),
        TestResult("tests/a.py::t3", ("EXG-02",), "failed"),
        TestResult("tests/a.py::t4", ("EXG-03",), "skipped"),
        TestResult("tests/a.py::t5", (), "passed"),
    ]


def test_matrix_statuses():
    rows = {r.exigence.id: r for r in build_matrix(EXIGENCES[:4], _results())}
    assert rows["EXG-01"].status == STATUS_VERIFIED
    assert rows["EXG-02"].status == STATUS_FAILED
    assert rows["EXG-03"].status == STATUS_NOT_RUN
    assert rows["EXG-04"].status == STATUS_NOT_COVERED


def test_a_test_can_cover_several_exigences():
    rows = {r.exigence.id: r for r in build_matrix(EXIGENCES[:2], _results())}
    assert ("tests/a.py::t2", "passed") in rows["EXG-01"].tests
    assert ("tests/a.py::t2", "passed") in rows["EXG-02"].tests


def test_orphan_tests_are_listed():
    assert orphan_tests(_results()) == ["tests/a.py::t5"]


def test_markdown_contains_table_and_orphans():
    rows = build_matrix(EXIGENCES[:4], _results())
    md = render_markdown(rows, _results(), NOW)
    assert "| EXG-01 |" in md and "VERIFIEE" in md and "NON COUVERTE" in md
    assert "Tests sans exigence rattachée" in md and "a.py::t5" in md


def test_csv_has_one_line_per_test_and_one_for_uncovered(tmp_path):
    rows = build_matrix(EXIGENCES[:4], _results())
    out = tmp_path / "m.csv"
    write_csv(rows, out)
    with open(out, encoding="utf-8-sig", newline="") as handle:
        lines = list(csv.reader(handle, delimiter=";"))
    # en-tête + t1, t2 (EXG-01) + t2, t3 (EXG-02) + t4 (EXG-03) + ligne vide (EXG-04)
    assert len(lines) == 1 + 2 + 2 + 1 + 1
