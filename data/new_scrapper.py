# -*- coding: utf-8 -*-
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000005635129"

def parse_table(table_tag):
    """Extracts an HTML table into a list of dicts."""
    rows = table_tag.find_all("tr")
    if not rows:
        return []

    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
    data = []
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all(["th", "td"])]
        if len(cells) == len(headers):
            data.append(dict(zip(headers, cells)))
        else:
            data.append({"row": cells})
    return data


def scrape_legifrance(url):
    """Scrape the Légifrance page (with Selenium) and extract convention content."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--lang=fr-FR")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(8)  # wait for lazy-loaded articles and annexes

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Metadata
    title = soup.find("h1").get_text(strip=True)
    idcc = "2412"
    date = "6 juillet 2004"
    version = soup.find("div", class_="dateTexte")
    last_update = version.get_text(strip=True) if version else None

    # Articles
    articles = []
    for article in soup.select("section.article, div.article, div[data-article-id]"):
        number_tag = article.find(["h3", "h2"])
        title_tag = article.find(["h4", "h3"])
        text = article.get_text(separator="\n", strip=True)
        articles.append({
            "number": number_tag.get_text(strip=True) if number_tag else None,
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "text": text
        })

    # Annexes
    annexes = []
    for annex in soup.select("section.annexe, div.annexe"):
        annex_title = annex.find(["h2", "h3"])
        text = annex.get_text(separator="\n", strip=True)
        annexes.append({
            "title": annex_title.get_text(strip=True) if annex_title else None,
            "text": text
        })

    # Salary Tables
    tables = []
    for table in soup.find_all("table"):
        caption = table.find("caption")
        caption_text = caption.get_text(strip=True) if caption else "Tableau sans titre"
        table_data = parse_table(table)
        tables.append({
            "title": caption_text,
            "rows": table_data
        })

    # Build JSON structure
    convention = {
        "metadata": {
            "title": title,
            "idcc": idcc,
            "source": url,
            "date": date,
            "last_update": last_update
        },
        "articles": articles,
        "annexes": annexes,
        "salary_tables": tables
    }

    return convention


if __name__ == "__main__":
    data = scrape_legifrance(URL)
    output_file = "D:/1_TRAVAIL/WEB/wamp64/www/OpenCCCA/data/convention_animation_full.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Convention saved successfully → {output_file}")
    
# python D:\1_TRAVAIL\WEB\wamp64\www\OpenCCCA\data\new_scrapper.py
