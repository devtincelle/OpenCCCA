from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from enum import Enum
import re


# ─────────────────────────────────────────────
# Severity + Issue + Result
# ─────────────────────────────────────────────

class Severity(str, Enum):
    ERROR   = "ERROR"
    WARNING = "WARNING"
    INFO    = "INFO"


@dataclass
class ValidationIssue:
    severity: Severity
    field: str
    message: str

    def __str__(self):
        return f"[{self.severity.value}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    entity: str
    key: str
    issues: List[ValidationIssue] = field(default_factory=list)

    def error(self, f: str, msg: str):
        self.issues.append(ValidationIssue(Severity.ERROR, f, msg))

    def warn(self, f: str, msg: str):
        self.issues.append(ValidationIssue(Severity.WARNING, f, msg))

    def info(self, f: str, msg: str):
        self.issues.append(ValidationIssue(Severity.INFO, f, msg))

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def summary(self) -> str:
        status = "✅ OK" if self.is_valid else "❌ INVALID"
        return f"{status}  {self.entity}({self.key})  — {len(self.errors)} error(s), {len(self.warnings)} warning(s)"

    def __str__(self):
        lines = [self.summary()]
        for issue in self.issues:
            lines.append(f"    {issue}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# Interface
# ─────────────────────────────────────────────

class IValidatable(ABC):

    @abstractmethod
    def validate(self) -> ValidationResult:
        """Run all checks and return a ValidationResult."""
        ...


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

ROMAN_PATTERN = re.compile(
    r'^(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))[AB]?$',
    re.IGNORECASE
)

HEADER_SIGNALS = ("emplois", "niveau", "coefficient", "les emplois")


# ─────────────────────────────────────────────
# Validators
# ─────────────────────────────────────────────

class ValidateJob:

    @staticmethod
    def validate(job) -> ValidationResult:
        name = (job.job_title or {}).get("male") or (job.job_title or {}).get("female") or "?"
        r = ValidationResult(entity="Job", key=name)

        if not job.job_title:
            r.error("job_title", "Missing entirely")
        else:
            male   = (job.job_title.get("male")   or "").strip()
            female = (job.job_title.get("female") or "").strip()

            if not male and not female:
                r.error("job_title", "Both male and female keys are empty")

            title = male or female
            if len(title) > 80:
                r.error("job_title", f"Title too long to be a job name ({len(title)} chars)")

            if any(title.lower().startswith(s) for s in HEADER_SIGNALS):
                r.error("job_title", f"Looks like a header row: {title[:40]!r}")

        if not any([job.monthly_salary, job.daily_salary, job.weekly_salary]):
            r.warn("salary", "No salary defined")

        return r


class ValidateFiliere:

    @staticmethod
    def validate(filiere) -> ValidationResult:
        r = ValidationResult(entity="Filiere", key=filiere.name or filiere.slug or "?")

        if not filiere.name:
            r.error("name", "Filiere has no name")
        if not filiere.slug:
            r.warn("slug", "No slug — equality checks may be unreliable")
        if not filiere.text:
            r.warn("text", "Empty text body")
        elif len(filiere.text.strip()) < 10:
            r.warn("text", f"Very short text ({len(filiere.text)} chars)")
        if not filiere.article:
            r.info("article", "Not linked to an article")

        return r


class ValidateArticle:

    @staticmethod
    def validate(article) -> ValidationResult:
        r = ValidationResult(entity="Article", key=f"{article.number or '?'}_{article.title or ''}")

        if not article.title:
            r.error("title", "No title")
        if not article.number:
            r.warn("number", "Article has no number")
        if not article.body:
            r.warn("body", "Empty body")
        if not article.pages:
            r.info("pages", "No page references recorded")
        if not article.source:
            r.warn("source", "No source document reference")

        for table in article.tables:
            tr = ValidateTable.validate(table)
            if not tr.is_valid:
                r.error("tables", f"Invalid table → {tr.summary()}")

        return r


class ValidateTable:

    @staticmethod
    def validate(table) -> ValidationResult:
        r = ValidationResult(entity="Table", key=table.key or f"table-{table.table_number}")

        if not table.rows:
            r.error("rows", "Table has no rows")
            return r

        row_lengths = [len(row) for row in table.rows]
        if len(set(row_lengths)) > 1:
            r.warn("rows", f"Inconsistent row widths: {sorted(set(row_lengths))}")

        empty_rows = sum(1 for row in table.rows if not any(str(c).strip() for c in row))
        if empty_rows:
            r.warn("rows", f"{empty_rows} fully-empty row(s)")

        if not table.article:
            r.info("article", "Table not linked to any article")
        if table.page_number is None:
            r.info("page_number", "No page number")

        return r


class ValidateCategory:

    @staticmethod
    def validate(category) -> ValidationResult:
        r = ValidationResult(entity="Category", key=category.number or category.name or "?")
        if not category.number:
            r.error("number", "Category has no number")
        elif not ROMAN_PATTERN.match(category.number.strip()):
            r.warn("number", f"Not a valid roman numeral (with optional A/B): {category.number!r}")
        return r


class ValidateSector:

    @staticmethod
    def validate(sector) -> ValidationResult:
        r = ValidationResult(entity="Sector", key=sector.number or sector.name or "?")
        if not sector.name:
            r.error("name", "Sector has no name")
        if not sector.number:
            r.warn("number", "Sector has no number")
        return r


class ValidatePage:

    @staticmethod
    def validate(page) -> ValidationResult:
        r = ValidationResult(entity="Page", key=page.key or page.number or "?")

        if not page.number:
            r.error("number", "Page has no number")

        return r


class ValidateConvention:

    @staticmethod
    def validate(convention) -> ValidationResult:
        r = ValidationResult(entity="Convention", key=convention.name or str(convention.id or "?"))

        if not convention.name:
            r.error("name", "Convention has no name")
        if not convention.articles:
            r.error("articles", "No articles parsed")
        else:
            r.info("articles", f"{len(convention.articles)} article(s)")
        if not convention.jobs:
            r.warn("jobs", "No jobs parsed")
        else:
            r.info("jobs", f"{len(convention.jobs)} job(s)")
        if not convention.filieres:
            r.warn("filieres", "No filieres parsed")

        for job in (convention.jobs or []):
            jr = ValidateJob.validate(job)
            if not jr.is_valid:
                r.error("jobs", f"Invalid job → {jr.summary()}")

        for filiere in (convention.filieres or []):
            fr = ValidateFiliere.validate(filiere)
            if not fr.is_valid:
                r.warn("filieres", f"Suspect filiere → {fr.summary()}")

        return r


# ─────────────────────────────────────────────
# Batch helpers
# ─────────────────────────────────────────────

def validate_all(items: List[IValidatable]) -> List[ValidationResult]:
    return [item.validate() for item in items]


def print_report(results: List[ValidationResult], only_invalid: bool = False):
    for r in results:
        if only_invalid and r.is_valid:
            continue
        print(r)
        print()