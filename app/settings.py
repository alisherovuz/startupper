"""
DB-backed settings with an in-process cache (replaces src/Core/Settings.php).
"""
import json

from . import db

_cache: dict = {}


def _cast(value, type_: str):
    if value is None:
        return None
    if type_ == "number":
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    if type_ == "boolean":
        return str(value).strip().lower() in ("1", "true", "yes", "on")
    if type_ == "json":
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return value


async def get(key: str, default=None):
    if key in _cache:
        return _cache[key]

    row = await db.fetch(
        "SELECT setting_value, setting_type FROM settings WHERE setting_key = ?", key
    )
    if not row:
        return default

    value = _cast(row["setting_value"], row["setting_type"])
    _cache[key] = value
    return value


async def set(key: str, value, type_: str = "string"):
    string_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    await db.execute(
        """
        INSERT INTO settings (setting_key, setting_value, setting_type)
        VALUES (?, ?, ?)
        ON CONFLICT (setting_key)
        DO UPDATE SET setting_value = EXCLUDED.setting_value,
                      setting_type  = EXCLUDED.setting_type
        """,
        key,
        string_value,
        type_,
    )
    _cache[key] = value


def clear_cache():
    _cache.clear()
