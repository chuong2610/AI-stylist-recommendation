import asyncio
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ai_stylist.clients.product_client import ProductServiceClient
from ai_stylist.config import settings
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.llm.search_term_generator import TargetSearchTerms


class ProductSearchCandidate(BaseModel):
    product_id: str
    target: str
    matched_text: str = ""
    text_score: float = 0.0
    vector_score: float = 0.0
    retrieval_score: float = 0.0
    sources: list[str] = Field(default_factory=list)
    light_metadata: dict[str, Any] = Field(default_factory=dict)


class HybridProductRetriever:
    """
    Product retrieval through real hybrid search.

    Sources:
    - Qdrant semantic vector search over product embeddings.
    - Product Service text search over the live product catalog.

    There is no local lexical index or local cosine search path.
    """

    def __init__(self, gemini: GeminiClient, product_client: ProductServiceClient | None = None):
        self._gemini = gemini
        self._product_client = product_client or ProductServiceClient()
        self._collection = settings.qdrant_product_collection
        self._base_url = settings.qdrant_url.rstrip("/")
        self._timeout = settings.qdrant_timeout

    async def search(
        self,
        search_terms: list[TargetSearchTerms],
        limit_per_target: int | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
    ) -> dict[str, list[ProductSearchCandidate]]:
        limit = limit_per_target or settings.hybrid_search_limit_per_target
        search_limit = limit * 3 if price_min is not None or price_max is not None else limit
        queries = [
            (target_terms.item, term)
            for target_terms in search_terms
            for term in target_terms.terms
            if term.strip()
        ]
        if not queries:
            return {}

        vectors = await self._gemini.embed_texts([term for _, term in queries])
        results_by_target: dict[str, dict[str, ProductSearchCandidate]] = {}

        async with httpx.AsyncClient(timeout=self._timeout) as qdrant_client:
            tasks = [
                self._search_one(qdrant_client, target, term, vector, search_limit, price_min, price_max)
                for (target, term), vector in zip(queries, vectors)
            ]
            results = await asyncio.gather(*tasks)

        for target, candidates in results:
            target_results = results_by_target.setdefault(target, {})
            _merge_candidates(target_results, candidates)

        return {
            target: sorted(candidates.values(), key=lambda c: c.retrieval_score, reverse=True)[:limit]
            for target, candidates in results_by_target.items()
        }

    async def _search_one(
        self,
        qdrant_client: httpx.AsyncClient,
        target: str,
        term: str,
        vector: list[float],
        limit: int,
        price_min: float | None,
        price_max: float | None,
    ) -> tuple[str, list[ProductSearchCandidate]]:
        qdrant_task = self._search_qdrant(qdrant_client, target, vector, limit, price_min, price_max)
        text_task = self._product_client.search_text(term, target, limit)
        qdrant_results, text_results = await asyncio.gather(qdrant_task, text_task)

        candidates = [
            _candidate_from_qdrant(target, term, point)
            for point in qdrant_results
        ]
        candidates.extend(
            _candidate_from_product_service(target, term, hit)
            for hit in text_results
        )
        return target, [
            candidate for candidate in candidates
            if _matches_price(candidate.light_metadata.get("price"), price_min, price_max)
            and _matches_target(candidate.light_metadata.get("category"), target)
        ]

    async def _search_qdrant(
        self,
        client: httpx.AsyncClient,
        target: str,
        vector: list[float],
        limit: int,
        price_min: float | None = None,
        price_max: float | None = None,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "score_threshold": settings.qdrant_score_threshold,
        }
        qdrant_filter = _qdrant_filter(target, price_min, price_max)
        if qdrant_filter:
            body["filter"] = qdrant_filter

        response = await client.post(
            f"{self._base_url}/collections/{self._collection}/points/search",
            json=body,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("result", [])
        return result if isinstance(result, list) else []


def _candidate_from_qdrant(target: str, query: str, point: dict[str, Any]) -> ProductSearchCandidate:
    payload = point.get("payload") or {}
    product_id = str(payload.get("product_id") or point.get("id"))
    score = round(float(point.get("score") or 0.0), 4)
    return ProductSearchCandidate(
        product_id=product_id,
        target=target,
        matched_text=payload.get("search_text") or query,
        vector_score=score,
        sources=["qdrant"],
        light_metadata=_light_metadata(payload),
    )


def _candidate_from_product_service(target: str, query: str, hit: dict[str, Any]) -> ProductSearchCandidate:
    score = round(float(hit.get("_score") or hit.get("score") or 0.0), 4)
    return ProductSearchCandidate(
        product_id=str(hit["product_id"]),
        target=target,
        matched_text=hit.get("search_text") or hit.get("name") or query,
        text_score=score,
        sources=["product_service_text"],
        light_metadata=_light_metadata(hit),
    )


def _merge_candidates(
    target_results: dict[str, ProductSearchCandidate],
    candidates: list[ProductSearchCandidate],
) -> None:
    for candidate in candidates:
        existing = target_results.get(candidate.product_id)
        if existing is None:
            _score_candidate(candidate)
            target_results[candidate.product_id] = candidate
            continue

        previous_score = existing.retrieval_score
        existing.text_score = max(existing.text_score, candidate.text_score)
        existing.vector_score = max(existing.vector_score, candidate.vector_score)
        existing.sources = sorted(set(existing.sources + candidate.sources))
        _score_candidate(existing)
        if existing.retrieval_score >= previous_score and candidate.matched_text:
            existing.matched_text = candidate.matched_text
        if not existing.light_metadata:
            existing.light_metadata = candidate.light_metadata


def _score_candidate(candidate: ProductSearchCandidate) -> None:
    multi_source_bonus = settings.hybrid_multi_source_bonus if len(candidate.sources) > 1 else 0.0
    candidate.retrieval_score = round(
        (settings.hybrid_vector_weight * candidate.vector_score)
        + (settings.hybrid_text_weight * candidate.text_score)
        + multi_source_bonus,
        4,
    )


def _qdrant_filter(target: str, price_min: float | None, price_max: float | None) -> dict[str, Any] | None:
    must: list[dict[str, Any]] = []

    categories = _target_categories(target)
    if categories:
        must.append({"key": "category", "match": {"any": categories}})

    price_range: dict[str, float] = {}
    if price_min is not None:
        price_range["gte"] = float(price_min)
    if price_max is not None:
        price_range["lte"] = float(price_max)
    if price_range:
        must.append({"key": "price", "range": price_range})

    if not must:
        return None
    return {"must": must}


def _matches_price(price: Any, price_min: float | None, price_max: float | None) -> bool:
    if price_min is None and price_max is None:
        return True
    if price is None:
        return False
    try:
        value = float(price)
    except (TypeError, ValueError):
        return False
    if price_min is not None and value < price_min:
        return False
    if price_max is not None and value > price_max:
        return False
    return True


def _matches_target(category: Any, target: str) -> bool:
    categories = _target_categories(target)
    if not categories:
        return True
    return str(category or "").lower() in categories


def _target_categories(target: str) -> list[str]:
    normalized = str(target or "").strip().lower()
    mapping = {
        "top": ["top"],
        "bottom": ["bottom"],
        "dress": ["dress"],
        "shoes": ["shoes"],
        "shoe": ["shoes"],
        "bag": ["bag"],
        "accessory": ["accessory"],
        "accessories": ["accessory"],
    }
    return mapping.get(normalized, [])


def _light_metadata(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": product.get("name"),
        "description": product.get("description"),
        "category": product.get("category"),
        "brand": product.get("brand"),
        "color": product.get("color", []),
        "size": product.get("size", []),
        "material": product.get("material"),
        "price": product.get("price"),
        "stock_status": product.get("stock_status"),
        "rating": product.get("rating"),
        "tags": product.get("tags", []),
    }
