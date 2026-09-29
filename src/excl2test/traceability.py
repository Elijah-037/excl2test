"""Matrice de traçabilité : exigences -> conception -> tests -> résultats.

Ce module ne lance aucun test : il assemble des résultats déjà collectés
(voir tests/conftest.py) et produit un rapport Markdown et un fichier CSV.
"""

import csv
from dataclasses import dataclass

STATUS_VERIFIED = "VERIFIEE"
STATUS_FAILED = "ECHEC"
STATUS_NOT_COVERED = "NON COUVERTE"
STATUS_NOT_RUN = "NON VERIFIEE"


@dataclass(frozen=True)
class TestResult:
    __test__ = False  # empêche pytest de prendre cette classe pour un test

    nodeid: str
    exigence_ids: tuple
    outcome: str  # "passed", "failed" ou "skipped"


@dataclass(frozen=True)
class MatrixRow:
    exigence: object
    tests: tuple  # tuples (nodeid, outcome)
    status: str


def _status(outcomes):
    if not outcomes:
        return STATUS_NOT_COVERED
    if "failed" in outcomes:
        return STATUS_FAILED
    if all(o == "passed" for o in outcomes):
        return STATUS_VERIFIED
    return STATUS_NOT_RUN


def build_matrix(exigences, results):
    """Une ligne par exigence, avec ses tests et son statut."""
    rows = []
    for exg in exigences:
        tests = tuple(
            (r.nodeid, r.outcome) for r in results if exg.id in r.exigence_ids
        )
        rows.append(MatrixRow(exg, tests, _status([o for _, o in tests])))
    return rows


def orphan_tests(results):
    """Tests qui ne se rattachent à aucune exigence."""
    return [r.nodeid for r in results if not r.exigence_ids]


def _short(nodeid):
    """tests/test_x.py::test_y -> test_x.py::test_y"""
    return nodeid.replace("tests/", "").replace("tests\\", "")


def render_markdown(rows, results, generated_at):
    verified = sum(1 for r in rows if r.status == STATUS_VERIFIED)
    lines = [
        "# Matrice de traçabilité : exigences, conception, tests, résultats",
        "",
        f"Générée le {generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC à partir de {len(results)} test(s) exécuté(s).",
        f"Exigences vérifiées : {verified} sur {len(rows)}.",
        "",
        "| Exigence | Titre | Critère | Conception | Tests | Statut |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        passed = sum(1 for _, o in r.tests if o == "passed")
        lines.append(
            f"| {r.exigence.id} | {r.exigence.titre} | {r.exigence.critere} | "
            f"{r.exigence.conception} | {passed}/{len(r.tests)} | {r.status} |"
        )
    lines += ["", "## Détail par exigence", ""]
    for r in rows:
        lines.append(f"### {r.exigence.id} : {r.exigence.titre}")
        lines.append("")
        if not r.tests:
            lines.append("Aucun test rattaché.")
        for nodeid, outcome in r.tests:
            lines.append(f"- {_short(nodeid)} : {outcome}")
        lines.append("")
    orphans = orphan_tests(results)
    if orphans:
        lines += ["## Tests sans exigence rattachée", ""]
        lines += [f"- {_short(n)}" for n in orphans]
        lines.append("")
    return "\n".join(lines)


def write_markdown(rows, results, generated_at, path):
    path.write_text(render_markdown(rows, results, generated_at), encoding="utf-8")


def write_csv(rows, path):
    """CSV séparé par des points-virgules, avec BOM : s'ouvre correctement dans Excel FR."""
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(
            ["Exigence", "Titre", "Critere", "Conception", "Test", "Resultat", "Statut exigence"]
        )
        for r in rows:
            if not r.tests:
                writer.writerow(
                    [r.exigence.id, r.exigence.titre, r.exigence.critere,
                     r.exigence.conception, "", "", r.status]
                )
            for nodeid, outcome in r.tests:
                writer.writerow(
                    [r.exigence.id, r.exigence.titre, r.exigence.critere,
                     r.exigence.conception, _short(nodeid), outcome, r.status]
                )
