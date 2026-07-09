"""
HTTP client for Product Service hydration.

Product retrieval is managed by the AI service through hybrid search. Product
Service contributes text-search candidates and is also the source of truth for
fetching full product metadata after product IDs have been selected.

Java product-service only exposes per-id/paginated public endpoints (no batch
fetch or scored text search), wraps everything in ApiResponse{success,data,...}
and uses camelCase field names (id, basePrice, targetDemographic). This client
adapts that real contract to the snake_case Product schema used internally.
"""
import asyncio
import json
from pathlib import Path

import httpx

from ai_stylist.config import settings
from ai_stylist.schemas.product import Category, Product, ProductImage, ProductVariant


def _derive_slot(category_names: list[str]) -> str:
    """
    Recommendation-slot classification (top/bottom/dress/...). Java's category
    taxonomy has no such field, so it's inferred from Vietnamese category names.
    """
    lowered = [name.lower() for name in category_names]
    if any(name.startswith("áo") for name in lowered):
        return "top"
    if any("đầm" in name for name in lowered):
        return "dress"
    if any(name.startswith("quần") or "chân váy" in name for name in lowered):
        return "bottom"
    return "product"


def _dict_to_product(d: dict) -> Product:
    return Product(
        product_id=d["product_id"],
        name=d["name"],
        description=d.get("description"),
        base_price=d["base_price"],
        target_demographic=d.get("target_demographic", "UNISEX"),
        status=d.get("status", "ACTIVE"),
        categories=[Category(**c) for c in d.get("categories", [])],
        variants=[ProductVariant(**v) for v in d.get("variants", [])],
        images=[ProductImage(**img) for img in d.get("images", [])],
        slot=d.get("slot") or _derive_slot([c.get("name", "") for c in d.get("categories", [])]),
    )


def _java_product_to_dict(data: dict) -> dict:
    """Maps a Java ProductResponse JSON object (camelCase) to the internal seed shape."""
    categories = [
        {"name": c["name"]} for c in data.get("categories") or [] if c.get("name")
    ]
    return {
        "product_id": data["id"],
        "name": data.get("name"),
        "description": data.get("description"),
        "base_price": data.get("basePrice"),
        "target_demographic": data.get("targetDemographic", "UNISEX"),
        "status": data.get("status", "ACTIVE"),
        "categories": categories,
        "images": [
            {
                "image_url": img.get("imageUrl"),
                "image_public_id": img.get("publicId"),
                "is_primary": img.get("isPrimary", False),
            }
            for img in data.get("images") or []
        ],
        "variants": [
            {
                "id": v.get("id"),
                "product_id": v.get("productId"),
                "sku": v.get("sku"),
                "size": v.get("size"),
                "color": v.get("color"),
                "material": v.get("material"),
                "price_override": v.get("priceOverride"),
                "stock_quantity": v.get("stockQuantity", 0),
                "active": v.get("active", True),
            }
            for v in data.get("variants") or []
        ],
        "slot": _derive_slot([c["name"] for c in categories]),
    }


def _unwrap_api_response(payload: object) -> object | None:
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data")
    return payload


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


class ProductServiceClient:
    """
    Fetches product metadata and text-search hits from Product Service.

    In local development without Product Service, reads scripts/seeds/products.json
    for metadata hydration only. Product search does not use seed data.
    """

    def __init__(self):
        self._base_url = settings.product_service_base_url.rstrip("/")
        self._products_path = settings.product_service_products_path
        self._timeout = settings.product_service_timeout

    async def batch_fetch(self, product_ids: list[str]) -> list[Product]:
        if not product_ids:
            return []

        fetched: dict[str, Product] = {}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                responses = await asyncio.gather(
                    *(
                        client.get(f"{self._base_url}{self._products_path}/{pid}")
                        for pid in product_ids
                    ),
                    return_exceptions=True,
                )
            for pid, resp in zip(product_ids, responses):
                if isinstance(resp, Exception) or resp.status_code != 200:
                    continue
                data = _unwrap_api_response(resp.json())
                if isinstance(data, dict):
                    fetched[pid] = _dict_to_product(_java_product_to_dict(data))
        except Exception:
            pass

        missing = [pid for pid in product_ids if pid not in fetched]
        if missing:
            for product in self._seed_batch_fetch(missing):
                fetched[product.product_id] = product

        return [fetched[pid] for pid in product_ids if pid in fetched]

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
                resp = await client.get(
                    f"{self._base_url}{self._products_path}",
                    params={"search": query, "page": 0, "size": limit},
                )
                resp.raise_for_status()
                data = _unwrap_api_response(resp.json())
                content = (data or {}).get("content", []) if isinstance(data, dict) else []
        except Exception:
            return []

        hits: list[dict] = []
        for index, item in enumerate(content[:limit]):
            if not isinstance(item, dict) or "id" not in item:
                continue
            hit = _java_product_to_dict(item)
            hit["_score"] = max(0.0, 1.0 - (index / max(limit, 1)))
            hits.append(hit)
        return hits
