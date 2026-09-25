import subprocess
import json
import csv
import re
import sys
import time
import urllib.request
import bs4

SESSION_NAME = "demo-session"

def run_browser_act(args, stdin_data=None):
    cmd = ["browser-act", "--session", SESSION_NAME] + args
    result = subprocess.run(
        cmd,
        input=stdin_data,
        text=True,
        capture_output=True,
        encoding='utf-8',
        errors='replace'
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def eval_js(js_code):
    stdout, stderr, rc = run_browser_act(["eval", "--stdin"], stdin_data=js_code)
    if rc != 0:
        return None
    try:
        return json.loads(stdout)
    except Exception:
        return stdout

def get_top_10_jobs():
    search_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=AI+Engineer&location=Hyderabad&start=0"
    req = urllib.request.Request(
        search_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
    )
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    
    soup = bs4.BeautifulSoup(html, "html.parser")
    cards = soup.find_all("li")
    jobs = []
    
    for card in cards:
        title_el = card.find("h3", class_="base-search-card__title")
        company_el = card.find("h4", class_="base-search-card__subtitle")
        loc_el = card.find("span", class_="job-search-card__location")
        link_el = card.find("a", class_="base-card__full-link")
        date_el = card.find("time", class_="job-search-card__listdate")
        
        if not title_el or not link_el:
            continue
            
        title = title_el.text.strip()
        company = company_el.text.strip() if company_el else ""
        location = loc_el.text.strip() if loc_el else ""
        raw_url = link_el["href"]
        # Clean URL to standard format
        clean_url = raw_url.split("?")[0]
        date_posted = date_el.text.strip() if date_el else ""
        
        job_id_match = re.search(r'-(\d+)$', clean_url) or re.search(r'/view/.*?(\d+)', clean_url)
        job_id = job_id_match.group(1) if job_id_match else ""
        
        jobs.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "date_posted": date_posted,
            "url": clean_url
        })
        if len(jobs) >= 10:
            break
            
    return jobs

def scrape_job_details(job):
    url = job["url"]
    print(f"\n[BrowserAct] Navigating to: {job['title']} at {job['company']}")
    print(f"URL: {url}")
    
    # 1. Navigate via browser-act
    out, err, rc = run_browser_act(["navigate", url])
    time.sleep(2)  # Allow JS and layout rendering
    
    # 2. Dismiss sign-in popup if present
    dismiss_js = """
    (() => {
        const dismissBtn = document.querySelector('button[aria-label="Dismiss"], .modal__dismiss, [data-tracking-control-name="public_jobs_contextual-sign-in-modal_modal_dismiss"]');
        if (dismissBtn) {
            dismissBtn.click();
            return true;
        }
        return false;
    })()
    """
    eval_js(dismiss_js)
    
    # 3. Expand 'Show more' if present
    expand_js = """
    (() => {
        const moreBtn = document.querySelector('.show-more-less-html__button--more, button[aria-label="Show more"]');
        if (moreBtn) {
            moreBtn.click();
            return true;
        }
        return false;
    })()
    """
    eval_js(expand_js)
    time.sleep(1)
    
    # 4. Extract rich details via browser DOM
    extract_js = """
    (() => {
        const title = document.querySelector('.top-card-layout__title, .topcard__title, h1')?.innerText?.trim() || '';
        const company = document.querySelector('.topcard__flavor, .topcard__org-name-link, a[data-tracking-control-name*="subtitle"]')?.innerText?.trim() || '';
        const location = document.querySelector('.topcard__flavor--bullet, span[class*="location"]')?.innerText?.trim() || '';
        const desc = document.querySelector('.show-more-less-html__markup, .description__text')?.innerText?.trim() || '';
        
        const criteriaItems = Array.from(document.querySelectorAll('.description__job-criteria-item'));
        const criteria = {};
        criteriaItems.forEach(item => {
            const h = item.querySelector('.description__job-criteria-subheader')?.innerText?.trim();
            const t = item.querySelector('.description__job-criteria-text')?.innerText?.trim();
            if (h && t) criteria[h] = t;
        });
        
        return JSON.stringify({
            title,
            company,
            location,
            criteria,
            description: desc
        });
    })()
    """
    data_str = eval_js(extract_js)
    page_data = {}
    if data_str:
        try:
            page_data = json.loads(data_str)
        except Exception as e:
            print(f"Error parsing page data: {e}")
            
    # Fallback to guest API endpoint if browser description is empty or truncated
    description = page_data.get("description", "").strip()
    if not description and job["job_id"]:
        print(f"Fallback to guest API for job_id {job['job_id']}")
        try:
            api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job['job_id']}"
            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                }
            )
            with urllib.request.urlopen(req) as resp:
                detail_html = resp.read().decode('utf-8', errors='replace')
            detail_soup = bs4.BeautifulSoup(detail_html, "html.parser")
            markup = detail_soup.find("div", class_="show-more-less-html__markup")
            if markup:
                description = markup.get_text(separator="\n").strip()
        except Exception as ex:
            print(f"Guest API fallback error: {ex}")

    criteria = page_data.get("criteria", {})
    
    return {
        "Job ID": job.get("job_id", ""),
        "Job Title": page_data.get("title") or job.get("title", ""),
        "Company Name": page_data.get("company") or job.get("company", ""),
        "Location": page_data.get("location") or job.get("location", ""),
        "Date Posted": job.get("date_posted", ""),
        "Seniority Level": criteria.get("Seniority level", "Not specified"),
        "Employment Type": criteria.get("Employment type", "Not specified"),
        "Job Function": criteria.get("Job function", "Not specified"),
        "Industries": criteria.get("Industries", "Not specified"),
        "Job Description": description,
        "Job URL": job.get("url", "")
    }

def main():
    print("=== Scraping Top 10 AI Engineer Jobs in Hyderabad ===")
    jobs = get_top_10_jobs()
    print(f"Found {len(jobs)} jobs to process.")
    
    scraped_records = []
    for idx, job in enumerate(jobs, 1):
        print(f"\n[{idx}/10] Processing: {job['title']} - {job['company']}")
        try:
            rec = scrape_job_details(job)
            desc_preview = rec['Job Description'][:150].replace('\n', ' ') if rec['Job Description'] else "EMPTY"
            print(f"Scraped description length: {len(rec['Job Description'])} chars")
            print(f"Preview: {desc_preview}...")
            scraped_records.append(rec)
        except Exception as e:
            print(f"Failed to scrape job {job['title']}: {e}")
            
    csv_file = "linkedin_ai_engineer_jobs_hyderabad.csv"
    fieldnames = [
        "Job ID",
        "Job Title",
        "Company Name",
        "Location",
        "Date Posted",
        "Seniority Level",
        "Employment Type",
        "Job Function",
        "Industries",
        "Job Description",
        "Job URL"
    ]
    
    with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scraped_records)
        
    print(f"\nSUCCESS: Successfully saved {len(scraped_records)} jobs to {csv_file}!")

if __name__ == "__main__":
    main()
