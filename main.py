from pathlib import Path
from src.application_agent import (
    load_json,
    load_resume,
    create_application_package,
    generate_documents,
    save_package,
    JOBS_FILE,
    OUTPUT_DIR,
)
from src.auto_submitter import (
    setup_directories,
    load_completed_applications,
    apply,
    SUBMITTED_DIR,
)

TARGET_BATCH_SIZE = 10

def run_pipeline():
    setup_directories()
    
    print("=" * 60)
    print("🤖 INTERNSHIP AGENT - PIPELINE COMPLETA")
    print("=" * 60)

    # ---------------------------------------------------------
    # FASE 1: GENERAZIONE DOCUMENTI (Fino a 10 offerte)
    # ---------------------------------------------------------
    jobs = load_json(JOBS_FILE)
    resume = load_resume()

    if not jobs:
        print("❌ Nessuna offerta trovata nel database.")
        return

    print(f"\n🔍 Ricerca e preparazione di {TARGET_BATCH_SIZE} candidature...")
    
    prepared_count = 0
    for job in jobs:
        if prepared_count >= TARGET_BATCH_SIZE:
            break

        job_id = job.get("id", str(hash(job["application_url"])))
        pending_file = OUTPUT_DIR / f"{job_id}.json"
        submitted_file = SUBMITTED_DIR / f"{job_id}.json"

        # Salta se già inviata o già generata in coda
        if submitted_file.exists() or pending_file.exists():
            continue

        print(f"\n[{prepared_count + 1}/{TARGET_BATCH_SIZE}] Generazione per: {job['company']} - {job['role']}")
        package = create_application_package(job, resume)

        try:
            generated_data = generate_documents(package["prompt"])
            package["tailored_resume"] = generated_data.get("tailored_resume", "")
            package["cover_letter"] = generated_data.get("cover_letter", "")
            package["application_answers"] = generated_data.get("application_answers", {})
            package["status"] = "completed"
            
            save_package(package)
            print("✅ Documenti generati e salvati!")
            prepared_count += 1
        except Exception as e:
            print(f"⚠️ Errore durante la generazione per {job['company']}: {e}")

    # ---------------------------------------------------------
    # FASE 2: AUTO SUBMISSION A CATENA
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("🚀 AVVIO CANDIDATURE NEL BROWSER")
    print("=" * 60)

    apps = load_completed_applications()
    if not apps:
        print("Nessuna candidatura pronta in coda.")
        return

    print(f"Trovate {len(apps)} candidature da completare.")
    for app_file, app_data in apps:
        apply(app_file, app_data)

    print("\n🎉 Tutte le candidature in coda sono state gestite!")

if __name__ == "__main__":
    run_pipeline()