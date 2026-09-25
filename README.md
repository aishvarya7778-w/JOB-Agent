# JOB-Agent
### AI-Powered Job Search & Application Assistant

> **Discover. Evaluate. Tailor. Apply. Track. Prepare.**

JOB-Agent is an AI-assisted job application workflow designed to reduce the repetitive work involved in finding relevant jobs and preparing personalized applications.

The system helps a candidate move from **job discovery → job evaluation → resume tailoring → cover-letter generation → application tracking → interview preparation** while keeping the candidate involved in the final decision and application process.

---

## The Idea

Job searching is not just about finding job postings.

A candidate typically has to:

- Search through hundreds of job listings
- Filter irrelevant or senior-level roles
- Read long job descriptions
- Determine whether their skills actually match
- Modify their resume for each position
- Write a customized cover letter
- Track applications
- Prepare for interviews
- Follow up on applications

JOB-Agent brings these steps together into one AI-assisted workflow.

The core idea is:

```text
                    ┌───────────────────────┐
                    │   Search for Jobs     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Filter Relevant Jobs  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Read Job Description  │
                    └───────────┬───────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Do I Fit the   │
                       │      Job?       │
                       └────────┬────────┘
                                │
                              YES
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Tailor Your Resume  │
                    │   + Cover Letter      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Review & Apply        │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Track Application     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Interview Preparation │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Follow Up & Track     │
                    └───────────────────────┘
```

The system is intentionally **human-in-the-loop**.

It assists with research, evaluation, personalization, and tracking, while the candidate reviews the generated materials and controls the actual application decision.

---

# Problem Statement

Traditional job applications involve significant repetitive work.

For every job, a candidate may need to:

1. Find the job.
2. Read the entire description.
3. Compare requirements with their resume.
4. Identify matching skills.
5. Rewrite their resume.
6. Create a cover letter.
7. Prepare for the interview.
8. Record the application.
9. Track the application status.

Doing this manually for dozens of applications quickly becomes time-consuming.

JOB-Agent automates the repetitive preparation work while keeping the candidate's real qualifications as the source of truth.

---

# Solution

JOB-Agent provides an AI-assisted pipeline that:

- Discovers relevant AI/ML job opportunities
- Filters jobs based on early-career relevance
- Extracts structured job information
- Analyzes job descriptions
- Evaluates candidate-job fit
- Identifies relevant skills
- Tailors the candidate's resume
- Generates customized cover letters
- Generates interview-preparation topics
- Creates PDF and DOCX application documents
- Tracks applications using Google Sheets
- Prevents duplicate application records

The system is designed around **truthful personalization**.

It should emphasize and reorganize existing candidate experience rather than fabricate skills, projects, certifications, or employment history.

---

# Workflow

## Step 1 — Search for Jobs

The system discovers AI/ML opportunities using dedicated job-discovery scripts.

Examples of target roles include:

- AI Engineer
- AI/ML Engineer
- Junior AI Engineer
- AI Engineer — Fresher
- Entry-Level AI Engineer
- Machine Learning Engineer
- Generative AI roles
- AI/ML internships

---

## Step 2 — Filter Relevant Jobs

The fresher-focused workflow filters out obvious senior-level roles.

Examples of excluded seniority terms include:

- Senior
- Sr.
- Lead
- Principal
- Staff
- Manager
- Director
- Head
- Architect

The goal is to focus the candidate's attention on opportunities more appropriate for an early-career profile.

---

## Step 3 — Read and Extract Job Descriptions

The job-discovery layer collects structured information from job postings.

Typical information includes:

- Job title
- Company
- Location
- Job ID
- Date posted
- Seniority
- Employment type
- Job function
- Industry
- Job description
- Job URL

The collected data is stored in machine-readable formats such as JSON and CSV.

---

# Step 4 — Decide: "Do I Fit the Job?"

This is the main AI-assisted decision point.

