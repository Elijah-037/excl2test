"""Structures de données partagées par le parseur, le validateur et la CLI."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DictEntry:
    """Une ligne du dictionnaire de données : unité attendue et plage autorisée."""

    unit: str
    min: float
    max: float


@dataclass(frozen=True)
class RawCase:
    """Une ligne de la feuille de cas de test, telle que lue (aucune interprétation)."""

    row: int  # numéro de ligne Excel (l'en-tête est la ligne 1)
    values: dict[str, Any]  # nom de colonne -> valeur brute de la cellule


@dataclass(frozen=True)
class Issue:
    """Une anomalie détectée, localisée précisément et identifiée par un code stable."""

    code: str
    sheet: str
    cell: str  # ex. "C2"
    message: str
    case_id: str | None = None
    severity: str = "ERREUR"
