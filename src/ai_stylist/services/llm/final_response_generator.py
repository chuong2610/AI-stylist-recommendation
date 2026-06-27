import json
from typing import Any

from pydantic import BaseModel, Field

from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.product.hybrid_retriever import ProductSearchCandidate
from ai_stylist.services.recommendation.search_plan import OutfitSearchPlan


class FinalOutfitItem(BaseModel):
    target: str
    product_id: str
    reason: str | None = None


class FinalDayOutfit(BaseModel):
    day: int = 1
    context: str = ""
    items: list[FinalOutfitItem] = Field(default_factory=list)
    styling_reason: str = ""
    styling_tip: str | None = None
    constraint_check: dict[str, bool] = Field(default_factory=dict)


class FinalOutfitResult(BaseModel):
    summary: str
    outfit_plan: list[FinalDayOutfit] = Field(default_factory=list)


_SYSTEM = (
    "You are the final AI stylist response generator. "
    "Choose outfit items only from the provided products_by_target. "
    "Use the knowledge graph rules to choose items that work together. "
    "Do not invent product IDs. Do not include excluded items. "
    "If an optional target does not improve the outfit, skip it. "
    "If a required target has no valid product, explain that clearly."
)

_PROMPT_TEMPLATE = """Create the final outfit response.

User intent:
{intent_json}

Knowledge graph rules:
{rules_json}

Outfit search plan:
{search_plan_json}

Products by target (USE ONLY THESE PRODUCT IDS):
{products_json}

Return JSON matching the schema. The outfit should be coherent as a whole, not simply the top scoring product from each target."""


class FinalResponseGenerator:
    def __init__(self, client: GeminiClient):
        self.client = client

    async def generate(
        self,
        intent: dict[str, Any],
        rules: dict[str, Any],
        search_plan: OutfitSearchPlan,
        candidates_by_target: dict[str, list[ProductSearchCandidate]],
    ) -> FinalOutfitResult:
        products_json = {
            target: [_candidate_summary(c) for c in candidates]
            for target, candidates in candidates_by_target.items()
        }
        prompt = _PROMPT_TEMPLATE.format(
            intent_json=json.dumps(intent, ensure_ascii=False, indent=2),
            rules_json=json.dumps(rules, ensure_ascii=False, indent=2),
            search_plan_json=search_plan.model_dump_json(indent=2),
            products_json=json.dumps(products_json, ensure_ascii=False, indent=2),
        )

        try:
            result: Any = await self.client.generate_structured(
                prompt=prompt,
                response_schema=FinalOutfitResult,
                system_instruction=_SYSTEM,
                temperature=0.35,
            )
            if isinstance(result, FinalOutfitResult):
                return result
            if isinstance(result, dict):
                return FinalOutfitResult(**result)
        except Exception:
            pass

        return _fallback_result(search_plan, candidates_by_target)


def _candidate_summary(candidate: ProductSearchCandidate) -> dict[str, Any]:
    meta = candidate.light_metadata
    return {
        "product_id": candidate.product_id,
        "target": candidate.target,
        "name": meta.get("name"),
        "description": meta.get("description"),
        "color": meta.get("color", []),
        "size": meta.get("size", []),
        "material": meta.get("material"),
        "price": meta.get("price"),
        "stock_status": meta.get("stock_status"),
        "tags": meta.get("tags", []),
        "retrieval_score": candidate.retrieval_score,
        "matched_text": candidate.matched_text,
        "sources": candidate.sources,
    }


def _fallback_result(
    search_plan: OutfitSearchPlan,
    candidates_by_target: dict[str, list[ProductSearchCandidate]],
) -> FinalOutfitResult:
    items: list[FinalOutfitItem] = []
    for target in search_plan.targets:
        candidates = candidates_by_target.get(target.item, [])
        if not candidates and target.required:
            continue
        if candidates:
            items.append(FinalOutfitItem(
                target=target.item,
                product_id=candidates[0].product_id,
                reason=f"Phù hợp với vai trò {target.role} trong outfit.",
            ))

    return FinalOutfitResult(
        summary="Mình chọn các sản phẩm phù hợp nhất từ kết quả tìm kiếm hiện có.",
        outfit_plan=[
            FinalDayOutfit(
                day=1,
                context="Outfit được tạo từ kết quả hybrid search.",
                items=items,
                styling_reason="Các món được chọn theo target trong search plan và tránh item bị loại trừ.",
                constraint_check={"fallback_used": True},
            )
        ] if items else [],
    )
