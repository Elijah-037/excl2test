"""Catalogue des exigences du POC.

Chaque exigence est rattachée à un critère de réussite du cahier des charges
et à un module de conception. Les tests y renvoient avec le marqueur
@pytest.mark.exigence("EXG-01"), ce qui permet de générer la matrice
exigences -> conception -> tests -> résultats.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Exigence:
    id: str
    titre: str
    critere: str  # critère de réussite du cahier des charges (section 7)
    conception: str  # module(s) qui réalisent l'exigence


EXIGENCES = [
    Exigence(
        "EXG-01",
        "Vérifier la structure du template (feuilles, en-têtes) et refuser un fichier illisible",
        "Robustesse",
        "parser.py",
    ),
    Exigence(
        "EXG-02",
        "Ne jamais interpréter silencieusement une valeur ambiguë (nombre saisi en texte, champ vide)",
        "Robustesse",
        "validator.py",
    ),
    Exigence(
        "EXG-03",
        "Contrôler unités et plages des valeurs d'après le dictionnaire de données",
        "Robustesse",
        "validator.py, schema.py",
    ),
    Exigence(
        "EXG-04",
        "Signaler chaque anomalie par un code, une cellule et une cause, de façon reproductible",
        "Robustesse",
        "validator.py, models.py",
    ),
    Exigence(
        "EXG-05",
        "Détecter les identifiants mal formés ou en doublon et les exigences manquantes",
        "Robustesse",
        "validator.py",
    ),
    Exigence(
        "EXG-06",
        "Fournir des jeux d'essai de référence (un fichier valide, un fichier défectueux)",
        "Couverture",
        "sample_data.py",
    ),
    Exigence(
        "EXG-07",
        "Calculer l'empreinte SHA-256 des fichiers d'entrée",
        "Traçabilité",
        "manifest.py",
    ),
    Exigence(
        "EXG-08",
        "Produire un manifeste JSON (entrées, versions, horodatage, résultat, anomalies)",
        "Traçabilité",
        "manifest.py, runner.py",
    ),
    Exigence(
        "EXG-09",
        "Produire un journal TXT lisible de chaque exécution",
        "Traçabilité",
        "runner.py",
    ),
    Exigence(
        "EXG-10",
        "Tracer aussi les exécutions en échec (fichier absent ou inexploitable)",
        "Traçabilité",
        "runner.py",
    ),
    Exigence(
        "EXG-11",
        "Fournir des codes de retour exploitables par l'automatisation (CI)",
        "Transférabilité",
        "cli.py",
    ),
]
