"""
utils/linkedin_scraper.py  —  LinkedIn Australia job scraper

Uses LinkedIn's public job search page (no auth required for basic listings).
Fetches JSON embedded in the page and parses job cards.

Rate limiting: 2s delay between requests, max 3 keyword searches.
If LinkedIn changes their HTML structure, update the selectors below.

Alternative: Use the Apify LinkedIn Jobs Scraper (free 5 runs/month)
  → set APIFY_TOKEN in .env for more reliable scraping.
"""
import time, re, json, requests
from bs4 import BeautifulSoup
from config import LINKEDIN_GEO_ID, LINKEDIN_JOB_TYPE

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.linkedin.com/",
}


def _build_search_url(keyword: str, start: int = 0) -> str:
    kw = keyword.replace(" ", "%20")
    return (
        f"https://www.linkedin.com/jobs/search?"
        f"keywords={kw}"
        f"&geoId={LINKEDIN_GEO_ID}"
        f"&f_JT={LINKEDIN_JOB_TYPE}"
        f"&sortBy=DD"          # date descending
        f"&start={start}"
    )


def _parse_jobs_from_html(html: str, keyword: str) -> list[dict]:
    """Parse LinkedIn job cards from search results page."""
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # LinkedIn uses <ul> with data-results or class="jobs-search__results-list"
    cards = soup.select("ul.jobs-search__results-list li")
    if not cards:
        # Try the public (non-auth) page structure
        cards = soup.select("div.base-card")

    for card in cards[:15]:
        try:
            # Title
            title_el = (card.select_one("h3.base-search-card__title") or
                        card.select_one("h3.job-result-card__title"))
            # Company
            company_el = (card.select_one("h4.base-search-card__subtitle") or
                          card.select_one("h4.result-card__subtitle"))
            # Location
            loc_el = (card.select_one("span.job-search-card__location") or
                      card.select_one("span.result-card__location"))
            # Link
            link_el = card.select_one("a[href*='/jobs/view/']")

            title   = title_el.get_text(strip=True)   if title_el   else ""
            company = company_el.get_text(strip=True)  if company_el else ""
            loc     = loc_el.get_text(strip=True)      if loc_el     else "Australia"
            url     = link_el["href"].split("?")[0]    if link_el    else ""

            if title and url:
                jobs.append({
                    "title":      title,
                    "company":    company,
                    "location":   loc,
                    "url":        url,
                    "source":     "linkedin",
                    "posted_on":  _extract_date(card),
                })
        except Exception:
            continue
    return jobs


def _extract_date(card) -> str:
    """Try to extract the posted date from a card."""
    from datetime import date, timedelta
    time_el = card.select_one("time") or card.select_one("[datetime]")
    if time_el and time_el.get("datetime"):
        return time_el["datetime"][:10]
    text = (card.get_text() or "").lower()
    if "today" in text or "just now" in text:
        return str(date.today())
    if "yesterday" in text:
        return str(date.today() - timedelta(days=1))
    m = re.search(r"(\d+)\s*(day|hour|week)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        days = n if "day" in unit else (n * 7 if "week" in unit else 0)
        return str(date.today() - timedelta(days=days))
    return str(date.today())


def scrape_linkedin(keywords: list[str], max_per_keyword: int = 15) -> list[dict]:
    """
    Main entry point. Searches LinkedIn for each keyword in Australia.
    Returns list of job dicts.
    """
    all_jobs = []
    # Limit to 3 keywords to stay under LinkedIn's rate limits
    for kw in keywords[:3]:
        print(f"  🔍 LinkedIn: '{kw}'")
        url = _build_search_url(kw)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 429:
                print("  ⏳ LinkedIn rate limited — waiting 30s")
                time.sleep(30)
                resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code != 200:
                print(f"  ⚠️  LinkedIn returned {resp.status_code} for '{kw}'")
                continue
            jobs = _parse_jobs_from_html(resp.text, kw)
            all_jobs.extend(jobs)
            print(f"     found {len(jobs)} jobs")
        except Exception as e:
            print(f"  LinkedIn error ({kw}): {e}")
        time.sleep(2.5)   # respectful delay

    # Deduplicate by URL
    seen, unique = set(), []
    for j in all_jobs:
        if j["url"] not in seen and j["url"]:
            seen.add(j["url"])
            unique.append(j)

    return unique


# ── Apify fallback (more reliable, free tier available) ───────────────────────

def scrape_linkedin_via_apify(keywords: list[str]) -> list[dict]:
    """
    Uses Apify's LinkedIn Jobs Scraper actor.
    Requires APIFY_TOKEN in .env — free tier: 5 actor runs/month.
    Sign up: https://apify.com
    Actor: https://apify.com/curious_coder/linkedin-jobs-scraper
    """
    import os
    token = os.getenv("APIFY_TOKEN", "")
    if not token:
        return []

    run_url = "https://api.apify.com/v2/acts/curious_coder~linkedin-jobs-scraper/run-sync-get-dataset-items"
    payload = {
        "queries":   keywords[:4],
        "location":  "Australia",
        "maxResults": 20,
        "jobType":   "full-time",
    }
    try:
        resp = requests.post(
            f"{run_url}?token={token}",
            json=payload, timeout=120   # Apify runs can take a minute
        )
        items = resp.json()
        return [{
            "title":     i.get("title", ""),
            "company":   i.get("companyName", ""),
            "location":  i.get("location", "Australia"),
            "url":       i.get("jobUrl", ""),
            "source":    "linkedin",
            "posted_on": i.get("postedAt", "")[:10],
        } for i in items if i.get("title") and i.get("jobUrl")]
    except Exception as e:
        print(f"  Apify error: {e}")
        return []
