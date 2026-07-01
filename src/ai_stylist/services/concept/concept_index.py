import uuid
from typing import Any

import httpx

from ai_stylist.config import settings
from ai_stylist.services.llm.gemini_client import GeminiClient


def concept_text(concept: dict[str, Any]) -> str:
    alias_str = " ".join(str(alias) for alias in concept.get("aliases", []))
    return (
        f"{concept.get('name', '')} "
        f"{concept.get('type', '')} "
        f"{concept.get('description') or ''} "
        f"{alias_str}"
    ).strip()


async def upsert_concepts_to_index(concepts: list[dict[str, Any]], gemini: GeminiClient) -> int:
    valid_concepts = [concept for concept in concepts if concept.get("id") and concept.get("name")]
    if not valid_concepts:
        return 0

    texts = [concept_text(concept) for concept in valid_concepts]
    embeddings = await gemini.embed_texts(texts)
    if not embeddings:
        return 0

    async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
        await ensure_concept_collection(client, len(embeddings[0]))
        response = await client.put(
            f"{_base_url()}/collections/{settings.qdrant_concept_collection}/points",
            params={"wait": "true"},
            json={
                "points": [
                    {
                        "id": concept_point_id(str(concept["id"])),
                        "vector": embedding,
                        "payload": {
                            "concept_id": concept["id"],
                            "name": concept["name"],
                            "type": concept.get("type"),
                            "description": concept.get("description"),
                            "aliases": concept.get("aliases", []),
                            "text": text,
                        },
                    }
                    for concept, text, embedding in zip(valid_concepts, texts, embeddings)
                ]
            },
        )
        response.raise_for_status()
    return len(valid_concepts)


async def delete_concepts_from_index(concept_ids: set[str]) -> int:
    if not concept_ids:
        return 0

    async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
        if not await concept_collection_exists(client):
            return 0
        response = await client.post(
            f"{_base_url()}/collections/{settings.qdrant_concept_collection}/points/delete",
            params={"wait": "true"},
            json={"points": [concept_point_id(concept_id) for concept_id in concept_ids]},
        )
        response.raise_for_status()
    return len(concept_ids)


async def concept_collection_exists(client: httpx.AsyncClient) -> bool:
    response = await client.get(f"{_base_url()}/collections/{settings.qdrant_concept_collection}")
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


async def ensure_concept_collection(client: httpx.AsyncClient, vector_size: int, recreate: bool = False) -> None:
    exists = await concept_collection_exists(client)
    if exists and recreate:
        response = await client.delete(f"{_base_url()}/collections/{settings.qdrant_concept_collection}")
        response.raise_for_status()
        exists = False
    if exists:
        return

    response = await client.put(
        f"{_base_url()}/collections/{settings.qdrant_concept_collection}",
        json={
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            }
        },
    )
    response.raise_for_status()
    await _create_payload_indexes(client)


async def _create_payload_indexes(client: httpx.AsyncClient) -> None:
    for field_name in ("concept_id", "type"):
        response = await client.put(
            f"{_base_url()}/collections/{settings.qdrant_concept_collection}/index",
            json={"field_name": field_name, "field_schema": "keyword"},
        )
        response.raise_for_status()


def concept_point_id(concept_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"ai-stylist-concept:{concept_id}"))


def _base_url() -> str:
    return settings.qdrant_url.rstrip("/")
