"""Collecte des résultats de test et génération de la matrice de traçabilité.

À la fin de chaque exécution de pytest, la matrice exigences -> tests -> résultats
est écrite dans sorties/matrice_tracabilite.md et sorties/matrice_tracabilite.csv.
"""

from datetime import datetime, timezone

from excl2test.exigences import EXIGENCES
from excl2test.traceability import (
    STATUS_VERIFIED,
    TestResult,
    build_matrix,
    write_csv,
    write_markdown,
)

_ids_by_nodeid = {}
_outcomes = {}


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "exigence(*ids): rattache le test à une ou plusieurs exigences (ex. EXG-01)"
    )


def pytest_collection_modifyitems(items):
    for item in items:
        ids = []
        for mark in item.iter_markers(name="exigence"):
            ids.extend(mark.args)
        _ids_by_nodeid[item.nodeid] = tuple(ids)


def pytest_runtest_logreport(report):
    # On garde la phase "call" ; une erreur ou un skip en "setup" compte aussi.
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        outcome = "failed" if report.outcome == "failed" else report.outcome
        _outcomes[report.nodeid] = outcome


def pytest_terminal_summary(terminalreporter, config):
    results = [
        TestResult(nodeid, _ids_by_nodeid.get(nodeid, ()), outcome)
        for nodeid, outcome in _outcomes.items()
    ]
    if not results:
        return
    out_dir = config.rootpath / "sorties"
    out_dir.mkdir(exist_ok=True)
    rows = build_matrix(EXIGENCES, results)
    now = datetime.now(timezone.utc)
    write_markdown(rows, results, now, out_dir / "matrice_tracabilite.md")
    write_csv(rows, out_dir / "matrice_tracabilite.csv")
    verified = sum(1 for r in rows if r.status == STATUS_VERIFIED)
    terminalreporter.write_sep("-", "matrice de traçabilité")
    terminalreporter.write_line(
        f"{verified}/{len(rows)} exigences vérifiées -> sorties/matrice_tracabilite.md"
    )
