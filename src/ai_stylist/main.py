import asyncio
import logging
import sys
from contextlib import asynccontextmanager

# psycopg3 doesn't support Windows ProactorEventLoop; switch to SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_stylist.config import settings
from ai_stylist.db.postgres import create_all_tables, close_db
from ai_stylist.db.neo4j import close_driver
from ai_stylist.services.agent.checkpointer import setup_checkpointer, close_checkpointer
from ai_stylist.services.agent.store import setup_store, close_store
from ai_stylist.api.v1.router import api_router

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Stylist service...")
    await create_all_tables()
    logger.info("Database tables ready.")
    await setup_checkpointer()
    await setup_store()
    yield
    logger.info("Shutting down...")
    await close_store()
    await close_checkpointer()
    await close_db()
    await close_driver()


app = FastAPI(
    title="AI Stylist",
    description="AI-powered fashion chatbot with LangGraph ReAct agent + outfit recommendation pipeline",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-stylist", "version": "0.2.0"}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
