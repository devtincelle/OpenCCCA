



import os
from dataclasses import asdict
from model.Entities import Article,Filiere,Table,Job,Category,Convention,Sector
import uuid
import re
from bs4 import BeautifulSoup
from model.JobParser import JobParser
from model.ValueParser import ValueParser
from typing import Optional, List
from utils.Utils import to_english,clean_text,parse_french_date,serialize

class ConventionParserHTML:
    
    value_parser = ValueParser("html")
    job_parser = JobParser("html")

    def __init__(self):
        self._parsing_id = int(uuid.uuid4().int % 10_000_000)

    # --------------------------------------------------

    def parse(self, html: str) -> Convention:
        soup = BeautifulSoup(html, "html.parser")

        convention = Convention(
            name="Convention collective animation",
            source="legifrance",
            parsing_id=self._parsing_id
        )

        current_filiere: Filiere | None = None
        current_contract_type: str | None = None
        table_index = 0

        for node in soup.find("article").descendants:

            # -------- Filière detection
            if node.name == "p" and node.text.strip().lower().startswith("filière"):
                current_filiere = self._parse_filiere(node, convention)
                continue

            # -------- Contract type (CDI / CDD usage)
            if node.name == "p" and "salaires minima" in node.text.lower():
                current_contract_type = node.text.strip()
                continue
            
            current_sector = None

            # -------- Tables
            if node.name == "table":
                table_index += 1
                table = self._parse_table(
                    node,
                    table_index,
                    current_sector,
                    current_filiere,
                    current_contract_type,
                    convention
                )
                if table:
                    # attach table to a pseudo article later if needed
                    pass

        return convention

    # --------------------------------------------------
    # Filière
    # --------------------------------------------------

    def _parse_filiere(self, p, convention: Convention) -> Filiere:
        raw = clean_text(p.text)
        match = re.match(r"Filière\s+(\d+)\s*:\s*(.+)", raw, re.I)

        filiere = Filiere(
            number=match.group(1) if match else None,
            name=match.group(2) if match else raw,
            slug=serialize(raw),
            text=raw,
            parsing_id=self._parsing_id,
            source=convention.source
        )

        if filiere not in convention.filieres:
            convention.filieres.append(filiere)

        return filiere

    # --------------------------------------------------
    # Table
    # --------------------------------------------------

    def _parse_table(
        self,
        table_html,
        table_number: int,
        sector:Sector,
        filiere: Filiere,
        contract_type: str,
        convention: Convention
    ) -> Table:

        rows = []
        headers = []

        for tr in table_html.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            row = [clean_text(c.get_text()) for c in cells]
            rows.append(row)

            if tr.find("th"):
                headers = row

        table = Table(
            table_number=table_number,
            rows=rows,
            document=contract_type
        )

        table = table.clean()
        
        

        self._extract_jobs_from_table(
            table,
            headers,
            filiere,
            sector,
            convention
        )

        return table

    # --------------------------------------------------
    # Job extraction
    # --------------------------------------------------

    def _extract_jobs_from_table(
        self,
        table: Table,
        headers: list[str],
        filiere: Filiere,
        sector: Sector,
        convention: Convention
    ):

        current_sector = None
        current_category = None
        
        jobs = self.job_parser.parse_jobs(table)
        
        print(jobs)
        
        for job in jobs:
            job.filiere = filiere
            job.sector = sector
            convention.jobs.append(job)


    # --------------------------------------------------
    # Salary mapping
    # --------------------------------------------------

    def _assign_salary(self, job: Job, headers: list[str], values: list[str]):
        for h, v in zip(headers, values):
            amount = self._parse_euro(v)
            if amount is None:
                continue

            h = h.lower()
            if "jour" in h:
                job.daily_salary = amount
            elif "hebdo" in h:
                job.weekly_salary = amount
            elif "mensuel" in h:
                job.monthly_salary = amount

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _parse_euro(self, text: str):
        if not text or text == "–":
            return None
        try:
            return float(text.replace("€", "").replace(" ", "").replace(",", "."))
        except ValueError:
            return None

    def _looks_like_sector(self, text: str) -> bool:
        return text and len(text) > 3 and text[0].isupper()

    def _get_or_create_sector(self, name: str, convention: Convention) -> Sector:
        key = serialize(name)
        for s in convention.sectors:
            if s.key == key:
                return s

        sector = Sector(
            name=name,
            key=key,
            parsing_id=self._parsing_id
        )
        convention.sectors.append(sector)
        return sector

    def _get_or_create_category(self, name: str, convention: Convention) -> Category:
        key = serialize(name)
        for c in convention.categories:
            if c.key == key:
                return c

        category = Category(
            name=name,
            key=key,
            parsing_id=self._parsing_id
        )
        convention.categories.append(category)
        return category
