import inspect
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from ai_stylist.config import settings


def _strip_additional_properties(schema: dict) -> None:
    """Remove additionalProperties from a JSON schema dict in-place.

    The Gemini Developer API (free tier) doesn't support additionalProperties.
    This includes both `false` (strict Pydantic object) and typed dicts like
    `{"type": "boolean"}` (generated for dict[str, bool] fields).
    """
    schema.pop("additionalProperties", None)
    for v in schema.get("properties", {}).values():
        if isinstance(v, dict):
            _strip_additional_properties(v)
    for v in schema.get("$defs", {}).values():
        if isinstance(v, dict):
            _strip_additional_properties(v)
    if isinstance(schema.get("items"), dict):
        _strip_additional_properties(schema["items"])
    for sub in schema.get("anyOf", []):
        if isinstance(sub, dict):
            _strip_additional_properties(sub)
    for sub in schema.get("allOf", []):
        if isinstance(sub, dict):
            _strip_additional_properties(sub)


class GeminiClient:
    def __init__(self):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns one float vector per input text."""
        import asyncio

        # Limit concurrent requests to avoid hitting free-tier rate limits (15 RPM)
        sem = asyncio.Semaphore(5)

        async def _one(text: str) -> list[float]:
            async with sem:
                response = await self._client.aio.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=text,
                )
                return list(response.embeddings[0].values)

        return await asyncio.gather(*[_one(t) for t in texts])

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Any,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> Any:
        """Generate JSON-structured output validated against response_schema.

        Strips additionalProperties from Pydantic schemas before sending to the
        Gemini Developer API, which rejects them in non-Enterprise mode.
        """
        pydantic_cls = None
        api_schema: Any = response_schema

        if inspect.isclass(response_schema) and issubclass(response_schema, BaseModel):
            pydantic_cls = response_schema
            schema_dict = response_schema.model_json_schema()
            _strip_additional_properties(schema_dict)
            api_schema = schema_dict

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=api_schema,
            temperature=temperature,
            max_output_tokens=8192,
        )
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        if pydantic_cls is not None:
            return pydantic_cls.model_validate_json(response.text)
        return response.parsed
