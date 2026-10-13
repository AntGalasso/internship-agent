import json
import re
from pathlib import Path


JOBS_FILE = Path("data/jobs.json")
PROFILE_FILE = Path("data/profile.json")
OUTPUT_FILE = Path("data/matched_jobs.json")
TOP_JOBS_FILE = Path("data/top_jobs.json")

TOP_N = 50


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def skill_matches(skill, text):
    skill_normalized = normalize(skill)

    if len(skill_normalized) <= 2:
        pattern = rf"\b{re.escape(skill_normalized)}\b"
        return bool(re.search(pattern, text))

    return skill_normalized in text


def job_key(job):
    """
    Identifica una posizione in modo indipendente dall'ID
    generato dal collector.
    """

    return (
        normalize(job.get("company", "")),
        normalize(job.get("role", "")),
        normalize(job.get("location", "")),
    )


def deduplicate_jobs(jobs):
    """
    Elimina duplicati logici.
    Mantiene la prima occorrenza.
    """

    unique = {}

    for job in jobs:
        key = job_key(job)

        if key not in unique:
            unique[key] = job

    return list(unique.values())


def calculate_score(job, profile):
    role_text = normalize(job["role"])
    location_text = normalize(job["location"])

    score = 0
    matched_skills = []
    matched_categories = []

    # ---------------------------------------------------------
    # 1. ROLE CATEGORY
    # ---------------------------------------------------------

    ai_keywords = [
        "machine learning",
        "artificial intelligence",
        "ai intern",
        "ml intern",
        "deep learning",
        "research intern",
        "research engineer",
        "research scientist",
        "applied scientist",
        "nlp",
        "natural language",
        "computer vision",
        "generative ai",
        "machine learning engineer",
        "ai engineer",
    ]

    swe_keywords = [
        "software engineer",
        "software engineering",
        "software developer",
        "backend",
        "frontend",
        "full stack",
        "fullstack",
        "developer intern",
    ]

    research_keywords = [
        "research intern",
        "research engineer",
        "research scientist",
        "applied scientist",
    ]

    is_ai = any(
        keyword in role_text
        for keyword in ai_keywords
    )

    is_swe = any(
        keyword in role_text
        for keyword in swe_keywords
    )

    is_research = any(
        keyword in role_text
        for keyword in research_keywords
    )

    if is_ai:
        score += 50
        matched_categories.append("AI/ML")

    if is_research:
        score += 15
        matched_categories.append("Research")

    if is_swe:
        score += 25
        matched_categories.append("Software Engineering")

    # ---------------------------------------------------------
    # 2. TARGET ROLE MATCH
    # ---------------------------------------------------------

    for target_role in profile["target_roles"]:
        target = normalize(target_role)

        if target in role_text:
            score += 20
            break

    # ---------------------------------------------------------
    # 3. SKILLS
    # ---------------------------------------------------------

    searchable_text = normalize(
        f'{job["company"]} '
        f'{job["role"]} '
        f'{job["location"]}'
    )

    for skill in profile["skills"]:
        if skill_matches(skill, searchable_text):
            matched_skills.append(skill)
            score += 5

    # ---------------------------------------------------------
    # 4. LOCATION
    # ---------------------------------------------------------

    for location in profile["preferred_locations"]:
        if normalize(location) in location_text:
            score += 15
            break

    # ---------------------------------------------------------
    # 5. EXCLUDED KEYWORDS
    # ---------------------------------------------------------

    for keyword in profile["exclude_keywords"]:
        if normalize(keyword) in role_text:
            score -= 50

    return (
        score,
        matched_skills,
        matched_categories,
    )


def match_jobs(jobs, profile):
    matched_jobs = []

    for job in jobs:

        (
            score,
            matched_skills,
            matched_categories,
        ) = calculate_score(
            job,
            profile,
        )

        result = {
            **job,
            "score": score,
            "matched_skills": matched_skills,
            "matched_categories": matched_categories,
        }

        matched_jobs.append(result)

    matched_jobs.sort(
        key=lambda job: job["score"],
        reverse=True,
    )

    return matched_jobs


def save_json(path, jobs):
    with open(
        path,
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

    jobs = load_json(JOBS_FILE)
    profile = load_json(PROFILE_FILE)

    # ---------------------------------------------------------
    # 1. DEDUPLICAZIONE
    # ---------------------------------------------------------

    original_count = len(jobs)

    jobs = deduplicate_jobs(jobs)

    duplicate_count = original_count - len(jobs)

    print(
        f"Offerte originali: {original_count}"
    )

    print(
        f"Duplicati rimossi: {duplicate_count}"
    )

    print(
        f"Offerte uniche: {len(jobs)}"
    )

    # ---------------------------------------------------------
    # 2. MATCHING
    # ---------------------------------------------------------

    matched_jobs = match_jobs(
        jobs,
        profile,
    )

    # ---------------------------------------------------------
    # 3. SALVA TUTTI I RISULTATI
    # ---------------------------------------------------------

    save_json(
        OUTPUT_FILE,
        matched_jobs,
    )

    # ---------------------------------------------------------
    # 4. SALVA TOP 50
    # ---------------------------------------------------------

    top_jobs = matched_jobs[:TOP_N]

    save_json(
        TOP_JOBS_FILE,
        top_jobs,
    )

    print(
        f"\nRisultati completi salvati in: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"TOP {TOP_N} salvati in: "
        f"{TOP_JOBS_FILE}"
    )

    # ---------------------------------------------------------
    # 5. STAMPA TOP 20
    # ---------------------------------------------------------

    print("\nTOP 20:\n")

    for job in matched_jobs[:20]:

        categories = ", ".join(
            job["matched_categories"]
        )

        print(
            f'{job["score"]:>3} | '
            f'{job["company"]} | '
            f'{job["role"]} | '
            f'{job["location"]}'
        )

        if categories:
            print(
                f'      Categories: {categories}'
            )

        if job["matched_skills"]:
            print(
                f'      Skills: '
                f'{", ".join(job["matched_skills"])}'
            )


if __name__ == "__main__":
    main()
