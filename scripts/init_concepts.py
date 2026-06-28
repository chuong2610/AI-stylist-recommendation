"""
Sync the Postgres semantic concept store from scripts/seeds/knowledge_graph.json.

Usage:
    uv run python scripts/init_concepts.py --index
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import delete

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_stylist.config import settings
from ai_stylist.db.postgres import AsyncSessionFactory, create_all_tables
from ai_stylist.models.concept import Concept, ConceptAlias
from ai_stylist.services.concept.embedding_service import EmbeddingService
from ai_stylist.services.llm.gemini_client import GeminiClient


def _load_concepts(path_value: str) -> list[dict[str, Any]]:
    path = Path(path_value)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path_value} must contain a JSON object")
    concepts = data.get("concepts", [])
    return concepts if isinstance(concepts, list) else []


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=settings.kg_seed_path)
    parser.add_argument("--index", action="store_true")
    args = parser.parse_args()

    concepts = _load_concepts(args.seed)
    if not concepts:
        raise ValueError(f"No concepts found in {args.seed}")

    await create_all_tables()
    concept_ids = [concept["id"] for concept in concepts]
    async with AsyncSessionFactory() as db:
        await db.execute(delete(ConceptAlias).where(ConceptAlias.concept_id.in_(concept_ids)))

        for row in concepts:
            concept = await db.get(Concept, row["id"])
            if concept is None:
                concept = Concept(id=row["id"])
                db.add(concept)
            concept.name = row["name"]
            concept.type = row["type"]
            concept.description = row.get("description")
            for alias in row.get("aliases", []):
                db.add(ConceptAlias(
                    concept_id=row["id"],
                    alias=alias,
                    language="vi" if any(ord(ch) > 127 for ch in alias) else "en",
                ))

        await db.commit()

        indexed_count = 0
        if args.index:
            indexed_count = await EmbeddingService(GeminiClient()).index_all(db)

    message = f"Synced {len(concepts)} semantic concept(s) into Postgres"
    if args.index:
        message += f" and indexed {indexed_count} embedding(s)"
    print(message + ".")


if __name__ == "__main__":
    asyncio.run(main())
