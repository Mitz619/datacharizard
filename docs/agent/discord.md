# Discord Setup Reference
> Load this when working on Discord bot, webhooks, or slash command issues.

---

## Architecture choice

DataCharizard uses TWO Discord mechanisms — understand which is which:

**Webhooks** — for automated posting (no bot process running needed)
- News digest → `DISCORD_WEBHOOK_NEWS`
- Job alerts → `DISCORD_WEBHOOK_JOBS`
- Weekly review → `DISCORD_WEBHOOK_WEEKLY`
- These are just HTTPS POST requests. They work even if the bot is offline.

**Bot** (`python main.py bot`) — for interactive commands
- `/quiz`, `/lesson`, `/jobs`, `/stats` slash commands
- Needs to be a running process (use PM2 or Railway)
- Bot token: `DISCORD_BOT_TOKEN`

---

## Server channel structure

| Channel | Webhook env var | Purpose |
|---|---|---|
| `#datacharizard-news` | `DISCORD_WEBHOOK_NEWS` | Daily digest posts |
| `#jobs-au` | `DISCORD_WEBHOOK_JOBS` | New job alerts |
| `#weekly-review` | `DISCORD_WEBHOOK_WEEKLY` | Sunday summary |
| `#coach` | (bot commands) | `/quiz`, `/lesson` |

---

## Bot invite URL template

Replace `CLIENT_ID` with your application's client ID:
```
https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=2147485696&scope=bot%20applications.commands
```

Permissions needed: Send Messages, Embed Links, Use Slash Commands.

---

## Slash command sync

Commands sync to a specific guild (server) for instant availability.
Global sync takes up to 1 hour.

Current sync: `setup_hook()` in `discord_bot.py` syncs to `DISCORD_GUILD_ID`.

If commands don't appear after bot restart:
1. Check `DISCORD_GUILD_ID` is correct (right-click server → Copy Server ID)
2. Bot must have `applications.commands` scope
3. Re-run `python main.py bot` and wait 30 seconds

---

## Embed colour codes

| Task | Hex | Meaning |
|---|---|---|
| News | `0xe25822` | DataCharizard orange |
| Jobs | `0x5865F2` | LinkedIn blue |
| Weekly | `0xf0a500` | Gold |
| Quiz correct | `0x57F287` | Green |
| Quiz wrong | `0xED4245` | Red |
| Stats | `0xe25822` | Orange |

---

## Rate limits

Discord webhook: 30 requests/minute per webhook URL.
News digest batches all articles into ONE embed — never one post per article.
Job alerts batch all new jobs into ONE embed — never one post per job.

If you see `429` from Discord: the `_post_webhook` function already retries after 2s.

---

## Keeping the bot online

The bot process must stay running for slash commands to work.

**Local development:** `python main.py bot` in a terminal tab
**Production options (cheapest first):**

1. **Railway** — free tier (500 hours/month), add a worker process:
   - Start command: `python main.py bot`
   - Environment: all `.env` vars added in Railway dashboard

2. **PM2 (on a VPS):**
   ```bash
   npm install -g pm2
   pm2 start "python main.py bot" --name datacharizard-bot
   pm2 save
   pm2 startup   # auto-restart on reboot
   ```

3. **systemd (on a VPS):**
   Create `/etc/systemd/system/datacharizard.service` and enable it.

The webhooks (news, jobs, weekly) do NOT need the bot running — cron handles those.
