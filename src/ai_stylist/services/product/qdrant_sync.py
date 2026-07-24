import uuid
from typing import Any

import httpx

from ai_stylist.config import settings
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.product.bm25_encoder import encode_documents


def product_point_id(product_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"ai-stylist-product:{product_id}"))


def build_search_text(product: dict[str, Any]) -> str:
    parts = [
        product.get("search_text", ""),
        product.get("name", ""),
        product.get("description", ""),
        " ".join(c.get("name", "") for c in product.get("categories", [])),
        " ".join(v.get("color", "") for v in product.get("variants", [])),
        " ".join(product.get("tags", [])),
    ]
    return " ".join(part for part in parts if part).strip()


async def upsert_product(gemini: GeminiClient, product: dict[str, Any]) -> None:
    search_text = build_search_text(product)
    dense_vectors = await gemini.embed_texts([search_text])
    if not dense_vectors:
        raise RuntimeError(f"No embedding generated for product {product.get('product_id')}")
    sparse_vector = encode_documents([search_text])[0]

    point = {
        "id": product_point_id(product["product_id"]),
        "vector": {"dense": dense_vectors[0], "bm25": sparse_vector},
        "payload": {**product, "search_text": search_text},
    }

    async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
        response = await client.put(
            f"{settings.qdrant_url.rstrip('/')}/collections/{settings.qdrant_product_collection}/points",
            params={"wait": "true"},
            json={"points": [point]},
        )
        response.raise_for_status()


async def delete_product(product_id: str) -> None:
    async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
        response = await client.post(
            f"{settings.qdrant_url.rstrip('/')}/collections/{settings.qdrant_product_collection}/points/delete",
            params={"wait": "true"},
            json={"points": [product_point_id(product_id)]},
        )
        response.raise_for_status()
