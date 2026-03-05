from model.ValueParser import ValueParser
from model.Entities import Filiere, Table, Job
from model.GuessContext import GuessContext
from dataclasses import fields
from typing import List, Optional

import hashlib
from utils.Utils import to_english


class TableParser():

    _parser = ValueParser()

    # use a set — no duplicates, O(1) lookup
    _known_headers: set = {
        "Responsabilité",
    }

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    def _hash(self, *parts) -> str:
        """Hash one or more string parts together to form a stable unique key."""
        raw = "_".join(str(p) for p in parts if p)
        return str(int(hashlib.sha1(raw.encode("utf-8")).hexdigest(), 16) % (10 ** 8))

    def is_admin_table(self, table_number: int) -> bool:
        return table_number in [1, 2, 3]

    def _make_job_key(self, tslice: dict) -> str:
        """
        Build a collision-resistant key.
        Priority: title + definition > title + salary > title alone.
        """
        title      = tslice.get("job_title") or ""
        definition = tslice.get("definition") or ""
        salary     = tslice.get("monthly_salary") or tslice.get("daily_salary") or ""
        category   = tslice.get("category") or ""
        return self._hash(title, definition or salary, category)

    def _to_job(self, job_data: dict, table: Table) -> Job:
        """Normalize, attach context, filter to Job fields, instantiate."""
        # normalize each value
        for key, value in job_data.items():
            job_data[key] = self._parser.conform(key, value)

        # attach table context
        job_data["article"]     = table.article
        job_data["page_number"] = table.page_number
        job_data["source"]      = table.document
        job_data["parsing_id"]  = table.key

        # keep only valid Job fields
        job_field_names = {f.name for f in fields(Job)}
        valid_data = {k: v for k, v in job_data.items() if k in job_field_names}

        return Job(**valid_data)

    # ─────────────────────────────────────────
    # Main parse
    # ─────────────────────────────────────────

    def parse_jobs(self, table: Table) -> List[Job]:
        """
        Parse messy multi-row tables from pdfplumber into Job instances.
        Expected logical columns: Secteur, Fonction, Position, Catégorie, Définition.
        """
        job_table: dict  = {}
        current_key      = None
        last_job_title   = None
        last_category    = None
        last_sector      = None
        table_number     = table.table_number

        for row_number, row in enumerate(table):

            tslice = self.parse_slice(row, row_number, table_number)
            if not tslice:
                continue

            tslice["row_number"]       = row_number
            tslice["table_number"]     = table_number
            tslice["table_nb_columns"] = len(row)

            job_title      = tslice.get("job_title")
            position       = tslice.get("position")
            sector         = tslice.get("sector")
            category       = tslice.get("category")
            daily_salary   = tslice.get("daily_salary")
            monthly_salary = tslice.get("monthly_salary")
            definition     = tslice.get("definition")

            # ── carry-forward context ────────────────────
            if sector and sector != "Secteur":
                last_sector = sector
            if category:
                last_category = category

            tslice["sector"]   = sector   or last_sector
            tslice["category"] = category or last_category

            # if we only have a position, borrow the last known title
            if position and not job_title:
                job_title = last_job_title

            if job_title:
                last_job_title = job_title

            # ── skip known header rows ───────────────────
            if job_title in self._known_headers:
                continue

            # ── decide if this row starts a new entry ────
            is_new_entry = False

            if job_title:
                if self.is_admin_table(table_number):
                    is_new_entry = True
                elif definition:
                    is_new_entry = True
                elif daily_salary or monthly_salary:
                    is_new_entry = True

            if is_new_entry:
                tslice["job_title"] = job_title
                job_key = self._make_job_key(tslice)
                job_table[job_key] = tslice
                current_key = job_key
                continue

            # ── continuation row — append to current entry ──
            if current_key is None:
                continue  # no current entry yet, skip orphan row

            if definition and not job_title:
                existing = job_table[current_key].get("definition") or ""
                job_table[current_key]["definition"] = (existing + " " + definition).strip()

            if job_title:
                existing_title = job_table[current_key].get("job_title") or ""
                job_table[current_key]["job_title"] = (existing_title + " " + job_title).strip()
                job_table[current_key]["category"]  = tslice["category"]

        # ── build Job objects ────────────────────────────
        return [self._to_job(job_data, table) for job_data in job_table.values()]

    # ─────────────────────────────────────────
    # Row parsing
    # ─────────────────────────────────────────

    def is_header(self, value: str) -> bool:
        return value in {
            'FONCTION (EN ITALIQUE LA VERSION FÉMINISÉE)',
            'Définition',
            'Catégorie',
            'Secteur',
            'Postes (en Italique la version féminisée)',
            'Position',
            'Cadre / Non Cadre',
            'Minima 2021',
            'hebdo 35h',
            'hebdo 39h',
            'mensuel sur base 35h',   # fixed: was missing comma before, merged with next string
            'Responsabilité',
            'Catégories',
        }

    def parse_slice(self, row: list, row_number: int = None, table_number: int = None) -> Optional[dict]:
        """
        Convert a raw table row into a keyed dict.
        Header cells are skipped individually — they no longer kill the whole row.
        Returns None only if the row is entirely made of header/empty cells.
        """
        data = {}

        for column_index, value in enumerate(row):

            if not value or str(value).strip() == "":
                continue

            # skip individual header cells instead of aborting the whole row
            if self.is_header(str(value).strip()):
                continue

            context = GuessContext(
                value=value,
                column_index=column_index,
                table_number=table_number,
                row_number=row_number,
                nb_columns=len(row)
            )

            key = self._parser.guess_key(context)
            if key:
                # merge duplicate keys (e.g. split job title across columns)
                if key in data and isinstance(data[key], str):
                    data[key] = (data[key] + " " + str(value)).strip()
                else:
                    data[key] = value
            else:
                data[str(column_index)] = value

        return data if data else None

    # ─────────────────────────────────────────
    # Filiere matching (stub)
    # ─────────────────────────────────────────

    def _find_filiere(self, job: Job, filieres: List[Filiere]) -> Optional[Filiere]:
        if not filieres:
            return None
        title = None
        if job.job_title and isinstance(job.job_title, dict):
            title = job.job_title.get("male") or job.job_title.get("female")
        if not title:
            return filieres[0]
        for filiere in filieres:
            if filiere.has_job(title):
                return filiere
        return filieres[0]