"""
Async PostgreSQL layer (replaces src/Core/Database.php).

Keeps the PHP-style `?` placeholders so queries stay readable; they are
translated to Postgres $1,$2,... on the way out. JSON/JSONB columns are
decoded to / encoded from Python objects automatically.
"""
import json
import re
from typing import Any, Optional

import asyncpg

from . import config

_pool: Optional[asyncpg.Pool] = None


def _qmark_to_pg(sql: str) -> str:
    """Replace each ? with $1, $2, ... (we control all SQL, so no literals contain ?)."""
    counter = {"n": 0}

    def repl(_m):
        counter["n"] += 1
        return f"${counter['n']}"

    return re.sub(r"\?", repl, sql)


async def _init_conn(conn: asyncpg.Connection):
    # Encode/decode jsonb <-> python dict/list transparently.
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=config.normalized_dsn(),
            min_size=1,
            max_size=10,
            init=_init_conn,
        )
    return _pool


async def close():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def fetch(sql: str, *params) -> Optional[dict]:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(_qmark_to_pg(sql), *params)
        return dict(row) if row else None


async def fetch_all(sql: str, *params) -> list[dict]:
    async with _pool.acquire() as conn:
        rows = await conn.fetch(_qmark_to_pg(sql), *params)
        return [dict(r) for r in rows]


async def execute(sql: str, *params) -> str:
    async with _pool.acquire() as conn:
        return await conn.execute(_qmark_to_pg(sql), *params)


async def fetch_val(sql: str, *params) -> Any:
    async with _pool.acquire() as conn:
        return await conn.fetchval(_qmark_to_pg(sql), *params)


# --- Convenience helpers mirroring the PHP Database class ---

async def insert(table: str, data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING id"
    return int(await fetch_val(sql, *data.values()))


async def update(table: str, data: dict, where: str, *where_params) -> int:
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
    status = await execute(sql, *data.values(), *where_params)
    # status like "UPDATE 3"
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0


async def delete(table: str, where: str, *params) -> int:
    status = await execute(f"DELETE FROM {table} WHERE {where}", *params)
    try:
        return int(status.split()[-1])
    except (ValueError, IndexError):
        return 0


async def count(table: str, where: str = "1=1", *params) -> int:
    val = await fetch_val(f"SELECT COUNT(*) FROM {table} WHERE {where}", *params)
    return int(val or 0)
