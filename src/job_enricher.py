import json
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup


INPUT_FILE = Path("data/top_jobs.json")
OUTPUT_FILE = Path("data/enriched_jobs.json")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def load_jobs():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def fetch_html(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True,
    )

    response.raise_for_status()
    return response.text


def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
    ]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)

    return re.sub(r"\s+", " ", text)


def detect_ats(url):
    url_lower = url.lower()

    if "greenhouse.io" in url_lower:
        return "greenhouse"

    if "myworkdayjobs.com" in url_lower:
        return "workday"

    if "smartrecruiters.com" in url_lower:
        return "smartrecruiters"

    if "careerpuck.com" in url_lower:
        return "careerpuck"

    return "unknown"


def extract_sections(text):
    sections = {
        "requirements": [],
        "qualifications": [],
        "responsibilities": [],
        "education": [],
    }

    text_lower = text.lower()

    keywords = {
        "requirements": [
            "requirements",
            "required qualifications",
            "basic qualifications",
        ],
        "qualifications": [
            "qualifications",
            "preferred qualifications",
            "minimum qualifications",
        ],
        "responsibilities": [
            "responsibilities",
            "what you'll do",
            "what you will do",
        ],
        "education": [
            "education",
            "degree",
            "bachelor",
            "master",
            "phd",
        ],
    }

    for section, section_keywords in keywords.items():
        found = []

        for keyword in section_keywords:
            position = text_lower.find(keyword)

            if position != -1:
                start = max(0, position - 100)
                end = min(len(text), position + 1500)

                found.append(
                    text[start:end]
                )

        sections[section] = found

    return sections


def enrich_job(job):
    url = job["application_url"]

    ats = detect_ats(url)

    result = {
        **job,
        "ats": ats,
        "description": "",
        "requirements": [],
        "qualifications": [],
        "responsibilities": [],
        "education": [],
        "enrichment_status": "pending",
    }

    try:
        html = fetch_html(url)
        text = clean_text(html)

        result["description"] = text

        sections = extract_sections(text)

        result.update(sections)

        result["enrichment_status"] = "success"

    except Exception as error:
        result["enrichment_status"] = "error"
        result["enrichment_error"] = str(error)

    return result


def save_jobs(jobs):
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            jobs,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main():
    jobs = load_jobs()

    print(f"Offerte da analizzare: {len(jobs)}")
    print()

    enriched_jobs = []

    # Per ora analizziamo solo le prime 3.
    # Quando il parser funziona, passeremo alle TOP 50.
    test_jobs = jobs[:3]

    for index, job in enumerate(test_jobs, start=1):

        print(
            f"[{index}/{len(test_jobs)}] "
            f'{job["company"]} | {job["role"]}'
        )

        print(
            f'ATS: {detect_ats(job["application_url"])}'
        )

        enriched = enrich_job(job)

        print(
            f'Status: {enriched["enrichment_status"]}'
        )

        if enriched.get("enrichment_error"):
            print(
                f'Errore: {enriched["enrichment_error"]}'
            )

        print(
            f'Descrizione: '
            f'{len(enriched["description"])} caratteri'
        )

        enriched_jobs.append(enriched)

        print()

    save_jobs(enriched_jobs)

    print(
        f"Salvate {len(enriched_jobs)} offerte in:"
    )
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
