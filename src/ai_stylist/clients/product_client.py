"""
HTTP client for Product Service hydration.

Product retrieval is now managed inside the AI service via BM25 + vector
retrievers. Product Service is only used as the source of truth for fetching
full product metadata after candidate product IDs have been selected.
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
    path = Path(settings.product_catalog_seed_path)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


class ProductServiceClient:
    """
    Fetches full product metadata from Product Service.

    Falls back to scripts/seeds/product_catalog_seed.json while Product Service
    is unavailable.
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
            return self._mock_batch_fetch(product_ids)

    def _mock_batch_fetch(self, product_ids: list[str]) -> list[Product]:
        products_by_id = {p["product_id"]: p for p in _load_catalog_seed()}
        return [
            _dict_to_product(products_by_id[pid])
            for pid in product_ids
            if pid in products_by_id
        ]
