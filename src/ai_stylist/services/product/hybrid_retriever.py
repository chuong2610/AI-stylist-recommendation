import math
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

from ai_stylist.config import settings


class ProductSearchCandidate(BaseModel):
    product_id: str
    target: str
    matched_text: str = ""
    bm25_score: float = 0.0
    vector_score: float = 0.0
    retrieval_score: float = 0.0
    sources: list[str] = Field(default_factory=list)
    light_metadata: dict[str, Any] = Field(default_factory=dict)


class HybridProductRetriever:
    """
    AI-managed hybrid retrieval.

    BM25 and vector search are deliberately target/item based. No structured
    category search is used here; category can still exist as product metadata
    returned later by Product Service.
    """

    def __init__(self):
        catalog = _load_json(settings.product_catalog_seed_path)
        self._catalog_by_id = {p["product_id"]: p for p in catalog}
        self._bm25 = BM25ProductSearcher(self._catalog_by_id)
        self._vector = MockQdrantProductSearcher(self._catalog_by_id)

    async def search(self, search_terms: dict[str, list[str]], limit_per_target: int | None = None) -> dict[str, list[ProductSearchCandidate]]:
        limit = limit_per_target or settings.hybrid_search_limit_per_target
        results_by_target: dict[str, dict[str, ProductSearchCandidate]] = {}

        for target, terms in search_terms.items():
            target_results: dict[str, ProductSearchCandidate] = {}
            for term in terms:
                bm25_results = self._bm25.search(target, term, limit=limit)
                vector_results = self._vector.search(target, term, limit=limit)
                _merge_candidates(target_results, bm25_results)
                _merge_candidates(target_results, vector_results)

            candidates = list(target_results.values())
            for candidate in candidates:
                multi_source_bonus = 0.1 if len(candidate.sources) > 1 else 0.0
                candidate.retrieval_score = round(
                    (0.45 * candidate.bm25_score)
                    + (0.45 * candidate.vector_score)
                    + multi_source_bonus,
                    4,
                )
            candidates.sort(key=lambda c: c.retrieval_score, reverse=True)
            results_by_target[target] = candidates[:limit]

        return results_by_target


class BM25ProductSearcher:
    def __init__(self, catalog_by_id: dict[str, dict]):
        docs = _load_json(settings.product_bm25_seed_path)
        self._docs = docs
        self._catalog_by_id = catalog_by_id
        tokenized = [_tokenize(doc.get("text", "")) for doc in docs]
        self._bm25 = BM25Okapi(tokenized) if tokenized else None

    def search(self, target: str, query: str, limit: int) -> list[ProductSearchCandidate]:
        if not self._bm25 or not self._docs:
            return []

        scores = self._bm25.get_scores(_tokenize(query))
        max_score = max(scores) if len(scores) and max(scores) > 0 else 1.0
        ranked = sorted(zip(self._docs, scores), key=lambda pair: pair[1], reverse=True)

        results: list[ProductSearchCandidate] = []
        for doc, score in ranked[:limit]:
            if score <= 0:
                continue
            product_id = doc["product_id"]
            results.append(ProductSearchCandidate(
                product_id=product_id,
                target=target,
                matched_text=doc.get("text", ""),
                bm25_score=round(float(score) / float(max_score), 4),
                sources=["bm25"],
                light_metadata=_light_metadata(self._catalog_by_id.get(product_id, {})),
            ))
        return results


class MockQdrantProductSearcher:
    """
    Local vector-search mock for development.

    It reads Qdrant-like seed documents and computes cosine similarity over a
    lightweight token vector. Replace this class with a real Qdrant client when
    the collection is available.
    """

    def __init__(self, catalog_by_id: dict[str, dict]):
        self._docs = _load_json(settings.product_vector_seed_path)
        self._catalog_by_id = catalog_by_id
        for doc in self._docs:
            product = catalog_by_id.get(doc["product_id"], {})
            doc["_vector_text"] = " ".join([
                doc.get("semantic_text", ""),
                product.get("name", ""),
                product.get("description", ""),
                " ".join(product.get("tags", [])),
            ])
            doc["_vector"] = _text_vector(doc["_vector_text"])

    def search(self, target: str, query: str, limit: int) -> list[ProductSearchCandidate]:
        query_vector = _text_vector(query)
        scored: list[tuple[dict, float]] = []
        for doc in self._docs:
            score = _cosine(query_vector, doc["_vector"])
            if score > 0:
                scored.append((doc, score))

        if not scored:
            return []

        max_score = max(score for _, score in scored) or 1.0
        ranked = sorted(scored, key=lambda pair: pair[1], reverse=True)
        results: list[ProductSearchCandidate] = []
        for doc, score in ranked[:limit]:
            product_id = doc["product_id"]
            results.append(ProductSearchCandidate(
                product_id=product_id,
                target=target,
                matched_text=doc.get("semantic_text", ""),
                vector_score=round(score / max_score, 4),
                sources=["qdrant"],
                light_metadata=_light_metadata(self._catalog_by_id.get(product_id, {})),
            ))
        return results


def _merge_candidates(target_results: dict[str, ProductSearchCandidate], candidates: list[ProductSearchCandidate]) -> None:
    for candidate in candidates:
        existing = target_results.get(candidate.product_id)
        if existing is None:
            target_results[candidate.product_id] = candidate
            continue
        existing.bm25_score = max(existing.bm25_score, candidate.bm25_score)
        existing.vector_score = max(existing.vector_score, candidate.vector_score)
        existing.sources = sorted(set(existing.sources + candidate.sources))
        if not existing.matched_text:
            existing.matched_text = candidate.matched_text


def _load_json(path_value: str) -> list[dict]:
    path = Path(path_value)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _light_metadata(product: dict) -> dict[str, Any]:
    return {
        "name": product.get("name"),
        "description": product.get("description"),
        "category": product.get("category"),
        "color": product.get("color", []),
        "size": product.get("size", []),
        "material": product.get("material"),
        "price": product.get("price"),
        "stock_status": product.get("stock_status"),
        "rating": product.get("rating"),
        "tags": product.get("tags", []),
    }


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ỹ]+", text.lower())


def _text_vector(text: str) -> Counter[str]:
    return Counter(_tokenize(text))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b.get(token, 0) for token in a)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
