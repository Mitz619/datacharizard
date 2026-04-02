"""
tasks/news_digest.py  —  Task 1
Fetches RSS feeds, summarises with Claude, saves to DB, sends daily email.
"""
import feedparser
from datetime import date
from utils.db import get_conn, init_db
from utils.claude_client import ask
from utils.email_sender import send_email, build_news_email
from config import NEWS_FEEDS, GMAIL_RECIPIENT


SYSTEM = """You are a data engineering news curator. 
Given an article title and description, write a 2-sentence plain-English summary 
that a data engineer would find useful. Be specific about what's new or interesting.
Do NOT use marketing fluff. Return only the summary, nothing else."""


def fetch_all_news(max_per_feed: int = 5) -> list[dict]:
    """Fetch and parse all RSS feeds."""
    items = []
    for url in NEWS_FEEDS:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", url)
        for entry in feed.entries[:max_per_feed]:
            title  = entry.get("title", "")
            link   = entry.get("link", "")
            desc   = entry.get("summary", entry.get("description", ""))[:800]
            items.append({"title": title, "url": link,
                          "source": source, "desc": desc})
    return items


def summarise_and_store(items: list[dict]) -> list[dict]:
    """Ask Claude to summarise each item, skip already-cached URLs."""
    today = str(date.today())
    with get_conn() as conn:
        cached = {r[0] for r in conn.execute(
            "SELECT url FROM news_cache WHERE fetched_on=?", (today,)).fetchall()}

    fresh = []
    for item in items:
        if item["url"] in cached:
            continue
        summary = ask(SYSTEM, f"Title: {item['title']}\n\nDescription: {item['desc']}")
        item["summary"] = summary

        with get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO news_cache (title,url,source,summary) VALUES (?,?,?,?)",
                (item["title"], item["url"], item["source"], summary)
            )
        fresh.append(item)
        print(f"  📰 cached: {item['title'][:60]}")
    return fresh


def run():
    """Entry point — call this from the scheduler."""
    print("\n── Task 1: News Digest ─────────────────────────────────")
    init_db()
    raw   = fetch_all_news()
    items = summarise_and_store(raw)

    if not items:
        print("  No new articles today.")
        return

    # Discord (primary)
    from utils.discord_bot import post_news_digest
    post_news_digest(items)

    # Email (backup/archive)
    html = build_news_email(items)
    send_email(f"🔥 DataCharizard Daily — {date.today()}", html)
    print(f"  Done! Sent {len(items)} articles via Discord + email.")


if __name__ == "__main__":
    run()
