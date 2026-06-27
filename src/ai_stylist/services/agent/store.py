"""
Long-term memory store cho LangGraph.

Short-term memory  → AsyncPostgresSaver (checkpointer.py)
  - Scope: 1 conversation thread (thread_id)
  - Lưu: toàn bộ message history + tool calls trong session
  - Tự động restore khi user tiếp tục session

Long-term memory   → AsyncPostgresStore (store.py — file này)
  - Scope: cross-thread, theo user_id
  - Lưu: user profile, style preferences, outfit history, conversation summaries
  - Tồn tại vĩnh viễn (hoặc theo TTL), không bị xóa khi session kết thúc

Namespace pattern:
  ("users", user_id, "profile")         → style profile, body type, budget
  ("users", user_id, "outfit_history")  → past outfit recommendations
  ("users", user_id, "summaries")       → conversation summaries
"""
import logging
from contextlib import AbstractAsyncContextManager

from langgraph.store.postgres import AsyncPostgresStore
from langgraph.store.memory import InMemoryStore

from ai_stylist.config import settings

logger = logging.getLogger(__name__)

_store: AsyncPostgresStore | InMemoryStore | None = None
_store_cm: AbstractAsyncContextManager | None = None


def _build_store_dsn() -> str:
    return (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


async def setup_store() -> AsyncPostgresStore | InMemoryStore:
    global _store, _store_cm
    try:
        conn_string = _build_store_dsn()
        _store_cm = AsyncPostgresStore.from_conn_string(
            conn_string, pool_config={"min_size": 1, "max_size": 10}
        )
        _store = await _store_cm.__aenter__()
        await _store.setup()
        logger.info("LangGraph AsyncPostgresStore ready.")
    except Exception as e:
        logger.warning("AsyncPostgresStore unavailable (%s), falling back to InMemoryStore.", e)
        _store = InMemoryStore()
        _store_cm = None
    return _store


async def close_store() -> None:
    global _store, _store_cm
    if _store_cm is not None:
        try:
            await _store_cm.__aexit__(None, None, None)
        except Exception:
            pass
    _store = None
    _store_cm = None
    logger.info("LangGraph store closed.")


def get_store() -> AsyncPostgresStore | InMemoryStore:
    if _store is None:
        raise RuntimeError("Store not initialized. Call setup_store() first.")
    return _store
