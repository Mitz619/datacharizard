"""
utils/discord_bot.py  —  DataCharizard Discord integration

TWO modes:
  A) Webhooks — for automated posting (news, jobs, weekly review).
     No bot process needed. Just POST to a webhook URL.
     
  B) Bot with slash commands — for interactive coaching.
     Run as a long-lived process: python main.py bot

Slash commands:
  /quiz  topic:spark_sql          → sends a quiz question with buttons
  /lesson topic:pyspark number:3  → sends lesson content
  /jobs                           → shows latest 5 Australian jobs
  /stats                          → shows your XP + level
  /xp                             → quick XP card

Discord setup:
  1. discord.com/developers → New Application → Bot → copy token
  2. Enable "Message Content Intent" in Bot settings
  3. Invite bot: OAuth2 → URL Generator → bot + applications.commands
  4. Create text channels: #datacharizard-news, #jobs-au, #weekly-review
  5. Each channel → Edit → Integrations → Webhooks → New Webhook → copy URL
"""
import asyncio, json, textwrap
import requests as req_sync
import discord
from discord.ext import commands
from discord import app_commands

from config import (DISCORD_BOT_TOKEN, DISCORD_WEBHOOK_NEWS,
                    DISCORD_WEBHOOK_JOBS, DISCORD_WEBHOOK_WEEKLY,
                    DISCORD_GUILD_ID)
from utils.db import get_total_xp, get_level, init_db


# ── Webhook helpers (no bot process needed) ───────────────────────────────────

def _post_webhook(url: str, payload: dict) -> bool:
    """POST a message to a Discord webhook."""
    if not url:
        print("  ⚠️  Discord webhook URL not set in .env")
        return False
    try:
        r = req_sync.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  ❌ Discord webhook error: {e}")
        return False


def post_news_digest(news_items: list[dict]):
    """Post today's news digest to #datacharizard-news."""
    if not news_items:
        return
    description = ""
    for item in news_items[:8]:
        description += f"**[{item['title'][:80]}]({item['url']})**\n"
        description += f"*{item['source']}* — {item['summary'][:120]}...\n\n"

    payload = {
        "username": "DataCharizard 🔥",
        "avatar_url": "https://i.imgur.com/wSTFkRM.png",
        "embeds": [{
            "title": "📰 Daily Data Engineering Digest",
            "description": description,
            "color": 0xe25822,
            "footer": {"text": "DataCharizard — stay current, stay ahead 🔥"}
        }]
    }
    ok = _post_webhook(DISCORD_WEBHOOK_NEWS, payload)
    print(f"  Discord news posted: {ok}")


def post_job_alerts(jobs: list[dict]):
    """Post new job listings to #jobs-au."""
    if not jobs:
        return
    description = ""
    for j in jobs[:10]:
        skills = json.loads(j.get("skills", "[]"))
        skill_tags = " · ".join(f"`{s}`" for s in skills[:4])
        description += (f"**[{j['title']}]({j['url']})**\n"
                        f"🏢 {j['company']} — 📍 {j['location']} — "
                        f"🔗 {j['source'].upper()}\n"
                        f"{skill_tags}\n\n")

    payload = {
        "username": "DataCharizard 🔥",
        "embeds": [{
            "title": f"🧑‍💻 {len(jobs)} new data jobs in Australia",
            "description": description,
            "color": 0x5865F2,
            "footer": {"text": "DataCharizard jobs tracker"}
        }]
    }
    ok = _post_webhook(DISCORD_WEBHOOK_JOBS, payload)
    print(f"  Discord jobs posted: {ok}")


