"""
FastAPI entrypoint (replaces webhook/index.php).

On startup: connect to Postgres, apply schema, register the webhook with Telegram
and set the bot command list. The webhook endpoint returns 200 immediately and
processes the update in the background so Telegram never times out / retries.
"""
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request

from . import config, db
from .bot_handler import BotHandler
from .telegram import Telegram

telegram: Telegram | None = None

DEFAULT_COMMANDS = [
    {"command": "start", "description": "Asosiy menyu / Main menu"},
    {"command": "find", "description": "E'lonlarni ko'rish / Browse"},
    {"command": "post", "description": "E'lon joylash / Post a request"},
    {"command": "my_requests", "description": "E'lonlarim / My requests"},
    {"command": "resources", "description": "Resurslar / Resources"},
    {"command": "profile", "description": "Profilim / My profile"},
    {"command": "language", "description": "Til / Language"},
    {"command": "help", "description": "Yordam / Help"},
]


async def apply_schema():
    schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
    if schema_path.exists():
        sql = schema_path.read_text(encoding="utf-8")
        await db.execute(sql)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    await db.init()
    await apply_schema()

    telegram = Telegram(config.BOT_TOKEN)

    # Register webhook + commands (best-effort; don't crash the app if Telegram is flaky)
    if config.WEBHOOK_URL:
        try:
            await telegram.set_webhook(config.WEBHOOK_URL + config.WEBHOOK_PATH)
            print(f"Webhook set: {config.WEBHOOK_URL + config.WEBHOOK_PATH}")
        except Exception as e:  # noqa: BLE001
            print(f"setWebhook failed: {e}")
    try:
        await telegram.set_my_commands(DEFAULT_COMMANDS)
    except Exception as e:  # noqa: BLE001
        print(f"setMyCommands failed: {e}")

    yield

    if telegram:
        await telegram.close()
    await db.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health():
    return {"ok": True, "service": "startupper-bot"}


async def _process(update: dict):
    handler = BotHandler(telegram)
    await handler.handle(update)


@app.post(config.WEBHOOK_PATH)
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    # Validate the shared secret if one is configured.
    if config.WEBHOOK_SECRET and x_telegram_bot_api_secret_token != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")

    update = await request.json()
    if update:
        asyncio.create_task(_process(update))
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
