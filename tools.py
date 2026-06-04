import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# 1. ADZUNA - India Jobs
# ─────────────────────────────────────────
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
                "url": job.get("redirect_url", "N/A")
            })
        return jobs
    except Exception as e:
        print(f"Adzuna error: {e}")
        return []


# ─────────────────────────────────────────
# 2. JSEARCH - LinkedIn/Indeed Jobs
# ─────────────────────────────────────────
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
                "url": job.get("job_apply_link", "N/A")
            })
        return jobs
    except Exception as e:
        print(f"JSearch error: {e}")
        return []


# ─────────────────────────────────────────
# 3. THE MUSE - Remote/Global Jobs
# ─────────────────────────────────────────
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
                "url": job.get("refs", {}).get("landing_page", "N/A")
            })
        return jobs
    except Exception as e:
        print(f"Muse error: {e}")
        return []


# ─────────────────────────────────────────
# 4. USAJOBS - US Government Jobs
# ─────────────────────────────────────────
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
                "url": position.get("PositionURI", "N/A")
            })
        return jobs
    except Exception as e:
        print(f"USAJobs error: {e}")
        return []
    
# ─────────────────────────────────────────
# 5. ARBEITNOW - European/Remote Jobs
# ─────────────────────────────────────────
def fetch_arbeitnow_jobs(role, num_results=5):
    """Fetch jobs from Arbeitnow API - No API key needed!"""

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
                "tags": job.get("tags", [])
            })
        return jobs
    except Exception as e:
        print(f"Arbeitnow error: {e}")
        return []
    
# ─────────────────────────────────────────
# 6. FINDWORK - Tech/Developer Jobs
# ─────────────────────────────────────────
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
                "tags": job.get("keywords", [])
            })
        return jobs
    except Exception as e:
        print(f"Findwork error: {e}")
        return []
    
# ─────────────────────────────────────────
# 7. JOOBLE - Global Job Search Engine
# ─────────────────────────────────────────
def fetch_jooble_jobs(role, location="India", num_results=5):
    """Fetch jobs from Jooble API - Uses POST request"""
    api_key = os.getenv("JOOBLE_API_KEY")

    if not api_key:
        print("Jooble API key missing!")
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
                "type": job.get("type", "N/A")
            })
        return jobs
    except Exception as e:
        print(f"Jooble error: {e}")
        return []

# ─────────────────────────────────────────
# CV PARSER
# ─────────────────────────────────────────
def extract_cv_from_pdf(pdf_path):
    try:
        import fitz
        doc=fitz.open(pdf_path)
        text=""
        for page in doc:
            text+=page.get_text()
        doc.close()
        print(f"CV extracted : {len(text)} characters")
        return text
    except Exception as e:
        print(f"PDF extraction failed :{e}")
        return None
    
def extract_latex_from_overleaf(tex_path):
    try:
        with open(tex_path,"r",encoding="utf-8") as f:
            latex_content=f.read()
        print(f"Latex extracted: {len(latex_content)} characters")
        return latex_content
    except Exception as e:
        print(f"Latex extraction failed: {e}")
        return None
    
def load_cv(pdf_path=None,tex_path=None):
    cv_text=None
    latex_content=None
    if tex_path and os.path.exists(tex_path):
        latex_content=extract_latex_from_overleaf(tex_path)
        print("Using Latex/overleaf CV format")
    elif pdf_path and os.path.exists(pdf_path):
        cv_text=extract_cv_from_pdf(pdf_path)
        print("Using PDF CV Format")
    else:
        print("No CV file found-using sample profile ")
        cv_text="sample candidates profile"

    return cv_text,latex_content


# ─────────────────────────────────────────
# 5. COMBINED FETCHER - All platforms
# ─────────────────────────────────────────
def fetch_all_jobs(role, location="India", num_results=5):
    """Fetch jobs from all platforms and combine"""
    print(f"\n🔍 Fetching jobs for: {role}")
    print("─" * 40)

    jsearch_jobs = fetch_jsearch_jobs(role, location, num_results)
    print(f"✅ JSearch: {len(jsearch_jobs)} jobs found")

    adzuna_jobs = fetch_adzuna_jobs(role, location, num_results)
    print(f"✅ Adzuna: {len(adzuna_jobs)} jobs found")

    muse_jobs = fetch_muse_jobs(role, num_results)
    print(f"✅ The Muse: {len(muse_jobs)} jobs found")

    usajobs_jobs = fetch_usajobs(role, num_results)
    print(f"✅ USAJobs: {len(usajobs_jobs)} jobs found")

    arbeitnow_jobs = fetch_arbeitnow_jobs(role, num_results)
    print(f"✅ arbeitnow jobs : {len(arbeitnow_jobs)} jobs found")

    findwork_jobs = fetch_findwork_jobs(role, num_results)
    print(f"✅ findwork jobs : {len(findwork_jobs)} jobs found")

    jooble_jobs = fetch_jooble_jobs(role,location, num_results)
    print(f"✅ findwork jobs : {len(jooble_jobs)} jobs found")

    all_jobs = adzuna_jobs + jsearch_jobs + muse_jobs + usajobs_jobs + arbeitnow_jobs + findwork_jobs + jooble_jobs
    print(f"\n📋 Total jobs fetched: {len(all_jobs)}")
    return all_jobs


# ─────────────────────────────────────────
# TEST - Run this file directly to test
# ─────────────────────────────────────────
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