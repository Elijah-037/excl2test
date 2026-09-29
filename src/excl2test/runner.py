"""Exécution complète d'une vérification : analyse, journal TXT et manifeste JSON.

Même quand le fichier est inexploitable, une trace est écrite : un échec non
archivé est un échec dont on ne peut rien prouver.
"""

import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, schema
from .manifest import build_manifest, sha256_file, write_manifest
from .parser import TemplateError, load
from .validator import validate

STATUS_VALID = "VALIDE"
STATUS_FAILED = "ECHEC"
STATUS_UNUSABLE = "INEXPLOITABLE"

EXIT_CODES = {STATUS_VALID: 0, STATUS_FAILED: 1, STATUS_UNUSABLE: 2}


@dataclass(frozen=True)
class CheckResult:
    status: str
    exit_code: int
    lines: list  # lignes de résultat, affichées à l'écran et écrites dans le journal
    log_path: Path
    manifest_path: Path


def format_issue(issue):
    ident = f" ({issue.case_id})" if issue.case_id else ""
    return f"{issue.severity} [{issue.code}] {issue.sheet}!{issue.cell}{ident} : {issue.message}"


def check(path, output_dir="sorties", now=None):
    """Analyse un fichier, écrit le journal et le manifeste, renvoie le résultat."""
    now = now or datetime.now(timezone.utc)
    path = Path(path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sha = sha256_file(path) if path.is_file() else None

    cases, dictionary, issues, fatal = [], None, [], None
    try:
        cases, dictionary = load(path)
        issues = validate(cases, dictionary)
    except TemplateError as exc:
        fatal = str(exc)

    lines = [f"Fichier : {path}"]
    if sha:
        lines.append(f"SHA-256 : {sha}")

    if fatal:
        status = STATUS_UNUSABLE
        lines.append(f"ERREUR DE STRUCTURE : {fatal}")
        lines.append("Résultat : INEXPLOITABLE - analyse interrompue.")
    elif issues:
        status = STATUS_FAILED
        lines.extend(format_issue(i) for i in issues)
        rows = len({i.cell[1:] for i in issues})
        lines.append(
            f"Résultat : ECHEC - {len(issues)} anomalie(s) sur {rows} ligne(s), {len(cases)} cas lus."
        )
    else:
        status = STATUS_VALID
        lines.append(f"Résultat : VALIDE - {len(cases)} cas lus, aucune anomalie.")

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    base = output_dir / f"{path.stem}_{stamp}"
    log_path = base.with_suffix(".log")
    manifest_path = base.with_suffix(".json")

    header = [
        f"excl2test {__version__} - template {schema.TEMPLATE_VERSION}",
        f"Horodatage (UTC) : {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Python : {platform.python_version()}",
    ]
    log_path.write_text("\n".join(header + lines) + "\n", encoding="utf-8")

    manifest = build_manifest(path, sha, status, len(cases), issues, dictionary, now, fatal)
    write_manifest(manifest, manifest_path)

    return CheckResult(status, EXIT_CODES[status], lines, log_path, manifest_path)
