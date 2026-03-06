import re
import os
import uuid
import pdfplumber

from typing import List, Dict, Optional
from dataclasses import asdict

from model.JobParser import JobParser
from model.ValueParser import ValueParser
from model.FiliereParser import FiliereParser
from model.Entities import Article, Filiere, Table, Job, Category, Convention, Sector
from utils.Utils import to_english, clean_text, parse_french_date


class ConventionParserPDF():

    def __init__(self):
        self._parsing_id:           str                  = str(uuid.uuid4())[-8:]
        self._article_table:        Dict[str, Article]   = {}
        self._articles:             List[Article]        = []
        self._jobs:                 List[Job]            = []
        self._filieres:             List[Filiere]        = []
        self._categories:           List[Category]       = []
        self._sectors:              List[Sector]         = []
        self._last_article_key:     Optional[str]        = None
        self._document_lines:       List[str]            = []
        self._line:                 int                  = -1
        self._document_version:     Optional[str]        = None
        self._document_version_data:Optional[dict]       = None
        self._document_name:        Optional[str]        = None
        self._job_parser:           JobParser            = JobParser()
        self._value_parser:         ValueParser          = ValueParser()
        self._filiere_parser:       FiliereParser        = FiliereParser()

    # ─────────────────────────────────────────
    # Entry point
    # ─────────────────────────────────────────

    def parse(self, _pdf: str = None) -> Optional[Convention]:
        if not _pdf:
            print("Error pdf is None")
            return None
        if not os.path.exists(_pdf):
            print("Error pdf does not exist:", _pdf)
            return None

        self._document_name = os.path.basename(_pdf)

        with pdfplumber.open(_pdf) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                if page_number == 1:
                    self.parse_document_version(page.extract_text())
                self.parse_page(page, page_number)

        self.parse_filieres()
        self.parse_sub_articles()
        self.parse_tables()
        self.parse_jobs()
        self._build_article_list()

        return Convention(
            parsing_id   = self._parsing_id,
            articles     = self._articles,
            jobs         = self._jobs,
            categories   = self._categories,
            sectors      = self._sectors,
            filieres     = self._filieres,
            name         = self._document_name,
            version_name = self._document_version,
            version_data = self._document_version_data,
        )

    # ─────────────────────────────────────────
    # Document version
    # ─────────────────────────────────────────

    def parse_convention_first_page(self, text: str) -> dict:
        data = {}

        title_match = re.match(r"^(.*?)(?:du|de) (\d{1,2} \w+ \d{4})", text)
        if title_match:
            data["title"]             = title_match.group(1).strip()
            data["date_of_signature"] = title_match.group(2).strip()

        extended_match = re.search(r"Etendue par arrêté le (\d{1,2} \w+ \d{4})", text)
        if extended_match:
            data["extended_by_order"] = parse_french_date(extended_match.group(1).strip())

        idcc_match = re.search(r"IDCC\s*:\s*(\d+)", text)
        if idcc_match:
            data["IDCC"] = int(idcc_match.group(1))

        brochure_match = re.search(r"Brochure n°\s*(\d+)", text)
        if brochure_match:
            data["brochure_number"] = int(brochure_match.group(1))

        version_match = re.search(r"Version consolidée au (\d+\w* \w+ \d{4})", text)
        if version_match:
            data["version_consolidated"] = str(parse_french_date(version_match.group(1).strip()))

        note_match = re.search(r"En italique\s*:\s*(.*)", text)
        if note_match:
            data["note"] = note_match.group(1).strip()

        return data

    def parse_document_version(self, _text: str) -> Optional[str]:
        data = self.parse_convention_first_page(_text)
        self._document_version_data = data

        idcc      = data.get("IDCC", "?")
        brochure  = data.get("brochure_number", "?")
        version   = data.get("version_consolidated", "?")

        self._document_version = f"IDCC-{idcc}_B-{brochure}_{version}"
        return self._document_version

    # ─────────────────────────────────────────
    # Article extraction
    # ─────────────────────────────────────────

    def extract_articles(self, texte: str, _start_line: int = None) -> List[Article]:
        pattern = re.compile(
            r'^(?:Article|Art\.?)\s*(\d+)\s*[-–—]\s*(.+?)$',
            re.IGNORECASE | re.UNICODE | re.MULTILINE
        )
        articles = []
        for numero, titre in pattern.findall(texte):
            titre = titre.strip()
            if re.search(r'\.{3,}\s*$', titre):
                continue
            article            = Article(_start_line)
            article.title      = titre.replace(".", "")
            article.number     = numero
            article.parsing_id = self._parsing_id
            articles.append(article)
        return articles

    def extract_sub_articles(self, texte: str, line_number: int) -> List[Article]:
        pattern = re.compile(r'^\s*(\d+(?:\.\d+)+)\.\s*(.+)$', re.MULTILINE)
        sous_articles = []
        for numero, titre in pattern.findall(texte):
            titre = titre.strip()
            if re.search(r'\.{3,}\s*$', titre):
                continue
            article        = Article(line_number)
            article.title  = titre.replace(".", "")
            article.number = numero
            sous_articles.append(article)
        return sous_articles

    # ─────────────────────────────────────────
    # Page parsing
    # ─────────────────────────────────────────

    def parse_page(self, page, _page_number: int):
        raw_text   = page.extract_text()
        raw_tables = page.extract_tables()
        lines      = raw_text.split('\n')
        current_key: Optional[str] = self._last_article_key

        for line in lines:
            self._line += 1
            self._document_lines.append(line)

            articles = self.extract_articles(line, self._line)
            if articles:
                current_key = articles[0].get_key()
                self._article_table[current_key] = articles[0]
                self._article_table[current_key].pages.append(_page_number)
                self._last_article_key = current_key
                continue

            if self._article_table.get(current_key):
                self._article_table[current_key].body.append(line)

        if self._article_table.get(current_key):
            for table_number, t in enumerate(raw_tables):
                table = Table(
                    article      = current_key,
                    page_number  = _page_number,
                    table_number = table_number,
                    rows         = t,
                ).clean()
                self._article_table[current_key].tables.append(table)

    # ─────────────────────────────────────────
    # Sub-article parsing
    # ─────────────────────────────────────────

    def parse_sub_articles(self):
        new_articles: List[Article] = []

        for key, article in self._article_table.items():
            line_number         = article.start_line
            current_subarticle: Optional[Article] = None
            raw_body            = article.body
            article.body        = []

            for line in raw_body:
                line_number += 1
                sub_articles = self.extract_sub_articles(line, line_number)
                if sub_articles:
                    if current_subarticle:
                        article.add_sub_article(current_subarticle)
                        new_articles.append(current_subarticle)
                    current_subarticle        = sub_articles[0]
                    current_subarticle.pages  = article.pages
                    continue
                if current_subarticle:
                    current_subarticle.body.append(line)
                else:
                    article.body.append(line)

        for sa in new_articles:
            self._article_table[sa.get_key()] = sa

    # ─────────────────────────────────────────
    # Filiere parsing
    # ─────────────────────────────────────────

    def parse_filieres(self) -> List[Filiere]:
        for article in self._article_table.values():
            line_number:          int              = article.start_line - 1
            last_filiere: Optional[Filiere]        = None

            for line in article.body:
                line_number += 1
                filiere = self._filiere_parser.parse_from_line(line)
                if filiere:
                    filiere.parsing_id = self._parsing_id
                    filiere.article    = article.get_key()
                    filiere.start_line = line_number
                    filiere.source     = self._document_version
                    last_filiere       = filiere
                    article.filieres.append(filiere)
                    continue
                if last_filiere:
                    if not last_filiere.text:
                        last_filiere.text = ""
                    last_filiere.text += to_english(clean_text(line.lower()).replace(" ", ""))

        merged: Dict[str, Filiere] = {}
        for article in self._article_table.values():
            for f in article.filieres:
                rep = next((k for k in merged if k == f), None)
                if rep is None:
                    merged[f.id] = f
                else:
                    merged[rep.id] = rep.merge_with(f)

        self._filieres = list(merged.values())
        return self._filieres

    # ─────────────────────────────────────────
    # Table + job parsing
    # ─────────────────────────────────────────

    def parse_tables(self):
        table_counter: int = -1

        for key, article in self._article_table.items():
            if not article.tables:
                continue

            for table in article.tables:
                table_counter      += 1
                table.table_number  = table_counter
                table.article       = article.get_key()

                jobs: List[Job] = self._job_parser.parse_jobs(table)

                for job in jobs:
                    job.source = self._document_version

                    # link job to filiere by title match
                    male   = (job.job_title or {}).get("male")   if job.job_title else None
                    female = (job.job_title or {}).get("female") if job.job_title else None
                    for f in self._filieres:
                        if f.has_job(male) or f.has_job(female):
                            job.filiere = f.name
                            break

                article.jobs.extend(jobs)

    def parse_jobs(self) -> List[Job]:
        """
        Return a single deduplicated list of Jobs.
        Duplicates (same __eq__) are merged via Job.merge_with().
        """
        merged: Dict[str, Job] = {}

        for article in self._article_table.values():
            for job in article.jobs:
                rep = next((k for k in merged if k == job), None)
                if rep is None:
                    merged[job.id] = job
                else:
                    merged[rep.id] = rep.merge_with(job)

        self._jobs = list(merged.values())
        for job in self._jobs:
            job.parsing_id = self._parsing_id

        return self._jobs

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    def _build_article_list(self):
        self._articles = [a for a in self._article_table.values() if a]