from typing import Any

from ai_stylist.clients.product_client import ProductServiceClient
from ai_stylist.schemas.product import Product
from ai_stylist.services.concept.embedding_service import EmbeddingService
from ai_stylist.services.concept.knowledge_graph import KnowledgeGraphService
from ai_stylist.services.llm.final_response_generator import FinalOutfitResult, FinalResponseGenerator
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.llm.intent_extractor import ExtractedIntent
from ai_stylist.services.llm.search_term_generator import SearchTermGenerator
from ai_stylist.services.product.hybrid_retriever import HybridProductRetriever, ProductSearchCandidate


class RecommendationPipeline:
    """
    Outfit recommendation pipeline.

    Current shape:
      intent
      -> semantic concept resolution
      -> KG rules
      -> LLM-generated search terms per target item
      -> hybrid product retrieval (Qdrant semantic + Product Service text)
      -> final response generator chooses KG-compatible outfit
      -> Product Service batch fetch hydrates full product data
    """

    def __init__(self):
        self._gemini = GeminiClient()
        self._embedding_svc = EmbeddingService(self._gemini)
        self._term_generator = SearchTermGenerator(self._gemini)
        self._product_client = ProductServiceClient()
        self._retriever = HybridProductRetriever(self._gemini, self._product_client)
        self._response_generator = FinalResponseGenerator(self._gemini)

    async def run(
        self,
        intent: ExtractedIntent,
        original_message: str,
        budget_max: float | None = None,
    ) -> dict[str, Any]:
        resolved_concepts: list[str] = []
        rules_dict: dict[str, Any] = {}

        kg_svc = KnowledgeGraphService()
        resolved = await self._embedding_svc.resolve_from_intent(intent.model_dump())
        resolved_concepts = [r.concept_id for r in resolved]
        rules_dict = _rules_to_dict(await kg_svc.get_rules(resolved))

        intent_dict = intent.model_dump()
        intent_dict["budget_max"] = budget_max or intent.budget_max
        intent_dict["original_message"] = original_message

        search_terms_result = await self._term_generator.generate(
            intent=intent_dict,
            rules=rules_dict,
        )

        candidates_by_target = await self._retriever.search(search_terms_result.search_terms)

        plan_result = await self._response_generator.generate(
            intent=intent_dict,
            rules=rules_dict,
            search_terms=search_terms_result,
            candidates_by_target=candidates_by_target,
        )

        selected_ids = _selected_product_ids(plan_result)
        fetched_products = await self._product_client.batch_fetch(selected_ids)
        outfit_plan = self._format_outfit_plan(plan_result, fetched_products, candidates_by_target)

        return {
            "summary": plan_result.summary,
            "outfit_plan": outfit_plan,
            "resolved_concepts": resolved_concepts,
            "debug": {
                "search_terms": [terms.model_dump() for terms in search_terms_result.search_terms],
                "candidates_by_target": {k: len(v) for k, v in candidates_by_target.items()},
                "selected_product_ids": selected_ids,
                "fetched_products_total": len(fetched_products),
            },
        }

    def _format_outfit_plan(
        self,
        plan_result: FinalOutfitResult,
        products: list[Product],
        candidates_by_target: dict[str, list[ProductSearchCandidate]],
    ) -> list[dict]:
        product_map = {p.product_id: p for p in products}
        candidate_targets = {
            candidate.product_id: target
            for target, candidates in candidates_by_target.items()
            for candidate in candidates
        }

        result = []
        for day in plan_result.outfit_plan:
            items = []
            for item in day.items:
                product = product_map.get(item.product_id)
                if not product:
                    continue
                items.append({
                    "product_id": item.product_id,
                    "target": item.target or candidate_targets.get(item.product_id),
                    "name": product.name,
                    "categories": product.category_names,
                    "target_demographic": product.target_demographic,
                    "color": product.colors,
                    "size": product.sizes,
                    "material": product.material,
                    "base_price": product.base_price,
                    "image_url": product.primary_image_url,
                    "reason": item.reason,
                })

            total_price = sum(i["base_price"] for i in items if i["base_price"] is not None)
            result.append({
                "day": day.day,
                "context": day.context,
                "items": items,
                "total_price": total_price,
                "styling_tip": day.styling_tip,
                "styling_reason": day.styling_reason,
                "constraint_check": day.constraint_check,
            })
        return result


def _rules_to_dict(rules) -> dict[str, Any]:
    return {
        "style_rules": rules.style_rules,
        "body_rules": rules.body_rules,
        "occasion_rules": rules.occasion_rules,
        "modesty_rules": rules.modesty_rules,
        "preferred_item_types": rules.preferred_item_types,
        "avoided_item_types": rules.avoided_item_types,
        "preferred_colors": rules.preferred_colors,
        "preferred_targets": rules.preferred_targets,
        "excluded_items": rules.excluded_items,
        "pairing_rules": rules.pairing_rules,
    }


def _selected_product_ids(plan_result: FinalOutfitResult) -> list[str]:
    ids: list[str] = []
    for day in plan_result.outfit_plan:
        for item in day.items:
            if item.product_id not in ids:
                ids.append(item.product_id)
    return ids
