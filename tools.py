import requests
import os
import time
from dotenv import load_dotenv
from datetime import datetime,timedelta,timezone
from playwright.sync_api import sync_playwright
import logging

logger=logging.getLogger("Scrapper")

load_dotenv()

def get_browser():
    playwright=sync_playwright().start()
    browser=playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox","--disable-setuid-sandbox"]
    )
    context=browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"
    )
    return playwright,browser,context

def scrape_remotive(role, num_results=10):
    
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {
            "search": role,
            "limit": num_results
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        jobs = []
        for job in data.get("jobs", [])[:num_results]:
            jobs.append({
                "source": "Remotive",
                "title": job.get("title", "N/A"),
                "company": job.get("company_name", "N/A"),
                "location": job.get("candidate_required_location", "Remote"),
                "description": job.get("description", "N/A")[:300],
                "url": job.get("url", "N/A"),
                "date_posted": job.get("publication_date", None),
                "days_ago": "Unknown"
            })
        
        return jobs
    except Exception as e:
        
        return []
    
def scrape_weworkremotely(role, num_results=10):
    """Fetch jobs from WeWorkRemotely RSS feed"""
    try:
        import xml.etree.ElementTree as ET

        urls = [
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
            "https://weworkremotely.com/remote-jobs.rss"
        ]

        jobs = []
        # Split role into keywords for flexible matching
        keywords = role.lower().split()

        for url in urls:
            response = requests.get(url, timeout=15)
            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                pubdate_el = item.find("pubDate")
                region_el = item.find(
                    "{https://weworkremotely.com}region"
                )

                title = title_el.text \
                        if title_el is not None else "N/A"
                desc = desc_el.text or ""

                # Flexible keyword matching
                combined = (title + " " + desc).lower()
                if not any(kw in combined for kw in keywords):
                    continue

                # Parse company:title format
                if ":" in title:
                    parts = title.split(":", 1)
                    company = parts[0].strip()
                    job_title = parts[1].strip()
                else:
                    company = "N/A"
                    job_title = title

                jobs.append({
                    "source": "WeWorkRemotely",
                    "title": job_title,
                    "company": company,
                    "location": region_el.text
                               if region_el is not None else "Remote",
                    "description": desc[:300],
                    "url": link_el.text
                           if link_el is not None else "N/A",
                    "date_posted": pubdate_el.text
                                   if pubdate_el is not None else None,
                    "days_ago": "Unknown"
                })

                if len(jobs) >= num_results:
                    break

            if len(jobs) >= num_results:
                break

        
        return jobs

    except Exception as e:
        
        return []

def scrape_internshala(role, num_results=10):
    """Scrape jobs from Internshala"""
    
    playwright, browser, context = get_browser()

    try:
        page = context.new_page()
        url = (f"https://internshala.com/jobs/"
               f"{role.replace(' ', '-').lower()}-jobs")
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )
        time.sleep(3)

        jobs = []
        job_cards = page.query_selector_all(
            "div.individual_internship"
        )

        for card in job_cards[:num_results]:
            try:
                # Exact selectors from debug
                title = card.query_selector("a.job-title-href") or \
                        card.query_selector("h2.job-internship-name")

                company = card.query_selector("p.company-name") or \
                          card.query_selector("div.company_name")

                location = card.query_selector("p.locations") or \
                           card.query_selector("a.location_link")

                salary = card.query_selector("div.row-1-item span.desktop")

                description = card.query_selector("div.about_job")

                link = card.query_selector("a.job-title-href")

                if not title:
                    continue

                href = link.get_attribute("href") if link else ""
                full_url = f"https://internshala.com{href}" \
                           if href.startswith("/") else href

                jobs.append({
                    "source": "Internshala",
                    "title": title.inner_text().strip(),
                    "company": company.inner_text().strip()
                               if company else "N/A",
                    "location": location.inner_text().strip()
                                if location else "India",
                    "description": description.inner_text().strip()[:300]
                                   if description else "Internshala job",
                    "salary": salary.inner_text().strip()
                              if salary else "N/A",
                    "url": full_url,
                    "date_posted": None,
                    "days_ago": "Unknown"
                })
            except Exception:
                continue

        
        return jobs

    except Exception as e:
        
        return []
    finally:
        browser.close()
        playwright.stop()

