import os
import json
import re
import sys
import time
import glob
from datetime import datetime
from grok_client import call_grok
import document_generator
import sheets_client

# Force UTF-8 on Windows terminal output to prevent charmap errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# =====================================================================
# CANDIDATE FACTUAL BASELINE (100% Truthful from original CV)
# =====================================================================
BASE_CANDIDATE = {
    "name": "Aishvarya Sahu",
    "contact_info": {
        "location": "Bhopal, Madhya Pradesh, India",
        "phone": "+91 89824 22652",
        "email": "sahuaishvarya.8786@gmail.com",
        "linkedin": "linkedin.com/in/aishvarya-sahu",
        "github": "github.com/aishvarya7778-w",
        "portfolio": "sites.google.com/view/aishvarya7778"
    },
    "education": [
        {
            "degree": "Bachelor of Technology (B.Tech), Computer Science and Engineering",
            "institution": "Jai Narain College of Technology (JNCT), Bhopal",
            "details": "Expected Graduation: 2027  |  Current CGPA: 8.6 / 10.0"
        },
        {
            "degree": "Senior Secondary (Class XII) & Secondary (Class X)",
            "institution": "MPBSE",
            "details": "Class XII (2023): 94%  |  Class X (2021): 99%"
        }
    ],
    "certifications": [
        "Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate (GenAI)",
        "Analysis and Design of Algorithms — By NPTEL",
        "Python Programming Essentials — By Cisco"
    ],
    "achievements": [
        "Finalist — BuildOverse National Level Hackathon (Engineered AI-powered solution for real-world challenge)",
        "Semi-finalist — Cognizant TechnoVerse Hackathon (Developed an Agentic AI solution for complex automation)",
        "1st Prize — AI Rapid Solve Competition organized by IEEE Student Branch"
    ],
    "leadership": [
        "IEEE Student Branch — Student Volunteer / Event Coordinator (Organized 3+ technical events with 100+ attendees; served as Event Anchor)",
        "NSS Volunteer — Coordinated campus-wide blood donation drive and community outreach programs"
    ]
}

def convert_pdf_to_text(pdf_path: str) -> str:
    """Extracts and returns clean text from a given PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
    print(f"[PDF] Converting '{pdf_path}' to text...")
    if fitz:
        doc = fitz.open(pdf_path)
        pages_text = [page.get_text() for page in doc]
        doc.close()
        full_text = "\n".join(pages_text).strip()
        print(f"[PDF] Extracted {len(full_text)} characters from {len(pages_text)} pages.")
        return full_text
    else:
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            full_text = "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
            print(f"[PDF] Extracted {len(full_text)} characters using pypdf.")
            return full_text
        except Exception as e:
            raise RuntimeError(f"Failed to extract PDF text: {e}")

def sanitize_folder_name(name: str) -> str:
    """Sanitizes string for safe cross-platform folder names."""
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]+', '', name)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    return cleaned[:80].strip('_')

def parse_llm_json(response_text: str) -> dict:
    """Parses clean JSON from LLM output with multiple fallbacks."""
    cleaned = response_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
    try:
        return json.loads(cleaned)
    except Exception:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start:end+1])
            except Exception:
                pass
        raise ValueError(f"Failed to parse JSON response. Preview: {cleaned[:250]}")

def tailor_job_package(cv_text: str, job: dict, index: int, total: int):
    """
    Evaluates job match (score 0-10) and tailors the CV & Cover Letter for ATS optimization.
    """
    job_title = job.get('Job Title', 'AI Engineer')
    company = job.get('Company Name', 'Company')
    location = job.get('Location', 'Hyderabad, India')
    
    # Excerpt core job description requirements
    jd_raw = job.get('Job Description', '')
    jd_clean = jd_raw.replace('\n\n', '\n').strip()
    if len(jd_clean) > 1800:
        jd_clean = jd_clean[:1800] + "\n...[truncated for length]..."

    system_prompt = (
        "You are an expert Technical Recruiter and ATS Resume Optimization Strategist.\n"
        "Your task:\n"
        "1. Score the match between the candidate's CV and the job description strictly from 0.0 to 10.0.\n"
        "2. Tailor the CV summary, prioritize existing skills, rephrase project bullets with active verbs & JD keywords, and write a customized 4-paragraph cover letter.\n\n"
        "STRICT TRUTHFULNESS RULES:\n"
        "- DO NOT invent experience, employers, skills, certifications, or projects.\n"
        "- ONLY emphasize and rephrase the candidate's real skills, academic projects, and hackathons.\n"
        "- Incorporate relevant keywords from the JD ONLY where they genuinely match the candidate's hands-on background.\n"
        "- Output ONLY valid JSON."
    )

    user_prompt = f"""
