import hashlib
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/README.md"

OUTPUT_FILE = Path("data/jobs.json")


def fetch_readme():
    response = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": "internship-agent/1.0"
        },
    )

    print("Status code:", response.status_code)

    if response.status_code != 200:
        print("Errore nel download del README.")
        return None

    return response.text


def create_job_id(
    company,
    role,
    location,
    application_url,
):
    raw = (
        f"{company}|"
        f"{role}|"
        f"{location}|"
        f"{application_url}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:16]


def extract_application_links(cell):
    """
    Estrae i link dalla colonna Application.

    Il README normalmente contiene:
    - link alla candidatura
    - link alla pagina Simplify
    """

    application_url = None
    simplify_url = None

    links = cell.find_all("a")

    for link in links:
        href = link.get("href")

        if not href:
            continue

        if "simplify.jobs/p/" in href:
            simplify_url = href
        else:
            application_url = href

    return application_url, simplify_url


def parse_jobs(readme):
    soup = BeautifulSoup(
        readme,
        "html.parser",
    )

    jobs = []

    # Tiene traccia dell'ultima azienda reale.
    # Serve per le righe che nel README hanno "↳".
    last_company = None

    tables = soup.find_all("table")

    print(
        f"Tabelle trovate nel README: {len(tables)}"
    )

    for table in tables:

        rows = table.select("tbody tr")

        for row in rows:

            cells = row.find_all("td")

            if len(cells) < 5:
                continue

            company = cells[0].get_text(
                " ",
                strip=True,
            )

            role = cells[1].get_text(
                " ",
                strip=True,
            )

            location = cells[2].get_text(
                " ",
                strip=True,
            )

            age = cells[4].get_text(
                " ",
                strip=True,
            )

            # -------------------------------------------------
            # GESTIONE ↳
            # -------------------------------------------------

            if company == "↳":
                company = last_company
            else:
                last_company = company

            # Se per qualche motivo non abbiamo ancora
            # un'azienda, scartiamo la riga.
            if not company:
                continue

            # -------------------------------------------------
            # APPLICATION URL
            # -------------------------------------------------

            application_url, simplify_url = (
                extract_application_links(
                    cells[3]
                )
            )

            # Se manca completamente il link di candidatura,
            # teniamo comunque la posizione.
            job_id = create_job_id(
                company,
                role,
                location,
                application_url,
            )

            job = {
                "id": job_id,
                "company": company,
                "role": role,
                "location": location,
                "application_url": application_url,
                "simplify_url": simplify_url,
                "age": age,
            }

            jobs.append(job)

    return jobs


def remove_duplicates(jobs):
    """
    Elimina eventuali duplicati usando l'ID.
    """

    unique_jobs = {}
    
    for job in jobs:
        unique_jobs[job["id"]] = job

    return list(unique_jobs.values())


def save_jobs(jobs):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    print(
        f"\nSalvate {len(jobs)} offerte "
        f"in {OUTPUT_FILE}"
    )


def print_sample(jobs):
    print("\nPrime 10 offerte:\n")

    for job in jobs[:10]:

        print(
            f'{job["company"]} | '
            f'{job["role"]} | '
            f'{job["location"]}'
        )


def main():

    readme = fetch_readme()

    if not readme:
        return

    jobs = parse_jobs(readme)

    print(
        f"\nJobs trovati prima della deduplicazione: "
        f"{len(jobs)}"
    )

    jobs = remove_duplicates(jobs)

    print(
        f"Jobs dopo la deduplicazione: "
        f"{len(jobs)}"
    )

    print_sample(jobs)

    save_jobs(jobs)


if __name__ == "__main__":
    main()
