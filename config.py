"""
DataCharizard — Central Config
Set your secrets in a .env file (never commit that file to git).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Claude ────────────────────────────────────────────────────────────────────
CLAUDE_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL     = "claude-sonnet-4-20250514"

# ── Discord ───────────────────────────────────────────────────────────────────
# Bot token from discord.com/developers
DISCORD_BOT_TOKEN        = os.getenv("DISCORD_BOT_TOKEN", "")
# Webhook URLs — create one per channel in Server Settings → Integrations
DISCORD_WEBHOOK_NEWS     = os.getenv("DISCORD_WEBHOOK_NEWS", "")   # #news channel
DISCORD_WEBHOOK_JOBS     = os.getenv("DISCORD_WEBHOOK_JOBS", "")   # #jobs channel
DISCORD_WEBHOOK_WEEKLY   = os.getenv("DISCORD_WEBHOOK_WEEKLY", "") # #weekly-review
DISCORD_GUILD_ID         = int(os.getenv("DISCORD_GUILD_ID", "0")) # your server ID

# ── Email (weekly review fallback) ────────────────────────────────────────────
GMAIL_SENDER     = os.getenv("GMAIL_SENDER", "")
GMAIL_RECIPIENT  = os.getenv("GMAIL_RECIPIENT", "")

# ── Paths ─────────────────────────────────────────────────────────────────────
DB_PATH          = "datacharizard.db"
OBSIDIAN_VAULT   = os.path.expanduser("/Users/mithunkarthickmuthu/Documents/Obsidian/Mithun\'s_Notes/DataCharizard")

# ── News RSS feeds ────────────────────────────────────────────────────────────
NEWS_FEEDS = [
    "https://feeds.feedburner.com/oreilly/radar",
    "https://towardsdatascience.com/feed",
    "https://www.dataengineeringweekly.com/feed",
    "https://feeds.feedburner.com/kdnuggets-data-mining-analytics",
    "https://databricks.com/feed",
    "https://medium.com/feed/tag/data-engineering",
]

# ── Gamification ──────────────────────────────────────────────────────────────
XP_PER_LESSON   = 10
XP_PER_CORRECT  = 5
XP_PER_STREAK   = 15
LEVELS = {
    0:   "Charmander 🔥",
    100: "Charmeleon 🔥🔥",
    300: "Charizard 🔥🔥🔥",
    600: "DataCharizard ⚡🔥",
}

# ── Football data (football-data.org — free tier) ─────────────────────────────
# Get free key at: https://www.football-data.org/client/register
FOOTBALL_API_KEY     = os.getenv("FOOTBALL_API_KEY", "")
FOOTBALL_LEAGUES     = {
    "PL":  "Premier League",
    "ELC": "Championship",
}
FOOTBALL_SEASON      = 2024   # current season year

# ── Job scraping ──────────────────────────────────────────────────────────────
JOB_KEYWORDS  = ["data engineer", "data analyst", "analytics engineer",
                  "databricks", "snowflake", "spark", "dbt"]
JOB_LOCATION  = "Australia"
JOB_SOURCES   = ["seek", "indeed", "linkedin"]

# LinkedIn search config
LINKEDIN_GEO_ID   = "101452733"   # Australia geo ID
LINKEDIN_JOB_TYPE = "F"           # F=full-time, P=part-time, C=contract
