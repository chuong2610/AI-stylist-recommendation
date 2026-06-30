import hashlib
import json
from pathlib import Path
from typing import Any

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


async def merge_concepts_into_cache(concepts: list[dict[str, Any]], gemini: GeminiClient) -> int:
    valid_concepts = [concept for concept in concepts if concept.get("id") and concept.get("name")]
    if not valid_concepts:
        return 0

    cache = _load_existing_cache()
    cached_rows = {
        str(row["id"]): row
        for row in cache.get("concepts", [])
        if isinstance(row, dict) and row.get("id")
    }

    changed = [
        concept for concept in valid_concepts
        if _cache_row_needs_update(cached_rows.get(str(concept["id"])), concept)
    ]
    if not changed:
        return 0

    texts = [concept_text(concept) for concept in changed]
    embeddings = await gemini.embed_texts(texts)
    for concept, text, embedding in zip(changed, texts, embeddings):
        cached_rows[str(concept["id"])] = {
            "id": concept["id"],
            "name": concept["name"],
            "type": concept["type"],
            "description": concept.get("description"),
            "aliases": concept.get("aliases", []),
            "text": text,
            "embedding": embedding,
        }

    cache["source_path"] = settings.kg_seed_path
    cache["source_hash"] = _source_hash()
    cache["embedding_model"] = settings.gemini_embedding_model
    cache["concepts"] = list(cached_rows.values())

    path = Path(settings.concept_embedding_cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(changed)


def remove_concepts_from_cache(concept_ids: set[str]) -> int:
    if not concept_ids:
        return 0

    cache = _load_existing_cache()
    rows = cache.get("concepts", [])
    if not isinstance(rows, list):
        return 0

    kept_rows = [
        row for row in rows
        if not (isinstance(row, dict) and str(row.get("id")) in concept_ids)
    ]
    removed = len(rows) - len(kept_rows)
    if not removed:
        return 0

    cache["concepts"] = kept_rows
    path = Path(settings.concept_embedding_cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return removed


def _load_existing_cache() -> dict[str, Any]:
    path = Path(settings.concept_embedding_cache_path)
    if not path.exists():
        return {"concepts": []}
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"concepts": []}
    return cache if isinstance(cache, dict) else {"concepts": []}


def _cache_row_needs_update(row: dict[str, Any] | None, concept: dict[str, Any]) -> bool:
    if row is None:
        return True
    return (
        row.get("name") != concept.get("name")
        or row.get("type") != concept.get("type")
        or row.get("description") != concept.get("description")
        or row.get("aliases", []) != concept.get("aliases", [])
    )


def _source_hash() -> str:
    path = Path(settings.kg_seed_path)
    return hashlib.sha256(path.read_bytes()).hexdigest()
