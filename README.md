# Convention Collective Parser

A Python pipeline for parsing French **conventions collectives** (collective labor agreements) from PDF and HTML sources into structured, validated, and enriched data.

---

## Overview

French conventions collectives are complex legal documents defining job classifications, salary grids, categories, and filieres for a given industry. This project scrapes, parses, validates, and enriches that data into clean JSON output.

The current implementation targets:
- **IDCC 2412** — Convention Collective de la Production de Films d'Animation (2015, 2021, 2024)

---

## Architecture

The pipeline follows a strict linear flow:

```
PDF / HTML
    │
    ▼
ConventionParser       — extracts raw Convention object from document
    │
    ▼
filter_invalid()       — removes entities that fail validation
    │
    ▼
enrich()               — imputes missing fields from existing data
    │
    ▼
get_dict()             — serializes to JSON-ready dict
```

Each scrapper targets a specific version of the document:

| Class | Source | Year |
|---|---|---|
| `ConventionScrapper2015` | PDF | 2015 |
| `ConventionScrapper2021` | PDF | 2021 |
| `ConventionScrapper2024` | HTML | 2024 |

---

## Project Structure

```
app/
├── main.py
├── model/
│   ├── Entities.py               # Data models (Convention, Job, Article, ...)
│   ├── Validation.py             # Validation logic (ValidateJob, ValidateFiliere, ...)
│   ├── Enrichment.py             # Enrichment logic (EnrichJob, EnrichFiliere, ...)
│   ├── ConventionParserPDF.py    # PDF parser
│   ├── ConventionParserHTML.py   # HTML parser
│   ├── JobParser.py              # Table-to-Job parser
│   ├── TableParser.py            # Raw table row parser
│   ├── ValueParser.py            # Cell value classifier and conformer
│   └── GuessContext.py           # Context object for value classification
└── utils/
    └── Utils.py                  # serialize, to_english, clean_text
```

---

## Entities

| Entity | Description |
|---|---|
| `Convention` | Top-level document — holds all other entities |
| `Article` | A numbered section of the document |
| `Job` | A job definition with title, salary, category, filiere |
| `Filiere` | A job family / branch (e.g. "Réalisation", "Administrative") |
| `Category` | A roman-numeral classification level (e.g. I, IIA, IV) |
| `Sector` | A sub-filiere grouping |
| `Table` | A raw parsed table from the document |
| `Page` | A page reference |

All entities implement `IValidatable` and the enrichable ones also implement `IEnrichable`.

---

## Validation

Each entity has a `validate()` method that returns a `ValidationResult`:

```python
result = job.validate()
print(result.is_valid)    # True / False
print(result.summary())   # ✅ OK  Job(Réalisateur) — 0 error(s), 1 warning(s)
print(result)             # full report with all issues
```

Issues are categorized by severity:

| Severity | Meaning |
|---|---|
| `ERROR` | Data is unusable — entity will be filtered out |
| `WARNING` | Suspicious but recoverable |
| `INFO` | Optional field missing |

`filter_invalid()` on `Convention` removes all entities with at least one `ERROR`, then nullifies dangling references on remaining jobs.

---

## Enrichment (Imputation)

After filtering, `enrich()` fills in missing fields from existing data:

**Salary inference** — all directions are covered:

| Known | Inferred |
|---|---|
| `monthly_salary` | `daily_salary`, `weekly_salary` |
| `daily_salary` | `monthly_salary`, `weekly_salary` |
| `weekly_salary` | `monthly_salary` |

**Cadre inference** — two-step:
1. From `category` — if category is in `{"IV", "V", "Hors catégorie"}` → `is_cadre = True`
2. Fallback from salary — if `monthly_salary >= 3000` → `is_cadre = True`

**Key generation** — `job.key` is generated from `serialize(job_title.male or female)` if missing.

**Slug inference** — `filiere.slug` is generated from `serialize(filiere.name)` if missing.

---

## Constants (Enrichment.py)

```python
WORKING_DAYS_PER_MONTH  = 21.67
WORKING_DAYS_PER_WEEK   = 5.0
WORKING_WEEKS_PER_YEAR  = 52
WORKING_MONTHS_PER_YEAR = 12
CADRE_SALARY_THRESHOLD  = 3000
CADRE_CATEGORIES        = {"IV", "V", "Hors catégorie"}
```

---

## Design Patterns

| Pattern | Where |
|---|---|
| **Pipeline** | `parse → filter_invalid → enrich → get_dict` |
| **Template Method** | `IValidatable`, `IEnrichable` — interface defines contract, each class implements it |
| **Strategy** | `ValueParser._content_guess_table` — dict of callables selected at runtime |
| **Factory** | `TableParser._to_job()` — builds a `Job` from raw table data |
| **Chain of Responsibility** | `Convention.filter_invalid()` and `enrich()` cascade down to children |
| **Value Object** | `ValidationResult`, `ValidationIssue` — data bags with no side effects |

---

## Running Tests

```bat
cd tests
run_test.bat
```

Output is saved to `tests/output/YYYYMMDD_HHMM/all/`.

---

## Requirements

- Python 3.11+
- pdfplumber
- beautifulsoup4