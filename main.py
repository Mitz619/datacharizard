"""
main.py  —  DataCharizard v2 entry point

Usage:
  python main.py              # run all daily tasks (news + jobs → Discord)
  python main.py coach        # interactive CLI learning session
  python main.py bot          # start Discord bot (interactive commands)
  python main.py news         # news digest only
  python main.py jobs         # job scraper only (Seek + Indeed + LinkedIn)
  python main.py weekly       # weekly review (run on Sundays)
  python main.py dashboard    # launch Streamlit dashboard
  python main.py setup        # first-time setup check

Cron (add via: crontab -e):
  # Daily at 7am — news + jobs
  0 7 * * * cd /path/to/datacharizard && python main.py >> logs/daily.log 2>&1

  # Weekly review every Sunday 8am
  0 8 * * 0 cd /path/to/datacharizard && python main.py weekly >> logs/weekly.log 2>&1
"""
import sys, os


def run_daily():
    from tasks.news_digest import run as news_run
    from tasks.job_tracker import run as jobs_run
    from tasks.obsidian_writer import rebuild_master_index
    print("\n🔥 DataCharizard v2 — daily run starting\n")
    news_run()
    jobs_run()
    rebuild_master_index()
    print("\n✅ Daily run complete! Check Discord for updates.\n")


def run_coach():
    from tasks.coach import run as coach_run
    coach_run()


def run_bot():
    """Start the interactive Discord bot (blocking process)."""
    print("\n🤖 Starting DataCharizard Discord bot...\n")
    from utils.discord_bot import run_bot as _run_bot
    _run_bot()


def run_weekly():
    from tasks.weekly_review import run as weekly_run
    weekly_run()


def run_setup():
    from utils.db import init_db
    from config import (CLAUDE_API_KEY, GMAIL_SENDER, OBSIDIAN_VAULT,
                        DISCORD_BOT_TOKEN, DISCORD_WEBHOOK_NEWS,
                        FOOTBALL_API_KEY)
    print("\n🔥 DataCharizard v2 Setup Check\n")
    init_db()
    checks = [
        ("Claude API key",        bool(CLAUDE_API_KEY),         "Set ANTHROPIC_API_KEY in .env"),
        ("Discord bot token",     bool(DISCORD_BOT_TOKEN),      "Set DISCORD_BOT_TOKEN in .env"),
        ("Discord webhook (news)",bool(DISCORD_WEBHOOK_NEWS),   "Set DISCORD_WEBHOOK_NEWS in .env"),
        ("Football API key",      bool(FOOTBALL_API_KEY),       "Set FOOTBALL_API_KEY in .env (free at football-data.org)"),
        ("Gmail sender",          bool(GMAIL_SENDER),            "Set GMAIL_SENDER in .env (optional, for email backup)"),
        ("Obsidian vault",        os.path.exists(OBSIDIAN_VAULT),f"Create folder: {OBSIDIAN_VAULT}"),
    ]
    all_good = True
    for name, ok, fix in checks:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")
        if not ok:
            print(f"       → {fix}")
            all_good = False
    if all_good:
        print("\n  All systems go! Run: python main.py\n")
    else:
        print("\n  Fix the ❌ items above, then re-run python main.py setup\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daily"
    os.makedirs("logs", exist_ok=True)

    if cmd == "coach":
        run_coach()
    elif cmd == "bot":
        run_bot()
    elif cmd == "news":
        from tasks.news_digest import run; run()
    elif cmd == "jobs":
        from tasks.job_tracker import run; run()
    elif cmd == "weekly":
        run_weekly()
    elif cmd == "dashboard":
        os.system("streamlit run dashboard/app.py")
    elif cmd == "setup":
        run_setup()
    else:
        run_daily()
