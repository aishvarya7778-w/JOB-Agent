import os
import sys
import json
import glob
import time
import socket
import webbrowser
import wsgiref.simple_server
import wsgiref.util
from datetime import datetime
from typing import List, Dict, Any, Optional

# Force UTF-8 on Windows terminal output to prevent charmap errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import gspread
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
try:
    from google_auth_oauthlib.flow import _ExclusiveWSGIServer, _WSGIRequestHandler
except ImportError:
    _ExclusiveWSGIServer = wsgiref.simple_server.WSGIServer
    _WSGIRequestHandler = wsgiref.simple_server.WSGIRequestHandler
from google.auth.transport.requests import Request

# Google Sheets Spreadsheet ID specified by user
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "1yK4N7VxlEda41e5hpoBP8RaD8lufXwirA3qh5nI1RY0")

# Scopes required for reading and writing to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

EXPECTED_HEADERS = [
    "Job Title",
    "Company Name",
    "Match Score (%)",
    "Interview Prep Topics",
    "Acceptance Chance (%)",
    "Application Status",
    "Application Date"
]

def find_credentials_file() -> Optional[str]:
    """
    Locates Google API credentials file in the current directory or via env vars.
    Supports Service Account JSON or OAuth2 Installed Client JSON.
    """
    # 1. Check environment variable
    env_cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CREDENTIALS_FILE")
    if env_cred and os.path.exists(env_cred):
        return env_cred
        
    # 2. Check for explicit files
    candidates = [
        "credentials.json",
        "service_account.json",
        "client_secret.json"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
            
    # 3. Check for any client_secret*.json pattern in workspace
    client_secret_matches = glob.glob("client_secret*.json")
    if client_secret_matches:
        return client_secret_matches[0]
        
    # 4. Check for any json with credentials keywords
    for f in glob.glob("*.json"):
        if f.endswith("jobs_hyderabad.json") or f == "token.json":
            continue
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                if isinstance(data, dict) and ("installed" in data or "type" in data or "web" in data):
                    return f
        except Exception:
            pass
            
    return None

class _RobustOAuthRedirectApp:
    """
    WSGI application that handles Google OAuth redirect callbacks.
    Unlike the basic _RedirectWSGIApp in google_auth_oauthlib, this app:
    - Gracefully responds to browser /favicon.ico requests without terminating the server.
    - Handles health-check TCP connections / root probes without throwing state mismatch errors.
    - Captures the callback URI containing the authorization 'code=' or 'error='.
    - Renders an informative HTML page to the user upon success or failure.
    """
    def __init__(self, success_message: str):
        self.success_message = success_message
        self.last_request_uri = None
        self.error = None

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        query = environ.get("QUERY_STRING", "")

        # Ignore browser favicon requests so they don't consume the one-shot listener
        if "favicon.ico" in path:
            start_response("204 No Content", [("Content-Length", "0")])
            return [b""]

        req_uri = wsgiref.util.request_uri(environ)

        # Check for OAuth authorization response
        if "code=" in query:
            self.last_request_uri = req_uri
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Authorization Successful</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background: #f8f9fa; color: #202124; text-align: center; padding-top: 60px; }}
                    .card {{ background: white; max-width: 520px; margin: 0 auto; padding: 40px; border-radius: 10px; box-shadow: 0 4px 14px rgba(0,0,0,0.08); }}
                    h1 {{ color: #0F9D58; font-size: 24px; margin-bottom: 12px; }}
                    p {{ color: #5f6368; font-size: 15px; line-height: 1.6; margin: 0; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>✓ {self.success_message}</h1>
                    <p>Google Sheets authorization was successful.<br>You can safely close this browser window and return to your terminal.</p>
                </div>
            </body>
            </html>
            """
            return [html.encode("utf-8")]
        elif "error=" in query:
            self.error = query
            self.last_request_uri = req_uri
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h1 style="color: #d93025;">Authorization Declined</h1>
                <p>Google returned an error: <code>{query}</code></p>
                <p>You can return to the terminal.</p>
            </body>
            </html>
            """
            return [html.encode("utf-8")]
        else:
            # Informational response for health check or manual navigation before callback
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>OAuth Listener Active</title></head>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h2 style="color: #1a73e8;">OAuth Callback Listener Active</h2>
                <p>Waiting for Google authorization callback. Please complete sign-in on your Google consent window.</p>
            </body>
            </html>
            """
            return [html.encode("utf-8")]

def find_available_port(preferred_port: int, candidate_ports: List[int]) -> int:
    """Finds an available TCP port on localhost (127.0.0.1)."""
    ports_to_try = [preferred_port] + [p for p in candidate_ports if p != preferred_port]
    for p in ports_to_try:
        if p == 0:
            return 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return 0

def run_local_server_robust(
    flow: InstalledAppFlow,
    host: str = "localhost",
    port: Optional[int] = None,
    open_browser: bool = True,
    timeout_seconds: int = 300
) -> Credentials:
    """
    Runs a robust local OAuth listener for InstalledAppFlow.
    Unlike standard flow.run_local_server which exits immediately upon any non-auth probe
    (e.g., Test-NetConnection or browser pre-connect), this implementation:
    1. Keeps listening until the OAuth authorization code is received or timeout expires.
    2. Uses a predictable, stable port (default 8090, or GOOGLE_OAUTH_PORT from env) to avoid random ephemeral ports.
    3. Handles port contention by trying a pool of fallback ports.
    4. Automatically logs listener status, verification commands, and authorization URLs.
    """
    if port is None:
        env_port = os.getenv("GOOGLE_OAUTH_PORT")
        port = int(env_port) if env_port and env_port.isdigit() else 8090

    candidate_ports = [port, 8085, 8088, 8091, 8092, 0]
    chosen_port = find_available_port(port, candidate_ports)

    success_msg = "Authorization Complete"
    wsgi_app = _RobustOAuthRedirectApp(success_msg)

    local_server = wsgiref.simple_server.make_server(
        host,
        chosen_port,
        wsgi_app,
        server_class=_ExclusiveWSGIServer,
        handler_class=_WSGIRequestHandler,
    )

    actual_port = local_server.server_port
    flow.redirect_uri = f"http://{host}:{actual_port}/"
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    print("\n" + "=" * 70, flush=True)
    print(f"[Google Sheets OAuth] Callback server listening on: http://localhost:{actual_port}/", flush=True)
    print(f"[Google Sheets OAuth] Redirect URI: {flow.redirect_uri}", flush=True)
    print(f"[Google Sheets OAuth] Verify listener active in another terminal with:", flush=True)
    print(f"    Test-NetConnection localhost -Port {actual_port}", flush=True)
    print(f"    netstat -ano | findstr :{actual_port}", flush=True)
    print("=" * 70 + "\n", flush=True)

    if open_browser:
        print("[Google Sheets OAuth] Opening browser for Google account consent...", flush=True)
        try:
            webbrowser.open(auth_url, new=1, autoraise=True)
        except Exception as e:
            print(f"[Google Sheets OAuth] Could not automatically open browser: {e}", flush=True)

    print(f"[Google Sheets OAuth] If your browser did not open automatically, visit this URL:", flush=True)
    print(f"\n{auth_url}\n", flush=True)
    print(f"[Google Sheets OAuth] Waiting for you to complete authorization in your browser (timeout: {timeout_seconds}s)...", flush=True)

    local_server.timeout = 2.0
    start_time = time.time()

    try:
        while not wsgi_app.last_request_uri:
            if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                raise TimeoutError(
                    f"OAuth authorization timed out after {timeout_seconds} seconds waiting for browser callback."
                )
            
            try:
                local_server.handle_request()
            except Exception as req_err:
                print(f"[Google Sheets OAuth Debug] Connection handled ({req_err}), continuing listener...", flush=True)

            if wsgi_app.error:
                raise RuntimeError(f"Google OAuth authorization was declined: {wsgi_app.error}")

        # Convert http to https for oauthlib validation
        auth_response = wsgi_app.last_request_uri.replace("http://", "https://", 1)
        print("[Google Sheets OAuth] Authorization response received! Exchanging code for tokens...", flush=True)
        flow.fetch_token(authorization_response=auth_response)
        print("[Google Sheets OAuth] [✓] Authentication successful! Token obtained.", flush=True)
        return flow.credentials

    finally:
        local_server.server_close()
        print(f"[Google Sheets OAuth] Callback server on port {actual_port} shut down cleanly.", flush=True)

def get_gspread_client(credentials_file: Optional[str] = None) -> gspread.Client:
    """
    Authenticates and returns an authorized gspread Client.
    Supports Service Account and OAuth2 Installed App flow (with token caching).
    """
    if not credentials_file:
        credentials_file = find_credentials_file()
        
    if not credentials_file or not os.path.exists(credentials_file):
        raise FileNotFoundError(
            "Google credentials file not found! Please place your 'credentials.json', "
            "'service_account.json', or 'client_secret_*.json' in the project directory, "
            "or set GOOGLE_APPLICATION_CREDENTIALS in .env."
        )

    # Inspect credentials file type
    with open(credentials_file, "r", encoding="utf-8") as f:
        cred_data = json.load(f)

    # 1. Service Account Flow
    if cred_data.get("type") == "service_account":
        print(f"[Google Sheets] Authenticating using Service Account: {credentials_file}")
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
        return gspread.authorize(creds)

    # 2. OAuth2 Desktop / Installed App Flow
    elif "installed" in cred_data or "web" in cred_data:
        token_file = "token.json"
        creds = None
        
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
                print(f"[Google Sheets] Loaded existing OAuth credentials from '{token_file}'.", flush=True)
            except Exception as e:
                print(f"[Google Sheets] Existing token in '{token_file}' could not be parsed ({e}). Re-authenticating...", flush=True)
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("[Google Sheets] Refreshing expired OAuth token...", flush=True)
                    creds.refresh(Request())
                    print("[Google Sheets] [✓] Successfully refreshed OAuth token.", flush=True)
                except Exception as refresh_err:
                    print(f"[Google Sheets] OAuth token refresh failed ({refresh_err}). Starting new authorization...", flush=True)
                    creds = None

            if not creds or not creds.valid:
                print(f"[Google Sheets] Starting OAuth authorization flow using '{credentials_file}'...", flush=True)
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = run_local_server_robust(flow, open_browser=True)
                
            # Save the credentials for next runs
            try:
                with open(token_file, "w", encoding="utf-8") as token_out:
                    token_out.write(creds.to_json())
                print(f"[Google Sheets] [✓] Saved credentials token to '{token_file}'.", flush=True)
            except Exception as save_err:
                print(f"[Google Sheets Warning] Failed to save token to '{token_file}': {save_err}", flush=True)

        return gspread.authorize(creds)
    else:
        raise ValueError(f"Unrecognized credentials format in {credentials_file}")

class GoogleSheetJobTracker:
    def __init__(self, spreadsheet_id: str = SPREADSHEET_ID, credentials_file: Optional[str] = None):
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self.client: Optional[gspread.Client] = None
        self.sheet: Optional[gspread.Worksheet] = None

    def connect(self):
        """Connects to Google Sheets and ensures the header row exists."""
        if self.sheet is not None:
            return self.sheet
            
        self.client = get_gspread_client(self.credentials_file)
        print(f"[Google Sheets] Opening spreadsheet ID: {self.spreadsheet_id}...")
        
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            raise RuntimeError(
                f"Failed to open Google Sheet '{self.spreadsheet_id}'. "
                f"Ensure the sheet is shared with the authenticated account. Details: {e}"
            )

        # Use first worksheet
        self.sheet = spreadsheet.sheet1
        self._ensure_headers()
        self._load_existing_keys()
        return self.sheet

    def _load_existing_keys(self):
        """Loads existing (job_title, company) keys to prevent redundant network fetches on each append."""
        self._existing_keys = set()
        try:
            vals = self.sheet.get_all_values()
            for r in vals[1:]:
                if len(r) >= 2:
                    self._existing_keys.add(f"{str(r[0]).strip().lower()}::{str(r[1]).strip().lower()}")
        except Exception as e:
            print(f"[Google Sheets Warning] Could not preload existing keys: {e}")

    def _ensure_headers(self):
        """Ensures the sheet has the required columns as its header."""
        try:
            existing_values = self.sheet.get_all_values()
            if not existing_values or len(existing_values) == 0:
                print(f"[Google Sheets] Sheet is empty. Adding header row...")
                self.sheet.append_row(EXPECTED_HEADERS, value_input_option="USER_ENTERED")
            else:
                first_row = existing_values[0]
                # If first row does not contain the headers, check if we need to insert header
                if not any("Job Title" in str(col) for col in first_row):
                    print(f"[Google Sheets] Inserting header row at row 1...")
                    self.sheet.insert_row(EXPECTED_HEADERS, index=1, value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"[Google Sheets Warning] Header verification failed: {e}")

    def append_job_row(
        self,
        job_title: str,
        company_name: str,
        match_score_pct: Any,
        interview_prep_topics: str,
        acceptance_chance_pct: Any,
        application_status: str = "Applied",
        application_date: Optional[str] = None,
        skip_if_exists: bool = True
    ) -> bool:
        """
        Appends a single job application row to the Google Sheet.
        Prevents duplicate entries when skip_if_exists is True.
        
        Columns:
        1. Job Title
        2. Company Name
        3. Match Score (%)
        4. Interview Prep Topics
        5. Acceptance Chance (%)
        6. Application Status (default: "Applied")
        7. Application Date (default: current date)
        """
        self.connect()

        # Check for duplicates using cached keys
        clean_title = str(job_title).strip().lower()
        clean_company = str(company_name).strip().lower()
        combo_key = f"{clean_title}::{clean_company}"

        if skip_if_exists:
            if hasattr(self, '_existing_keys') and combo_key in self._existing_keys:
                print(f"[Google Sheets] Row already exists for '{company_name} - {job_title}'. Skipping duplicate append.")
                return False
        
        # Format match score
        if isinstance(match_score_pct, (int, float)):
            match_score_str = f"{round(float(match_score_pct))}%"
        else:
            match_score_str = str(match_score_pct).strip()
            if not match_score_str.endswith("%"):
                match_score_str = f"{match_score_str}%"

        # Format acceptance chance
        if isinstance(acceptance_chance_pct, (int, float)):
            acceptance_chance_str = f"{round(float(acceptance_chance_pct))}%"
        else:
            acceptance_chance_str = str(acceptance_chance_pct).strip()
            if not acceptance_chance_str.endswith("%"):
                acceptance_chance_str = f"{acceptance_chance_str}%"

        # Format application date
        if not application_date:
            application_date = datetime.now().strftime("%Y-%m-%d")

        # Format interview prep topics (ensure concise string)
        if isinstance(interview_prep_topics, list):
            topics_str = ", ".join([str(t).strip() for t in interview_prep_topics if str(t).strip()])
        else:
            topics_str = str(interview_prep_topics).strip()

        row = [
            str(job_title).strip(),
            str(company_name).strip(),
            match_score_str,
            topics_str,
            acceptance_chance_str,
            application_status if application_status else "Applied",
            application_date
        ]

        print(f"[Google Sheets] Appending row: {company_name} - {job_title} | Score: {match_score_str} | Acceptance: {acceptance_chance_str}...")
        self.sheet.append_row(row, value_input_option="USER_ENTERED")
        if hasattr(self, '_existing_keys'):
            self._existing_keys.add(combo_key)
        print(f"[Google Sheets] [✓] Successfully appended to sheet.")
        return True

def sync_existing_evaluated_jobs():
    """
    Convenience function to populate Google Sheet with existing jobs from
    linkedin_ai_engineer_jobs_hyderabad.json using calculated match scores and topics.
    """
    json_path = "linkedin_ai_engineer_jobs_hyderabad.json"
    if not os.path.exists(json_path):
        print(f"[Error] File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Pre-calculated evaluations matching candidate's baseline
    evaluations = {
        "ValGenesis": {
            "score": 62, "chance": 45,
            "topics": "Python, Scikit-learn, LangChain, Vector DBs, MLOps (MLflow), Model Deployment, Teamwork"
        },
        "Inspire Infosol Pvt Ltd. India": {
            "score": 72, "chance": 70,
            "topics": "RAG Systems, Vector Databases, LangChain, PyTorch, Prompt Engineering, CI/CD, Problem Solving"
        },
        "Franklin Templeton": {
            "score": 45, "chance": 20,
            "topics": "Agentic AI Architectures, LangGraph, Enterprise GenAI Governance, Python, System Architecture, Leadership"
        },
        "Anblicks": {
            "score": 48, "chance": 25,
            "topics": "LLM Fine-Tuning, LangChain, Cloud AI Services, Python Microservices, Client Communication"
        },
        "L&T Technology Services": {
            "score": 50, "chance": 25,
            "topics": "Autonomous Agents, Multi-agent Coordination, Vector Search, Python OOP, Clean Code Practices"
        },
        "Deccan AI": {
            "score": 62, "chance": 65,
            "topics": "Machine Learning Fundamentals, Scikit-learn, Feature Engineering, Flask API, Data Structures, STAR Method"
        },
        "Prasanz": {
            "score": 65, "chance": 65,
            "topics": "Generative AI, LangChain, RAG Pipelines, Pinecone, Gemini API Integration, Rapid Prototyping"
        },
        "Truveta": {
            "score": 38, "chance": 15,
            "topics": "Large Scale Distributed Systems, Clinical Data NLP, Advanced Machine Learning, System Design"
        },
        "Optum India": {
            "score": 55, "chance": 25,
            "topics": "Transformers Architecture, Advanced NLP, Vector Databases, Healthcare AI Compliance, Scalability"
        },
        "Clarus Advisers": {
            "score": 42, "chance": 20,
            "topics": "Applied AI Engineering, Production GenAI Systems, Python Software Architecture, Stakeholder Management"
        }
    }

    tracker = GoogleSheetJobTracker()
    tracker.connect()
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n[Google Sheets] Syncing {len(jobs)} jobs to Sheet ID {SPREADSHEET_ID}...\n")
    
    for idx, job in enumerate(jobs, 1):
        title = job.get("Job Title", "Unknown Title")
        company = job.get("Company Name", "Unknown Company")
        
        eval_data = evaluations.get(company, {
            "score": 50, "chance": 30,
            "topics": "Python, Machine Learning, Generative AI, Data Structures, Behavioral"
        })
        
        tracker.append_job_row(
            job_title=title,
            company_name=company,
            match_score_pct=eval_data["score"],
            interview_prep_topics=eval_data["topics"],
            acceptance_chance_pct=eval_data["chance"],
            application_status="Applied",
            application_date=today
        )

if __name__ == "__main__":
    import sys
    print("=" * 60)
    print("Google Sheets Job Tracker Diagnostic & Sync")
    print("=" * 60)
    cred_file = find_credentials_file()
    print(f"Credentials detected: {cred_file}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        sync_existing_evaluated_jobs()
    else:
        print("Connecting to Google Sheets...")
        try:
            tracker = GoogleSheetJobTracker()
            sheet = tracker.connect()
            print(f"[✓] Connected successfully! Sheet title: '{sheet.title}'")
            print(f"Headers: {sheet.row_values(1)}")
            print("\nTip: Run 'python sheets_client.py --sync' to populate existing jobs.")
        except Exception as e:
            print(f"[!] Connection failed: {e}")

