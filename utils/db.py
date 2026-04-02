"""
utils/db.py  —  SQLite helper for DataCharizard
Tables: news_cache | jobs | user_progress | quiz_results
"""
import sqlite3, json
from datetime import date
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS news_cache (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT,
            url         TEXT UNIQUE,
            source      TEXT,
            summary     TEXT,
            fetched_on  TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            url         TEXT UNIQUE,
            skills      TEXT,   -- JSON list
            source      TEXT,
            posted_on   TEXT,
            scraped_on  TEXT DEFAULT (date('now')),
            alerted     INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS user_progress (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            topic       TEXT,    -- e.g. 'spark_sql', 'pyspark', 'python'
            lesson_num  INTEGER,
            xp_earned   INTEGER DEFAULT 0,
            completed   INTEGER DEFAULT 0,  -- 0/1
            date_done   TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS quiz_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            topic       TEXT,
            question    TEXT,
            correct     INTEGER,  -- 0/1
            xp_earned   INTEGER,
            date_done   TEXT DEFAULT (date('now'))
        );
        """)
    print("✅ DB initialised")


# ── User XP helpers ───────────────────────────────────────────────────────────

def get_total_xp():
    with get_conn() as conn:
        row = conn.execute("SELECT COALESCE(SUM(xp_earned),0) FROM user_progress").fetchone()
        row2 = conn.execute("SELECT COALESCE(SUM(xp_earned),0) FROM quiz_results").fetchone()
    return (row[0] or 0) + (row2[0] or 0)


def get_level(xp):
    from config import LEVELS
    level_name = LEVELS[0]
    for threshold, name in sorted(LEVELS.items()):
        if xp >= threshold:
            level_name = name
    return level_name


def add_progress(topic, lesson_num, xp):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_progress (topic, lesson_num, xp_earned, completed) VALUES (?,?,?,1)",
            (topic, lesson_num, xp)
        )


def add_quiz_result(topic, question, correct, xp):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO quiz_results (topic, question, correct, xp_earned) VALUES (?,?,?,?)",
            (topic, question, int(correct), xp)
        )


# ── Job helpers ───────────────────────────────────────────────────────────────

def save_job(title, company, location, url, skills, source, posted_on):
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO jobs
                   (title,company,location,url,skills,source,posted_on)
                   VALUES (?,?,?,?,?,?,?)""",
                (title, company, location, url, json.dumps(skills), source, posted_on)
            )
        return True
    except Exception as e:
        print(f"  job save error: {e}")
        return False


def get_new_jobs(since=None):
    """Return jobs not yet alerted, optionally filtered by date."""
    since = since or str(date.today())
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE alerted=0 AND scraped_on >= ?", (since,)
        ).fetchall()
    return [dict(r) for r in rows]


def mark_jobs_alerted(job_ids):
    with get_conn() as conn:
        conn.executemany("UPDATE jobs SET alerted=1 WHERE id=?", [(i,) for i in job_ids])
