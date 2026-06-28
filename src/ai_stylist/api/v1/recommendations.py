import uuid

from fastapi import APIRouter

from ai_stylist.schemas.recommendation import OutfitRequest, OutfitRecommendationResponse, DayOutfit, OutfitItem
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.llm.intent_extractor import IntentExtractor
from ai_stylist.services.recommendation.pipeline import RecommendationPipeline

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/outfit", response_model=OutfitRecommendationResponse)
async def recommend_outfit(body: OutfitRequest):
    gemini = GeminiClient()
    extractor = IntentExtractor(gemini)
    intent = await extractor.extract(body.message)

    pipeline = RecommendationPipeline()
    result = await pipeline.run(intent, body.message, budget_max=body.budget_max)

    outfits: list[DayOutfit] = []
    for day_plan in result.get("outfit_plan", []):
        items = [
            OutfitItem(
                product_id=item["product_id"],
                name=item["name"],
                category=item["category"],
                target=item.get("target"),
                price=item.get("price"),
                image_url=item.get("image_url"),
                product_url=item.get("product_url"),
                reason=item.get("reason"),
            )
            for item in day_plan.get("items", [])
        ]
        outfits.append(
            DayOutfit(
                day=day_plan["day"],
                context=day_plan.get("context", ""),
                items=items,
                styling_tip=day_plan.get("styling_tip"),
                constraint_check=day_plan.get("constraint_check"),
            )
        )

    return OutfitRecommendationResponse(
        recommendation_id=str(uuid.uuid4()),
        summary=result.get("summary", ""),
        outfits=outfits,
        resolved_concepts=result.get("resolved_concepts", []),
    )