The LLM compares the candidate profile with the job description and produces:

- Match score
- Match percentage
- Evaluation summary
- Relevant skills
- Interview preparation topics
- Heuristic acceptance estimate

The system is instructed to evaluate the candidate using their existing qualifications.

It does not intentionally create qualifications that do not exist.

### Example

```text
Candidate Skills
       +
Job Description
       ↓
   LLM Analysis
       ↓
 ┌──────────────────────┐
 │ Match Score          │
 │ Matching Skills      │
 │ Evaluation Summary   │
 │ Interview Topics     │
 │ Acceptance Estimate  │
 └──────────────────────┘
```

> **Important:** Match scores and acceptance estimates are heuristic outputs. They are not guarantees of interview selection or employment.

---

# Step 5 — Tailor the Resume

For relevant opportunities, JOB-Agent generates a job-specific version of the candidate's resume.

The system can tailor:

- Professional summary
- Relevant skills
- Project descriptions
- Project bullet points
- Job-specific keywords
- Overall emphasis of the candidate profile

The LLM is instructed to follow a strict truthfulness rule:

> Only emphasize, reorganize, and rephrase existing candidate experience.

This makes the generated resume **job-specific without intentionally fabricating experience**.

---

# Step 6 — Generate a Cover Letter

JOB-Agent generates a customized cover letter based on:

- Target company
- Target position
- Job description
- Candidate background
- Relevant technical skills
- Relevant projects
- Achievements

The generated cover letter is designed to connect the candidate's existing experience with the requirements of the target role.

---

# Step 7 — Review & Apply

The candidate reviews:

- Job description
- Match evaluation
- Tailored CV
- Cover letter
- Application details

The candidate remains responsible for the final application decision.

JOB-Agent is designed as an **application-assistance system**, not an unattended job-application bot.

---

# Step 8 — Track Applications

JOB-Agent integrates with Google Sheets to maintain an application tracker.

The tracker can record information such as:

| Field | Purpose |
|---|---|
| Job Title | Target role |
| Company Name | Hiring organization |
| Match Score | Candidate-job alignment |
| Interview Prep Topics | Recommended preparation |
| Acceptance Chance | Heuristic estimate |
| Application Status | Application state |
| Application Date | Date processed/applied |

This makes it easier to maintain a centralized record of processed opportunities.

---

# Step 9 — Prepare for the Interview

The system generates interview-preparation topics based on the target role.

Examples include:

- Python
- Machine Learning
- LangChain
- RAG
- Vector Databases
- Agentic AI
- NLP
- Transformers
- System Design
- Behavioral / STAR questions

The preparation topics are selected based on the target role and the job-analysis output.

---

# Step 10 — Follow Up

After applying and interviewing, the candidate can continue tracking the application through the application tracker.

The long-term goal is to provide a single workflow from:

**Job Discovery → Application → Interview → Follow-up**

---

# Architecture

```text
                         JOB DISCOVERY
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ LinkedIn Job Sources     │
                 │ Public Job Endpoints     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Job Scraping & Filtering│
                 │ BeautifulSoup / Python   │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ JSON / CSV Job Dataset  │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Candidate Profile       │
                 │ + Job Description       │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ LLM Analysis            │
                 │ xAI Grok / Groq         │
                 └────────────┬────────────┘
                              │
             ┌────────────────┼─────────────────┐
             │                │                 │
             ▼                ▼                 ▼
       Match Score      Tailored CV       Cover Letter
             │                │                 │
             │                └────────┬────────┘
             │                         │
             ▼                         ▼
      Interview Prep          PDF / DOCX Files
             │
             └───────────────┬─────────────────┘
                             ▼
                   Google Sheets Tracker
```

---

# Core Components

## 1. Job Discovery

### `scrape_fresher_jobs.py`

Focused on discovering fresher/entry-level AI opportunities and producing structured job data.

### `scrape_jobs.py`

