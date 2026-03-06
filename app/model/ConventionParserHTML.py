import os
import uuid
import re

from typing import Optional, List
from bs4 import BeautifulSoup

from model.Entities import Article, Filiere, Table, Job, Category, Convention, Sector
from model.JobParser import JobParser
from model.ValueParser import ValueParser
from model.FiliereParser import FiliereParser
from utils.Utils import to_english, clean_text, parse_french_date, serialize


class ConventionParserHTML:

    def __init__(self):
        self._parsing_id:   int         = int(uuid.uuid4().int % 10_000_000)
        self._value_parser: ValueParser  = ValueParser("html")
        self._job_parser:   JobParser    = JobParser("html")
        self._filiere_parser: FiliereParser = FiliereParser("html")

    # ─────────────────────────────────────────
    # Entry point
    # ─────────────────────────────────────────

    def parse(self, html: str) -> Optional[Convention]:
        if not html:
            print("Error: html is None")
            return None

        soup = BeautifulSoup(html, "html.parser")

        convention = Convention(
            name       = "Convention collective animation",
            source     = "legifrance",
            parsing_id = self._parsing_id,
        )

        current_filiere:       Optional[Filiere] = None
        current_contract_type: Optional[str]     = None
        table_index: int = 0

        article_node = soup.find("article")
        if not article_node:
            print("Error: no <article> tag found in HTML")
            return convention

        for node in article_node.descendants:

            # ── filière detection ────────────────────
            if node.name == "p" and node.text.strip().lower().startswith("filière"):
                current_filiere = self._parse_filiere(node, convention)
                continue

            # ── contract type (CDI / CDD) ────────────
            if node.name == "p" and "salaires minima" in node.text.lower():
                current_contract_type = node.text.strip()
                continue

            # ── tables ───────────────────────────────
            if node.name == "table":
                table_index += 1
                self._parse_table(
                    node,
                    table_index,
                    current_filiere,
                    current_contract_type,
                    convention,
                )

        return convention

    # ─────────────────────────────────────────
    # Filière
    # ─────────────────────────────────────────

    def _parse_filiere(self, p, convention: Convention) -> Optional[Filiere]:
        raw     = clean_text(p.text)
        filiere = self._filiere_parser.parse_from_line(raw)

        if not filiere:
            return None

        filiere.parsing_id = self._parsing_id
        filiere.source     = convention.source

        if filiere not in convention.filieres:
            convention.filieres.append(filiere)

        return filiere

    # ─────────────────────────────────────────
    # Table
    # ─────────────────────────────────────────

    def _parse_table(
        self,
        table_html,
        table_number: int,
        filiere:       Optional[Filiere],
        contract_type: Optional[str],
        convention:    Convention,
    ) -> Optional[Table]:

        rows: List[list] = []

        for tr in table_html.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            row   = [clean_text(c.get_text()) for c in cells]
            rows.append(row)

        table = Table(
            table_number = table_number,
            rows         = rows,
            document     = contract_type,
        ).clean()

        if not table.rows:
            return None

        self._extract_jobs_from_table(table, filiere, convention)

        return table

    # ─────────────────────────────────────────
    # Job extraction
    # ─────────────────────────────────────────

    def _extract_jobs_from_table(
        self,
        table:      Table,
        filiere:    Optional[Filiere],
        convention: Convention,
    ):
        jobs: List[Job] = self._job_parser.parse_jobs(table)

        for job in jobs:
            job.parsing_id = self._parsing_id
            job.filiere    = (filiere.slug or filiere.name) if filiere else None
            convention.jobs.append(job)

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    def _parse_euro(self, text: str) -> Optional[float]:
        if not text or text == "–":
            return None
        try:
            return float(text.replace("€", "").replace(" ", "").replace(",", "."))
        except ValueError:
            return None

    def _get_or_create_sector(self, name: str, convention: Convention) -> Sector:
        key = serialize(name)
        for s in convention.sectors:
            if s.key == key:
                return s
        sector = Sector(name=name, key=key, parsing_id=self._parsing_id)
        convention.sectors.append(sector)
        return sector

    def _get_or_create_category(self, name: str, convention: Convention) -> Category:
        key = serialize(name)
        for c in convention.categories:
            if c.key == key:
                return c
        category = Category(name=name, key=key, parsing_id=self._parsing_id)
        convention.categories.append(category)
        return category