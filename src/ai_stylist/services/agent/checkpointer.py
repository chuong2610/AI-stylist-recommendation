"""
PostgreSQL checkpointer cho LangGraph.
Dùng psycopg3 (psycopg) riêng với SQLAlchemy asyncpg vì langgraph-checkpoint-postgres
yêu cầu psycopg3 connection pool.
"""
import logging
from contextlib import asynccontextmanager

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ai_stylist.config import settings

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None


def _build_psycopg_dsn() -> str:
    """Build psycopg3-compatible DSN (không có driver prefix)."""
    return (
        f"host={settings.postgres_host} "
        f"port={settings.postgres_port} "
        f"dbname={settings.postgres_db} "
        f"user={settings.postgres_user} "
        f"password={settings.postgres_password}"
    )


async def setup_checkpointer() -> AsyncPostgresSaver:
    global _pool, _checkpointer

    dsn = _build_psycopg_dsn()
    _pool = AsyncConnectionPool(conninfo=dsn, max_size=10, open=False, kwargs={"autocommit": True})
    await _pool.open()

    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()  # tạo langgraph checkpoint tables nếu chưa có
    logger.info("LangGraph PostgreSQL checkpointer ready.")
    return _checkpointer


async def close_checkpointer() -> None:
    global _pool, _checkpointer
    if _pool:
        await _pool.close()
        _pool = None
        _checkpointer = None
        logger.info("LangGraph checkpointer closed.")


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Call setup_checkpointer() first.")
    return _checkpointer
