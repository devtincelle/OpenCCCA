import pdfplumber
import re
import requests
import json
import uuid

PDF_URL = "https://www.animfrance.fr/storage/wsm_medias/la-convention-collective-nationale-de-lanimation-et-la-grille-des-minima.pdf"

def download_pdf(url, filename="convention_animation.pdf"):
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)
    return filename

def clean_key(name):
    return re.sub(r"\s+|-", "_", name.lower())

def parse_pdf(pdf_path):
    categories = {}
    filieres = {}
    fonctions = {}

    current_category = None
    current_filiere = None
    document_version = "IDCC-2412_B-3314_2015-03-01"

    cat_pattern = re.compile(r"(?:Cat[eé]gorie|CATEGORIE)\s*(V|I|II|III|IV|V?V?)\s*[:\-–]?\s*(.*)", re.IGNORECASE)
    salary_line_pattern = re.compile(
        r"(?P<filiere>\d+\s*\w+)\s+(?P<category>[IVX]+)\s+(?P<fonction>.+?)\s+(?P<salaire_mensuel>\d+(?:[.,]\d+)?)\s+(?P<salaire_journalier>\d+(?:[.,]\d+)?)"
    )

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # Check for categories
                cat_match = cat_pattern.match(line)
                if cat_match:
                    cat_key = cat_match.group(1)
                    description = cat_match.group(2).strip()
                    categories[cat_key] = {"name": cat_key, "description": description}
                    current_category = cat_key
                    continue

                # Check for salary/function line
                salary_match = salary_line_pattern.match(line)
                if salary_match:
                    filiere_name = salary_match.group("filiere")
                    category = salary_match.group("category")
                    fonction_name = salary_match.group("fonction")
                    salaire_mensuel = float(salary_match.group("salaire_mensuel").replace(",", "."))
                    salaire_journalier = float(salary_match.group("salaire_journalier").replace(",", "."))

                    filiere_key = clean_key(filiere_name)
                    if filiere_key not in filieres:
                        filieres[filiere_key] = {"name": filiere_name, "description": ""}

                    key = f"{filiere_key}-{clean_key(fonction_name)}"
                    fonctions[key] = {
                        "fonction": fonction_name,
                        "version_feminisee": "",  # optional, can fill later
                        "category": category,
                        "filiere": filiere_name,
                        "category_object": categories.get(category, {"name": category, "description": ""}),
                        "filiere_object": filieres[filiere_key],
                        "page_number": str(i),
                        "document_version": document_version,
                        "nom": fonction_name,
                        "parsing_id": str(uuid.uuid4().int)[:5],
                        "definition": "",  # can be added by extra parsing if available
                        "salaire_brut_mensuel": salaire_mensuel,
                        "salaire_brut_journalier": salaire_journalier,
                        "id": str(uuid.uuid4())
                    }

    return {"fonctions": fonctions, "categories": categories, "filieres": filieres}

if __name__ == "__main__":
    pdf_file = download_pdf(PDF_URL)
    data = parse_pdf(pdf_file)
    with open("D:/1_TRAVAIL/WEB/wamp64/www/OpenCCCA/data/convention_animation_full_2.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ Saved final JSON with categories, filieres, and fonctions.")

    #with open("D:/1_TRAVAIL/WEB/wamp64/www/OpenCCCA/data/convention_animation_full_2.json", "w", encoding="utf-8") as f:
# python D:\1_TRAVAIL\WEB\wamp64\www\OpenCCCA\data\new_scrapper_2.py
