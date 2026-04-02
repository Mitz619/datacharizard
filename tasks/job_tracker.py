"""
tasks/job_tracker.py  —  Task 3
Scrapes Seek.com.au and Indeed AU for data engineering jobs.
Saves to DB, alerts new jobs via email.

Note: Web scraping is rate-limited and respectful (1-2s delays).
For production, consider using Seek's partner API or Indeed's publisher API.
"""
import time, json, re, requests
from datetime import date
from bs4 import BeautifulSoup
from utils.db import save_job, get_new_jobs, mark_jobs_alerted, init_db
from utils.email_sender import send_email, build_news_email
from utils.claude_client import ask
from config import JOB_KEYWORDS, JOB_LOCATION


HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36")
}

SKILL_EXTRACT_SYSTEM = """Extract technical skills from this job description.
Return ONLY a JSON array of skill strings, e.g.: ["Python", "Spark", "Databricks"]
Include: languages, frameworks, cloud platforms, data tools. Max 10 items."""


# ── Seek scraper ──────────────────────────────────────────────────────────────

def scrape_seek(keyword: str, pages: int = 2) -> list[dict]:
    jobs = []
    for page in range(1, pages + 1):
        url = (f"https://www.seek.com.au/{keyword.replace(' ', '-')}-jobs"
               f"/in-All-Australia?page={page}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Seek renders job cards with data-testid attributes
            for card in soup.select("[data-testid='job-card']")[:20]:
                title_el   = card.select_one("[data-testid='job-title']")
                company_el = card.select_one("[data-testid='job-card-company']")
                loc_el     = card.select_one("[data-testid='job-card-location']")
                link_el    = card.select_one("a[href*='/job/']")

                if not title_el:
                    continue

                title   = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "N/A"
                loc     = loc_el.get_text(strip=True) if loc_el else "Australia"
                href    = link_el["href"] if link_el else ""
                job_url = f"https://www.seek.com.au{href}" if href.startswith("/") else href

                jobs.append({"title": title, "company": company,
                              "location": loc, "url": job_url,
                              "source": "seek", "posted_on": str(date.today())})

            time.sleep(1.5)  # be polite
        except Exception as e:
            print(f"  seek error ({keyword} p{page}): {e}")
    return jobs


def scrape_indeed(keyword: str) -> list[dict]:
    """Indeed AU search — light scrape."""
    jobs = []
    url = f"https://au.indeed.com/jobs?q={keyword.replace(' ', '+')}&l=Australia"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select(".job_seen_beacon")[:15]:
            title_el   = card.select_one("h2.jobTitle a")
            company_el = card.select_one("[data-testid='company-name']")
            loc_el     = card.select_one("[data-testid='text-location']")

            if not title_el:
                continue

            title   = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "N/A"
            loc     = loc_el.get_text(strip=True) if loc_el else "Australia"
            href    = title_el.get("href", "")
            job_url = f"https://au.indeed.com{href}" if href.startswith("/") else href

            jobs.append({"title": title, "company": company,
                          "location": loc, "url": job_url,
                          "source": "indeed", "posted_on": str(date.today())})
        time.sleep(1)
    except Exception as e:
        print(f"  indeed error ({keyword}): {e}")
    return jobs


def extract_skills(job: dict) -> list[str]:
    """Use Claude to pull skills from the title (fast, no full page fetch)."""
    try:
        raw = ask(SKILL_EXTRACT_SYSTEM, f"Job title: {job['title']} at {job['company']}")
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception:
        return []


def run():
    """Entry point — scrape Seek, Indeed, LinkedIn; store; Discord + email alert."""
    print("\n── Task 3: Job Tracker ─────────────────────────────────")
    init_db()

    all_jobs = []

    # ── Seek + Indeed ──────────────────────────────────────────────
    for kw in JOB_KEYWORDS[:4]:
        print(f"  🔍 Seek/Indeed: '{kw}'")
        all_jobs.extend(scrape_seek(kw))
        all_jobs.extend(scrape_indeed(kw))

    # ── LinkedIn ───────────────────────────────────────────────────
    try:
        from utils.linkedin_scraper import scrape_linkedin, scrape_linkedin_via_apify
        import os
        if os.getenv("APIFY_TOKEN"):
            linkedin_jobs = scrape_linkedin_via_apify(JOB_KEYWORDS[:4])
        else:
            linkedin_jobs = scrape_linkedin(JOB_KEYWORDS[:3])
        print(f"  LinkedIn: {len(linkedin_jobs)} listings found")
        all_jobs.extend(linkedin_jobs)
    except Exception as e:
        print(f"  LinkedIn scraper skipped: {e}")

    # ── Deduplicate & save ─────────────────────────────────────────
    seen_urls, unique_jobs = set(), []
    for j in all_jobs:
        if j["url"] and j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            unique_jobs.append(j)

    saved = 0
    for job in unique_jobs:
        skills = extract_skills(job)
        if save_job(job["title"], job["company"], job["location"],
                    job["url"], skills, job["source"], job["posted_on"]):
            saved += 1
    print(f"  💾 Saved {saved} new jobs (Seek + Indeed + LinkedIn)")

    # ── Discord job alerts ─────────────────────────────────────────
    new_jobs = get_new_jobs(since=str(date.today()))
    if new_jobs:
        from utils.discord_bot import post_job_alerts
        post_job_alerts(new_jobs)
        # Email fallback
        from utils.email_sender import send_email, build_news_email
        html = build_news_email([], jobs=new_jobs)
        send_email(f"🧑‍💻 {len(new_jobs)} new data jobs — {date.today()}", html)
        mark_jobs_alerted([j["id"] for j in new_jobs])
        print(f"  ✅ Alerted {len(new_jobs)} new jobs via Discord + email")
    else:
        print("  No new jobs to alert today.")


if __name__ == "__main__":
    run()
