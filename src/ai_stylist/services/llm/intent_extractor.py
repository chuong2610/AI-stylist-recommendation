from typing import Any

from pydantic import BaseModel

from ai_stylist.services.llm.gemini_client import GeminiClient


class Duration(BaseModel):
    days: int = 1
    nights: int = 0


class BodyContext(BaseModel):
    height_group: str | None = None
    body_shape: str | None = None


class RequiredOutput(BaseModel):
    type: str = "single_outfit"
    number_of_days: int = 1


class ExtractedIntent(BaseModel):
    intent: str  # outfit_recommendation | general_qa | style_advice
    request_mode: str | None = None  # complete_outfit | outfit_with_main_item
    gender: str | None = None  # male | female | nonbinary | null
    occasion: str | None = None
    destination: str | None = None
    duration: Duration = Duration()
    style_preferences: list[str] = []
    requested_items: list[str] = []
    body_context: BodyContext = BodyContext()
    modesty_level: str | None = None
    comfort_needs: list[str] = []
    avoid: list[str] = []
    budget_max: float | None = None
    required_output: RequiredOutput = RequiredOutput()
    raw_keywords: list[str] = []


_SYSTEM = (
    "You are a fashion intent parser. Extract structured information from the user's message. "
    "Set intent to 'outfit_recommendation' if the user asks for an outfit or clothing suggestions, "
    "and 'general_qa' for fashion questions or advice without product/outfit requests. "
    "Use request_mode='outfit_with_main_item' when the user asks to build an outfit around a "
    "mentioned item, for example 'lên outfit với váy'. Use request_mode='complete_outfit' when "
    "the user asks for a full outfit without specifying a main item. "
    "Only use complete_outfit or outfit_with_main_item in the outfit recommendation flow. "
    "Put natural item names from the user in requested_items, for example ['váy'], ['quần'], ['áo sơ mi']."
)

_PROMPT_TEMPLATE = """Extract fashion intent from this message:
"{message}"

Return JSON matching the schema.

Guidelines:
- requested_items are item names in the user's language, not broad system categories.
- "lên outfit với váy đi tiệc" => intent=outfit_recommendation, request_mode=outfit_with_main_item, requested_items=["váy"], occasion=party.
- "tìm váy đi tiệc" => request_mode=outfit_with_main_item, requested_items=["váy"].
- "gợi ý outfit đi tiệc" => request_mode=complete_outfit.
- Vietnamese destinations like Vũng Tàu, Nha Trang, Phú Quốc imply occasion=beach.
- If the user says nam/con trai/male/men, set gender=male. If the user says nữ/female/women, set gender=female.
- For modesty_level use: low | medium | medium_high | high.
- For height_group use: short_or_petite | average | tall."""


class IntentExtractor:
    def __init__(self, client: GeminiClient):
        self.client = client

    async def extract(self, message: str) -> ExtractedIntent:
        prompt = _PROMPT_TEMPLATE.format(message=message)
        result: Any = await self.client.generate_structured(
            prompt=prompt,
            response_schema=ExtractedIntent,
            system_instruction=_SYSTEM,
            temperature=0.1,
        )
        if isinstance(result, ExtractedIntent):
            return result
        return ExtractedIntent(**result) if isinstance(result, dict) else ExtractedIntent(intent="general_qa")

