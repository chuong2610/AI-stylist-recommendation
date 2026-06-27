import json
from typing import Any

from pydantic import BaseModel, Field

from ai_stylist.services.llm.gemini_client import GeminiClient


class SearchTermsResult(BaseModel):
    search_terms: dict[str, list[str]] = Field(default_factory=dict)


_SYSTEM = (
    "You are a fashion product search query generator. "
    "Given the user's intent, fashion knowledge graph rules, and an item-level search plan, "
    "generate concrete Vietnamese product search phrases that resemble real product titles. "
    "Generate phrases only for targets in the search plan. Do not add category-default items."
)

_PROMPT_TEMPLATE = """User intent:
{intent_json}

Fashion knowledge graph rules:
{rules_json}

Item-level search plan:
{search_plan_json}

For each search target where search=true, generate 2-3 short Vietnamese search phrases.
Use the target item and context as the anchor. Use fashion rules only to enrich those item phrases.
Do not generate phrases for excluded items or for any item not present in the search plan.
Return JSON matching the schema, with one entry per target item."""


class SearchTermGenerator:
    """
    Stage 5: turns ExtractedIntent + Knowledge Graph rules + item-level
    search plan into target-specific phrases for hybrid retrieval.
    """

    def __init__(self, client: GeminiClient):
        self.client = client

    async def generate(
        self,
        intent: dict[str, Any],
        rules: dict[str, Any],
        search_plan: dict[str, Any],
    ) -> SearchTermsResult:
        prompt = _PROMPT_TEMPLATE.format(
            intent_json=json.dumps(intent, ensure_ascii=False, indent=2),
            rules_json=json.dumps(rules, ensure_ascii=False, indent=2),
            search_plan_json=json.dumps(search_plan, ensure_ascii=False, indent=2),
        )

        result: Any = await self.client.generate_structured(
            prompt=prompt,
            response_schema=SearchTermsResult,
            system_instruction=_SYSTEM,
            temperature=0.3,
        )

        if isinstance(result, SearchTermsResult) and result.search_terms:
            return result
        if isinstance(result, dict) and result.get("search_terms"):
            return SearchTermsResult(**result)

        targets = [
            target.get("item")
            for target in search_plan.get("targets", [])
            if target.get("search", True) and target.get("item")
        ]
        return SearchTermsResult(search_terms={item: [item] for item in targets})