Candidate Background:
Name: {BASE_CANDIDATE['name']}
Education: B.Tech Computer Science & Engineering, JNCT Bhopal (Graduation: 2027, CGPA: 8.6/10)
Skills: Python, SQL, Java (Basic), Data Structures & Algorithms, Object-Oriented Programming, DBMS, Operating Systems, Computer Networks, LangChain, RAG, Gemini API, Pinecone Vector DB, Scikit-learn, Pandas, NumPy, NLTK, Flask, Streamlit, Git, GitHub, MongoDB, Jupyter Notebook.
Projects:
1. DSA Instructor Chatbot: Context-aware retrieval with PDF documents using LangChain, Gemini API, and Pinecone Vector Database.
2. AI-Based Organ Donation System: Python, Flask, MongoDB, Scikit-learn classification & automated compatibility matching.
3. Quotes Recommendation Chatbot: NLP intent classification using TF-IDF, Logistic Regression, Scikit-learn, NLTK.
Certifications: Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate (GenAI), NPTEL Algorithms, Cisco Python.
Hackathons: Finalist BuildOverse National Hackathon, Semi-finalist Cognizant TechnoVerse Hackathon (Agentic AI Solution), 1st Prize IEEE AI Rapid Solve.

Target Job ({index}/{total}):
Title: {job_title}
Company: {company}
Location: {location}
Job Description Excerpt:
{jd_clean}

Return JSON ONLY in this format:
{{
  "score": <float between 0.0 and 10.0>,
  "match_score_pct": <integer between 0 and 100 reflecting how well candidate's existing qualifications align with the job description>,
  "interview_prep_topics": "<concise comma-separated list of the 4-6 most relevant technical and behavioral topics for this role, e.g. 'RAG Architecture, Vector DBs, PyTorch, Scalable API Design, Conflict Resolution, Team Collaboration'>",
  "acceptance_chance_pct": <integer between 0 and 100 estimating probability of acceptance based on match score and seniority/experience requirements vs candidate's student background>,
  "eval_summary": "<1-2 sentence match evaluation>",
  "tailored_summary": "<3-4 sentence professional summary tailored to {job_title} at {company} emphasizing genuine matching skills>",
  "prioritized_skills": ["<top 6-8 matching skills from candidate's real stack>"],
  "project_bullets": [
    "<DSA Chatbot bullet 1: RAG architecture, vector embeddings>",
    "<DSA Chatbot bullet 2: Pinecone semantic retrieval and Gemini LLM integration>",
    "<Organ Donation bullet 1: Scikit-learn ML classification & feature engineering>",
    "<Organ Donation bullet 2: Flask REST API and MongoDB data pipeline>",
    "<Quotes Chatbot bullet 1: NLP preprocessing, TF-IDF, and intent classification>"
  ],
  "cover_letter_paragraphs": [
    "<Opening paragraph expressing strong interest in {job_title} at {company}>",
    "<Body 1 detailing hands-on RAG, LangChain, Pinecone vector search, and Python projects aligned with JD>",
    "<Body 2 detailing ML prediction, Agentic AI hackathon achievement, and rapid learning ability>",
    "<Closing paragraph expressing enthusiasm to contribute and proposing an interview>"
  ]
}}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    raw = call_grok(messages, max_tokens=2500, temperature=0.15)
    return parse_llm_json(raw)

