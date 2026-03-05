from dataclasses import dataclass, field, fields, asdict
from typing import Any, Iterator, List, Optional, Dict

from utils.Utils import to_english, clean_text, serialize
from model.Validation import (IValidatable, ValidationResult,
                               ValidateJob, ValidateFiliere, ValidateArticle,
                               ValidateTable, ValidateCategory, ValidateSector,
                               ValidatePage, ValidateConvention)
from model.Enrichment import (IEnrichable,
                               EnrichJob, EnrichFiliere, EnrichArticle, EnrichConvention)


# ─────────────────────────────────────────────
# Convention
# ─────────────────────────────────────────────

@dataclass
class Convention(IValidatable, IEnrichable):
    id:           Optional[int]              = None
    name:         Optional[str]              = None
    version_name: Optional[str]              = None
    version_data: Optional[Dict]             = field(default_factory=dict)
    articles:     Optional[List['Article']]  = field(default_factory=list)
    jobs:         Optional[List['Job']]      = field(default_factory=list)
    categories:   Optional[List['Category']] = field(default_factory=list)
    filieres:     Optional[List['Filiere']]  = field(default_factory=list)
    sectors:      Optional[List['Sector']]   = field(default_factory=list)
    parsing_id:   int = None
    source:       str = None

    def get_dict(self) -> dict:
        return {
            "id":           self.id,
            "name":         self.name,
            "source":       self.source,
            "version_name": self.version_name,
            "version_data": self.version_data,
            "articles":     [item.get_dict() for item in self.articles],
            "categories":   [asdict(item) for item in self.categories],
            "jobs":         [asdict(item) for item in self.jobs],
            "filieres":     [asdict(item) for item in self.filieres],
            "sectors":      [asdict(item) for item in self.sectors],
        }

    def validate(self) -> ValidationResult:
        return ValidateConvention.validate(self)

    def enrich(self) -> "Convention":
        return EnrichConvention.enrich(self)

    def filter_invalid(self) -> "Convention":
        before_jobs       = len(self.jobs)
        before_filieres   = len(self.filieres)
        before_articles   = len(self.articles)
        before_categories = len(self.categories)
        before_sectors    = len(self.sectors)

        self.jobs       = [j for j in self.jobs       if j.validate().is_valid]
        self.filieres   = [f for f in self.filieres   if f.validate().is_valid]
        self.categories = [c for c in self.categories if c.validate().is_valid]
        self.sectors    = [s for s in self.sectors    if s.validate().is_valid]
        self.articles   = [a for a in self.articles   if a.validate().is_valid]
        for article in self.articles:
            article.tables = [t for t in article.tables if t.validate().is_valid]

        # nullify dangling refs on jobs
        valid_filieres   = {f.name for f in self.filieres}
        valid_categories = {c.name for c in self.categories}
        valid_sectors    = {s.name for s in self.sectors}

        for job in self.jobs:
            if job.filiere  not in valid_filieres:
                job.filiere = None
            if job.category not in valid_categories:
                job.category = None
            if job.sector  not in valid_sectors:
                job.sector = None

        print(f"Jobs       : {len(self.jobs)}/{before_jobs} kept")
        print(f"Filieres   : {len(self.filieres)}/{before_filieres} kept")
        print(f"Categories : {len(self.categories)}/{before_categories} kept")
        print(f"Sectors    : {len(self.sectors)}/{before_sectors} kept")
        print(f"Articles   : {len(self.articles)}/{before_articles} kept")
        return self


# ─────────────────────────────────────────────
# Article
# ─────────────────────────────────────────────

@dataclass
class Article(IValidatable, IEnrichable):
    start_line:   Optional[int]   = None
    name:         Optional[str]   = None
    title:        Optional[str]   = None
    number:       Optional[str]   = None
    coord:        Optional[str]   = None
    source:       Optional[str]   = None
    parsing_id:   Optional[int]   = None
    body:         List[str]       = field(default_factory=list)
    jobs:         List['Job']     = field(default_factory=list)
    sub_articles: List[str]       = field(default_factory=list)
    tables:       List['Table']   = field(default_factory=list)
    filieres:     List['Filiere'] = field(default_factory=list)
    pages:        List            = field(default_factory=list)

    def __str__(self) -> str:
        return f"<ARTICLE : {self.number} {self.title} --- {self.body[:20]}....{len(self.body)} >"

    def __repr__(self) -> str:
        return str(self)

    def add_sub_article(self, _sa):
        self.coord = self.coord or f"{self.number}"
        _sa.coord  = f"{self.coord}-{_sa.number}"
        self.sub_articles.append(_sa.get_key())

    def get_key(self) -> str:
        self.coord = self.coord or f"{self.number}"
        sanitized_title = to_english(self.title.lower()).split(" ")[0][:10]
        return f"{self.coord}_{sanitized_title}"

    def get_coord(self) -> str:
        return f"{self.number}"

    def get_dict(self) -> dict:
        return {
            "start_line":   self.start_line,
            "name":         self.name,
            "title":        self.title,
            "coord":        self.coord,
            "pages":        self.pages,
            "number":       self.number,
            "body":         self.body,
            "sub_articles": self.sub_articles,
            "filieres":     [f"{f.name}({f.start_line})" for f in self.filieres],
            "tables":       [asdict(t) for t in self.tables],
            "jobs":         [asdict(j) for j in self.jobs],
        }

    def validate(self) -> ValidationResult:
        return ValidateArticle.validate(self)

    def enrich(self) -> "Article":
        return EnrichArticle.enrich(self)