Provides another job-discovery workflow for AI Engineer opportunities and supports browser-assisted extraction through the project's browser skill.

---

## 2. LLM Client

### `grok_client.py`

Provides the LLM integration layer.

The client supports:

- xAI Grok
- Groq
- Environment-based API configuration
- Configurable models
- HTTP requests
- Retry handling for rate-limit responses

Supported environment variables include:

```env
GROK_API_KEY=
XAI_API_KEY=
GROQ_API_KEY=
GROK_MODEL=
```

---

## 3. AI Job Matching

### `main.py`

The main processing pipeline:

1. Loads the candidate resume
2. Loads the collected job dataset
3. Processes each job
4. Sends job/candidate information to the LLM
5. Calculates a match score
6. Generates an evaluation summary
7. Generates interview-preparation topics
8. Generates tailored resume content
9. Generates cover-letter content
10. Creates application documents
11. Records application information in Google Sheets

---

## 4. Document Generation

### `document_generator.py`

Generates:

- Tailored CV — PDF
- Tailored CV — DOCX
- Cover Letter — PDF
- Cover Letter — DOCX

Technologies used:

- `python-docx`
- ReportLab

---

## 5. Google Sheets Integration

### `sheets_client.py`

Provides application tracking through Google Sheets.

The module supports:

- Google authentication
- OAuth 2.0
- Service-account authentication
- Token handling
- Spreadsheet connection
- Header management
- Application-row insertion
- Duplicate checking

---

# Tech Stack

## Programming Language

- Python

## AI / LLM

- xAI Grok
- Groq
- LLM-based job matching
- Prompt engineering
- AI-assisted resume tailoring
- AI-assisted cover-letter generation

## Web / Data Extraction

- LinkedIn job data
- BeautifulSoup
- Python `urllib`
- Browser-assisted extraction

## Document Processing

- python-docx
- ReportLab
- PyMuPDF / PDF text extraction
- pypdf fallback

## Data

- JSON
- CSV

## APIs & Integrations

- Google Sheets API
- Google OAuth 2.0
- gspread
- xAI API
- Groq API

## Development

- Git
- GitHub
- Environment variables
- `.gitignore`

---

# Project Structure

```text
JOB-Agent/
│
├── .agents/
│   └── skills/
│       └── browser-act/
│           └── SKILL.md
│
├── .env.example
├── .gitignore
│
├── main.py
│   └── Main AI application-processing pipeline
│
├── grok_client.py
│   └── xAI Grok / Groq LLM integration
│
├── document_generator.py
│   └── PDF and DOCX CV / cover-letter generation
│
├── sheets_client.py
│   └── Google Sheets authentication and tracking
│
├── scrape_fresher_jobs.py
│   └── Fresher / entry-level AI job discovery
│
├── scrape_jobs.py
│   └── AI Engineer job discovery
│
├── linkedin_fresher_ai_jobs.csv
├── linkedin_fresher_ai_jobs.json
│   └── Fresher AI job dataset
│
├── linkedin_ai_engineer_jobs_hyderabad.csv
├── linkedin_ai_engineer_jobs_hyderabad.json
│   └── AI Engineer job dataset
│
├── requirements.txt
└── README.md
```

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/aishvarya7778-w/JOB-Agent.git
cd JOB-Agent
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Configuration

Create a local `.env` file using `.env.example`.

### Windows

```powershell
Copy-Item .env.example .env
```

Then configure the required LLM credentials.

Example:

```env
GROK_API_KEY=your_api_key_here
GROK_MODEL=grok-2-latest
```

Alternatively, configure the appropriate Groq environment variable:

```env
GROQ_API_KEY=your_api_key_here
```

### Security

Never commit:

```text
.env
token.json
credentials.json
client_secret*.json
```

API keys and authentication credentials must remain local.

---

# Google Sheets Configuration

JOB-Agent can connect to a Google Spreadsheet for application tracking.

The Google Sheets integration uses:

