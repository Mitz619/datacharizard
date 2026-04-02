# DataCharizard — Full Implementation Guide
> Complete setup from zero to a running agent. Follow in order.
> Estimated time: 45–60 minutes.

---

## Before you start — what you need

| Thing | Where to get it | Cost |
|---|---|---|
| Python 3.10+ | python.org | Free |
| A Discord account | discord.com | Free |
| A Gmail account | gmail.com | Free |
| Claude API key | console.anthropic.com | Pay-as-you-go (~$10/mo) |
| Football-data.org key | football-data.org/client/register | Free |
| Obsidian | obsidian.md | Free |
| A terminal (Mac/Linux/WSL on Windows) | Built in | Free |

---

## Phase 1 — Get the code running locally (20 min)

### Step 1.1 — Download and extract

Download `datacharizard_v2.zip` and extract it:

```bash
unzip datacharizard_v2.zip
cd datacharizard
```

### Step 1.2 — Create a Python virtual environment

Always use a virtual environment — keeps dependencies isolated:

```bash
python3 -m venv .venv

# Activate it (do this every time you open a terminal for this project):
source .venv/bin/activate        # Mac / Linux
.venv\Scripts\activate           # Windows
```

You should see `(.venv)` in your terminal prompt.

### Step 1.3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs: anthropic, discord.py, feedparser, requests, beautifulsoup4,
streamlit, pandas, python-dotenv, and others. Takes ~2 minutes.

### Step 1.4 — Create your .env file

```bash
cp .env.example .env
```

Now open `.env` in any text editor. You'll fill it in during Phase 2.

---

## Phase 2 — Get your API keys (15 min)

### Step 2.1 — Claude API key

1. Go to **console.anthropic.com**
2. Sign up / log in
3. Click **API Keys** in the left sidebar
4. Click **Create Key** → name it "DataCharizard" → copy it
5. Paste into `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

### Step 2.2 — Football data key (free, 2 minutes)

1. Go to **football-data.org/client/register**
2. Fill in name + email → submit
3. Check your email → copy the API key
4. Paste into `.env`:
   ```
   FOOTBALL_API_KEY=abc123...
   ```

Free tier gives you: Premier League, Championship, Champions League.
Limit: 10 requests/minute — DataCharizard stays well within this.

### Step 2.3 — Gmail app password

This lets DataCharizard send emails without your real password:

1. Go to **myaccount.google.com**
2. Security → **2-Step Verification** (must be ON)
3. Then go to https://myaccount.google.com/apppasswords
4. enter **App name** → type "DataCharizard" → Generate
5. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
6. Paste into `.env`:
   ```
   GMAIL_SENDER=youremail@gmail.com
   GMAIL_RECIPIENT=youremail@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

> Note: If you don't see App Passwords, 2-Step Verification isn't enabled yet.

---

## Phase 3 — Discord setup (15 min)

This is the most steps but each is quick.

### Step 3.1 — Create a Discord server (if you don't have one)

