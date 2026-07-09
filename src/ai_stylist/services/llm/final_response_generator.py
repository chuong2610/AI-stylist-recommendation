import json
from typing import Any

from pydantic import BaseModel, Field

from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.llm.search_term_generator import SearchTermsResult
from ai_stylist.services.product.hybrid_retriever import ProductSearchCandidate


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
    "Use the user's message, intent, and knowledge graph rules to choose items that work together. "
    "Do not invent product IDs. Do not include items that conflict with KG rules. "
    "If a target has no useful product, skip it or explain the gap clearly. "
    "Use body wording carefully: for male users with a solid or stocky build, say 'solid build', "
    "'stocky build', or Vietnamese equivalents like 'dáng chắc/đậm người'. Do not use 'curvy' "
    "for male users unless the user explicitly used that word."
)

_PROMPT_TEMPLATE = """Create the final outfit response.

User intent:
{intent_json}

Knowledge graph rules:
{rules_json}

Search terms that were used to retrieve products:
{search_terms_json}

Products by target (USE ONLY THESE PRODUCT IDS):
{products_json}

Return JSON matching the schema.
Use the user's request_mode to decide the shape:
- complete_outfit: choose enough items to form a coherent outfit.
- outfit_with_main_item: include the requested/main item when available, then choose compatible support items.
The outfit should be coherent as a whole, not simply the top scoring product from each target.
In summary, styling_reason, and item reasons, use the user's gender/body context wording from the intent and KG rules; avoid unsupported body labels."""


class FinalResponseGenerator:
    def __init__(self, client: GeminiClient):
        self.client = client

    async def generate(
        self,
        intent: dict[str, Any],
        rules: dict[str, Any],
        search_terms: SearchTermsResult,
        candidates_by_target: dict[str, list[ProductSearchCandidate]],
    ) -> FinalOutfitResult:
        products_json = {
            target: [_candidate_summary(candidate) for candidate in candidates]
            for target, candidates in candidates_by_target.items()
        }
        prompt = _PROMPT_TEMPLATE.format(
            intent_json=json.dumps(intent, ensure_ascii=False, indent=2),
            rules_json=json.dumps(rules, ensure_ascii=False, indent=2),
            search_terms_json=search_terms.model_dump_json(indent=2),
            products_json=json.dumps(products_json, ensure_ascii=False, indent=2),
        )

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

        raise ValueError("FinalResponseGenerator returned invalid output")


def _candidate_summary(candidate: ProductSearchCandidate) -> dict[str, Any]:
    meta = candidate.light_metadata
    return {
        "product_id": candidate.product_id,
        "target": candidate.target,
        "name": meta.get("name"),
        "description": meta.get("description"),
        "categories": meta.get("categories", []),
        "color": meta.get("color", []),
        "size": meta.get("size", []),
        "material": meta.get("material"),
        "base_price": meta.get("base_price"),
        "status": meta.get("status"),
        "tags": meta.get("tags", []),
        "retrieval_score": candidate.retrieval_score,
        "text_score": candidate.text_score,
        "vector_score": candidate.vector_score,
        "matched_text": candidate.matched_text,
        "sources": candidate.sources,
    }
