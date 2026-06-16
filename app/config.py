"""
Configuration — all values come from environment variables (Railway → Variables).
Replaces the old config/config.php.
"""
import os


def _ids(raw: str) -> list[int]:
    out = []
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if part:
            try:
                out.append(int(part))
            except ValueError:
                pass
    return out


def _channels(raw: str) -> list[dict]:
    """REQUIRED_CHANNELS="@startupper_uz,@startupper_elon" -> [{'id','username'}]"""
    out = []
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if not part.startswith("@"):
            part = "@" + part
        out.append({"id": part, "username": part})
    return out


# --- Telegram ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "startupperuzbot").strip().lstrip("@")
REQUIRED_CHANNELS = _channels(os.environ.get("REQUIRED_CHANNELS", ""))
POSTING_CHANNEL = os.environ.get("POSTING_CHANNEL", "").strip()
ADMIN_IDS = _ids(os.environ.get("ADMIN_IDS", ""))
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "").strip()

# --- Registration / application flow (/apply) ---
# Channel the user must join before applying.
APPLY_CHANNEL = os.environ.get("APPLY_CHANNEL", "").strip()
if APPLY_CHANNEL and not APPLY_CHANNEL.startswith("@"):
    APPLY_CHANNEL = "@" + APPLY_CHANNEL
# Chat that receives the formatted application report.
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID", "").strip()
# Single admin allowed to run /export.
_admin_id_raw = os.environ.get("ADMIN_ID", "").strip()
if _admin_id_raw.lstrip("-").isdigit():
    ADMIN_ID = int(_admin_id_raw)
elif ADMIN_IDS:
    ADMIN_ID = ADMIN_IDS[0]
else:
    ADMIN_ID = None

# --- Database ---
# Railway exposes DATABASE_URL for its Postgres plugin.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# --- Webhook ---
# Base public URL of this service, e.g. https://your-app.up.railway.app
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip().rstrip("/")
# Optional shared secret; if set, Telegram must echo it back in a header.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()
# Path the webhook is served on. Secret-in-path keeps the endpoint unguessable.
WEBHOOK_PATH = "/webhook/" + (WEBHOOK_SECRET or "telegram")


def normalized_dsn() -> str:
    """asyncpg wants postgresql://, Railway sometimes gives postgres://."""
    dsn = DATABASE_URL
    if dsn.startswith("postgres://"):
        dsn = "postgresql://" + dsn[len("postgres://"):]
    return dsn