def post_weekly_review(review: dict):
    """Post weekly summary to #weekly-review."""
    payload = {
        "username": "DataCharizard 🔥",
        "embeds": [{
            "title": "📊 Weekly Review — DataCharizard",
            "color": 0xf0a500,
            "fields": [
                {"name": "🔥 Level",        "value": review["level"],        "inline": True},
                {"name": "⭐ Total XP",      "value": str(review["xp"]),      "inline": True},
                {"name": "📚 Lessons done",  "value": str(review["lessons"]), "inline": True},
                {"name": "🎯 Quiz accuracy", "value": review["accuracy"],     "inline": True},
                {"name": "💼 New jobs",      "value": str(review["new_jobs"]),"inline": True},
                {"name": "🔧 Top skill",     "value": review["top_skill"],    "inline": True},
                {"name": "💡 AI insight",    "value": review["ai_insight"],   "inline": False},
            ],
            "footer": {"text": "See you next week! Keep the streak going 🔥"}
        }]
    }
    ok = _post_webhook(DISCORD_WEBHOOK_WEEKLY, payload)
    print(f"  Discord weekly review posted: {ok}")


# ── Interactive Bot ────────────────────────────────────────────────────────────

class DataCharizardBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=DISCORD_GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"  ✅ Bot slash commands synced to guild {DISCORD_GUILD_ID}")

    async def on_ready(self):
        print(f"  🤖 DataCharizard bot online as {self.user}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="data pipelines fire up 🔥"
            )
        )


bot = DataCharizardBot()
tree = bot.tree


# ── /stats command ────────────────────────────────────────────────────────────

@tree.command(name="stats", description="Show your DataCharizard XP and level")
async def stats_command(interaction: discord.Interaction):
    xp    = get_total_xp()
    level = get_level(xp)
    from utils.db import get_conn
    with get_conn() as conn:
        lessons = conn.execute(
            "SELECT COUNT(*) FROM user_progress WHERE completed=1"
        ).fetchone()[0]
        quizzes = conn.execute("SELECT COUNT(*) FROM quiz_results").fetchone()[0]
        accuracy = conn.execute(
            "SELECT ROUND(AVG(correct)*100,0) FROM quiz_results"
        ).fetchone()[0] or 0

    thresholds = [0, 100, 300, 600]
    next_t = next((t for t in thresholds if t > xp), 600)
    prev_t = max((t for t in thresholds if t <= xp), default=0)
    pct = min(int((xp - prev_t) / max(next_t - prev_t, 1) * 10), 10)
    bar = "🟧" * pct + "⬜" * (10 - pct)

    embed = discord.Embed(title="🔥 DataCharizard Stats", color=0xe25822)
    embed.add_field(name="Level",     value=level,         inline=True)
    embed.add_field(name="Total XP",  value=str(xp),       inline=True)
    embed.add_field(name="Progress",  value=bar,           inline=False)
    embed.add_field(name="Lessons",   value=str(lessons),  inline=True)
    embed.add_field(name="Quizzes",   value=str(quizzes),  inline=True)
    embed.add_field(name="Accuracy",  value=f"{accuracy}%",inline=True)
    await interaction.response.send_message(embed=embed)


# ── /quiz command with buttons ────────────────────────────────────────────────

class QuizView(discord.ui.View):
    def __init__(self, question_data: dict, topic: str):
        super().__init__(timeout=120)
        self.q  = question_data
        self.topic = topic
        self.answered = False
        for letter in ["A", "B", "C", "D"]:
            btn = discord.ui.Button(
                label=f"{letter}. {question_data['options'][letter][:40]}",
                custom_id=letter,
                style=discord.ButtonStyle.secondary,
                row=0 if letter in "AB" else 1
            )
            btn.callback = self._make_callback(letter)
            self.add_item(btn)

    def _make_callback(self, letter: str):
        async def callback(interaction: discord.Interaction):
            if self.answered:
                await interaction.response.send_message(
                    "Already answered!", ephemeral=True)
                return
            self.answered = True
            correct = (letter == self.q["answer"])
            xp = 5 if correct else 0
            from utils.db import add_quiz_result
            add_quiz_result(self.topic, self.q["question"], correct, xp)
            emoji = "✅" if correct else "❌"
            color = 0x57F287 if correct else 0xED4245
            embed = discord.Embed(
                title=f"{emoji} {'Correct!' if correct else 'Not quite!'}",
                description=f"**Correct answer:** {self.q['answer']}. "
                            f"{self.q['options'][self.q['answer']]}\n\n"
                            f"💡 {self.q['explanation']}\n\n"
                            f"{'🔥 +5 XP earned!' if correct else '📖 Study this and try again!'}",
                color=color
            )
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(embed=embed)
        return callback


