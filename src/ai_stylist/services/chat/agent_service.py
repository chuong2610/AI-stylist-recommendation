"""
AgentService: bridge giữa FastAPI và LangGraph ReAct agent.

Memory flow:
  SHORT-TERM (per session):
    - thread_id = str(session_id)
    - LangGraph checkpointer tự restore/save toàn bộ conversation state
    - pre_model_hook trim xuống MAX_MESSAGES khi cần

  LONG-TERM (per user, cross-session):
    - user_id truyền vào config["configurable"]["user_id"]
    - Tools dùng InjectedStore để đọc/ghi user profile, outfit history
    - Namespace: ("users", user_id, "profile" | "outfit_history" | "summaries")

  Our messages table:
    - Lưu clean history (chỉ user + assistant text) để hiển thị UI
    - Không lưu tool calls/ToolMessages nội bộ của LangGraph
"""
import json
import uuid
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.services.chat.session_service import SessionService
from ai_stylist.services.agent.checkpointer import get_checkpointer
from ai_stylist.services.agent.store import get_store
from ai_stylist.services.agent.graph import create_graph


class AgentService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._session_svc = SessionService(db)

    async def handle(self, session_id: uuid.UUID, user_message: str, user_id: str = "anonymous") -> dict[str, Any]:
        """
        Gửi message tới LangGraph ReAct agent.

        Config truyền vào graph:
          thread_id → checkpointer dùng để restore/save short-term state
          user_id   → tools dùng để namespace long-term store
          db        → tools dùng cho request-scoped app data khi cần

        Returns:
            { "reply": str, "outfit_plan": dict | None, "tool_used": str | None }
        """
        session = await self._session_svc.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        await self._session_svc.save_user_message(session_id, user_message)

        graph = create_graph(get_checkpointer(), get_store())
        config = {
            "configurable": {
                "thread_id": str(session_id),   # SHORT-TERM: session scope
                "user_id": user_id,             # LONG-TERM: user scope
                "db": self._db,                 # per-request DB session
            }
        }

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
        )

        last_msg = result["messages"][-1]
        if isinstance(last_msg.content, str):
            reply_text = last_msg.content
        elif isinstance(last_msg.content, list):
            reply_text = "".join(
                block["text"] if isinstance(block, dict) and "text" in block else str(block)
                for block in last_msg.content
            )
        else:
            reply_text = str(last_msg.content)

        tool_used, outfit_plan = _extract_tool_result(result["messages"])

        await self._session_svc.save_assistant_message(
            session_id=session_id,
            content=reply_text,
            intent=tool_used,
            metadata={"outfit_plan": outfit_plan} if outfit_plan else None,
        )

        if not session.title:
            await self._session_svc._sessions.update_title(session_id, user_message[:60].strip())

        return {
            "reply": reply_text,
            "outfit_plan": outfit_plan,
            "tool_used": tool_used,
        }


def _extract_tool_result(messages: list) -> tuple[str | None, dict | None]:
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", None) or _infer_tool_name(msg.content)
            if tool_name == "recommend_outfit":
                try:
                    return "outfit_recommendation", json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    return "outfit_recommendation", None
            if tool_name == "search_products":
                return "product_search", None
            if tool_name == "get_fashion_knowledge":
                return "fashion_knowledge", None
            if tool_name == "save_user_style_profile":
                return "profile_update", None
            if tool_name in ("get_user_style_profile", "get_outfit_history"):
                return "memory_lookup", None
    return None, None


def _infer_tool_name(content: str) -> str | None:
    if not isinstance(content, str):
        return None
    if "outfits" in content and "summary" in content:
        return "recommend_outfit"
    if "products" in content and "query" in content:
        return "search_products"
    if "resolved_concepts" in content and "style_rules" in content:
        return "get_fashion_knowledge"
    return None
