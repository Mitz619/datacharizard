"""
tasks/weekly_review.py  —  Sunday weekly review

Generates a rich summary of:
  - Learning progress this week (XP, lessons, quiz accuracy)
  - Job market trends (new listings, top skills, top companies)
  - Premier League data fun fact (keeps it interesting)
  - AI-generated personalised insight from Claude

Posts to Discord #weekly-review channel.
Also sends a backup email if configured.

Cron (run every Sunday at 8am):
  0 8 * * 0 cd /path/to/datacharizard && python main.py weekly
"""
import json
from datetime import date, timedelta
from collections import Counter

from utils.db import get_conn, get_total_xp, get_level
from utils.claude_client import ask
from utils.discord_bot import post_weekly_review
from utils.football_api import get_standings, get_top_scorers
from utils.email_sender import send_email
from config import GMAIL_RECIPIENT


INSIGHT_SYSTEM = """You are DataCharizard, a supportive data engineering coach.
Given a student's weekly stats, write ONE paragraph (3-4 sentences) of personalised, 
encouraging and specific coaching advice. Be practical and direct — mention actual 
topics they should focus on next week based on their accuracy and lessons done.
Keep it human and motivating, not generic. Reference the Premier League data where fun."""


def _get_week_range() -> tuple[str, str]:
    today = date.today()
    start = today - timedelta(days=6)
    return str(start), str(today)


def _get_learning_stats(since: str) -> dict:
    with get_conn() as conn:
        lessons = conn.execute(
            "SELECT topic, COUNT(*) as n FROM user_progress "
            "WHERE completed=1 AND date_done >= ? GROUP BY topic",
            (since,)
        ).fetchall()
        quiz = conn.execute(
            "SELECT COUNT(*) as n, SUM(correct) as c, SUM(xp_earned) as xp "
            "FROM quiz_results WHERE date_done >= ?",
            (since,)
        ).fetchone()
        week_xp = conn.execute(
            "SELECT COALESCE(SUM(xp_earned),0) FROM user_progress WHERE date_done >= ?",
            (since,)
        ).fetchone()[0]
        streak = conn.execute(
            "SELECT COUNT(DISTINCT date_done) FROM user_progress "
            "WHERE completed=1 AND date_done >= ?",
            (since,)
        ).fetchone()[0]

    topic_summary = {r["topic"]: r["n"] for r in lessons}
    quiz_q   = quiz["n"] or 0
    quiz_c   = quiz["c"] or 0
    quiz_xp  = quiz["xp"] or 0
    accuracy = f"{round(quiz_c / quiz_q * 100)}%" if quiz_q else "N/A"

    return {
        "lessons_by_topic": topic_summary,
        "total_lessons":    sum(topic_summary.values()),
        "quiz_questions":   quiz_q,
        "quiz_correct":     quiz_c,
        "accuracy":         accuracy,
        "week_xp":          (week_xp or 0) + (quiz_xp or 0),
        "days_active":      streak,
    }


def _get_job_stats(since: str) -> dict:
    with get_conn() as conn:
        total_new = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE scraped_on >= ?", (since,)
        ).fetchone()[0]

        all_skills_raw = conn.execute(
            "SELECT skills FROM jobs WHERE scraped_on >= ? AND skills IS NOT NULL",
            (since,)
        ).fetchall()
        top_companies_raw = conn.execute(
            "SELECT company, COUNT(*) as n FROM jobs WHERE scraped_on >= ? "
            "GROUP BY company ORDER BY n DESC LIMIT 5",
            (since,)
        ).fetchall()
        source_counts = conn.execute(
            "SELECT source, COUNT(*) as n FROM jobs WHERE scraped_on >= ? "
            "GROUP BY source",
            (since,)
        ).fetchall()

    # flatten skills
    all_skills = []
    for row in all_skills_raw:
        try:
            all_skills.extend(json.loads(row[0]))
        except Exception:
            pass
    top_skill = Counter(all_skills).most_common(1)[0][0] if all_skills else "N/A"
    top_5_skills = [s for s, _ in Counter(all_skills).most_common(5)]

    return {
        "new_jobs":       total_new,
        "top_skill":      top_skill,
        "top_5_skills":   top_5_skills,
        "top_companies":  [r["company"] for r in top_companies_raw],
        "by_source":      {r["source"]: r["n"] for r in source_counts},
    }


def _get_football_fact() -> str:
    """Grab a fun Premier League stat for the weekly review."""
    try:
        scorers   = get_top_scorers("PL", 3)
        standings = get_standings("PL")
        leader    = standings[0] if standings else {}
        top       = scorers[0] if scorers else {}
        return (f"{leader.get('team','?')} lead the Premier League with "
                f"{leader.get('points','?')} pts. "
                f"{top.get('player','?')} ({top.get('team','?')}) tops the scoring "
                f"charts with {top.get('goals','?')} goals 🏆")
    except Exception:
        return "Premier League data unavailable this week."


