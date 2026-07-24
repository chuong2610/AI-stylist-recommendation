from fastapi import APIRouter
from ai_stylist.api.v1.chat import router as chat_router
from ai_stylist.api.v1.knowledge import router as knowledge_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
