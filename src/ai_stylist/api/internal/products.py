import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from ai_stylist.clients.product_client import ProductServiceClient
from ai_stylist.config import settings
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.product.qdrant_sync import delete_product, upsert_product

logger = logging.getLogger(__name__)


async def _require_internal_token(x_internal_token: str = Header(default="", alias="X-Internal-Token")) -> None:
    if x_internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Forbidden")


router = APIRouter(
    prefix="/internal/v1/products",
    tags=["internal"],
    dependencies=[Depends(_require_internal_token)],
)


@router.post("/{product_id}/sync")
async def sync_product(product_id: str):
    try:
        product = await ProductServiceClient().fetch_live(product_id)
    except Exception as exc:
        logger.warning("Qdrant sync: failed to fetch product %s from Product Service: %s", product_id, exc)
        raise HTTPException(status_code=502, detail="Could not fetch product from Product Service") from exc

    await upsert_product(GeminiClient(), product.model_dump())
    logger.info("Qdrant sync: upserted product %s", product_id)
    return {"status": "synced", "product_id": product_id}


@router.delete("/{product_id}")
async def remove_product(product_id: str):
    await delete_product(product_id)
    logger.info("Qdrant sync: removed product %s", product_id)
    return {"status": "deleted", "product_id": product_id}
