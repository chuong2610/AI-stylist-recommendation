from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import httpx

from ai_stylist.config import settings
from ai_stylist.services.concept.concept_index import (
    concept_collection_exists,
    concept_text,
    ensure_concept_collection,
    upsert_concepts_to_index,
)
from ai_stylist.services.llm.gemini_client import GeminiClient


@dataclass
class ResolvedConcept:
    input_term: str
    concept_id: str
    concept_name: str
    concept_type: str
    confidence: float


@dataclass
class _IntentTerm:
    term: str
    allowed_types: set[str] | None = None


class EmbeddingService:
    """Semantic concept lookup through the Qdrant concept collection."""

    def __init__(self, gemini: GeminiClient):
        self._gemini = gemini

    async def embed_terms(self, terms: list[str]) -> list[list[float]]:
        return await self._gemini.embed_texts(terms)

    def concept_text(self, concept: dict[str, Any]) -> str:
        return concept_text(concept)

    async def resolve_terms(self, terms: list[str]) -> list[ResolvedConcept]:
        """Embed terms and find the closest JSON concept for each via cosine similarity."""
        return await self._resolve_term_specs([_IntentTerm(term=term) for term in terms if term.strip()])

    async def _resolve_term_specs(self, term_specs: list[_IntentTerm]) -> list[ResolvedConcept]:
        """Resolve terms with optional concept type constraints."""
        term_specs = [spec for spec in term_specs if spec.term.strip()]
        terms = [spec.term for spec in term_specs]
        if not terms:
            return []

        await self._ensure_index_exists()
        embeddings = await self.embed_terms(terms)
        results: list[ResolvedConcept] = []
        seen_ids: set[str] = set()

        for spec, embedding in zip(term_specs, embeddings):
            match = await self._search_one(embedding, spec.allowed_types)
            if match is None:
                continue

            payload, similarity = match
            concept_id = str(payload.get("concept_id") or "")
            if not concept_id or concept_id in seen_ids:
                continue

            seen_ids.add(concept_id)
            results.append(ResolvedConcept(
                input_term=spec.term,
                concept_id=concept_id,
                concept_name=str(payload.get("name") or concept_id),
                concept_type=str(payload.get("type") or ""),
                confidence=round(similarity, 3),
            ))

        return results

    async def resolve_from_intent(self, intent: dict) -> list[ResolvedConcept]:
        return await self._resolve_term_specs(_extract_intent_terms(intent))

    async def index_all(self) -> int:
        """Embed every JSON concept and persist vectors to Qdrant."""
        concepts = _load_json_concepts()
        if not concepts:
            return 0

        async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
            embeddings = await self._gemini.embed_texts([self.concept_text(concept) for concept in concepts[:1]])
            if not embeddings:
                return 0
            await ensure_concept_collection(client, len(embeddings[0]), recreate=True)

        return await upsert_concepts_to_index(concepts, self._gemini)

    async def _ensure_index_exists(self) -> None:
        async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
            if not await concept_collection_exists(client):
                await self.index_all()

    async def _search_one(
        self,
        embedding: list[float],
        allowed_types: set[str] | None,
    ) -> tuple[dict[str, Any], float] | None:
        body: dict[str, Any] = {
            "vector": embedding,
            "limit": 1,
            "with_payload": True,
            "score_threshold": settings.concept_similarity_threshold,
        }
        if allowed_types:
            body["filter"] = {
                "must": [
                    {
                        "key": "type",
                        "match": {"any": sorted(allowed_types)},
                    }
                ]
            }

        async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
            response = await client.post(
                f"{settings.qdrant_url.rstrip('/')}/collections/{settings.qdrant_concept_collection}/points/search",
                json=body,
            )
            if response.status_code == 404:
                await self.index_all()
                response = await client.post(
                    f"{settings.qdrant_url.rstrip('/')}/collections/{settings.qdrant_concept_collection}/points/search",
                    json=body,
                )
            response.raise_for_status()

        points = response.json().get("result", [])
        if not points:
            return None
        point = points[0]
        payload = point.get("payload") or {}
        return payload, float(point.get("score") or 0.0)


def _extract_intent_terms(intent: dict) -> list[_IntentTerm]:
    terms: list[_IntentTerm] = []
    if style_prefs := intent.get("style_preferences", []):
        terms.extend(_term(term, {"style"}) for term in style_prefs)
    if requested_items := intent.get("requested_items", []):
        terms.extend(_term(term, {"item_type"}) for term in requested_items)
    if occasion := intent.get("occasion"):
        terms.append(_term(occasion, {"occasion"}))
    if destination := intent.get("destination"):
        terms.append(_term(destination, {"occasion"}))
    if body_ctx := intent.get("body_context", {}):
        if h := body_ctx.get("height_group"):
            terms.append(_term(h, {"body_context"}))
        if shape := body_ctx.get("body_shape"):
            terms.append(_term(shape, {"body_context"}))
        if build := body_ctx.get("body_build"):
            terms.append(_term(_body_build_query(build, intent), {"body_context"}))
        measurement_query = _measurement_query(body_ctx, intent)
        if measurement_query:
            terms.append(_term(measurement_query, {"body_context"}))
    if gender := intent.get("gender"):
        terms.append(_term(_gender_query(gender), {"style", "user_context"}))
    if modesty := intent.get("modesty_level"):
        terms.append(_term(modesty, {"preference"}))
    if comfort := intent.get("comfort_needs", []):
        terms.extend(_term(term, {"preference", "material_property", "style"}) for term in comfort)
    return terms


def _term(value: Any, allowed_types: set[str]) -> _IntentTerm:
    return _IntentTerm(term=str(value).strip(), allowed_types=allowed_types)


def _gender_query(gender: str) -> str:
    normalized = gender.strip().lower()
    if normalized in {"male", "nam", "man", "men"}:
        return "mens casual male outfit"
    if normalized in {"female", "nu", "nữ", "woman", "women"}:
        return "feminine casual female outfit"
    return gender


def _body_build_query(body_build: str, intent: dict) -> str:
    normalized = body_build.strip().lower()
    gender = str(intent.get("gender") or "").strip().lower()
    if normalized in {"stocky", "solid", "đậm người", "dam nguoi"}:
        return "stocky solid build"
    if normalized == "curvy" and gender in {"male", "nam", "man", "men"}:
        return "stocky solid build"
    return body_build


def _measurement_query(body_ctx: dict[str, Any], intent: dict) -> str | None:
    height = body_ctx.get("height_cm")
    weight = body_ctx.get("weight_kg")
    if height is None or weight is None:
        return None

    gender = str(intent.get("gender") or "").strip().lower()
    try:
        height_value = int(height)
        weight_value = int(weight)
    except (TypeError, ValueError):
        return None

    if gender in {"male", "nam", "man", "men"} and height_value <= 175 and weight_value >= 75:
        return f"{height_value}cm {weight_value}kg stocky solid build"
    if height_value <= 160:
        return f"{height_value}cm petite body"
    return f"{height_value}cm {weight_value}kg body context"


def _load_json_concepts() -> list[dict[str, Any]]:
    path = Path(settings.kg_seed_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    concepts = data.get("concepts", []) if isinstance(data, dict) else []
    return concepts if isinstance(concepts, list) else []
