"""
Initialize the Qdrant product collection from scripts/seeds/products.json.

Usage:
    uv run python scripts/init_qdrant.py --recreate
"""
import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_stylist.config import settings
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.product.bm25_encoder import encode_documents


def _load_products(path_value: str) -> list[dict[str, Any]]:
    path = Path(path_value)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        products = data.get("products", [])
        return products if isinstance(products, list) else []
    return data if isinstance(data, list) else []


def _search_text(product: dict[str, Any]) -> str:
    parts = [
        product.get("search_text", ""),
        product.get("name", ""),
        product.get("description", ""),
        " ".join(c.get("name", "") for c in product.get("categories", [])),
        " ".join(v.get("color", "") for v in product.get("variants", [])),
        " ".join(product.get("tags", [])),
    ]
    return " ".join(part for part in parts if part).strip()


async def _collection_exists(client: httpx.AsyncClient, collection: str) -> bool:
    response = await client.get(f"{settings.qdrant_url.rstrip('/')}/collections/{collection}")
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


async def _create_collection(
    client: httpx.AsyncClient,
    collection: str,
    vector_size: int,
    recreate: bool,
) -> None:
    base_url = settings.qdrant_url.rstrip("/")
    exists = await _collection_exists(client, collection)
    if exists and recreate:
        response = await client.delete(f"{base_url}/collections/{collection}")
        response.raise_for_status()
        exists = False

    if exists:
        return

    response = await client.put(
        f"{base_url}/collections/{collection}",
        json={
            "vectors": {"dense": {"size": vector_size, "distance": "Cosine"}},
            "sparse_vectors": {"bm25": {"modifier": "idf"}},
        },
    )
    response.raise_for_status()


async def _upsert_products(
    client: httpx.AsyncClient,
    collection: str,
    products: list[dict[str, Any]],
    vectors: list[list[float]],
    sparse_vectors: list[dict[str, Any]],
) -> None:
    points = []
    for product, vector, sparse_vector in zip(products, vectors, sparse_vectors):
        product_id = str(product["product_id"])
        payload = {**product, "search_text": _search_text(product)}
        points.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"ai-stylist-product:{product_id}")),
            "vector": {"dense": vector, "bm25": sparse_vector},
            "payload": payload,
        })

    response = await client.put(
        f"{settings.qdrant_url.rstrip('/')}/collections/{collection}/points",
        params={"wait": "true"},
        json={"points": points},
    )
    response.raise_for_status()


async def _create_payload_indexes(client: httpx.AsyncClient, collection: str) -> None:
    for field_name, field_schema in {
        "base_price": "float",
        "slot": "keyword",
    }.items():
        response = await client.put(
            f"{settings.qdrant_url.rstrip('/')}/collections/{collection}/index",
            json={
                "field_name": field_name,
                "field_schema": field_schema,
            },
        )
        response.raise_for_status()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=settings.product_seed_path)
    parser.add_argument("--collection", default=settings.qdrant_product_collection)
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    products = _load_products(args.seed)
    if not products:
        raise ValueError(f"No products found in {args.seed}")

    search_texts = [_search_text(product) for product in products]
    vectors = await GeminiClient().embed_texts(search_texts)
    if not vectors:
        raise ValueError("No embeddings generated for products")
    sparse_vectors = encode_documents(search_texts)

    async with httpx.AsyncClient(timeout=settings.qdrant_timeout) as client:
        await _create_collection(client, args.collection, len(vectors[0]), args.recreate)
        await _upsert_products(client, args.collection, products, vectors, sparse_vectors)
        await _create_payload_indexes(client, args.collection)

    print(f"Initialized Qdrant collection '{args.collection}' with {len(products)} product(s).")


if __name__ == "__main__":
    asyncio.run(main())