- Google OAuth
- Google credentials
- gspread
- Google Sheets API

The required Google credential files should be stored locally and excluded from Git.

Once authentication is configured, the application tracker can record processed jobs and application information.

---

# Running the Project

## Discover Fresher AI Jobs

```bash
python scrape_fresher_jobs.py
```

This produces structured job data in CSV/JSON format.

---

## Discover AI Engineer Jobs

```bash
python scrape_jobs.py
```

---

## Process Job Applications

```bash
python main.py
```

The application automatically looks for:

```text
linkedin_fresher_ai_jobs.json
```

and can also process another JSON dataset supplied as a command-line argument.

Example:

```bash
python main.py linkedin_ai_engineer_jobs_hyderabad.json
```

---

# Generated Output

Generated application packages are stored locally under:

```text
Outputs/
```

For each processed opportunity, the system can generate:

```text
Outputs/
└── Company_JobTitle/
    ├── Tailored_cv.pdf
    ├── Tailored_cv.docx
    ├── Cover_letter.pdf
    └── Cover_letter.docx
```

These generated files are intentionally excluded from version control.

---

# Job Data

The repository includes collected job datasets in both CSV and JSON formats.

```text
linkedin_fresher_ai_jobs.csv
linkedin_fresher_ai_jobs.json

linkedin_ai_engineer_jobs_hyderabad.csv
linkedin_ai_engineer_jobs_hyderabad.json
```

The JSON format is used by the processing pipeline, while CSV provides a convenient format for inspection and analysis.

---

# AI Prompting & Truthfulness

A major design principle of JOB-Agent is **truthful personalization**.

The LLM is instructed to:

- Use the candidate's existing qualifications
- Prioritize relevant existing skills
- Rephrase project experience where appropriate
- Incorporate relevant job-description keywords only when they genuinely match
- Avoid inventing employers
- Avoid inventing projects
- Avoid inventing certifications
- Avoid inventing technical skills
- Avoid inventing professional experience

This allows the system to optimize the presentation of an application without intentionally fabricating the candidate's background.

---

# Human-in-the-Loop Design

JOB-Agent is not designed as a blind auto-apply system.

The candidate remains involved in the important decisions:

```text
AI discovers jobs
       ↓
AI analyzes job
       ↓
AI evaluates candidate-job fit
       ↓
AI prepares application materials
       ↓
┌─────────────────────────────┐
│      HUMAN REVIEW           │
│                             │
│  • Review job               │
│  • Review match             │
│  • Review CV                │
│  • Review cover letter      │
│  • Decide whether to apply  │
└──────────────┬──────────────┘
               ↓
          Apply / Track
```

This design reduces repetitive work while keeping the candidate responsible for the final application.

---

# Responsible Automation

The project is designed for personal productivity and educational use.

It does not attempt to bypass:

- CAPTCHAs
- Authentication systems
- Access controls
- Platform security mechanisms
- Rate limits

Job listings can change, expire, or become unavailable after collection.

The datasets in this repository should therefore be treated as **point-in-time snapshots** rather than live job databases.

---

# Match Score & Acceptance Estimate

JOB-Agent generates two different types of estimates.

### Match Score

The match score represents how closely the candidate's existing qualifications align with the target job description.

It is based on the LLM's analysis of the candidate profile and job requirements.

### Acceptance Chance

The acceptance estimate is a heuristic generated from factors such as:

- Match score
- Seniority
- Experience requirements
- Candidate's student/early-career profile

It is **not a statistical probability** and does not guarantee an interview or job offer.

---

# Example End-to-End Flow

```text
                    JOB POSTING
                         │
                         ▼
              ┌────────────────────┐
              │ Job Discovery      │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Job Filtering      │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ JD Extraction      │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ LLM Job Analysis   │
              └─────────┬──────────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Match Score          Missing / Relevant
                                Skills
             │                     │
             └──────────┬──────────┘
                        ▼
              ┌────────────────────┐
              │ Resume Tailoring   │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Cover Letter       │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ PDF + DOCX Output  │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Human Review       │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Application        │
              │ Tracking           │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Interview Prep     │
              └────────────────────┘
```

