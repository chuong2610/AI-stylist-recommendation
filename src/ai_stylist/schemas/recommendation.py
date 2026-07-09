from typing import Any
from pydantic import BaseModel, Field


class OutfitRequest(BaseModel):
    user_id: str
    message: str = Field(..., min_length=1, max_length=4000)
    budget_max: float | None = None
    locale: str = "vi-VN"


class OutfitItem(BaseModel):
    product_id: str
    name: str
    categories: list[str] = []
    target_demographic: str | None = None
    target: str | None = None
    base_price: float | None = None
    image_url: str | None = None
    reason: str | None = None


class DayOutfit(BaseModel):
    day: int
    context: str
    items: list[OutfitItem]
    styling_tip: str | None = None
    constraint_check: dict[str, bool] | None = None


class OutfitRecommendationResponse(BaseModel):
    recommendation_id: str
    summary: str
    outfits: list[DayOutfit]
    resolved_concepts: list[str] = []
    debug: dict[str, Any] | None = None
