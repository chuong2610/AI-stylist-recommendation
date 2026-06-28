import json
from typing import Any

from pydantic import BaseModel, Field

from ai_stylist.services.llm.gemini_client import GeminiClient


class TargetSearchTerms(BaseModel):
    item: str
    display_name: str
    terms: list[str] = Field(default_factory=list)


class SearchTermsResult(BaseModel):
    search_terms: list[TargetSearchTerms] = Field(default_factory=list)


_SYSTEM = (
    "You are a fashion product search query generator. "
    "Given the user's original message, structured intent, and fashion knowledge graph rules, "
    "decide which product groups should be searched and generate concrete Vietnamese product "
    "search phrases that resemble real product titles. "
    "The knowledge graph is the source of fashion constraints; the user's message is the source "
    "of what kind of outfit or main item is needed."
)

_PROMPT_TEMPLATE = """User intent:
{intent_json}

Fashion knowledge graph rules:
{rules_json}

Build the product search targets directly from the message, intent, and KG rules.

Rules:
- If request_mode is outfit_with_main_item, include the requested main item and compatible support items justified by the KG/message.
- If request_mode is complete_outfit, include enough product groups to form a coherent outfit.
- Respect KG avoided_item_types, excluded_items, and pairing_rules.
- Do not include conflicting items.
- Use `item` as a short stable target key, for example dress, top, bottom, shoes, bag, accessory.
- Use `display_name` as a readable item name.
- For each target, generate 2-4 short Vietnamese product search phrases.
- Return JSON matching the schema."""


class SearchTermGenerator:
    """
    Turns ExtractedIntent + Knowledge Graph rules directly into target-specific
    product search phrases for hybrid retrieval.
    """

    def __init__(self, client: GeminiClient):
        self.client = client

    async def generate(
        self,
        intent: dict[str, Any],
        rules: dict[str, Any],
    ) -> SearchTermsResult:
        prompt = _PROMPT_TEMPLATE.format(
            intent_json=json.dumps(intent, ensure_ascii=False, indent=2),
            rules_json=json.dumps(rules, ensure_ascii=False, indent=2),
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
            if isinstance(result["search_terms"], dict):
                return SearchTermsResult(search_terms=[
                    TargetSearchTerms(item=item, display_name=item, terms=terms)
                    for item, terms in result["search_terms"].items()
                ])
            return SearchTermsResult(**result)

        raise ValueError("SearchTermGenerator returned no search terms")