def fetch_adzuna_jobs(role, location="india", num_results=5):
    """Fetch jobs from Adzuna API"""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": num_results,
        "what": role,
        "where": location,
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        jobs = []
        for job in data.get("results", []):
            jobs.append({
                "source": "Adzuna",
                "title": job.get("title", "N/A"),
                "company": job.get("company", {}).get("display_name", "N/A"),
                "location": job.get("location", {}).get("display_name", "N/A"),
                "description": job.get("description", "N/A")[:300],
                "url": job.get("redirect_url", "N/A"),
                "data_posted":job.get("created",None)
            })
        return jobs
    except Exception as e:
        
        return []


def fetch_jsearch_jobs(role, location="India", num_results=5):
    """Fetch jobs from JSearch API via RapidAPI"""
    api_key = os.getenv("RAPIDAPI_KEY")

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query": f"{role} in {location}",
        "page": "1",
        "num_pages": "1",
        "num_results": num_results
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        jobs = []
        for job in data.get("data", [])[:num_results]:
            jobs.append({
                "source": "JSearch",
                "title": job.get("job_title", "N/A"),
                "company": job.get("employer_name", "N/A"),
                "location": job.get("job_city", "N/A"),
                "description": job.get("job_description", "N/A")[:300],
                "url": job.get("job_apply_link", "N/A"),
                "date_posted":job.get("job_posted_at_datetime_utc",None)
            })
        return jobs
    except Exception as e:
        
        return []


