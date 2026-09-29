"""Traçabilité : empreinte SHA-256 des entrées et construction du manifeste JSON.

Le manifeste répond à la question « qu'est-ce qui a été analysé, avec quoi,
quand, et avec quel résultat ? » : il permet de rejouer et de prouver une exécution.
"""

import hashlib
import json
import platform

from . import __version__, schema


def sha256_file(path):
    """Empreinte SHA-256 d'un fichier (lecture par blocs, sans tout charger en mémoire)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_dictionary(dictionary):
    """Empreinte du dictionnaire de données : prouve quelle configuration a été utilisée."""
    canonical = {
        signal: {"unite": e.unit, "min": e.min, "max": e.max}
        for signal, e in sorted(dictionary.items())
    }
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(path, sha256, status, cases_count, issues, dictionary, now, fatal_message):
    """Assemble le manifeste (dictionnaire Python prêt à être écrit en JSON)."""
    return {
        "outil": "excl2test",
        "version_outil": __version__,
        "version_template": schema.TEMPLATE_VERSION,
        "horodatage_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": platform.python_version(),
        "fichier_entree": {
            "nom": path.name,
            "chemin": str(path),
            "taille_octets": path.stat().st_size if path.is_file() else None,
            "sha256": sha256,
        },
        "dictionnaire_sha256": sha256_dictionary(dictionary) if dictionary else None,
        "resultat": status,
        "erreur_structure": fatal_message,
        "nb_cas": cases_count,
        "nb_anomalies": len(issues),
        "anomalies": [
            {
                "code": i.code,
                "feuille": i.sheet,
                "cellule": i.cell,
                "cas": i.case_id,
                "message": i.message,
            }
            for i in issues
        ],
    }


def write_manifest(manifest, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
