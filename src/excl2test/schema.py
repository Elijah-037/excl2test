"""Contrat du template Excel : source unique de vérité.

Le générateur d'exemples, le parseur et les tests importent tous ce fichier.
Modifier le template = modifier ce fichier, et uniquement lui.
"""

TEMPLATE_VERSION = "0.1"

SHEET_CASES = "CasTest"
SHEET_DICT = "Dictionnaire"

# Colonnes attendues, dans cet ordre, sur la feuille des cas de test.
CASES_COLUMNS = [
    "ID",
    "Exigence",
    "Signal_entree",
    "Valeur_entree",
    "Unite_entree",
    "Signal_sortie",
    "Valeur_attendue",
    "Unite_sortie",
    "Tolerance_pct",
]

# Colonnes attendues sur la feuille du dictionnaire de données.
DICT_COLUMNS = ["Signal", "Unite", "Min", "Max", "Description"]

# Dictionnaire de données du convertisseur DC/DC (buck) : (signal, unité, min, max, description)
DICTIONARY = [
    ("Vin", "V", 8, 60, "Tension d'entrée"),
    ("Vout", "V", 0, 30, "Tension de sortie régulée"),
    ("Iload", "A", 0, 10, "Courant de charge"),
    ("Duty", "%", 0, 100, "Rapport cyclique"),
    ("Fsw", "kHz", 10, 500, "Fréquence de découpage"),
    ("Temp", "degC", -40, 125, "Température ambiante"),
]
