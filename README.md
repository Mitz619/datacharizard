# 🔥 DataCharizard — Your Personal Data Career AI Agent

A three-in-one AI agent that:
1. **Emails you daily data engineering news** (Claude-curated digest)
2. **Teaches you Spark SQL, PySpark & Python** (gamified, with Obsidian notes)
3. **Tracks data jobs in Australia** (scrapes Seek/Indeed, Streamlit dashboard)

---

## ⚡ Quick start (5 steps)

### Step 1 — Clone and install
```bash
git clone <your-repo>
cd datacharizard
pip install -r requirements.txt
```

### Step 2 — Set up secrets
```bash
cp .env.example .env
# Edit .env with your Claude API key and Gmail app password
```

**Get your Claude API key:** https://console.anthropic.com  
**Gmail app password:** myaccount.google.com → Security → App passwords → Create one called "DataCharizard"

### Step 3 — Set your Obsidian vault path
Edit `config.py` line:
```python
OBSIDIAN_VAULT = os.path.expanduser("~/your/obsidian/vault/DataCharizard")
```

### Step 4 — Check setup
```bash
python main.py setup
```
All ticks = you're good to go!

### Step 5 — Run it!
```bash
# Interactive coach session (start here!)
python main.py coach

# Full daily run (news + jobs email)
python main.py

# Job market dashboard
python main.py dashboard

# Individual tasks
python main.py news
python main.py jobs
```

---

## ⏰ Automate with cron (runs every day at 7am)

```bash
crontab -e
```
Add this line:
```
0 7 * * * cd /full/path/to/datacharizard && python main.py >> logs/cron.log 2>&1
```

---

## 🌐 Deploy free on Railway

1. Push to GitHub
2. Go to railway.app → New Project → GitHub repo
3. Add environment variables from your `.env`
4. Add a cron job: `0 7 * * * python main.py`
5. Deploy the dashboard: `streamlit run dashboard/app.py`

---

## 💰 Monthly cost estimate

| Item | Cost |
|------|------|
| Claude API (Sonnet) | ~$8–15 |
| Railway hosting | $0–5 |
| Gmail | Free |
| Streamlit Cloud | Free |
| **Total** | **~$8–20/month** |

---

## 📁 Project structure

```
datacharizard/
├── main.py              # Entry point
├── config.py            # All settings
├── requirements.txt
├── .env.example
├── tasks/
│   ├── news_digest.py   # Task 1 — daily news email
│   ├── coach.py         # Task 2 — interactive learning coach
│   ├── obsidian_writer.py # Task 2b — Obsidian note generator
│   └── job_tracker.py   # Task 3 — job scraper + alerts
├── utils/
│   ├── db.py            # SQLite helpers
│   ├── claude_client.py # Claude API wrapper
│   └── email_sender.py  # Gmail sender
└── dashboard/
    └── app.py           # Streamlit job dashboard
```
