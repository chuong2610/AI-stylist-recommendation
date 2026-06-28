"""
Initialize the local concept embedding cache from scripts/seeds/knowledge_graph.json.

Usage:
    uv run python scripts/init_concepts.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_stylist.services.concept.embedding_service import EmbeddingService
from ai_stylist.services.llm.gemini_client import GeminiClient


async def main() -> None:
    svc = EmbeddingService(GeminiClient())
    count = await svc.index_all()
    print(f"Initialized local concept embedding cache with {count} concept(s).")


if __name__ == "__main__":
    asyncio.run(main())
