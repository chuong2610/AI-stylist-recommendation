import json
import math
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_stylist.config import settings
from ai_stylist.services.llm.gemini_client import GeminiClient


@dataclass
class ResolvedConcept:
    input_term: str
    concept_id: str
    concept_name: str
    concept_type: str
    confidence: float


@dataclass
class _IndexedConcept:
    id: str
    name: str
    type: str
    embedding: list[float]


class EmbeddingService:
    """Semantic concept lookup from knowledge_graph.json + in-memory vectors."""

    def __init__(self, gemini: GeminiClient):
        self._gemini = gemini
        self._concept_vectors: list[_IndexedConcept] | None = None

    async def embed_terms(self, terms: list[str]) -> list[list[float]]:
        return await self._gemini.embed_texts(terms)

    def concept_text(self, concept: dict[str, Any]) -> str:
        alias_str = " ".join(str(alias) for alias in concept.get("aliases", []))
        return (
            f"{concept.get('name', '')} "
            f"{concept.get('type', '')} "
            f"{concept.get('description') or ''} "
            f"{alias_str}"
        ).strip()

    async def resolve_terms(self, terms: list[str]) -> list[ResolvedConcept]:
        """Embed terms and find the closest JSON concept for each via cosine similarity."""
        if not terms:
            return []

        concepts = await self._load_or_index()
        if not concepts:
            return []

        embeddings = await self.embed_terms(terms)
        results: list[ResolvedConcept] = []
        seen_ids: set[str] = set()

        for term, embedding in zip(terms, embeddings):
            match = _best_match(embedding, concepts, settings.concept_similarity_threshold)
            if match is None:
                continue

            concept, similarity = match
            if concept.id in seen_ids:
                continue

            seen_ids.add(concept.id)
            results.append(ResolvedConcept(
                input_term=term,
                concept_id=concept.id,
                concept_name=concept.name,
                concept_type=concept.type,
                confidence=round(similarity, 3),
            ))

        return results

    async def resolve_from_intent(self, intent: dict) -> list[ResolvedConcept]:
        return await self.resolve_terms(_extract_intent_terms(intent))

    async def index_all(self) -> int:
        """Embed every JSON concept and persist vectors to the local cache."""
        concepts = _load_json_concepts()
        if not concepts:
            return 0

        texts = [self.concept_text(concept) for concept in concepts]
        embeddings = await self._gemini.embed_texts(texts)
        cache = {
            "source_path": settings.kg_seed_path,
            "source_hash": _source_hash(),
            "embedding_model": settings.gemini_embedding_model,
            "concepts": [
                {
                    "id": concept["id"],
                    "name": concept["name"],
                    "type": concept["type"],
                    "description": concept.get("description"),
                    "aliases": concept.get("aliases", []),
                    "text": text,
                    "embedding": embedding,
                }
                for concept, text, embedding in zip(concepts, texts, embeddings)
            ],
        }

        cache_path = _cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        self._concept_vectors = _indexed_from_cache(cache)
        return len(concepts)

    async def _load_or_index(self) -> list[_IndexedConcept]:
        if self._concept_vectors is not None:
            return self._concept_vectors

        cache = _load_cache()
        if cache is None:
            await self.index_all()
        else:
            self._concept_vectors = _indexed_from_cache(cache)

        return self._concept_vectors or []


def _extract_intent_terms(intent: dict) -> list[str]:
    terms: list[str] = []
    if style_prefs := intent.get("style_preferences", []):
        terms.extend(style_prefs)
    if requested_items := intent.get("requested_items", []):
        terms.extend(requested_items)
    if occasion := intent.get("occasion"):
        terms.append(occasion)
    if destination := intent.get("destination"):
        terms.append(destination)
    if body_ctx := intent.get("body_context", {}):
        if h := body_ctx.get("height_group"):
            terms.append(h)
    if modesty := intent.get("modesty_level"):
        terms.append(modesty)
    if comfort := intent.get("comfort_needs", []):
        terms.extend(comfort)
    if raw := intent.get("raw_keywords", []):
        terms.extend(raw)
    return terms


def _load_json_concepts() -> list[dict[str, Any]]:
    path = Path(settings.kg_seed_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    concepts = data.get("concepts", []) if isinstance(data, dict) else []
    return concepts if isinstance(concepts, list) else []


def _cache_path() -> Path:
    return Path(settings.concept_embedding_cache_path)


def _load_cache() -> dict[str, Any] | None:
    path = _cache_path()
    if not path.exists():
        return None
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if cache.get("embedding_model") != settings.gemini_embedding_model:
        return None
    if cache.get("source_hash") != _source_hash():
        return None
    if not isinstance(cache.get("concepts"), list):
        return None
    return cache


def _source_hash() -> str:
    path = Path(settings.kg_seed_path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _indexed_from_cache(cache: dict[str, Any]) -> list[_IndexedConcept]:
    indexed: list[_IndexedConcept] = []
    for row in cache.get("concepts", []):
        if not isinstance(row, dict):
            continue
        embedding = row.get("embedding")
        if not isinstance(embedding, list):
            continue
        indexed.append(_IndexedConcept(
            id=str(row["id"]),
            name=str(row.get("name") or row["id"]),
            type=str(row.get("type") or ""),
            embedding=[float(value) for value in embedding],
        ))
    return indexed


def _best_match(
    embedding: list[float],
    concepts: list[_IndexedConcept],
    min_similarity: float,
) -> tuple[_IndexedConcept, float] | None:
    best: tuple[_IndexedConcept, float] | None = None
    for concept in concepts:
        similarity = _cosine_similarity(embedding, concept.embedding)
        if similarity < min_similarity:
            continue
        if best is None or similarity > best[1]:
            best = (concept, similarity)
    return best


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