---

# Engineering Highlights

This project demonstrates practical implementation of:

- Python automation
- LLM API integration
- Prompt engineering
- Web scraping
- HTML parsing
- Structured data extraction
- Data normalization
- Job filtering
- Candidate-job matching
- Document automation
- PDF generation
- DOCX generation
- Google API integration
- OAuth 2.0
- Google Sheets automation
- Duplicate detection
- Retry handling
- Environment-based configuration
- Git/GitHub version control

---

# Challenges Addressed

## 1. Job Noise

Large job-search results contain many irrelevant or senior positions.

**Approach:** Apply role and seniority filtering before processing.

---

## 2. Resume Repetition

The same resume is rarely optimal for every job.

**Approach:** Use LLM-based tailoring to prioritize relevant existing skills and project experience.

---

## 3. Long Job Descriptions

Important requirements can be buried inside long descriptions.

**Approach:** Extract and process job-description content before generating application materials.

---

## 4. Application Tracking

Manually maintaining application spreadsheets becomes difficult as applications increase.

**Approach:** Integrate Google Sheets into the processing pipeline.

---

## 5. Maintaining Truthfulness

Automated resume generation can easily introduce unsupported claims.

**Approach:** Explicit prompting rules require the system to work from the candidate's existing background.

---

# Future Improvements

Potential extensions include:

- Multi-platform job discovery
- More configurable role and location filters
- Job-ranking and recommendation models
- Persistent job database
- Scheduled job discovery
- Application-status dashboard
- Job analytics and application statistics
- Better candidate-job skill-gap analysis
- Interview question generation
- Company research automation
- Follow-up reminder automation
- More robust document quality evaluation
- Improved duplicate detection across job sources

---

# Limitations

Current limitations include:

- Job data is dependent on the availability of accessible job sources.
- Job postings may expire or change after being collected.
- LLM-generated match scores are heuristic.
- Acceptance estimates are not predictive guarantees.
- Generated resumes and cover letters require human review.
- Google Sheets tracking requires appropriate Google credentials.
- API usage depends on the selected LLM provider and available quota.

---

# Repository Data & Privacy

The repository is designed to keep sensitive personal files and credentials out of version control.

Ignored files include:

```text
.env
token.json
credentials.json
client_secret*.json
AishvaryaSahuResume1.pdf
Outputs/
```

Publicly committed data should not contain API keys, OAuth credentials, or other authentication secrets.

---

# Why I Built This

The project was built around a practical problem:

> **How can AI reduce the repetitive work involved in a modern job search without taking away the candidate's control over the application?**

JOB-Agent explores this problem by combining:

**Web Automation + LLMs + Document Generation + APIs + Data Processing + Workflow Automation**

into a single application workflow.

---

# Project Outcome

JOB-Agent demonstrates how an LLM can be integrated into a practical workflow rather than being used only as a conversational chatbot.

The project connects multiple components:

```text
Job Data
   ↓
Data Processing
   ↓
LLM Reasoning
   ↓
Personalized Documents
   ↓
Human Review
   ↓
Application Tracking
   ↓
Interview Preparation
```

The result is an AI-assisted job application workflow that focuses on reducing repetitive work while preserving human decision-making.

---

# Author

## Aishvarya Sahu

Computer Science & Engineering Student  
Bhopal, India

**GitHub:**  
https://github.com/aishvarya7778-w

**LinkedIn:**  
https://linkedin.com/in/aishvarya-sahu

**Portfolio:**  
https://sites.google.com/view/aishvarya7778

---

# License

This project currently does not specify an open-source license.

If you intend to allow others to reuse or modify the project, consider adding an appropriate license such as MIT.