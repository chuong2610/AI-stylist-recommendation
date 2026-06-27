"""
One-time script: generate and store embeddings for all concepts in the DB.

Usage:
    uv run python scripts/index_concepts.py

Run this after seeding the concepts table, and again whenever concepts change.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_stylist.db.postgres import AsyncSessionFactory, create_all_tables
from ai_stylist.services.concept.embedding_service import EmbeddingService
from ai_stylist.services.llm.gemini_client import GeminiClient


async def main() -> None:
    print("Ensuring tables and pgvector extension exist...")
    await create_all_tables()

    gemini = GeminiClient()
    svc = EmbeddingService(gemini)

    async with AsyncSessionFactory() as db:
        print("Indexing concepts...")
        count = await svc.index_all(db)
        print(f"Done — {count} concept(s) indexed.")


if __name__ == "__main__":
    asyncio.run(main())
