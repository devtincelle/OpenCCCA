import pdfplumber
import requests
import json
import re

# PDF URL (official PDF from AnimFrance)
PDF_URL = "https://www.animfrance.fr/storage/wsm_medias/la-convention-collective-nationale-de-lanimation-et-la-grille-des-minima.pdf"

def download_pdf(url, filename="convention_animation.pdf"):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)
    return filename

def extract_pdf_to_json(pdf_path):
    metadata = {
        "title": "Convention collective nationale de la production de films d’animation",
        "idcc": "2412",
        "source": PDF_URL,
        "date": "6 juillet 2004",
        "last_update": None
    }

    articles = []
    annexes = []
    salary_tables = []

    current_section = None
    current_article = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                # Detect Article titles
                article_match = re.match(r"^(Article\s+\d+[\.\d]*)\s*(.*)", line, re.IGNORECASE)
                annex_match = re.match(r"^(Annexe\s+.*)", line, re.IGNORECASE)
                if article_match:
                    if current_article:
                        articles.append(current_article)
                    current_article = {
                        "number": article_match.group(1),
                        "title": article_match.group(2).strip(),
                        "text": ""
                    }
                    current_section = "article"
                elif annex_match:
                    if current_article:
                        articles.append(current_article)
                        current_article = None
                    current_section = "annex"
                    annexes.append({
                        "title": annex_match.group(1).strip(),
                        "text": ""
                    })
                else:
                    if current_section == "article" and current_article:
                        current_article["text"] += line + "\n"
                    elif current_section == "annex" and annexes:
                        annexes[-1]["text"] += line + "\n"

            # Extract tables
            for table in page.extract_tables():
                if table:
                    headers = table[0]
                    rows = [dict(zip(headers, row)) for row in table[1:]]
                    salary_tables.append({
                        "title": "Tableau extrait de la page {}".format(page.page_number),
                        "rows": rows
                    })

    # Append last article if exists
    if current_article:
        articles.append(current_article)

    return {
        "metadata": metadata,
        "articles": articles,
        "annexes": annexes,
        "salary_tables": salary_tables
    }

if __name__ == "__main__":
    pdf_file = download_pdf(PDF_URL)
    data = extract_pdf_to_json(pdf_file)
    with open("D:/1_TRAVAIL/WEB/wamp64/www/OpenCCCA/data/convention_animation_full.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ Saved full convention JSON as convention_animation_pdf.json")

    
# python D:\1_TRAVAIL\WEB\wamp64\www\OpenCCCA\data\new_scrapper_2.py
