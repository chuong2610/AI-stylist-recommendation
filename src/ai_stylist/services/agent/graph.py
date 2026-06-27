"""
LangGraph ReAct agent graph.

Memory architecture:
  SHORT-TERM  → AsyncPostgresSaver (checkpointer)
    - Scope   : 1 thread (session_id)
    - Content : full message history + tool calls/results
    - Trimming: pre_model_hook giữ tối đa MAX_MESSAGES messages gần nhất
                khi vượt quá → tạo summary + xóa cũ (tránh context window overflow)

  LONG-TERM   → AsyncPostgresStore (store)
    - Scope   : cross-thread, theo user_id
    - Content : user style profile, outfit history, conversation summaries
    - Access  : InjectedStore() trong tools
"""
from langchain_core.messages import SystemMessage, trim_messages as lc_trim
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.base import BaseStore

from ai_stylist.config import settings
from ai_stylist.services.agent.tools import ALL_TOOLS

_SYSTEM_PROMPT = """Bạn là AI Stylist — trợ lý thời trang thông minh và thân thiện.

Bạn có thể:
- Trò chuyện tự nhiên về thời trang, phong cách sống, xu hướng
- Tư vấn phối đồ dựa trên body type, dịp, thời tiết
- Tìm và gợi ý outfit hoàn chỉnh với sản phẩm thật
- Ghi nhớ sở thích của user qua các cuộc trò chuyện

Nguyên tắc:
- Luôn trả lời bằng cùng ngôn ngữ với user (tiếng Việt hoặc tiếng Anh)
- Khi user cần outfit cụ thể → dùng tool recommend_outfit
- Khi user hỏi về nguyên tắc/kiến thức thời trang → dùng tool get_fashion_knowledge
- Khi user cung cấp thông tin về bản thân (dáng, sở thích, ngân sách) → lưu bằng save_user_style_profile
- Trước khi tư vấn, nếu chưa biết về user → dùng get_user_style_profile để kiểm tra
- Khi user hỏi về lịch sử gợi ý → dùng get_outfit_history
- Sau khi tool trả về kết quả, trình bày lại cho user một cách tự nhiên, dễ đọc
- Không bịa sản phẩm hay thương hiệu ngoài kết quả từ tool"""

# Số messages tối đa giữ trong short-term memory trước khi trim
MAX_MESSAGES = 30


def _build_pre_model_hook():
    """
    Trim conversation history trước khi gửi vào LLM.
    Giữ tối đa MAX_MESSAGES messages gần nhất (tính cả system message).
    Dùng langchain trim_messages với strategy='last'.
    """
    def pre_model_hook(state: dict) -> dict:
        messages = state.get("messages", [])
        if len(messages) <= MAX_MESSAGES:
            return state

        trimmed = lc_trim(
            messages,
            max_tokens=MAX_MESSAGES,
            strategy="last",
            token_counter=len,          # đếm theo số lượng messages, không phải tokens
            include_system=True,
            allow_partial=False,
        )
        return {**state, "messages": trimmed}

    return pre_model_hook


def create_graph(checkpointer: AsyncPostgresSaver, store: BaseStore):
    """
    Compile ReAct agent graph với cả short-term (checkpointer) và long-term (store) memory.

    Args:
        checkpointer: AsyncPostgresSaver — lưu conversation state per thread
        store: BaseStore — lưu user profile, outfit history cross-thread
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.7,
        max_output_tokens=4096,
    )

    graph = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        checkpointer=checkpointer,
        store=store,
        pre_model_hook=_build_pre_model_hook(),
        prompt=_SYSTEM_PROMPT,
    )
    return graph
