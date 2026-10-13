import json
import os
import re
import requests
from pathlib import Path

JOBS_FILE = Path("d ata/top_jobs.json")
RESUME_FILE = Path("data/resume.txt")
OUTPUT_DIR = Path("data/applications")

# Inserisci qui la tua API Key di OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_resume():
    if not RESUME_FILE.exists():
        raise FileNotFoundError(f"CV non trovato: {RESUME_FILE}")
    return RESUME_FILE.read_text(encoding="utf-8").strip()

def build_prompt(job, resume):
    return f"""
You are an expert technical recruiter and application writer.

Prepare a job application for the candidate below.

JOB
Company: {job["company"]}
Role: {job["role"]}
Location: {job["location"]}

JOB DESCRIPTION
{job.get("description", "")}

CANDIDATE RESUME
{resume}

Create:
1. TAILORED RESUME
2. COVER LETTER
3. APPLICATION ANSWERS (why role, why company, why fit, technical experience, professional summary)

RULES:
- Never invent experience, employers, degrees, metrics, skills, or visa status.
- Only use information present in the candidate resume.
- Prioritize experience relevant to the specific job.

Return ONLY valid JSON in this exact structure without any conversational text:

{{
  "tailored_resume": "...",
  "cover_letter": "...",
  "application_answers": {{
    "why_role": "...",
    "why_company": "...",
    "why_fit": "...",
    "technical_experience": "...",
    "professional_summary": "..."
  }}
}}
"""

def generate_documents(prompt):
    print("Contattando OpenRouter (modello Nvidia Nemotron)...")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "messages": [{"role": "user", "content": prompt}],
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=120
    )
    
    if not response.ok:
        raise Exception(f"HTTP {response.status_code} - {response.text}")
        
    content = response.json()["choices"][0]["message"]["content"].strip()
    
    # Estrazione robusta del JSON (ignora il testo prima e dopo le parentesi graffe)
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if not match:
        raise ValueError(f"Impossibile trovare un JSON valido nella risposta: {content}")
        
    clean_json = match.group(0)
    
    return json.loads(clean_json)

def create_application_package(job, resume):
    return {
        "job": {
            "id": job.get("id"),
            "company": job.get("company"),
            "role": job.get("role"),
            "location": job.get("location"),
            "application_url": job.get("application_url"),
        },
        "score": job.get("score"),
        "prompt": build_prompt(job, resume),
        "tailored_resume": "",
        "cover_letter": "",
        "application_answers": {},
        "status": "ready_for_generation",
    }

def save_package(package):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    job_id = package["job"]["id"]
    output_file = OUTPUT_DIR / f"{job_id}.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(package, file, indent=2, ensure_ascii=False)

    return output_file

def main():
    jobs = load_json(JOBS_FILE)
    resume = load_resume()

    if not jobs:
        print("Nessuna offerta trovata.")
        return

    job = jobs[1]

    print("APPLICATION AGENT")
    print("-----------------")
    print(f'Company: {job["company"]}')
    print(f'Role: {job["role"]}')
    
    package = create_application_package(job, resume)
    
    try:
        generated_data = generate_documents(package["prompt"])
        package["tailored_resume"] = generated_data.get("tailored_resume", "")
        package["cover_letter"] = generated_data.get("cover_letter", "")
        package["application_answers"] = generated_data.get("application_answers", {})
        package["status"] = "completed"
        print("Documenti generati con successo!")
    except Exception as e:
        print(f"Errore durante la generazione: {e}")
        package["status"] = "error"

    output_file = save_package(package)
    print(f"Application package salvato: {output_file}")
    print(f"Status: {package['status']}")

if __name__ == "__main__":
    main()