# StartupperUZ Bot (Python / FastAPI)

Python port of the StartupperUZ Telegram bot, ready for Railway.
FastAPI webhook + httpx + PostgreSQL (asyncpg).

## Layout
```
app/
  main.py         FastAPI app + webhook (startup applies schema, sets webhook)
  config.py       env-based config (no secrets in code)
  db.py           asyncpg pool + ?->$n helper + insert/update/count
  telegram.py     Telegram API wrapper (async)
  settings.py     DB-backed settings (cached)
  lang.py         uz/en translations
  bot_handler.py  all bot logic (registration, wizard, carousel, admin panel)
schema.sql        idempotent Postgres schema (runs on every boot)
```

## Deploy on Railway
1. Push this folder to a GitHub repo and create a Railway project from it.
2. In the project, **+ New → Database → PostgreSQL**. Railway auto-sets `DATABASE_URL`.
3. On the bot service → **Variables**, add everything from `.env.example`
   (`BOT_TOKEN`, `BOT_USERNAME`, `REQUIRED_CHANNELS`, `POSTING_CHANNEL`,
   `ADMIN_IDS`, `WEBHOOK_SECRET`).
4. Service → **Settings → Networking → Generate Domain**. Copy the URL into a
   `WEBHOOK_URL` variable (e.g. `https://your-app.up.railway.app`).
5. Deploy. On boot the app applies the schema, registers the webhook, and sets
   the command list automatically. Visit `/` to health-check.

## Notes
- Add the bot as an **admin** to `POSTING_CHANNEL` so it can post approved requests.
- Your Telegram user id must be in `ADMIN_IDS` to use `/admin`.
- The old PHP web admin panel is **not** ported — all admin actions live in-bot.
