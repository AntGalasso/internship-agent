import json
import csv
import shutil
import os
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.pdf_generator import generate_cover_letter_pdf

# Inizializza variabili d'ambiente per OpenRouter
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

APPLICATIONS_DIR = Path("data/applications")
SUBMITTED_DIR = Path("data/submitted")
TRACKER_FILE = Path("applications_tracker.csv")
CV_PATH = Path("data/resume.pdf")
RESUME_TXT_PATH = Path("data/resume.txt")

MY_INFO = {
    "first_name": "Antonio",
    "last_name": "Galasso",
    "full_name": "Antonio Galasso",
    "email": "antogalassozerotre@gmail.com",
    "phone": "+393780840350",
    "city": "Naples",
    "linkedin": "https://www.linkedin.com/in/antonio-galasso-40960b255/",
    "github": "https://github.com/antgalasso"
}

def setup_directories():
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    SUBMITTED_DIR.mkdir(parents=True, exist_ok=True)
    Path("data/cover_letters").mkdir(parents=True, exist_ok=True)

def load_completed_applications():
    apps = []
    if not APPLICATIONS_DIR.exists(): return apps
    for file in APPLICATIONS_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("status") == "completed":
                apps.append((file, data))
    return apps

def log_to_csv(company, role, url):
    file_exists = TRACKER_FILE.exists()
    with open(TRACKER_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists: writer.writerow(["Data", "Azienda", "Ruolo", "Link Offerta"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), company, role, url])

def generate_motivation_letter(company: str, role: str) -> str:
    print(f"🤖 Contattando l'AI per scrivere la Motivation Letter per {company}...")
    resume_text = RESUME_TXT_PATH.read_text(encoding="utf-8") if RESUME_TXT_PATH.exists() else ""
    
    prompt = f"""
    Scrivi una Motivation Letter in INGLESE, breve (massimo 3 paragrafi) per il ruolo di {role} presso {company}.
    Basati ESATTAMENTE su questo CV:
    {resume_text}

    REGOLE RIGIDE:
    - NESSUNA intestazione in alto (niente data, niente nome o indirizzi).
    - Inizia DIRETTAMENTE con "Dear {company} Hiring Team,".
    - Paragrafo 1: Entusiasmo per il ruolo e forte base in computer science, machine learning research e architetture neurali.
    - Paragrafo 2: Metti in risalto la ricerca: MAMBA-MDD (Erasmus in Romania), l'analisi su Mamba (Eurotech), e soprattutto il solver esatto closed-form per MAMBA sviluppato a Taiwan (NCU) sottomesso a IEEE. Cita anche lo studio accettato a NeurIPS 2026.
    - Paragrafo 3: Collega le tue solide basi ingegneristiche (C/C++ alla 42 Florence) e operative (IT/Sicurezza doganale) al motivo per cui sei un fit eccellente per l'azienda.
    - Chiudi ESATTAMENTE con:
    "Sincerely,
    Antonio Galasso"

    RESTITUISCI SOLO IL TESTO DELLA LETTERA. NESSUN MARKDOWN, NESSUNA INTRODUZIONE.
    """
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "nvidia/nemotron-4-340b-instruct",
        "messages": [{"role": "user", "content": prompt}],
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"⚠️ Errore API: {response.status_code}")
            return ""
    except Exception as e:
        print(f"⚠️ Eccezione durante la chiamata AI: {e}")
        return ""

def is_form_present(page) -> bool:
    frames = [page] + page.frames
    for frame in frames:
        try:
            if frame.locator("input[type='email'], input[name*='first_name'], input[name*='name']").count() > 0:
                return True
        except Exception:
            continue
    return False

def find_and_click_apply(page):
    apply_keywords = ["Apply Now", "Apply for this job", "Apply", "Candidati", "Invia candidatura", "Apply Here"]
    for kw in apply_keywords:
        btn = page.get_by_role("button", name=kw, exact=False)
        if btn.count() > 0 and btn.first.is_visible():
            print(f"🖱️ Trovato bottone '{kw}', clicco...")
            btn.first.click()
            page.wait_for_timeout(3000)
            return True
            
    for kw in apply_keywords:
        link = page.get_by_role("link", name=kw, exact=False)
        if link.count() > 0 and link.first.is_visible():
            print(f"🖱️ Trovato link '{kw}', clicco...")
            link.first.click()
            page.wait_for_timeout(3000)
            return True
            
    for sel in [".apply-button", "#apply-button", "a[href*='apply']", "button[class*='apply']"]:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            print(f"🖱️ Trovato selettore '{sel}', clicco...")
            loc.first.click()
            page.wait_for_timeout(3000)
            return True
    return False

def fill_field(frame, keywords, selectors, value):
    for sel in selectors:
        try:
            loc = frame.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(value, timeout=500)
                return True
        except: pass
    for kw in keywords:
        try:
            loc = frame.get_by_label(kw, exact=False)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(value, timeout=500)
                return True
        except: pass
    return False

