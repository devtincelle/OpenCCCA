# Parseur de Convention Collective

Un pipeline Python pour extraire, valider et enrichir les données des **conventions collectives** françaises à partir de sources PDF et HTML.

---

## Vue d'ensemble

Les conventions collectives françaises sont des documents juridiques complexes définissant les classifications de postes, les grilles salariales, les catégories et les filières pour un secteur donné. Ce projet extrait, analyse, valide et enrichit ces données pour produire un JSON structuré.

L'implémentation actuelle cible :
- **IDCC 2412** — Convention Collective de la Production de Films d'Animation (2015, 2021, 2024)

---

## Architecture

Le pipeline suit un flux linéaire strict :

```
PDF / HTML
    │
    ▼
ConventionParser       — extrait l'objet Convention brut depuis le document
    │
    ▼
filter_invalid()       — supprime les entités qui échouent à la validation
    │
    ▼
enrich()               — impute les champs manquants à partir des données existantes
    │
    ▼
get_dict()             — sérialise en dict prêt pour JSON
```

Chaque scrapper cible une version spécifique du document :

| Classe | Source | Année |
|---|---|---|
| `ConventionScrapper2015` | PDF | 2015 |
| `ConventionScrapper2021` | PDF | 2021 |
| `ConventionScrapper2024` | HTML | 2024 |

---

## Structure du projet

```
app/
├── main.py
├── model/
│   ├── Entities.py               # Modèles de données (Convention, Job, Article, ...)
│   ├── Validation.py             # Logique de validation (ValidateJob, ValidateFiliere, ...)
│   ├── Enrichment.py             # Logique d'enrichissement (EnrichJob, EnrichFiliere, ...)
│   ├── ConventionParserPDF.py    # Parseur PDF
│   ├── ConventionParserHTML.py   # Parseur HTML
│   ├── JobParser.py              # Parseur de tables vers objets Job
│   ├── TableParser.py            # Parseur de lignes de tables brutes
│   ├── ValueParser.py            # Classificateur et conformateur de valeurs de cellules
│   └── GuessContext.py           # Objet contexte pour la classification des valeurs
└── utils/
    └── Utils.py                  # serialize, to_english, clean_text
```

---

## Entités

| Entité | Description |
|---|---|
| `Convention` | Document racine — contient toutes les autres entités |
| `Article` | Une section numérotée du document |
| `Job` | Une définition de poste avec titre, salaire, catégorie, filière |
| `Filiere` | Une famille de métiers (ex. "Réalisation", "Administrative et Commerciale") |
| `Category` | Un niveau de classification en chiffres romains (ex. I, IIA, IV) |
| `Sector` | Un sous-groupe de filière |
| `Table` | Une table brute extraite du document |
| `Page` | Une référence de page |

Toutes les entités implémentent `IValidatable`, et les entités enrichissables implémentent également `IEnrichable`.

---

## Validation

Chaque entité possède une méthode `validate()` qui retourne un `ValidationResult` :

```python
result = job.validate()
print(result.is_valid)    # True / False
print(result.summary())   # ✅ OK  Job(Réalisateur) — 0 erreur(s), 1 avertissement(s)
print(result)             # rapport complet avec tous les problèmes
```

Les problèmes sont classés par sévérité :

| Sévérité | Signification |
|---|---|
| `ERROR` | Donnée inutilisable — l'entité sera filtrée |
| `WARNING` | Suspect mais récupérable |
| `INFO` | Champ optionnel manquant |

`filter_invalid()` sur `Convention` supprime toutes les entités ayant au moins une `ERROR`, puis nullifie les références pendantes sur les jobs restants.

---

## Enrichissement (Imputation)

Après le filtrage, `enrich()` complète les champs manquants à partir des données existantes :

**Inférence salariale** — toutes les directions sont couvertes :

| Connu | Déduit |
|---|---|
| `monthly_salary` | `daily_salary`, `weekly_salary` |
| `daily_salary` | `monthly_salary`, `weekly_salary` |
| `weekly_salary` | `monthly_salary` |

**Inférence cadre** — en deux étapes :
1. Depuis la `category` — si la catégorie est dans `{"IV", "V", "Hors catégorie"}` → `is_cadre = True`
2. Repli depuis le salaire — si `monthly_salary >= 3000` → `is_cadre = True`

**Génération de clé** — `job.key` est généré depuis `serialize(job_title.male ou female)` si absent.

**Inférence de slug** — `filiere.slug` est généré depuis `serialize(filiere.name)` si absent.

---

## Constantes (Enrichment.py)

```python
WORKING_DAYS_PER_MONTH  = 21.67
WORKING_DAYS_PER_WEEK   = 5.0
WORKING_WEEKS_PER_YEAR  = 52
WORKING_MONTHS_PER_YEAR = 12
CADRE_SALARY_THRESHOLD  = 3000
CADRE_CATEGORIES        = {"IV", "V", "Hors catégorie"}
```

---

## Patrons de conception utilisés

| Patron | Où |
|---|---|
| **Pipeline** | `parse → filter_invalid → enrich → get_dict` |
| **Méthode Template** | `IValidatable`, `IEnrichable` — l'interface définit le contrat, chaque classe l'implémente |
| **Stratégie** | `ValueParser._content_guess_table` — dict de callables sélectionnés à l'exécution |
| **Fabrique** | `TableParser._to_job()` — construit un `Job` depuis des données de table brutes |
| **Chaîne de responsabilité** | `Convention.filter_invalid()` et `enrich()` se propagent aux enfants |
| **Objet Valeur** | `ValidationResult`, `ValidationIssue` — conteneurs de données sans effets de bord |

---

## Lancer les tests

```bat
cd tests
run_test.bat
```

Les résultats sont sauvegardés dans `tests/output/YYYYMMDD_HHMM/all/`.

---

## Prérequis

- Python 3.11+
- pdfplumber
- beautifulsoup4