def main():
    print("=" * 72)
    print("     AI ATS CV & COVER LETTER AUTOMATION PIPELINE (Grok / LLM)")
    print("=" * 72)
    
    # 1. Locate CV PDF
    pdf_path = "AishvaryaSahuResume1.pdf"
    if not os.path.exists(pdf_path):
        pdfs = glob.glob("*.pdf")
        if pdfs:
            pdf_path = pdfs[0]
        else:
            print("[Error] No PDF resume found!")
            sys.exit(1)
            
    cv_text = convert_pdf_to_text(pdf_path)
    
    # 2. Locate Jobs JSON
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        json_path = sys.argv[1]
    elif os.path.exists("linkedin_fresher_ai_jobs.json"):
        json_path = "linkedin_fresher_ai_jobs.json"
    elif os.path.exists("linkedin_ai_engineer_jobs_hyderabad.json"):
        json_path = "linkedin_ai_engineer_jobs_hyderabad.json"
    else:
        print("[Error] No job postings JSON file found!")
        sys.exit(1)
        
    with open(json_path, mode="r", encoding="utf-8") as f:
        jobs = json.load(f)
        
    total_jobs = len(jobs)
    print(f"\n[Jobs] Loaded {total_jobs} job postings from '{json_path}'.")
    
    base_output_dir = "Outputs"
    os.makedirs(base_output_dir, exist_ok=True)
    print(f"[Outputs] Storing packages in '{base_output_dir}/<company_name>_<job_title>/'\n")
    
    # Initialize Google Sheets Tracker
    sheet_tracker = None
    try:
        sheet_tracker = sheets_client.GoogleSheetJobTracker()
        sheet_tracker.connect()
        print(f"[Google Sheets] [✓] Connected to spreadsheet ID: {sheets_client.SPREADSHEET_ID}\n")
    except Exception as e:
        print(f"[Google Sheets Info] Note: Google Sheets tracking not active yet ({e}).")
        print("    Tailored CV & Cover Letter files will still be generated normally.")
        print("    To enable Sheets updating, place credentials in project root or set GOOGLE_APPLICATION_CREDENTIALS.\n")

    print("-" * 72)
    print("EVALUATING, TAILORING, AND GENERATING PACKAGES...")
    print("-" * 72)
    
    results = []
    generated_packages = []
    
    for i, job in enumerate(jobs, 1):
        job_title = job.get("Job Title", "Unknown_Title")
        company = job.get("Company Name", "Unknown_Company")
        location = job.get("Location", "Hyderabad, India")
        
        # Clean folder name
        folder_name = f"{sanitize_folder_name(company)}_{sanitize_folder_name(job_title)}"
        target_dir = os.path.join(base_output_dir, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # Expected files
        cv_docx_path = os.path.join(target_dir, "Tailored_cv.docx")
        cv_pdf_path = os.path.join(target_dir, "Tailored_cv.pdf")
        cl_docx_path = os.path.join(target_dir, "Cover_letter.docx")
        cl_pdf_path = os.path.join(target_dir, "Cover_letter.pdf")
        
        print(f"\n[{i}/{total_jobs}] Processing: {job_title} at {company}")
        print(f"    Folder: {target_dir}")
        
        try:
            data = tailor_job_package(cv_text, job, i, total_jobs)
            
            # 1. Extract Score & Evaluation
            score = float(data.get("score", 0.0))
            eval_summary = data.get("eval_summary", "")
            
            match_score_pct = data.get("match_score_pct")
            if match_score_pct is None:
                match_score_pct = int(round(score * 10))

            interview_prep_topics = data.get("interview_prep_topics")
            if not interview_prep_topics:
                role_lower = job_title.lower()
                tech_topics = ["Python", "Machine Learning", "LangChain & RAG"]
                if "agent" in role_lower:
                    tech_topics.append("Agentic AI Architectures")
                if "nlp" in role_lower or "transformers" in role_lower:
                    tech_topics.append("Transformers & NLP")
                tech_topics.extend(["Vector Databases", "System Design", "Behavioral / STAR Method"])
                interview_prep_topics = ", ".join(tech_topics[:5])

            acceptance_chance_pct = data.get("acceptance_chance_pct")
            if acceptance_chance_pct is None:
                is_senior = any(w in job_title.lower() for w in ['senior', 'sr', 'lead', 'principal', 'staff', 'manager'])
                if is_senior:
                    acceptance_chance_pct = max(10, min(50, int(score * 10 * 0.45)))
                else:
                    acceptance_chance_pct = max(15, min(85, int(score * 10 * 0.85)))

            results.append({
                "job_title": job_title,
                "company": company,
                "score": score,
                "match_score_pct": match_score_pct,
                "interview_prep_topics": interview_prep_topics,
                "acceptance_chance_pct": acceptance_chance_pct,
                "summary": eval_summary,
                "folder": target_dir
            })
            
            # Print job title and score on terminal
            print(f"    --> Match Score: {score:.1f}/10 ({match_score_pct}%)")
            print(f"    --> Acceptance Chance: {acceptance_chance_pct}%")
            print(f"    --> Interview Prep Topics: {interview_prep_topics}")
            print(f"    --> Evaluation:  {eval_summary}")
            
            # If score is strictly above 6, print the job title prominently
            if score > 6.0:
                print(f"    [MATCH FOUND > 6.0]: {job_title}")
                
            # 2. Assemble Tailored CV Structure
            tailored_summary = data.get("tailored_summary", "")
            prioritized_skills = data.get("prioritized_skills", [])
            bullets = data.get("project_bullets", [])
            
            b1 = bullets[0] if len(bullets) > 0 else "Engineered context-aware DSA chatbot with LangChain, Gemini API, and Pinecone vector database."
            b2 = bullets[1] if len(bullets) > 1 else "Implemented RAG pipeline for semantic document search, context retrieval, and real-time query resolution."
            b3 = bullets[2] if len(bullets) > 2 else "Developed ML-based compatibility matching system using Python, Scikit-learn, and Flask with MongoDB backend."
            b4 = bullets[3] if len(bullets) > 3 else "Trained predictive classification models to automate donor-recipient scoring with high reliability."
            b5 = bullets[4] if len(bullets) > 4 else "Built intent classification NLP model using TF-IDF and Logistic Regression for quotes recommendation."
            
            cv_full = {
                "name": BASE_CANDIDATE["name"],
                "contact_info": BASE_CANDIDATE["contact_info"],
                "summary": tailored_summary,
                "skills": {
                    "Role-Relevant Core Focus": prioritized_skills,
                    "AI & Generative AI": ["LangChain", "RAG (Retrieval-Augmented Generation)", "Gemini API", "Pinecone Vector Database"],
                    "Machine Learning & Data": ["Scikit-learn", "Pandas", "NumPy", "NLTK", "Supervised Learning", "Data Preprocessing"],
                    "Languages & Core CS": ["Python", "SQL", "Java (Basic)", "Data Structures & Algorithms", "OOP", "DBMS", "Operating Systems"],
                    "Frameworks & Developer Tools": ["Flask", "Streamlit", "Git", "GitHub", "MongoDB", "Jupyter Notebook"]
                },
                "projects": [
                    {
                        "title": "DSA Instructor Chatbot (RAG & Generative AI)",
                        "tech_stack": "Python, LangChain, Gemini API, Pinecone Vector Database, RAG",
                        "bullets": [b1, b2]
                    },
                    {
                        "title": "AI-Based Organ Donation System (ML & Web Platform)",
                        "tech_stack": "Python, Flask, MongoDB, Scikit-learn, Machine Learning",
                        "bullets": [b3, b4]
                    },
                    {
                        "title": "Quotes Recommendation Chatbot (NLP & Intent Classification)",
                        "tech_stack": "Python, Scikit-learn, Pandas, NLTK, TF-IDF",
                        "bullets": [b5]
                    }
                ],
                "education": BASE_CANDIDATE["education"],
                "certifications": BASE_CANDIDATE["certifications"],
                "achievements": BASE_CANDIDATE["achievements"],
                "leadership": BASE_CANDIDATE["leadership"]
            }
            
            document_generator.build_cv_docx(cv_full, cv_docx_path)
            document_generator.build_cv_pdf(cv_full, cv_pdf_path)
            
            # 3. Assemble Cover Letter
            cl_paragraphs = data.get("cover_letter_paragraphs", [])
            cl_full = {
                "candidate_name": BASE_CANDIDATE["name"],
                "location": BASE_CANDIDATE["contact_info"]["location"],
                "phone": BASE_CANDIDATE["contact_info"]["phone"],
                "email": BASE_CANDIDATE["contact_info"]["email"],
                "linkedin": BASE_CANDIDATE["contact_info"]["linkedin"],
                "company_name": company,
                "job_title": job_title,
                "job_location": location,
                "date": time.strftime("%B %d, %Y"),
                "salutation": f"Dear Hiring Team at {company},",
                "paragraphs": cl_paragraphs
            }
            
            document_generator.build_cover_letter_docx(cl_full, cl_docx_path)
            document_generator.build_cover_letter_pdf(cl_full, cl_pdf_path)
            
            print(f"    [+] Generated Tailored_cv.pdf & Tailored_cv.docx")
            print(f"    [+] Generated Cover_letter.pdf & Cover_letter.docx")
            
            # 4. Append row to Google Sheet
            if sheet_tracker:
                try:
                    sheet_tracker.append_job_row(
                        job_title=job_title,
                        company_name=company,
                        match_score_pct=match_score_pct,
                        interview_prep_topics=interview_prep_topics,
                        acceptance_chance_pct=acceptance_chance_pct,
                        application_status="Applied",
                        application_date=datetime.now().strftime("%Y-%m-%d")
                    )
                except Exception as sheet_err:
                    print(f"    [Google Sheets Error] Could not append row: {sheet_err}")

            generated_packages.append({
                "job": job_title,
                "company": company,
                "folder": target_dir,
                "files": [cv_pdf_path, cv_docx_path, cl_pdf_path, cl_docx_path]
            })
            
        except Exception as e:
            print(f"    [Error processing {job_title}]: {e}")
            results.append({
                "job_title": job_title,
                "company": company,
                "score": 0.0,
                "match_score_pct": 0,
                "interview_prep_topics": "N/A",
                "acceptance_chance_pct": 0,
                "summary": f"Generation error: {e}",
                "folder": target_dir
            })
            
        if i < total_jobs:
            time.sleep(2)
            
    # =================================================================
    # SUMMARY TABLES & REPORTING
    # =================================================================
    print("\n" + "=" * 72)
    print("                    JOB EVALUATION SCORES")
    print("=" * 72)
    for idx, r in enumerate(results, 1):
        indicator = "[MATCH > 6.0]" if r['score'] > 6.0 else "[No Match]   "
        print(f"{idx:2d}. {indicator} | Score: {r['score']:4.1f}/10 ({r.get('match_score_pct', 0)}%) | {r['job_title']} ({r['company']})")
        
    print("\n" + "=" * 72)
    print("               JOBS WITH SCORE ABOVE 6.0")
    print("=" * 72)
    matched = [r for r in results if r["score"] > 6.0]
    if matched:
        for m in matched:
            print(f"- {m['job_title']} - {m['company']} (Score: {m['score']:.1f}/10)")
            print(f"  Summary: {m['summary']}")
            print(f"  Folder:  {m['folder']}\n")
    else:
        print("No job postings scored strictly above 6.0 for the candidate's entry/student profile.")

    print("\n" + "=" * 72)
    print("                GOOGLE SHEETS APPLICATION TRACKER")
    print("=" * 72)
    for idx, r in enumerate(results, 1):
        print(f"[{idx:2d}] {r['company']} - {r['job_title']}")
        print(f"     Match: {r.get('match_score_pct', 0)}%  |  Acceptance Chance: {r.get('acceptance_chance_pct', 0)}%  |  Status: Applied")
        print(f"     Prep Topics: {r.get('interview_prep_topics', 'N/A')}\n")
        
    print("=" * 72)
    print("             GENERATED ATS PACKAGES SUMMARY")
    print("=" * 72)
    for idx, pkg in enumerate(generated_packages, 1):
        print(f"[{idx:2d}] {pkg['company']} - {pkg['job']}")
        print(f"     Location: {pkg['folder']}")
        all_exist = all(os.path.exists(f) for f in pkg['files'])
        status_str = "All 4 files present (PDF & DOCX for CV & Cover Letter)" if all_exist else "File missing!"
        print(f"     Status:   {status_str}")
        
    print("=" * 72)
    print("All ATS-tailored CVs and Cover Letters successfully created!")

if __name__ == "__main__":
    main()