def _build_ai_insight(learning: dict, jobs: dict, football_fact: str) -> str:
    prompt = f"""
Student weekly stats:
- Lessons completed: {learning['total_lessons']} ({learning['lessons_by_topic']})
- Quiz accuracy: {learning['accuracy']} ({learning['quiz_questions']} questions)
- XP earned this week: {learning['week_xp']}
- Days active: {learning['days_active']} out of 7

Job market this week:
- New jobs posted: {jobs['new_jobs']}
- Top skill in demand: {jobs['top_skill']}
- Top 5 skills: {jobs['top_5_skills']}

Premier League fun fact: {football_fact}

Write personalised coaching advice for next week.
"""
    return ask(INSIGHT_SYSTEM, prompt, max_tokens=300)


def _build_email_html(learning: dict, jobs: dict, football_fact: str,
                      insight: str, week_start: str, week_end: str) -> str:
    topic_rows = "".join(
        f"<tr><td style='padding:4px 8px'>{t}</td>"
        f"<td style='padding:4px 8px;text-align:center'>{n}</td></tr>"
        for t, n in learning["lessons_by_topic"].items()
    ) or "<tr><td colspan=2 style='padding:4px 8px;color:#aaa'>No lessons this week</td></tr>"

    skill_badges = " ".join(
        f"<span style='background:#e25822;color:#fff;padding:3px 8px;"
        f"border-radius:12px;font-size:12px;margin:2px'>{s}</span>"
        for s in jobs["top_5_skills"]
    )

    return f"""
<html><body style="font-family:Arial,sans-serif;max-width:640px;margin:auto;padding:24px">
  <h1 style="color:#e25822">🔥 DataCharizard Weekly Review</h1>
  <p style="color:#888">{week_start} → {week_end}</p>

  <h2>🎮 Your progress</h2>
  <table style="width:100%;border-collapse:collapse">
    <tr style="background:#f5f5f5">
      <td style="padding:4px 8px"><b>Level</b></td>
      <td style="padding:4px 8px;text-align:center">{get_level(get_total_xp())}</td>
    </tr>
    <tr><td style="padding:4px 8px"><b>XP this week</b></td>
        <td style="padding:4px 8px;text-align:center">{learning['week_xp']}</td></tr>
    <tr style="background:#f5f5f5">
      <td style="padding:4px 8px"><b>Quiz accuracy</b></td>
      <td style="padding:4px 8px;text-align:center">{learning['accuracy']}</td>
    </tr>
    <tr><td style="padding:4px 8px"><b>Days active</b></td>
        <td style="padding:4px 8px;text-align:center">{learning['days_active']} / 7</td></tr>
  </table>
  <h3>Lessons by topic</h3>
  <table style="width:100%;border-collapse:collapse">{topic_rows}</table>

  <h2>💼 Job market this week</h2>
  <p><b>{jobs['new_jobs']}</b> new data roles in Australia</p>
  <p><b>Top skills in demand:</b><br>{skill_badges}</p>
  <p><b>Top hiring companies:</b> {', '.join(jobs['top_companies'][:3])}</p>

  <h2>⚽ Premier League corner</h2>
  <p style="color:#444">{football_fact}</p>

  <h2>💡 Your coaching insight</h2>
  <p style="background:#fff8f0;border-left:4px solid #e25822;padding:12px;
            border-radius:4px">{insight}</p>

  <p style="color:#aaa;font-size:12px;margin-top:32px">
    DataCharizard weekly review · Keep the streak alive 🔥
  </p>
</body></html>"""


def run():
    """Generate and send the weekly review."""
    print("\n── Weekly Review ────────────────────────────────────────")
    week_start, week_end = _get_week_range()

    learning     = _get_learning_stats(week_start)
    jobs         = _get_job_stats(week_start)
    football_fact = _get_football_fact()
    insight      = _build_ai_insight(learning, jobs, football_fact)

    # Discord post
    xp    = get_total_xp()
    level = get_level(xp)
    post_weekly_review({
        "level":     level,
        "xp":        xp,
        "lessons":   learning["total_lessons"],
        "accuracy":  learning["accuracy"],
        "new_jobs":  jobs["new_jobs"],
        "top_skill": jobs["top_skill"],
        "ai_insight": insight,
    })

    # Email backup
    html = _build_email_html(learning, jobs, football_fact, insight,
                              week_start, week_end)
    from utils.email_sender import send_email
    send_email(f"🔥 DataCharizard weekly review — {week_end}", html)

    print(f"  ✅ Weekly review sent! ({learning['total_lessons']} lessons, "
          f"{jobs['new_jobs']} jobs, {learning['accuracy']} quiz accuracy)")


if __name__ == "__main__":
    run()