1. Open Discord
2. Click **+** in the left sidebar → **Create My Own** → **For me and my friends**
3. Name it "DataCharizard" → Create
4. **Right-click the server name** → **Copy Server ID**
   (If you don't see this option: User Settings → Advanced → Developer Mode → ON)
5. Paste into `.env`:
   ```
   DISCORD_GUILD_ID=123456789012345678
   ```

### Step 3.2 — Create the three channels

In your server, create these text channels:
- `#datacharizard-news`
- `#jobs-au`
- `#weekly-review`

### Step 3.3 — Create webhooks (one per channel)

For each channel:
1. Click the ⚙️ gear next to the channel name → **Edit Channel**
2. **Integrations** → **Webhooks** → **New Webhook**
3. Name it (e.g. "DataCharizard News") → **Copy Webhook URL**
4. Paste into `.env`

```
DISCORD_WEBHOOK_NEWS=https://discord.com/api/webhooks/111.../abc...
DISCORD_WEBHOOK_JOBS=https://discord.com/api/webhooks/222.../def...
DISCORD_WEBHOOK_WEEKLY=https://discord.com/api/webhooks/333.../ghi...
```

### Step 3.4 — Create the Discord bot

1. Go to **discord.com/developers/applications**
2. **New Application** → name it "DataCharizard" → Create
3. Left sidebar → **Bot**
4. Click **Reset Token** → confirm → **Copy** the token
5. Paste into `.env`:
   ```
   DISCORD_BOT_TOKEN=MTI3...
   ```
6. On the same Bot page, scroll down to **Privileged Gateway Intents**
7. Turn ON: **Message Content Intent** → Save Changes

### Step 3.5 — Invite the bot to your server

1. Left sidebar → **OAuth2** → **URL Generator**
2. Tick **bot** and **applications.commands**
3. Under Bot Permissions, tick: **Send Messages**, **Embed Links**, **Use Slash Commands**
4. Copy the generated URL at the bottom
5. Open it in your browser → select your DataCharizard server → Authorise

The bot should now appear in your server member list (offline until you run it).

---

## Phase 4 — Set up Obsidian (5 min)

### Step 4.1 — Create the vault folder

If you don't have Obsidian yet: download from **obsidian.md**

Create the folder where your notes will live. Pick one of:
```bash
# Option A — inside your existing Obsidian vault
mkdir -p ~/Documents/MyVault/DataCharizard

# Option B — standalone vault
mkdir -p ~/DataCharizardVault/DataCharizard
```

### Step 4.2 — Update config.py

Open `config.py` and update line 21:
```python
# Change this to match where you created the folder:
OBSIDIAN_VAULT = os.path.expanduser("~/Documents/MyVault/DataCharizard")
```

### Step 4.3 — Open in Obsidian

- Open Obsidian → **Open folder as vault** → select the **parent** folder
- (e.g. select `MyVault`, not `MyVault/DataCharizard`)
- The DataCharizard folder will appear in your vault

---

## Phase 5 — Verify setup (2 min)

Run the setup check:

```bash
python main.py setup
```

You should see all green ticks:
```
✅ Claude API key
✅ Discord bot token
✅ Discord webhook (news)
✅ Football API key
✅ Gmail sender
✅ Obsidian vault
```

Fix any ❌ items before continuing.

---

## Phase 6 — First run (try each mode)

### Run the coach first (most fun, no external dependencies needed):

```bash
python main.py coach
```

You'll see an XP bar, pick a topic, pick a lesson — Claude teaches you using
real Premier League data. After the lesson, check your Obsidian vault for the note.

### Test the news digest:

```bash
python main.py news
```

Check your Discord `#datacharizard-news` channel — you should see an embed with
today's data engineering headlines. You'll also get an email.

### Test job scraping:

```bash
python main.py jobs
```

Scrapes Seek + Indeed + LinkedIn, saves to DB, alerts Discord `#jobs-au`.
Check the channel and your dashboard:

```bash
python main.py dashboard
```

Opens at `http://localhost:8501` — you'll see job counts, skill trends, company breakdown.

### Start the interactive Discord bot:

```bash
python main.py bot
```

Go to Discord, type `/quiz` or `/lesson` in any channel where the bot has access.
The bot must be running for slash commands to work.

---

## Phase 7 — Automate with cron

Once everything works manually, automate it.

### On Mac/Linux:

```bash
crontab -e
```

Add these two lines (replace `/full/path/to/datacharizard` with your actual path):

```bash
# Daily at 7am — news digest + job alerts
0 7 * * * cd /full/path/to/datacharizard && /full/path/to/.venv/bin/python main.py >> logs/daily.log 2>&1

# Every Sunday at 8am — weekly review
0 8 * * 0 cd /full/path/to/datacharizard && /full/path/to/.venv/bin/python main.py weekly >> logs/weekly.log 2>&1
```

> Use full paths for both `cd` and `python` — cron doesn't inherit your shell's PATH.
> Find your python path with: `which python` (with venv active)

### On Windows:

Use **Task Scheduler**:
1. Search "Task Scheduler" → Create Basic Task
2. Trigger: Daily, 7:00 AM
3. Action: Start a program → `python.exe` → Arguments: `main.py` → Start in: `C:\path\to\datacharizard`
4. Repeat for Sunday weekly review

---

## Phase 8 — Keep the Discord bot running 24/7

The daily tasks (news + jobs) use webhooks — they work fine in cron without a running bot.

But the slash commands (`/quiz`, `/lesson`) need the bot process running.

### Option A — PM2 (recommended for a local machine or VPS)

```bash
npm install -g pm2

# Start the bot
pm2 start "python main.py bot" --name datacharizard-bot --cwd /path/to/datacharizard

# Auto-restart on reboot
pm2 save
pm2 startup

# Useful commands
pm2 status                    # see if it's running
pm2 logs datacharizard-bot    # view logs
pm2 restart datacharizard-bot # restart after code changes
```

### Option B — Railway (cloud, free tier)

1. Push your project to GitHub (make sure `.env` is in `.gitignore`)
2. Go to **railway.app** → New Project → Deploy from GitHub repo
3. Add all your environment variables in the Railway dashboard (Variables tab)
4. Set the start command to: `python main.py bot`
5. The daily cron can also run on Railway (add a Cron service with schedule `0 7 * * *`)

Railway free tier: 500 hours/month — enough for one always-on service.

---

## Phase 9 — LinkedIn (optional but recommended)

LinkedIn scraping works but can be rate-limited. Two options:

### Option A — Direct scraping (included, no extra setup)

Already built into `utils/linkedin_scraper.py`. Works out of the box.
If blocked, it logs a warning and continues with Seek + Indeed.

### Option B — Apify (more reliable, free 5 runs/month)

1. Sign up at **apify.com**
2. Profile → Settings → Integrations → API → copy your API token
3. Add to `.env`:
   ```
   APIFY_TOKEN=apify_api_...
   ```
4. DataCharizard automatically uses Apify when this token is present.

---

## Your complete .env file (filled in)

```bash
# Claude
ANTHROPIC_API_KEY=sk-ant-api03-...

# Discord
DISCORD_BOT_TOKEN=MTI3NzE...
DISCORD_GUILD_ID=1234567890
DISCORD_WEBHOOK_NEWS=https://discord.com/api/webhooks/111/abc
DISCORD_WEBHOOK_JOBS=https://discord.com/api/webhooks/222/def
DISCORD_WEBHOOK_WEEKLY=https://discord.com/api/webhooks/333/ghi

# Football
FOOTBALL_API_KEY=abc123def456

# Gmail
GMAIL_SENDER=you@gmail.com
GMAIL_RECIPIENT=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Optional
APIFY_TOKEN=apify_api_...
```

---

## Daily habit — how to use DataCharizard

**Morning (automated, you just check Discord):**
- `#datacharizard-news` — 7am news digest waiting for you
- `#jobs-au` — any new job listings from overnight scrape

**When you have 20-30 minutes to learn:**
```bash
python main.py coach
# OR from Discord:
/lesson topic:spark_sql number:3
/quiz topic:pyspark
```

**After a lesson — open Obsidian:**
- Your notes are auto-saved under `lessons/`
- Check `daily/<today>.md` for your session index
- Check `DataCharizard Index.md` for your all-time progress

**Friday/Saturday — prep for Sunday:**
- Check the Streamlit dashboard: `python main.py dashboard`
- See which skills are trending in Australian job listings this week

**Sunday (automated):**
- `#weekly-review` — Claude-written summary of your week lands at 8am

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with venv active |
| Discord commands don't appear | Wait 30s after bot starts; check `DISCORD_GUILD_ID` is correct |
| No news in Discord | Check `DISCORD_WEBHOOK_NEWS` URL; test with `python main.py news` |
| Football API returns fallback data | Check `FOOTBALL_API_KEY` is set and valid |
| Obsidian notes not appearing | Check `OBSIDIAN_VAULT` path in config.py; run `python main.py setup` |
| LinkedIn returns 0 jobs | Expected sometimes; Seek + Indeed will still work |
| Cron not running | Use full paths in crontab; check `logs/daily.log` for errors |
| Gmail auth error | Regenerate app password; make sure 2FA is enabled |

---

## Monthly cost breakdown

| Service | Typical usage | Cost |
|---|---|---|
| Claude API (Sonnet) | ~180k tokens/month | ~$8–15 |
| Railway (optional hosting) | 500h free | $0–5 |
| Gmail | Free | $0 |
| Football-data.org | Free tier | $0 |
| Streamlit Community Cloud | Free | $0 |
| Apify (optional) | 5 free runs/month | $0 |
| **Total** | | **~$8–20/month** |