def fetch_muse_jobs(role, num_results=5):
    """Fetch jobs from The Muse API"""
    api_key = os.getenv("MUSE_API_KEY")

    url = "https://www.themuse.com/api/public/jobs"
    params = {
        "api_key": api_key,
        "page": 0,
        "descending": "true"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        jobs = []
        for job in data.get("results", [])[:num_results]:
            jobs.append({
                "source": "The Muse",
                "title": job.get("name", "N/A"),
                "company": job.get("company", {}).get("name", "N/A"),
                "location": job.get("locations", [{}])[0].get("name", "Remote"),
                "description": job.get("contents", "N/A")[:300],
                "url": job.get("refs", {}).get("landing_page", "N/A"),
                "date_posted":job.get("publication_date",None)
            })
        return jobs
    except Exception as e:
        
        return []

def fetch_usajobs(role, num_results=5):
    """Fetch jobs from USAJobs API"""
    api_key = os.getenv("USAJOB_API_KEY")
    user_agent = os.getenv("USAJOB_USER_AGENT")

    url = "https://data.usajobs.gov/api/search"
    headers = {
        "Authorization-Key": api_key,
        "User-Agent": user_agent,
        "Host": "data.usajobs.gov"
    }
    params = {
        "Keyword": role,
        "ResultsPerPage": num_results
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        jobs = []
        results = data.get("SearchResult", {}).get("SearchResultItems", [])
        for job in results[:num_results]:
            position = job.get("MatchedObjectDescriptor", {})
            jobs.append({
                "source": "USAJobs",
                "title": position.get("PositionTitle", "N/A"),
                "company": position.get("OrganizationName", "N/A"),
                "location": position.get("PositionLocationDisplay", "N/A"),
                "description": position.get("UserArea", {}).get("Details", {}).get("JobSummary", "N/A")[:300],
                "url": position.get("PositionURI", "N/A"),
                "date_posted":job.get("PublicationStartDate",None)
            })
        return jobs
    except Exception as e:
        
        return []
    
def fetch_arbeitnow_jobs(role, num_results=5):
    

    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {
        "search": role,
        "page": 1
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        jobs = []
        for job in data.get("data", [])[:num_results]:
            jobs.append({
                "source": "Arbeitnow",
                "title": job.get("title", "N/A"),
                "company": job.get("company_name", "N/A"),
                "location": job.get("location", "Remote"),
                "description": job.get("description", "N/A")[:300],
                "url": job.get("url", "N/A"),
                "remote": job.get("remote", False),
                "tags": job.get("tags", []),
                "date_posted":job.get("created_at",None)
            })
        return jobs
    except Exception as e:
        
        return []
    
def fetch_findwork_jobs(role, num_results=5):
    """Fetch jobs from Findwork API - Great for tech jobs!"""
    api_key = os.getenv("FINDWORK_API_KEY")

    url = "https://findwork.dev/api/jobs/"
    headers = {
        "Authorization": f"Token {api_key}"
    }
    params = {
        "search": role,
        "sort_by": "relevance"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        jobs = []
        for job in data.get("results", [])[:num_results]:
            jobs.append({
                "source": "Findwork",
                "title": job.get("role", "N/A"),
                "company": job.get("company_name", "N/A"),
                "location": job.get("location", "Remote"),
                "description": job.get("text", "N/A")[:300],
                "url": job.get("url", "N/A"),
                "remote": job.get("remote", False),
                "tags": job.get("keywords", []),
                "date_posted":job.get("date_posted",None)
            })
        return jobs
    except Exception as e:
        
        return []
    
def fetch_jooble_jobs(role, location="India", num_results=5):
    """Fetch jobs from Jooble API - Uses POST request"""
    api_key = os.getenv("JOOBLE_API_KEY")

    if not api_key:
        
        return []

    url = f"https://jooble.org/api/{api_key}"
    payload = {
        "keywords": role,
        "location": location,
        "ResultOnPage": num_results,
        "page": 1
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        jobs = []
        for job in data.get("jobs", [])[:num_results]:
            jobs.append({
                "source": "Jooble",
                "title": job.get("title", "N/A"),
                "company": job.get("company", "N/A"),
                "location": job.get("location", "N/A"),
                "description": job.get("snippet", "N/A")[:300],
                "url": job.get("link", "N/A"),
                "salary": job.get("salary", "N/A"),
                "type": job.get("type", "N/A"),
                "date_posted":job.get("updated",None)
            })
        return jobs
    except Exception as e:
        
        return []
    

def filter_jobs_by_date(jobs,max_days=7):
    filtered=[]

    now=datetime.now(timezone.utc)
    cutoff=now-timedelta(days=max_days)

    no_date_count=0

    for job in jobs:
        date_str=job.get("date_posted")
        if not date_str:
            no_date_count+=1
            job["date_posted"]="UnKnown"
            job["days_ago"]="UnKnown"
            filtered.append(job)
            continue

        try:
            date_str=str(date_str).strip()
            if "T" in date_str:
                date_str=date_str.replace("Z","+00:00")
                posted_date=datetime.fromisoformat(date_str)
                if posted_date.tzinfo in None:
                    posted_date=posted_date.replace(
                        tzinfo=timezone.utc
                    )
            else:
                posted_date=datetime.strptime(
                    date_str[:10],"%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)

            days_ago=(now-posted_date).days
            job["days_ago"]=days_ago
            if posted_date >= cutoff:
                filtered.append(job)
        except Exception:
            job["days_ago"]="UnKnown"
            filtered.append(job)

    
    return filtered
            


def extract_cv_from_pdf(pdf_path):
    try:
        import fitz
        doc=fitz.open(pdf_path)
        text=""
        for page in doc:
            text+=page.get_text()
        doc.close()
        
        return text
    except Exception as e:
        
        return None
    
def extract_latex_from_overleaf(tex_path):
    try:
        with open(tex_path,"r",encoding="utf-8") as f:
            latex_content=f.read()
        
        return latex_content
    except Exception as e:
        
        return None
    
def load_cv(pdf_path=None,tex_path=None):
    cv_text=None
    latex_content=None
    if tex_path and os.path.exists(tex_path):
        latex_content=extract_latex_from_overleaf(tex_path)
        
    elif pdf_path and os.path.exists(pdf_path):
        cv_text=extract_cv_from_pdf(pdf_path)
        
    else:
        
        cv_text="sample candidates profile"

    return cv_text,latex_content


def fetch_all_jobs(role, location="India", num_results=5):
    """Fetch jobs from all platforms and combine"""
    

    jsearch_jobs = fetch_jsearch_jobs(role, location, num_results)
    

    adzuna_jobs = fetch_adzuna_jobs(role, location, num_results)
    

    muse_jobs = fetch_muse_jobs(role, num_results)
    

    usajobs_jobs = fetch_usajobs(role, num_results)
    

    arbeitnow_jobs = fetch_arbeitnow_jobs(role, num_results)
    

    findwork_jobs = fetch_findwork_jobs(role, num_results)
    

    jooble_jobs = fetch_jooble_jobs(role,location, num_results)
    

    all_jobs = adzuna_jobs + jsearch_jobs + muse_jobs + usajobs_jobs + arbeitnow_jobs + findwork_jobs + jooble_jobs
    
    return all_jobs

def fetch_jobs_from_sources(role, location="India", 
                             num_results=10, 
                             selected_sources=None):
    """
    Fetch jobs only from selected sources
    Returns jobs + count per source
    """
    if not selected_sources:
        return [], {}

    all_jobs = []
    source_counts = {}

    

    # ── APIs ──────────────────────────────
    if "Adzuna" in selected_sources:
        jobs = fetch_adzuna_jobs(role, location, num_results)
        source_counts["Adzuna"] = len(jobs)
        all_jobs.extend(jobs)
        

    if "JSearch" in selected_sources:
        jobs = fetch_jsearch_jobs(role, location, num_results)
        source_counts["JSearch"] = len(jobs)
        all_jobs.extend(jobs)
        

    if "The Muse" in selected_sources:
        jobs = fetch_muse_jobs(role, num_results)
        source_counts["The Muse"] = len(jobs)
        all_jobs.extend(jobs)
        
    if "USAJobs" in selected_sources:
        jobs = fetch_usajobs(role, num_results=num_results)
        source_counts["USAJobs"] = len(jobs)
        all_jobs.extend(jobs)
        

    if "Arbeitnow" in selected_sources:
        jobs = fetch_arbeitnow_jobs(role, num_results)
        source_counts["Arbeitnow"] = len(jobs)
        all_jobs.extend(jobs)
        

    if "Findwork" in selected_sources:
        jobs = fetch_findwork_jobs(role, num_results)
        source_counts["Findwork"] = len(jobs)
        all_jobs.extend(jobs)
        
    if "Jooble" in selected_sources:
        jobs = fetch_jooble_jobs(role, location, num_results)
        source_counts["Jooble"] = len(jobs)
        all_jobs.extend(jobs)
        

    # ── Scrapers ──────────────────────────
    

    

    if "Remotive" in selected_sources:
        jobs = scrape_remotive(role, num_results)
        source_counts["Remotive"] = len(jobs)
        all_jobs.extend(jobs)
        

    if "WeWorkRemotely" in selected_sources:
        jobs = scrape_weworkremotely(role, num_results)
        source_counts["WeWorkRemotely"] = len(jobs)
        all_jobs.extend(jobs)
        
    if "Internshala" in selected_sources:
        jobs = scrape_internshala(role, num_results)
        source_counts["Internshala"] = len(jobs)
        all_jobs.extend(jobs)
        
    return all_jobs, source_counts

if __name__ == "__main__":
    jobs = fetch_all_jobs("Backend Intern", "India")
    for i, job in enumerate(jobs, 1):
        print(f"\n--- Job {i} ---")
        print(f"Source:   {job['source']}")
        print(f"Title:    {job['title']}")
        print(f"Company:  {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Description: {job['description']}")
        print(f"URL:      {job['url']}")