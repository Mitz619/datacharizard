# Coaching System Reference
> Load when working on coach.py, quiz logic, XP system, or Obsidian notes.

---

## Curriculum structure

24 lessons total across 3 topics. 8 lessons each.

| Topic key | Display name | Football data used |
|---|---|---|
| `spark_sql` | Spark SQL (Databricks + Snowflake) | `pl_standings`, `pl_scorers` |
| `pyspark` | PySpark for data engineering | `pl_matches`, `pl_standings` |
| `python` | Python + sports analytics | all three tables |

Lessons are ordered by complexity — lesson 1 is always fundamentals, lesson 8 is always production-level.

---

## XP system

| Action | XP |
|---|---|
| Completing a lesson | +10 |
| Correct quiz answer | +5 |
| Streak bonus (3+ correct in a row) | +15 |

Levels (defined in `config.py`):

| XP threshold | Level name |
|---|---|
| 0 | Charmander 🔥 |
| 100 | Charmeleon 🔥🔥 |
| 300 | Charizard 🔥🔥🔥 |
| 600 | DataCharizard ⚡🔥 |

---

## Football data integration

Every lesson fetches real Premier League data via `utils/football_api.py`.

The `get_lesson_dataset()` function returns a markdown string with:
- Top 6 standings table
- Top 5 scorers
- Table names for code examples: `pl_standings`, `pl_scorers`, `pl_matches`

Claude uses this as the dataset in all code examples. A Spark SQL lesson on GROUP BY
will look like: "Find the top 3 teams by goals scored from `pl_standings`" not
"Find the top employees by salary."

If the API is unavailable, fallback data in `_fallback_*()` functions is used.

---

## Quiz question format

Claude generates JSON. The QUIZ_SYSTEM prompt requires:
```json
{
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer": "A",
  "explanation": "..."
}
```

Always strip markdown fences before `json.loads()`.
If JSON fails to parse, skip the question with a warning — don't crash.

---

## Obsidian note format

Every lesson creates a file at:
`{OBSIDIAN_VAULT}/lessons/{topic}_L{num:02d}_{safe_title}.md`

YAML frontmatter: `topic`, `lesson`, `date`, `tags`.
Body: full lesson content from Claude.

Daily index at:
`{OBSIDIAN_VAULT}/daily/{YYYY-MM-DD}.md`

Master index at:
`{OBSIDIAN_VAULT}/DataCharizard Index.md`

`rebuild_master_index()` in `obsidian_writer.py` regenerates the master index
at the end of every daily run. Call it whenever progress data changes.

---

## Discord vs CLI coach behaviour

| Feature | CLI (`python main.py coach`) | Discord (`/lesson`, `/quiz`) |
|---|---|---|
| Full lesson text | Yes, full length | Truncated to 1800 chars (Discord embed limit) |
| Obsidian save | Yes | Yes (background) |
| XP awarded | Yes | Yes |
| Quiz | Interactive 3-question sequence | Single question with buttons |
| Real-world problem | Yes | Not implemented (too long for Discord) |
| Football data | Yes | Yes |

---

## Adding a new lesson topic

1. Add to `CURRICULUM` dict in `tasks/coach.py`:
   ```python
   "dbt": [
       "What is dbt and why it matters",
       "Models, sources, and refs",
       ...
   ]
   ```
2. Add to `pick_topic()` menu with a new number option
3. Add to `/lesson` command description in `utils/discord_bot.py`
4. Optionally add topic-specific football data context in `utils/football_api.py`
