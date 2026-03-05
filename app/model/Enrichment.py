from abc import ABC, abstractmethod
from utils.Utils import serialize


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

WORKING_DAYS_PER_MONTH  = 21.67
WORKING_DAYS_PER_WEEK   = 5.0
WORKING_WEEKS_PER_YEAR  = 52
WORKING_MONTHS_PER_YEAR = 12
CADRE_CATEGORIES        = {"IV", "V", "Hors catégorie"}
CADRE_SALARY_THRESHOLD  = 3000  # fallback: infer cadre from monthly salary if category missing


# ─────────────────────────────────────────────
# Interface
# ─────────────────────────────────────────────

class IEnrichable(ABC):

    @abstractmethod
    def enrich(self) -> "IEnrichable":
        """Fill in missing fields from existing data. Always returns self."""
        ...


# ─────────────────────────────────────────────
# Enrichers
# ─────────────────────────────────────────────

class EnrichJob:

    @staticmethod
    def enrich(job) -> "Job":

        # ── salary inference ─────────────────────────
        if job.monthly_salary and not job.daily_salary:
            job.daily_salary  = round(job.monthly_salary / WORKING_DAYS_PER_MONTH, 2)

        if job.monthly_salary and not job.weekly_salary:
            job.weekly_salary = round(job.monthly_salary * WORKING_MONTHS_PER_YEAR / WORKING_WEEKS_PER_YEAR, 2)

        if job.daily_salary and not job.monthly_salary:
            job.monthly_salary = round(job.daily_salary * WORKING_DAYS_PER_MONTH, 2)

        if job.daily_salary and not job.weekly_salary:
            job.weekly_salary = round(job.daily_salary * WORKING_DAYS_PER_WEEK, 2)

        if job.weekly_salary and not job.monthly_salary:
            job.monthly_salary = round(job.weekly_salary * WORKING_WEEKS_PER_YEAR / WORKING_MONTHS_PER_YEAR, 2)

        # ── cadre inference ──────────────────────────
        if job.is_cadre is None and job.category:
            job.is_cadre = job.category in CADRE_CATEGORIES

        # fallback — infer from salary if category is missing
        if job.is_cadre is None and job.monthly_salary:
            job.is_cadre = job.monthly_salary >= CADRE_SALARY_THRESHOLD

        # ── key generation ───────────────────────────
        if not job.key and job.job_title:
            male   = (job.job_title.get("male")   or "").strip()
            female = (job.job_title.get("female") or "").strip()
            base   = male or female
            if base:
                job.key = serialize(base)

        return job


class EnrichFiliere:

    @staticmethod
    def enrich(filiere) -> "Filiere":

        # ── slug inference ───────────────────────────
        if not filiere.slug and filiere.name:
            filiere.slug = serialize(filiere.name)

        return filiere


class EnrichArticle:

    @staticmethod
    def enrich(article) -> "Article":

        # ── coord inference ──────────────────────────
        if not article.coord and article.number:
            article.coord = f"{article.number}"

        # ── cascade to jobs inside article ───────────
        for job in article.jobs:
            EnrichJob.enrich(job)

        return article


class EnrichConvention:

    @staticmethod
    def enrich(convention) -> "Convention":

        # filieres first — jobs may reference them
        for filiere in convention.filieres:
            EnrichFiliere.enrich(filiere)

        for job in convention.jobs:
            EnrichJob.enrich(job)

        for article in convention.articles:
            EnrichArticle.enrich(article)

        return convention