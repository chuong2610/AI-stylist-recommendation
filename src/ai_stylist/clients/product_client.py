"""
HTTP client for Product Service hydration.

Product retrieval is managed by the AI service through hybrid search. Product
Service contributes text-search candidates and is also the source of truth for
fetching full product metadata after product IDs have been selected.
"""
import json
from pathlib import Path

import httpx

from ai_stylist.config import settings
from ai_stylist.schemas.product import Product


def _dict_to_product(d: dict) -> Product:
    return Product(
        product_id=d["product_id"],
        name=d["name"],
        description=d.get("description"),
        category=d["category"],
        brand=d.get("brand"),
        color=d.get("color", []),
        size=d.get("size", []),
        material=d.get("material"),
        price=d.get("price"),
        stock_status=d.get("stock_status", "in_stock"),
        rating=d.get("rating"),
        review_count=d.get("review_count"),
        sales_count=d.get("sales_count"),
        image_url=d.get("image_url"),
        product_url=d.get("product_url"),
    )


def _load_catalog_seed() -> list[dict]:
    path = Path(settings.product_seed_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        products = data.get("products", [])
        return products if isinstance(products, list) else []
    return data if isinstance(data, list) else []


def _extract_product_hits(payload: object, limit: int) -> list[dict]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = (
            payload.get("products")
            or payload.get("results")
            or payload.get("items")
            or []
        )
    else:
        rows = []

    hits: list[dict] = []
    for index, row in enumerate(rows[:limit]):
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("product"), dict):
            product = dict(row["product"])
            score = row.get("score") or row.get("text_score") or row.get("relevance_score")
        else:
            product = dict(row)
            score = product.get("score") or product.get("text_score") or product.get("relevance_score")

        if "product_id" not in product:
            continue
        if score is None:
            score = max(0.0, 1.0 - (index / max(limit, 1)))
        product["_score"] = float(score)
        hits.append(product)
    return hits


class ProductServiceClient:
    """
    Fetches product metadata and text-search hits from Product Service.

    In local development without Product Service, reads scripts/seeds/products.json
    for metadata hydration only. Product search does not use seed data.
    """

    def __init__(self):
        self._base_url = settings.product_service_base_url
        self._timeout = settings.product_service_timeout

    async def batch_fetch(self, product_ids: list[str]) -> list[Product]:
        if not product_ids:
            return []

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/products/batch",
                    json={"product_ids": product_ids},
                )
                resp.raise_for_status()
                return [Product(**p) for p in resp.json()]
        except Exception:
            return self._seed_batch_fetch(product_ids)

    def _seed_batch_fetch(self, product_ids: list[str]) -> list[Product]:
        products_by_id = {p["product_id"]: p for p in _load_catalog_seed()}
        return [
            _dict_to_product(products_by_id[pid])
            for pid in product_ids
            if pid in products_by_id
        ]

    async def search_text(self, query: str, target: str, limit: int) -> list[dict]:
        if not query.strip():
            return []

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}{settings.product_service_text_search_path}",
                    json={
                        "query": query,
                        "target": target,
                        "limit": limit,
                    },
                )
                resp.raise_for_status()
                return _extract_product_hits(resp.json(), limit)
        except Exception:
            return []
