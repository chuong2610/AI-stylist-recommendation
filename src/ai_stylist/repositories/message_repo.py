import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        intent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        msg = Message(session_id=session_id, role=role, content=content, intent=intent, metadata_=metadata)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_by_session(self, session_id: uuid.UUID, limit: int = 100) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, session_id: uuid.UUID, n: int = 20) -> list[Message]:
        """Return last n messages ordered oldest-first (for LLM context)."""
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(n)
        )
        msgs = list(result.scalars().all())
        return list(reversed(msgs))
