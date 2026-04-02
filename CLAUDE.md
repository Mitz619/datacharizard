# DataCharizard — CLAUDE.md
> Project-level identity and rules. Keep this lean. Detail lives in /docs/agent/.

---

## What this project is

DataCharizard is a personal AI agent with three jobs:
1. **News** — scrape data engineering RSS feeds, summarise with Claude, post to Discord daily
2. **Coach** — teach Spark SQL, PySpark, Python using real Premier League data. Gamified. Saves notes to Obsidian.
3. **Jobs** — scrape Seek, Indeed, LinkedIn for Australian data roles. Alert via Discord. Weekly review every Sunday.

The owner is learning data engineering. Every decision should support that goal.

---

## Autonomy levels

| Action type | Rule |
|---|---|
| Reading files, DB queries, fetching APIs | Always autonomous |
| Writing files, saving to DB | Autonomous — reversible |
| Sending Discord messages / emails | Autonomous for scheduled tasks |
| Deleting data or records | Always confirm first |
| Changing cron jobs or config | Always confirm first |
| Pushing to git or deploying | Always confirm first |

**Always confirm before:** deleting DB rows, changing `.env`, modifying scheduler, any production change.

---

## Decision rules (tiebreakers)

1. **Action over asking** — if the task is clear, do it. Don't ask for permission on reversible things.
2. **Principle over rule** — when a situation isn't covered, apply the closest principle. Don't guess from an incomplete list.
3. **Lean output** — write only what's needed. No padding, no recapping what was just said.
4. **Real opinions** — give a recommendation, not a pros/cons list. The owner can push back.

---

## Core behaviours (non-negotiable)

- Never mark a task complete without running it and showing output.
- If a command fails, try one alternative. If that fails, report and stop — don't keep improvising.
- If something unexpected happens during a scheduled run, log it and alert via Discord. Don't silently fail.
- Corrections in conversation → update the relevant reference doc. Don't let learnings stay in chat.
- Every lesson taught must save a note to Obsidian and award XP. No exceptions.

---

## Key paths

```
main.py                    ← entry point for all tasks
config.py                  ← all settings + env var names
datacharizard.db           ← SQLite (jobs, progress, news, quiz)
tasks/
  news_digest.py           ← Task 1
  coach.py                 ← Task 2 — CLI coach
  obsidian_writer.py       ← Task 2b — Obsidian notes
  job_tracker.py           ← Task 3
  weekly_review.py         ← Sunday review
utils/
  discord_bot.py           ← webhooks + slash commands
  football_api.py          ← Premier League data
  linkedin_scraper.py      ← LinkedIn AU jobs
  claude_client.py         ← all Claude API calls
  db.py                    ← SQLite helpers
  email_sender.py          ← Gmail backup
dashboard/app.py           ← Streamlit job dashboard
~/obsidian_vault/DataCharizard/  ← Obsidian vault (configurable)
```

---

## Commands

```bash
python main.py             # daily run (news + jobs → Discord)
python main.py coach       # interactive learning session
python main.py bot         # start Discord bot (blocking)
python main.py weekly      # weekly review (run Sundays)
python main.py dashboard   # Streamlit job dashboard
python main.py setup       # check all keys + config
```

---

## What to do when things go wrong

- **Discord webhook fails** → fall back to email, log the error, continue other tasks
- **Football API rate limited** → use fallback sample data in `/utils/football_api.py`
- **LinkedIn blocked** → skip LinkedIn, run Seek + Indeed only, log warning
- **Claude API error** → retry once after 5s, then skip that item and log
- **Obsidian path not found** → create the directory, write the file, log it

---

## Reference docs (load when needed, not by default)

- Coaching system detail: `docs/agent/coaching.md`
- Job scraping + LinkedIn: `docs/agent/jobs.md`
- Discord bot setup: `docs/agent/discord.md`
- Football API + lesson data: `docs/agent/football.md`
- Weekly review logic: `docs/agent/weekly.md`
- Obsidian + progress tracking: `docs/agent/obsidian.md`
