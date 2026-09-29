# excl2test

Prévalidation de cas de test décrits dans Excel, avec traçabilité des exécutions.

## Pourquoi ce projet

J'ai décidé d'entreprendre ce projet dans l'objectif de le présenter lors de mon entretien auprès de Safran lundi 5 octobre 2026. Je me suis donner pour objectif de me mettre dans la peau de leur alternant en outil logiciel de génération de procédures de test.

Dans les équipes qui vérifient des logiciels embarqués les cas de test sont souvent écrits à la main dans un tableau Excel avant d'être transformés en procédures de test. Une faute de frappe sur un nom de signal, une unité oubliée ou un nombre saisi comme du texte passent facilement inaperçus et l'erreur se retrouve ensuite dans les procédures générées. 
J'ai voulu construire à petite échelle une "solution" pour aider sur cette phase de vérification.

Un outil qui relit le tableau comme un correcteur d'orthographe et signale précisément ce qui ne va pas sans jamais corriger de lui-même.

Le cas d'usage est un convertisseur DC/DC de type buck : Les tests fixent une valeur d'entrée que j'ai choisi (tension, courant de charge, température, fréquence) et une tension de sortie attendue avec sa tolérance. 
Les données sont bien évidemment fictives je les ai inventées pour les besoins du POC.

## Ce que fait l'outil

Il lit un fichier `.xlsx` composé de deux feuilles `CasTest` pour les cas de test et `Dictionnaire` pour les signaux autorisés, leurs unités et leurs plages de valeurs. 
Il vérifie d'abord la structure du fichier... puis applique des règles à chaque ligne. Toute anomalie est signalée avec un code stable ainsi que la cellule exacte et la cause. 

À chaque exécution, l'outil écrit un journal texte et un fichier JSON qui contiennent l'empreinte SHA-256 du fichier analysé.. celle du dictionnaire, les versions de l'outil et du template mais aussi l'horodatage, le résultat et sans oublier la liste des anomalies. 
Une exécution en échec même si c'est sur un fichier absent ou illisible laisse quoi qu'il arrive elle aussi une trace.

## Installation

Il faut Python 3.11 ou plus récent. Sous Windows :

```
py -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
```

Sous macOS ou Linux :

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Utilisation

Générer les deux fichiers d'exemple, un valide et un volontairement défectueux, puis les analyser :

```
py -m excl2test.sample_data
py -m excl2test data\cas_valides.xlsx
py -m excl2test data\cas_invalides.xlsx
```

Sous macOS ou Linux, remplacer `py` par `python` et `\` par `/`. L'option `--sortie` change le dossier où sont écrits le journal et le manifeste (`sorties` par défaut).

Voici un extrait du résultat sur le fichier défectueux :

```
ERREUR [SIGNAL_UNKNOWN] CasTest!C2 (TC-101) : signal 'Vinn' absent du dictionnaire de données
ERREUR [UNIT_MISMATCH] CasTest!E5 (TC-104) : unité 'A' incohérente avec 'Vin' (attendu : 'V')
ERREUR [OUT_OF_RANGE] CasTest!D6 (TC-105) : valeur 500 hors plage [8 ; 60] pour 'Vin'
Résultat : ECHEC - 10 anomalie(s) sur 10 ligne(s), 10 cas lus.
```

Le code de retour du programme permet de l'appeler depuis un script ou un pipeline : 0 si le fichier est valide... 1 si des anomalies sont détectées... 2 si le fichier est inexploitable (absent).

# Règles de prévalidation

| Code | Signification |
|---|---|
| `FIELD_EMPTY` | champ obligatoire vide |
| `ID_FORMAT` | identifiant de cas mal formé (attendu : `TC-001`) |
| `ID_DUPLICATE` | identifiant déjà utilisé plus haut dans le fichier |
| `REQ_EMPTY`, `REQ_FORMAT` | exigence de rattachement absente ou mal formé |
| `SIGNAL_UNKNOWN` | signal absent du dictionnaire de données |
| `UNIT_MISMATCH` | unité différente de celle du dictionnaire |
| `VALUE_NOT_NUMERIC` | valeur ou tolérance saisie comme du texte |
| `OUT_OF_RANGE` | valeur hors de la plage autorisée pour le signal |
| `TOLERANCE_RANGE` | tolérance hors de l'intervalle 0 à 100 % |

Un choix de conception à connaître : si le signal d'une ligne est inconnu, l'outil ne juge pas l'unité ni la plage de ce signal, puisqu'il ne sait pas à quoi les comparer. Cela évite des messages en cascade qui seraient faux, mais cela oblige parfois à deux passages pour tout corriger sur une même ligne.

## Vérification et traçabilité

La suite de tests se lance avec `pytest`. Elle couvre les cas nominaux... les valeurs limites (les bornes de plage sont accepter et un dépassement infime est refusé) les fichiers cassés et la reproductibilité des résultats.

Chaque test est rattaché à une ou plusieurs exigences avec un marqueur `@pytest.mark.exigence("EXG-01")`. 
Les exigences sont décrites dans `src/excl2test/exigences.py`, avec le critère visé et le module de conception. 
À la fin de chaque exécution de `pytest`, une matrice exigences, conception, tests, résultats est écrite dans `sorties/matrice_tracabilite.md` et `sorties/matrice_tracabilite.csv`. 
Un test contrôle que chaque exigence est couverte par au moins un test et qu'aucun marqueur ne pointe vers une exigence inconnue.

Sur GitHub, le workflow `Tests` installe le projet sur Linux et sur Windows, lance `pytest` exécute l'outil sur les fichiers d'exemple et archive les traces produites.

## Structure du dépôt

----------------------------
src/excl2test/
    schema.py         contrat du template Excel (feuilles, colonnes, dictionnaire)
    parser.py         lecture du classeur et contrôle de structure
    validator.py      règles de prévalidation
    models.py         structures de données (anomalie, cas, entrée du dictionnaire)
    manifest.py       empreintes SHA-256 et manifeste JSON
    runner.py         exécution complète : analyse, journal, manifeste
    cli.py            ligne de commande
    exigences.py      catalogue des exigences
    traceability.py   génération de la matrice de traçabilité
    sample_data.py    fichiers d'exemple valide et défectueux
tests/                tests automatisés et collecte de la matrice
.github/workflows/    intégration continue
----------------------------

## Limites connues

Ce projet reste un prototype et je préfère en dire clairement les limites. 
Les données, le template et le dictionnaire sont inventés : ils illustrent la démarche mais ne reflètent aucun vrai projet, et un template réel demanderait d'adapter `schema.py` et les règles. 
L'outil ne génère rien dans Simulink et n'utilise pas MATLAB, il s'arrête à la prévalidation. Les cas de test génériques, les alias, la résolution récursive, la détection de cycles et de contradictions ne sont pas traités.

Le classeur est lu avec les valeurs mises en cache par Excel : une formule que le fichier n'a jamais calculée apparaît comme une cellule vide et sera signalée comme telle. 
La matrice de traçabilité est une base de travail, pas une démarche de qualification d'outil au sens d'une norme comme la DO-330.

J'ai réalisé ce projet avec l'aide de Claude (Anthropic) pour l'architecture et le code ; je l'ai relu, testé et je peux expliquer chaque module

## Suite envisager

La prochaine étape logique serait de traiter les cas génériques avec résolution récursive... détection de cycles et gestion des conflits, puis d'ajouter la génération des blocs Test Sequence et Test Assessment 
côté MATLAB et Simulink ce qui suppose d'avoir accès aux licences correspondantes mais bon je ne les ai pas...
