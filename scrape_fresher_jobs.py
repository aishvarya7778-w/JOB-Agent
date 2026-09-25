import os
import json
import csv
import re
import sys
import time
import urllib.request
import urllib.parse
import bs4

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SEARCH_QUERIES = [
    ("Junior AI Engineer", "Hyderabad"),
    ("AI Engineer Fresher", "Hyderabad"),
    ("Entry Level AI Engineer", "Hyderabad"),
    ("Junior AI Engineer", "India"),
    ("AI Engineer Fresher", "India"),
    ("Entry Level AI Engineer", "India"),
    ("AI Engineering Intern", "India"),
    ("Generative AI Intern", "India"),
    ("Junior Machine Learning Engineer", "India")
]

EXCLUDE_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "architect", "staff", "director", "manager", "head of"
]

def fetch_job_cards():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    
    seen_ids = set()
    seen_combos = set()
    raw_cards = []
    
    for kw, loc in SEARCH_QUERIES:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={urllib.parse.quote_plus(kw)}&location={urllib.parse.quote_plus(loc)}&start=0"
        print(f"[Search] Querying: '{kw}' in '{loc}'...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            soup = bs4.BeautifulSoup(html, "html.parser")
            cards = soup.find_all("li")
            print(f"    --> Found {len(cards)} job cards.")
            
            for card in cards:
                title_el = card.find("h3", class_="base-search-card__title")
                comp_el = card.find("h4", class_="base-search-card__subtitle")
                loc_el = card.find("span", class_="job-search-card__location")
                link_el = card.find("a", class_="base-card__full-link")
                date_el = card.find("time", class_="job-search-card__listdate")
                
                if not title_el or not link_el:
                    continue
                    
                title = title_el.text.strip()
                company = comp_el.text.strip() if comp_el else "Unknown Company"
                location = loc_el.text.strip() if loc_el else "India"
                raw_url = link_el["href"]
                clean_url = raw_url.split("?")[0]
                date_posted = date_el.text.strip() if date_el else ""
                
                job_id_match = re.search(r'-(\d+)$', clean_url) or re.search(r'/view/.*?(\d+)', clean_url)
                job_id = job_id_match.group(1) if job_id_match else ""
                
                # Title filtering: avoid senior/lead roles
                title_lower = title.lower()
                if any(bad in title_lower for bad in EXCLUDE_TITLE_KEYWORDS):
                    continue
                    
                # Must be AI / ML / Data Science / GenAI / Agentic / Python relevant
                relevant_terms = ["ai", "ml", "machine learning", "artificial intelligence", "data", "deep learning", "nlp", "llm", "genai", "generative ai", "cloud", "software"]
                if not any(t in title_lower for t in relevant_terms):
                    continue
                
                # Deduplication
                combo_key = f"{title.lower()}::{company.lower()}"
                if job_id and job_id in seen_ids:
                    continue
                if combo_key in seen_combos:
                    continue
                    
                if job_id:
                    seen_ids.add(job_id)
                seen_combos.add(combo_key)
                
                raw_cards.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "date_posted": date_posted,
                    "url": clean_url
                })
        except Exception as e:
            print(f"    [Error] Search failed for '{kw}': {e}")
            
        time.sleep(1.5)
        
    return raw_cards

def fetch_job_details(job: dict) -> dict:
    job_id = job.get("job_id", "")
    url = job.get("url", "")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    
    description = ""
    criteria = {}
    
    # Try public guest API endpoint first
    if job_id:
        try:
            api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                detail_html = resp.read().decode('utf-8', errors='replace')
            soup = bs4.BeautifulSoup(detail_html, "html.parser")
            
            markup = soup.find("div", class_="show-more-less-html__markup")
            if markup:
                description = markup.get_text(separator="\n").strip()
                
            criteria_items = soup.find_all("li", class_="description__job-criteria-item")
            for item in criteria_items:
                h = item.find("h3", class_="description__job-criteria-subheader")
                v = item.find("span", class_="description__job-criteria-text")
                if h and v:
                    criteria[h.get_text(strip=True)] = v.get_text(strip=True)
        except Exception as e:
            print(f"    [Guest API Error for {job_id}]: {e}")
            
    # Clean up and normalize
    return {
        "Job ID": job_id,
        "Job Title": job.get("title", ""),
        "Company Name": job.get("company", ""),
        "Location": job.get("location", ""),
        "Date Posted": job.get("date_posted", ""),
        "Seniority Level": criteria.get("Seniority level", "Entry level / Not specified"),
        "Employment Type": criteria.get("Employment type", "Full-time"),
        "Job Function": criteria.get("Job function", "Engineering / AI"),
        "Industries": criteria.get("Industries", "Information Technology"),
        "Job Description": description,
        "Job URL": url
    }

def main():
    print("=" * 70)
    print("  LINKEDIN FRESHER / ENTRY-LEVEL AI ENGINEER DISCOVERY & EXTRACTION")
    print("=" * 70)
    
    cards = fetch_job_cards()
    print(f"\n[Filtering & Deduplication] Discovered {len(cards)} unique fresher/entry-level AI postings.")
    
    # Target top 10 unique fresher/entry-level AI postings with descriptions
    final_records = []
    
    for idx, card in enumerate(cards, 1):
        print(f"\n[{len(final_records) + 1}] Extracting JD: {card['title']} at {card['company']}")
        details = fetch_job_details(card)
        desc = details.get("Job Description", "")
        
        # Check description content and filter out senior roles that snuck in
        desc_lower = desc.lower()
        if "8+ years" in desc_lower or "10+ years" in desc_lower or "7+ years" in desc_lower:
            print("    [Skipped] Description specifies 7+ years senior experience.")
            continue
            
        if len(desc) < 100:
            print(f"    [Warning] Description too short ({len(desc)} chars).")
            # We still keep if we have enough info or move to next
            if len(desc) < 30:
                continue
                
        print(f"    [✓] Extracted description: {len(desc)} characters.")
        final_records.append(details)
        
        if len(final_records) >= 10:
            break
            
        time.sleep(1.0)
        
    print(f"\n[Complete] Successfully extracted {len(final_records)} entry-level AI job postings.")
    
    # Save to JSON and CSV
    json_path = "linkedin_fresher_ai_jobs.json"
    csv_path = "linkedin_fresher_ai_jobs.csv"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)
    print(f"[Saved] {json_path}")
    
    fieldnames = [
        "Job ID", "Job Title", "Company Name", "Location", "Date Posted",
        "Seniority Level", "Employment Type", "Job Function", "Industries",
        "Job Description", "Job URL"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_records)
    print(f"[Saved] {csv_path}")
    
    # Print preview table
    print("\n" + "=" * 70)
    print("                 DISCOVERED ENTRY-LEVEL AI JOBS")
    print("=" * 70)
    for i, r in enumerate(final_records, 1):
        print(f"{i:2d}. {r['Job Title']} | {r['Company Name']} | {r['Location']}")

if __name__ == "__main__":
    main()