# ─────────────────────────────────────────────
# Filiere
# ─────────────────────────────────────────────

@dataclass
class Filiere(IValidatable, IEnrichable):
    start_line:  Optional[int] = None
    name:        Optional[str] = None
    number:      Optional[str] = None
    page_number: Optional[int] = None
    text:        Optional[str] = None
    slug:        Optional[str] = None
    article:     Optional[str] = None
    source:      str           = None
    parsing_id:  int           = None

    @property
    def id(self):
        return serialize(self.name)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Filiere):
            return NotImplemented
        return bool(self.name and other.name and serialize(self.slug) == serialize(other.slug))

    def merge_with(self, other: "Filiere") -> "Filiere":
        if not isinstance(other, Filiere):
            raise TypeError("Can only merge with another Filiere instance")
        def _pick(a, b):
            return a if a is not None else b
        return Filiere(
            start_line = _pick(self.start_line, other.start_line),
            name       = _pick(self.name,       other.name),
            slug       = _pick(self.slug,       other.slug),
            text       = (self.text or "") + (other.text or ""),
            article    = _pick(self.article,    other.article),
        )

    def has_job(self, _job_title: str) -> bool:
        if not _job_title or not self.text:
            return False
        job = to_english(_job_title.lower().replace(" ", ""))
        return job in self.text.lower().replace(" ", "")

    def validate(self) -> ValidationResult:
        return ValidateFiliere.validate(self)

    def enrich(self) -> "Filiere":
        return EnrichFiliere.enrich(self)


# ─────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────

@dataclass
class Category(IValidatable):
    start_line: Optional[int] = None
    name:       Optional[str] = None
    number:     Optional[str] = None
    key:        Optional[str] = None
    article:    Optional[str] = None
    parsing_id: Optional[int] = None

    def validate(self) -> ValidationResult:
        return ValidateCategory.validate(self)


# ─────────────────────────────────────────────
# Sector
# ─────────────────────────────────────────────

@dataclass
class Sector(IValidatable):
    start_line: Optional[int] = None
    name:       Optional[str] = None
    number:     Optional[str] = None
    key:        Optional[str] = None
    article:    Optional[str] = None
    parsing_id: Optional[int] = None

    def validate(self) -> ValidationResult:
        return ValidateSector.validate(self)


# ─────────────────────────────────────────────
# Job
# ─────────────────────────────────────────────

@dataclass
class Job(IValidatable, IEnrichable):
    key:            Optional[str]   = None
    start_line:     Optional[int]   = None
    job_title:      Optional[dict]  = None
    article:        Optional[dict]  = None
    page_number:    Optional[dict]  = None
    table_number:   Optional[dict]  = None
    category:       Optional[str]   = None
    position:       Optional[str]   = None
    sector:         Optional[str]   = None
    filiere:        Optional[str]   = None
    definition:     Optional[str]   = None
    monthly_salary: Optional[float] = None
    daily_salary:   Optional[float] = None
    weekly_salary:  Optional[float] = None
    is_cadre:       Optional[bool]  = None
    source:         Optional[str]   = None
    parsing_id:     Optional[int]   = None

    @property
    def id(self):
        return self.get_slug()

    def get_slug(self) -> str:
        if not self.job_title:
            return None
        name = self.job_title.get("male") or self.job_title.get("female")
        if name:
            return serialize(name)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        if not self.job_title or not other.job_title:
            return False
        return self.id == other.id

    def merge_with(self, other: "Job") -> "Job":
        if not isinstance(other, Job):
            raise TypeError("Can only merge with another Job instance")
        def _pick(a, b):
            return a if a is not None else b
        kwargs = {f.name: _pick(getattr(self, f.name), getattr(other, f.name))
                  for f in fields(self)}
        return Job(**kwargs)

    def validate(self) -> ValidationResult:
        return ValidateJob.validate(self)

    def enrich(self) -> "Job":
        return EnrichJob.enrich(self)


# ─────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────

@dataclass
class Page(IValidatable):
    number:   str  = None
    key:      str  = None
    document: str  = None
    filieres: list = field(default_factory=list)

    def validate(self) -> ValidationResult:
        return ValidatePage.validate(self)


# ─────────────────────────────────────────────
# Table
# ─────────────────────────────────────────────

@dataclass
class Table(IValidatable):
    article:      str             = None
    page_number:  int             = None
    table_number: int             = None
    key:          str             = None
    document:     str             = None
    rows:         list[list[Any]] = field(default_factory=list)

    def __iter__(self) -> Iterator[list[Any]]:
        return iter(self.rows)

    def clean(self):
        def _deep_flatten(row):
            if not isinstance(row, list):
                return [row]
            result = []
            for r in row:
                result.extend(_deep_flatten(r))
            return result

        clean_rows = []
        for row in self.rows:
            if not row:
                continue
            row = _deep_flatten(row)
            row = [(str(cell).replace("\n", " ").strip() if cell else "") for cell in row]
            if any(cell.strip() for cell in row):
                clean_rows.append(row)

        return Table(
            page_number  = self.page_number,
            key          = self.key,
            document     = self.document,
            rows         = clean_rows,
        )

    def validate(self) -> ValidationResult:
        return ValidateTable.validate(self)