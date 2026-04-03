"""
tasks/job_tracker.py  —  Task 3
Uses python-jobspy for LinkedIn + Indeed (handles anti-bot properly).
Keeps custom Seek scraper (jobspy doesn't support Seek).
"""
import time, json, re, requests
from datetime import date
from bs4 import BeautifulSoup
from utils.db import save_job, get_new_jobs, mark_jobs_alerted, init_db
from utils.claude_client import ask
from config import JOB_KEYWORDS, JOB_LOCATION


HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36")
}

SKILL_EXTRACT_SYSTEM = """Extract technical skills from this job title.
Return ONLY a JSON array, e.g.: ["Python", "Spark", "Databricks"]
Max 6 items. Common data tools only."""


# ── JobSpy — LinkedIn + Indeed ─────────────────────────────────────────────────

def scrape_with_jobspy(keyword: str, results_per_site: int = 15) -> list[dict]:
    try:
        from jobspy import scrape_jobs

        df = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=keyword,
            location="Australia",
            results_wanted=results_per_site,
            hours_old=48,
            country_indeed="Australia",
            linkedin_fetch_description=False,
        )

        if df is None or df.empty:
            return []

        jobs = []
        for _, row in df.iterrows():
            title   = str(row.get("title", "") or "").strip()
            company = str(row.get("company", "") or "N/A").strip()
            loc     = str(row.get("location", "") or "Australia").strip()
            url     = str(row.get("job_url", "") or "").strip()
            source  = str(row.get("site", "") or "jobspy").strip()

            posted = str(date.today())
            date_posted = row.get("date_posted")
            if date_posted and str(date_posted) != "nan":
                try:
                    posted = str(date_posted)[:10]
                except Exception:
                    pass

            if title and url:
                jobs.append({
                    "title":     title,
                    "company":   company,
                    "location":  loc,
                    "url":       url,
                    "source":    source,
                    "posted_on": posted,
                })
        return jobs

    except ImportError:
        print("  ⚠️  python-jobspy not installed — run: pip install python-jobspy")
        return []
    except Exception as e:
        print(f"  JobSpy error ({keyword}): {e}")
        return []


# ── Seek scraper ───────────────────────────────────────────────────────────────

def scrape_seek(keyword: str, pages: int = 2) -> list[dict]:
    jobs = []
    for page in range(1, pages + 1):
        url = (f"https://www.seek.com.au/{keyword.replace(' ', '-')}-jobs"
               f"/in-All-Australia?page={page}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("[data-testid='job-card']")[:20]:
                title_el   = card.select_one("[data-testid='job-card-title']")
                company_el = card.select_one("[data-automation='jobCompany']")
                loc_els    = card.select("[data-automation='jobCardLocation']")
                link_el    = card.select_one("[data-automation='job-list-item-link-overlay']")

                if not title_el:
                    continue

                title   = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "N/A"
                loc     = ", ".join(
                    el.get_text(strip=True) for el in loc_els
                ) if loc_els else "Australia"
                href    = link_el["href"] if link_el else ""
                job_url = (f"https://www.seek.com.au{href}"
                           if href.startswith("/") else href)

                jobs.append({
                    "title":     title,
                    "company":   company,
                    "location":  loc,
                    "url":       job_url,
                    "source":    "seek",
                    "posted_on": str(date.today()),
                })

            time.sleep(1.5)
        except Exception as e:
            print(f"  seek error ({keyword} p{page}): {e}")
    return jobs


# ── Skill extraction — rule-based, no Claude API needed ───────────────────────

SKILL_KEYWORDS = [
    "python", "sql", "spark", "pyspark", "scala", "java", "r",
    "databricks", "snowflake", "redshift", "bigquery", "synapse",
    "dbt", "airflow", "kafka", "flink", "luigi", "prefect",
    "aws", "azure", "gcp", "s3", "glue", "lambda",
    "pandas", "numpy", "tensorflow", "pytorch",
    "tableau", "power bi", "looker", "superset",
    "docker", "kubernetes", "terraform", "git",
    "postgresql", "mysql", "mongodb", "cassandra",
    "delta lake", "iceberg", "parquet", "hdfs",
]

def extract_skills(job: dict) -> list[str]:
    """Rule-based skill extraction from title — no API call needed."""
    text = (job.get("title", "") + " " + job.get("company", "")).lower()
    found = [s for s in SKILL_KEYWORDS if s in text]
    return found[:8]


# ── Main run ───────────────────────────────────────────────────────────────────

def run():
    print("\n── Task 3: Job Tracker ─────────────────────────────────")
    init_db()

    all_jobs = []

    # ── Seek ───────────────────────────────────────────────────────
    for kw in JOB_KEYWORDS[:4]:
        print(f"  🔍 Seek: '{kw}'")
        all_jobs.extend(scrape_seek(kw))
        time.sleep(1)

    # ── LinkedIn + Indeed via JobSpy ───────────────────────────────
    for kw in JOB_KEYWORDS[:3]:
        print(f"  🔍 LinkedIn + Indeed (JobSpy): '{kw}'")
        jobs = scrape_with_jobspy(kw, results_per_site=15)
        print(f"     → {len(jobs)} found")
        all_jobs.extend(jobs)
        time.sleep(2)

    # ── Deduplicate ────────────────────────────────────────────────
    seen_urls, unique_jobs = set(), []
    for j in all_jobs:
        if j.get("url") and j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            unique_jobs.append(j)

    print(f"  📋 {len(unique_jobs)} unique jobs found")

    # ── Save (rule-based skill extraction — instant, no API) ───────
    saved = 0
    for job in unique_jobs:
        skills = extract_skills(job)
        if save_job(job["title"], job["company"], job["location"],
                    job["url"], skills, job["source"], job["posted_on"]):
            saved += 1

    print(f"  💾 {saved} new jobs saved (Seek + LinkedIn + Indeed)")

    # ── Discord + email alerts ─────────────────────────────────────
    new_jobs = get_new_jobs(since=str(date.today()))
    if new_jobs:
        from utils.discord_bot import post_job_alerts
        post_job_alerts(new_jobs)
        from utils.email_sender import send_email, build_news_email
        html = build_news_email([], jobs=new_jobs)
        send_email(
            f"🧑‍💻 {len(new_jobs)} new data jobs in Australia — {date.today()}",
            html
        )
        mark_jobs_alerted([j["id"] for j in new_jobs])
        print(f"  ✅ Alerted {len(new_jobs)} jobs via Discord + email")
    else:
        print("  No new jobs to alert today.")


if __name__ == "__main__":
    run()