@tree.command(name="quiz", description="Get a quiz question on a data topic")
@app_commands.describe(topic="spark_sql | pyspark | python")
async def quiz_command(interaction: discord.Interaction, topic: str = "spark_sql"):
    await interaction.response.defer()
    import re
    from utils.claude_client import ask

    QUIZ_SYSTEM = """Generate ONE multiple-choice question for a data engineering quiz.
Return ONLY valid JSON (no markdown):
{"question":"...","options":{"A":"...","B":"...","C":"...","D":"..."},"answer":"A","explanation":"..."}"""

    raw = ask(QUIZ_SYSTEM, f"Topic: {topic} (use a Premier League stats example if possible)")
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        q = json.loads(raw)
    except Exception:
        await interaction.followup.send("⚠️ Couldn't generate a question right now, try again!")
        return

    embed = discord.Embed(
        title=f"🎯 {topic.upper()} Quiz",
        description=f"**{q['question']}**",
        color=0x5865F2
    )
    view = QuizView(q, topic)
    await interaction.followup.send(embed=embed, view=view)


# ── /lesson command ───────────────────────────────────────────────────────────

@tree.command(name="lesson", description="Get a lesson on a data topic")
@app_commands.describe(
    topic="spark_sql | pyspark | python",
    number="Lesson number 1-8"
)
async def lesson_command(interaction: discord.Interaction,
                          topic: str = "spark_sql", number: int = 1):
    await interaction.response.defer()
    from tasks.coach import CURRICULUM, COACH_SYSTEM
    from utils.football_api import get_lesson_dataset
    from utils.claude_client import ask
    from tasks.obsidian_writer import save_note

    lessons = CURRICULUM.get(topic, CURRICULUM["spark_sql"])
    idx = max(0, min(number - 1, len(lessons) - 1))
    title = lessons[idx]

    football_ctx = get_lesson_dataset(topic)
    content = ask(COACH_SYSTEM,
                  f"Teach lesson: '{title}'\n\nUse this REAL data in your examples:\n{football_ctx}")

    # Discord has 4096 char embed limit
    short = content[:1800] + ("..." if len(content) > 1800 else "")
    embed = discord.Embed(
        title=f"📚 Lesson {number}: {title}",
        description=short,
        color=0x57F287
    )
    embed.set_footer(text="💡 Notes auto-saved to Obsidian · Use /quiz to test yourself")
    await interaction.followup.send(embed=embed)

    # Save to Obsidian and DB in background
    save_note(topic, number, title, content)
    from utils.db import add_progress
    from config import XP_PER_LESSON
    add_progress(topic, number, XP_PER_LESSON)


# ── /jobs command ─────────────────────────────────────────────────────────────

@tree.command(name="jobs", description="Show latest Australian data engineering jobs")
async def jobs_command(interaction: discord.Interaction):
    from utils.db import get_conn
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT title, company, location, url, source FROM jobs "
            "ORDER BY scraped_on DESC LIMIT 8"
        ).fetchall()
    if not rows:
        await interaction.response.send_message(
            "No jobs scraped yet. Run the daily task first!", ephemeral=True)
        return
    embed = discord.Embed(title="🧑‍💻 Latest data jobs in Australia", color=0x0A66C2)
    for r in rows:
        embed.add_field(
            name=f"{r['title'][:45]} — {r['company']}",
            value=f"📍 {r['location']} · {r['source'].upper()} · [Apply]({r['url']})",
            inline=False
        )
    await interaction.response.send_message(embed=embed)


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_bot():
    """Start the Discord bot (blocking). Call from main.py bot command."""
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not set in .env")
        return
    init_db()
    bot.run(DISCORD_BOT_TOKEN)
