import json
from pathlib import Path


OUTPUT_FILE = Path("data/glassdoor_jobs.json")


def normalize_job(job):
    """
    Converte una job nel formato standard usato dal progetto.
    """

    return {
        "company": job.get("company", ""),
        "role": job.get("role", ""),
        "location": job.get("location", ""),
        "application_url": job.get("application_url", ""),
        "source": "glassdoor",
        "source_url": job.get("source_url", ""),
    }


def save_jobs(jobs):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

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


def collect_jobs():
    """
    Punto di ingresso del collector Glassdoor.

    La sorgente effettiva verrà collegata qui tramite
    un'integrazione/API autorizzata.
    """

    jobs = []

    return [
        normalize_job(job)
        for job in jobs
    ]


def main():
    print("Glassdoor Collector")
    print("-------------------")

    jobs = collect_jobs()

    save_jobs(jobs)

    print(f"Offerte raccolte: {len(jobs)}")
    print(f"Salvate in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
