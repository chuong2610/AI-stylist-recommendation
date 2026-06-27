import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.models.session import ChatSession
from ai_stylist.models.message import Message
from ai_stylist.repositories.session_repo import SessionRepository
from ai_stylist.repositories.message_repo import MessageRepository


class SessionService:
    def __init__(self, db: AsyncSession):
        self._sessions = SessionRepository(db)
        self._messages = MessageRepository(db)

    async def create_session(self, user_id: str, title: str | None = None) -> ChatSession:
        return await self._sessions.create(user_id=user_id, title=title)

    async def get_session(self, session_id: uuid.UUID) -> ChatSession | None:
        return await self._sessions.get(session_id)

    async def list_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> list[ChatSession]:
        return await self._sessions.list_by_user(user_id, limit=limit, offset=offset)

    async def delete_session(self, session_id: uuid.UUID) -> bool:
        return await self._sessions.delete(session_id)

    async def get_history(self, session_id: uuid.UUID, n: int = 20) -> list[Message]:
        return await self._messages.get_recent(session_id, n=n)

    async def list_messages(self, session_id: uuid.UUID) -> list[Message]:
        return await self._messages.list_by_session(session_id)

    async def save_user_message(self, session_id: uuid.UUID, content: str) -> Message:
        return await self._messages.create(session_id=session_id, role="user", content=content)

    async def save_assistant_message(
        self,
        session_id: uuid.UUID,
        content: str,
        intent: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        msg = await self._messages.create(
            session_id=session_id,
            role="assistant",
            content=content,
            intent=intent,
            metadata=metadata,
        )
        await self._sessions.touch(session_id)
        return msg
