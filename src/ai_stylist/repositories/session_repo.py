import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.models.session import ChatSession


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, title: str | None = None) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get(self, session_id: uuid.UUID) -> ChatSession | None:
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_title(self, session_id: uuid.UUID, title: str) -> None:
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(title=title, updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def touch(self, session_id: uuid.UUID) -> None:
        await self.db.execute(
            update(ChatSession).where(ChatSession.id == session_id).values(updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def delete(self, session_id: uuid.UUID) -> bool:
        session = await self.get(session_id)
        if not session:
            return False
        await self.db.delete(session)
        await self.db.commit()
        return True
