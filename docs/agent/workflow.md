# DataCharizard — Workflow Reference
> Loaded by Claude Code when working on scheduling, orchestration, or debugging task flow.
> This is the reference doc. The routing layer is CLAUDE.md.

---

## Daily run (7am every day)

```
python main.py
    │
    ├── tasks/news_digest.py
    │       fetch RSS feeds (6 sources)
    │       → Claude summarises each article
    │       → save to news_cache table (skip if URL already cached today)
    │       → post embed to Discord #datacharizard-news (webhook)
    │       → send HTML email as backup
    │
    ├── tasks/job_tracker.py
    │       scrape Seek.com.au (keywords × pages)
    │       scrape Indeed AU
    │       scrape LinkedIn AU (or Apify if token set)
    │       → deduplicate by URL
    │       → Claude extracts skills from each title
    │       → save new jobs to jobs table
    │       → post new job alerts to Discord #jobs-au (webhook)
    │       → send email backup
    │       → mark jobs as alerted
    │
    └── tasks/obsidian_writer.py → rebuild_master_index()
            reads all progress + quiz tables
            → writes DataCharizard Index.md to vault root
```

---

## Weekly review (8am every Sunday)

```
python main.py weekly
    │
    └── tasks/weekly_review.py
            pull 7-day learning stats (xp, lessons, quiz accuracy, days active)
            pull 7-day job stats (new jobs, top skills, top companies, by source)
            fetch Premier League standings + top scorers (football_api.py)
            → Claude writes personalised coaching paragraph
            → post rich embed to Discord #weekly-review (webhook)
            → send HTML email backup
```

---

## Coach session (on demand)

```
python main.py coach
    │
    └── tasks/coach.py
            show XP bar + level
            user picks topic (spark_sql / pyspark / python)
            user picks lesson number (1-8 per topic)
            │
            ├── fetch Premier League data (football_api.py)
            │       used as dataset in all code examples
            │
            ├── Claude teaches lesson (COACH_SYSTEM prompt)
            │       → print to terminal
            │       → save Obsidian note (obsidian_writer.py)
            │       → award XP (db.add_progress)
            │
            ├── optional: quiz (3 questions)
            │       Claude generates JSON quiz question
            │       user answers A/B/C/D
            │       → score, award XP, save to quiz_results table
            │       → streak bonus at 3+ correct in a row
            │
            └── optional: real-world problem
                    Claude generates scenario using PL data
                    user types hint / solution / done
```

---

## Discord bot (long-running process)

```
python main.py bot
    │
    └── utils/discord_bot.py → run_bot()
            starts discord.py Bot
            syncs slash commands to guild
            listens for:
            │
            ├── /quiz [topic]
            │       Claude generates quiz question as JSON
            │       → sends embed with A/B/C/D buttons (QuizView)
            │       → on button click: grade, save to DB, show result
            │
            ├── /lesson [topic] [number]
            │       fetches PL data via football_api.py
            │       Claude teaches lesson
            │       → sends embed (≤1800 chars for Discord limit)
            │       → saves Obsidian note, awards XP in background
            │
            ├── /jobs
            │       queries jobs table (last 8, sorted by scraped_on)
            │       → sends embed with apply links
            │
            └── /stats
                    queries progress + quiz tables
                    → sends XP bar, level, lesson count, accuracy
```

---

## Cron schedule

```bash
# Edit with: crontab -e

# Daily 7am — news digest + job scraper
0 7 * * * cd /full/path/to/datacharizard && python main.py >> logs/daily.log 2>&1

# Sunday 8am — weekly review
0 8 * * 0 cd /full/path/to/datacharizard && python main.py weekly >> logs/weekly.log 2>&1

# Discord bot — keep alive (run separately, or use a process manager)
# Recommended: use PM2, systemd, or Railway for persistent bot process
```

---

## Data flow (SQLite tables)

```
news_cache      ← news_digest.py writes, never deletes
jobs            ← job_tracker.py writes, alerted flag updated after Discord post
user_progress   ← coach.py writes after each lesson (topic, lesson_num, xp)
quiz_results    ← coach.py + discord_bot.py write after each quiz question
```

---

## Error handling protocol

| Error | Action |
|---|---|
| RSS feed unreachable | skip that feed, continue with others |
| Claude API error | retry once after 5s, skip item if still fails, log |
| Discord webhook 4xx | log, fall back to email |
| Discord webhook 429 | wait 2s, retry once |
| Football API 429 | wait 12s, retry once, use fallback data if still fails |
| LinkedIn 403/429 | skip LinkedIn entirely, run Seek + Indeed only |
| Obsidian path missing | `os.makedirs`, then write file |
| SQLite locked | retry after 1s, max 3 retries |

All errors write to `logs/daily.log` or `logs/weekly.log`.
Serious errors (full task failure) also post to Discord via webhook if available.

---

## Adding a new topic to the curriculum

1. Add topic key + lesson list to `CURRICULUM` dict in `tasks/coach.py`
2. Add topic to the `pick_topic()` menu in `tasks/coach.py`
3. Update the `/lesson` slash command description in `utils/discord_bot.py`
4. Create reference doc at `docs/agent/<topic>.md` if it needs special handling
5. Update this workflow doc

---

## Extending the job scraper

1. Add new scraper function in `tasks/job_tracker.py` (follow `scrape_seek` pattern)
2. Call it inside `run()` and extend `all_jobs`
3. Add source name to `JOB_SOURCES` in `config.py`
4. Update `docs/agent/jobs.md` with the new source's quirks

---

## Monthly cost check

Run this to see Claude API usage this month:

```bash
# Check API usage at: console.anthropic.com/settings/usage
# Typical breakdown:
#   news: ~8 articles/day × 30 = 240 summaries × ~200 tokens = ~48k tokens/month
#   jobs: ~20 skill extractions/day × 30 = 600 × ~100 tokens = ~60k tokens/month
#   coach: ~2 lessons/day × 30 = 60 × ~500 tokens = ~30k tokens/month
#   quiz: ~6 questions/day × 30 = 180 × ~200 tokens = ~36k tokens/month
#   weekly: 4 × ~500 tokens = 2k tokens/month
# Total: ~176k input + output tokens/month ≈ $5-12/month on Sonnet
```