def apply_form_autofill(page, app_file: Path, job_info: dict, answers: dict):
    frames = [page] + page.frames
    
    for frame in frames:
        # Anagrafica Standard
        fill_field(frame, ["First Name", "Nome"], ["input[name*='first_name']"], MY_INFO["first_name"])
        fill_field(frame, ["Last Name", "Cognome"], ["input[name*='last_name']"], MY_INFO["last_name"])
        fill_field(frame, ["Full Name", "Complete Name"], ["input[name='name']"], MY_INFO["full_name"])
        fill_field(frame, ["Email", "E-mail"], ["input[type='email']", "input[name*='email']"], MY_INFO["email"])
        fill_field(frame, ["Phone", "Mobile"], ["input[type='tel']", "input[name*='phone']"], MY_INFO["phone"])
        fill_field(frame, ["LinkedIn", "Linkedin Profile"], ["input[name*='linkedin']"], MY_INFO["linkedin"])
        fill_field(frame, ["GitHub", "Portfolio"], ["input[name*='github']", "input[name*='portfolio']"], MY_INFO["github"])

        # INSERIMENTO DINAMICO DELLE RISPOSTE (Application Answers)
        if answers:
            for question, answer_text in answers.items():
                # Prova prima con la label esatta o parziale
                try:
                    loc = frame.get_by_label(question, exact=False)
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.fill(answer_text, timeout=500)
                        print(f"✅ Auto-compilata risposta per: '{question}'")
                        continue
                except Exception: pass
                
                # Prova a cercare un placeholder che contenga la domanda
                try:
                    loc_place = frame.get_by_placeholder(question, exact=False)
                    if loc_place.count() > 0 and loc_place.first.is_visible():
                        loc_place.first.fill(answer_text, timeout=500)
                        print(f"✅ Auto-compilata risposta per (placeholder): '{question}'")
                        continue
                except Exception: pass

        # Gestione Upload File (CV e Cover Letter)
        try:
            file_inputs = frame.locator("input[type='file']")
            if file_inputs.count() > 0:
                for idx in range(file_inputs.count()):
                    input_el = file_inputs.nth(idx)
                    tag_info = f"{input_el.get_attribute('name')} {input_el.get_attribute('id')} {input_el.get_attribute('aria-label')}".lower()

                    if any(w in tag_info for w in ["cover", "letter", "motivation"]):
                        pdf_dest = Path(f"data/cover_letters/CoverLetter_{app_file.stem}.pdf")
                        
                        if not pdf_dest.exists():
                            print("\n🔔 Trovato campo Motivation Letter! Avvio generazione dinamica...")
                            letter_text = generate_motivation_letter(job_info["company"], job_info["role"])
                            if letter_text:
                                generate_cover_letter_pdf(letter_text, pdf_dest)
                                print(f"✅ PDF Creato: {pdf_dest.name}")
                        
                        if pdf_dest.exists():
                            input_el.set_input_files(str(pdf_dest), timeout=1500)
                            print("✅ Motivation Letter allegata con successo!")
                    
                    elif any(w in tag_info for w in ["resume", "cv", "curriculum"]):
                        if CV_PATH.exists():
                            input_el.set_input_files(str(CV_PATH), timeout=1500)
                            print("✅ Resume PDF allegato con successo!")
                    else:
                        if CV_PATH.exists():
                            input_el.set_input_files(str(CV_PATH), timeout=1500)
        except Exception:
            pass

def apply(app_file, app_data):
    job_info = app_data["job"]
    url = job_info["application_url"]
    company = job_info["company"]
    role = job_info["role"]
    answers = app_data.get("application_answers", {})
    
    print(f"\n🚀 Avvio candidatura per: {company} - {role}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 850})
        page = context.new_page()
        
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            
            if not is_form_present(page):
                print("🔍 Modulo non rilevato immediatamente. Cerco il tasto Apply...")
                find_and_click_apply(page)
                page.wait_for_load_state("networkidle", timeout=10000)
            else:
                print("✅ Modulo di candidatura rilevato sulla pagina principale.")
            
            print("Avvio autocompilazione (inclusi campi AI) e analisi form...")
            # Passiamo esplicitamente 'answers' alla funzione di autofill
            apply_form_autofill(page, app_file, job_info, answers)
            
            # Stampa le risposte come backup per i campi non intercettati
            if answers:
                print("\n📄 BACKUP RISPOSTE (per eventuali campi falliti):")
                for key, text in answers.items():
                    print(f"- {key}: {text}")
            
            input("\n⏳ Controlla il modulo. PREMI INVIO qui nel terminale per confermare, salvare e passare alla successiva...")
            
            log_to_csv(company, role, url)
            app_data["status"] = "submitted"
            with open(app_file, "w", encoding="utf-8") as f:
                json.dump(app_data, f, indent=2, ensure_ascii=False)
            
            dest_file = SUBMITTED_DIR / app_file.name
            shutil.move(str(app_file), str(dest_file))
            print(f"✅ Archiviato in {dest_file}")
            
        except Exception as e:
            print(f"Errore: {e}")
        finally:
            browser.close()

def main():
    setup_directories()
    apps = load_completed_applications()
    if not apps:
        print("Nessuna candidatura pronta in coda.")
        return
    for app_file, app_data in apps:
        apply(app_file, app_data)

if __name__ == "__main__":
    main()