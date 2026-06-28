"""
LangChain tools cho ReAct agent.

Tool access:
  - DB session  → config["configurable"]["db"]      (per-request SQLAlchemy session for chat data)
  - user_id     → config["configurable"]["user_id"] (để namespace store)
  - Long-term store → InjectedStore() annotation   (LangGraph tự inject)
"""
import json
from datetime import datetime, timezone
from typing import Annotated, Any

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

from ai_stylist.services.llm.intent_extractor import IntentExtractor
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.llm.search_term_generator import TargetSearchTerms
from ai_stylist.services.recommendation.pipeline import RecommendationPipeline
from ai_stylist.services.concept.embedding_service import EmbeddingService
from ai_stylist.services.concept.knowledge_graph import KnowledgeGraphService
from ai_stylist.services.product.hybrid_retriever import HybridProductRetriever, ProductSearchCandidate
from ai_stylist.clients.product_client import ProductServiceClient


# ── helpers ──────────────────────────────────────────────────────────
def _get_user_id(config: RunnableConfig) -> str:
    return config.get("configurable", {}).get("user_id", "anonymous")


# ═══════════════════════════════════════════════════════════════════════
# SHORT-TERM tools (dùng DB session, không dùng store)
# ═══════════════════════════════════════════════════════════════════════

@tool
async def recommend_outfit(
    user_request: Annotated[str, "Toàn bộ yêu cầu outfit của user, bao gồm style, dịp, body type, v.v."],
    number_of_days: Annotated[int, "Số ngày cần outfit, mặc định 1"] = 1,
    budget_max: Annotated[float | None, "Ngân sách tối đa (VND), None nếu không giới hạn"] = None,
    config: RunnableConfig = None,
    store: Annotated[BaseStore, InjectedStore()] = None,
) -> str:
    """
    Tìm kiếm và gợi ý outfit hoàn chỉnh dựa trên yêu cầu của user.
    Sử dụng khi user hỏi về: gợi ý outfit, phối đồ cho dịp cụ thể,
    tìm đồ đi du lịch, đồ đi làm, đồ hẹn hò, v.v.
    Trả về outfit plan chi tiết kèm sản phẩm thật.
    """
    user_id = _get_user_id(config) if config else "anonymous"

    # Lấy user profile từ long-term store để enrich recommendation
    profile_ctx = ""
    if store:
        profile_item = await store.aget(("users", user_id, "profile"), "preferences")
        if profile_item:
            profile_ctx = f"\nUser profile from past interactions: {json.dumps(profile_item.value, ensure_ascii=False)}"

    gemini = GeminiClient()
    extractor = IntentExtractor(gemini)
    intent = await extractor.extract(user_request + profile_ctx)
    intent.required_output.number_of_days = number_of_days

    pipeline = RecommendationPipeline()
    result = await pipeline.run(intent, user_request, budget_max=budget_max)

    # Lưu outfit history vào long-term store
    if store and result.get("outfit_plan"):
        key = f"outfit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        await store.aput(
            ("users", user_id, "outfit_history"),
            key,
            {
                "request": user_request,
                "summary": result["summary"],
                "occasion": intent.occasion,
                "style": intent.style_preferences,
                "resolved_concepts": result.get("resolved_concepts", []),
                "number_of_days": number_of_days,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    output = {
        "summary": result["summary"],
        "resolved_concepts": result["resolved_concepts"],
        "outfits": [],
    }
    for day_plan in result.get("outfit_plan", []):
        output["outfits"].append({
            "day": day_plan["day"],
            "context": day_plan.get("context", ""),
            "styling_reason": day_plan.get("styling_reason", ""),
            "styling_tip": day_plan.get("styling_tip", ""),
            "items": [
                {
                    "name": item["name"],
                    "target": item.get("target"),
                    "category": item["category"],
                    "color": item.get("color", []),
                    "size": item.get("size", []),
                    "material": item.get("material"),
                    "price": item.get("price"),
                    "product_url": item.get("product_url"),
                    "image_url": item.get("image_url"),
                    "reason": item.get("reason"),
                }
                for item in day_plan.get("items", [])
            ],
        })

    return json.dumps(output, ensure_ascii=False, indent=2)


@tool
async def search_products(
    query: Annotated[str, "Specific product search query, e.g. 'white linen shirt'"],
    target: Annotated[str | None, "Product group: top, bottom, dress, shoes, bag, accessory; None if unknown"] = None,
    limit: Annotated[int, "Maximum number of products to return"] = 8,
    price_min: Annotated[float | None, "Minimum price in VND, None if no lower bound"] = None,
    price_max: Annotated[float | None, "Maximum price in VND, None if no upper bound"] = None,
    config: RunnableConfig = None,
    store: Annotated[BaseStore, InjectedStore()] = None,
) -> str:
    """
    Search real products for a specific query without creating a full outfit.
    Use when the user asks to find/view/buy a concrete product type or filter products by price.
    """
    capped_limit = max(1, min(limit, 20))
    target_key = (target or "product").strip() or "product"

    gemini = GeminiClient()
    product_client = ProductServiceClient()
    retriever = HybridProductRetriever(gemini, product_client)
    search_terms = [
        TargetSearchTerms(
            item=target_key,
            display_name=target_key,
            terms=[query],
        )
    ]
    candidates_by_target = await retriever.search(
        search_terms,
        limit_per_target=capped_limit,
        price_min=price_min,
        price_max=price_max,
    )
    candidates = candidates_by_target.get(target_key, [])
    product_ids = [candidate.product_id for candidate in candidates]
    products = await product_client.batch_fetch(product_ids)
    product_by_id = {product.product_id: product for product in products}

    output_products = []
    for candidate in candidates:
        product = product_by_id.get(candidate.product_id)
        if not product:
            continue
        output_products.append(_product_search_result(product, candidate))

    return json.dumps({
        "query": query,
        "target": target_key,
        "price_filter": {
            "min": price_min,
            "max": price_max,
        },
        "products": output_products[:capped_limit],
    }, ensure_ascii=False, indent=2)


@tool
async def get_fashion_knowledge(
    terms: Annotated[list[str], "Danh sách các khái niệm thời trang cần tra cứu, vd: ['style Hàn', 'người thấp', 'đi biển']"],
    config: RunnableConfig = None,
    store: Annotated[BaseStore, InjectedStore()] = None,
) -> str:
    """
    Tra cứu kiến thức thời trang từ Fashion Knowledge Graph.
    Sử dụng khi cần giải thích rules phối đồ, tư vấn style cho body type cụ thể,
    hoặc khi user hỏi về nguyên tắc thời trang mà không cần tìm sản phẩm.
    Ví dụ: 'người thấp nên mặc gì', 'màu nào hợp đi biển', 'Korean casual là gì'.
    """
    embedding_svc = EmbeddingService(GeminiClient())
    resolved = await embedding_svc.resolve_terms(terms)

    if not resolved:
        return json.dumps({"message": "Không tìm thấy khái niệm phù hợp", "terms": terms}, ensure_ascii=False)

    kg = KnowledgeGraphService()
    rules = await kg.get_rules(resolved)

    output = {
        "resolved_concepts": [
            {"term": r.input_term, "concept_id": r.concept_id, "type": r.concept_type}
            for r in resolved
        ],
        "style_rules": rules.style_rules[:5],
        "body_rules": rules.body_rules[:5],
        "occasion_rules": rules.occasion_rules[:5],
        "preferred_items": rules.preferred_item_types,
        "avoided_items": rules.avoided_item_types,
        "preferred_colors": rules.preferred_colors,
        "preferred_targets": rules.preferred_targets,
        "excluded_items": rules.excluded_items,
        "pairing_rules": rules.pairing_rules,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# LONG-TERM MEMORY tools (dùng InjectedStore)
# ═══════════════════════════════════════════════════════════════════════

@tool
async def save_user_style_profile(
    body_type: Annotated[str | None, "Dáng người: petite | average | tall | curvy | athletic"] = None,
    preferred_styles: Annotated[list[str] | None, "Styles yêu thích: ['korean_casual', 'minimalist', ...]"] = None,
    preferred_colors: Annotated[list[str] | None, "Màu sắc yêu thích: ['beige', 'white', 'pastel']"] = None,
    modesty_level: Annotated[str | None, "Mức độ kín đáo: low | medium | medium_high | high"] = None,
    budget_range: Annotated[str | None, "Ngân sách: budget | mid_range | premium"] = None,
    notes: Annotated[str | None, "Ghi chú thêm về sở thích của user"] = None,
    config: RunnableConfig = None,
    store: Annotated[BaseStore, InjectedStore()] = None,
) -> str:
    """
    Lưu thông tin style profile của user vào long-term memory.
    Gọi khi user cung cấp thông tin về bản thân như dáng người, màu sắc yêu thích,
    ngân sách, hoặc sở thích mặc đồ để cá nhân hóa gợi ý về sau.
    """
    if not store:
        return "Long-term memory không khả dụng."

    user_id = _get_user_id(config) if config else "anonymous"

    existing_item = await store.aget(("users", user_id, "profile"), "preferences")
    existing = existing_item.value if existing_item else {}

    updated: dict[str, Any] = {**existing}
    if body_type:
        updated["body_type"] = body_type
    if preferred_styles:
        updated["preferred_styles"] = preferred_styles
    if preferred_colors:
        updated["preferred_colors"] = preferred_colors
    if modesty_level:
        updated["modesty_level"] = modesty_level
    if budget_range:
        updated["budget_range"] = budget_range
    if notes:
        updated["notes"] = notes
    updated["updated_at"] = datetime.now(timezone.utc).isoformat()

    await store.aput(("users", user_id, "profile"), "preferences", updated)
    return f"Đã lưu profile: {json.dumps(updated, ensure_ascii=False)}"


@tool
async def get_user_style_profile(
    config: RunnableConfig = None,
    store: Annotated[BaseStore, InjectedStore()] = None,
) -> str:
    """
    Đọc thông tin style profile đã lưu của user từ long-term memory.
    Gọi khi cần biết sở thích, dáng người, ngân sách của user để tư vấn
    mà không cần hỏi lại từ đầu.
    """
    if not store:
        return "Long-term memory không khả dụng."

    user_id = _get_user_id(config) if config else "anonymous"
    item = await store.aget(("users", user_id, "profile"), "preferences")

    if not item:
        return "Chưa có thông tin profile. Hỏi user để tìm hiểu thêm."

    return json.dumps(item.value, ensure_ascii=False, indent=2)


@tool
async def get_outfit_history(
    limit: Annotated[int, "Số outfit history muốn lấy, tối đa 10"] = 5,
    config: RunnableConfig = None,
    store: Annotated[BaseStore, InjectedStore()] = None,
) -> str:
    """
    Lấy lịch sử outfit đã gợi ý cho user từ long-term memory.
    Dùng khi user hỏi về những lần gợi ý trước, muốn tránh lặp lại,
    hoặc muốn xem lại outfit đã được gợi ý.
    """
    if not store:
        return "Long-term memory không khả dụng."

    user_id = _get_user_id(config) if config else "anonymous"
    items = await store.asearch(
        ("users", user_id, "outfit_history"),
        limit=min(limit, 10),
    )

    if not items:
        return "Chưa có lịch sử outfit nào được lưu."

    history = [item.value for item in items]
    return json.dumps(history, ensure_ascii=False, indent=2)


ALL_TOOLS = [
    recommend_outfit,
    search_products,
    get_fashion_knowledge,
    save_user_style_profile,
    get_user_style_profile,
    get_outfit_history,
]


def _product_search_result(product, candidate: ProductSearchCandidate) -> dict[str, Any]:
    return {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "brand": product.brand,
        "color": product.color,
        "size": product.size,
        "material": product.material,
        "price": product.price,
        "currency": product.currency,
        "stock_status": product.stock_status,
        "rating": product.rating,
        "review_count": product.review_count,
        "sales_count": product.sales_count,
        "image_url": product.image_url,
        "product_url": product.product_url,
        "target": candidate.target,
        "matched_text": candidate.matched_text,
        "retrieval_score": candidate.retrieval_score,
        "text_score": candidate.text_score,
        "vector_score": candidate.vector_score,
        "sources": candidate.sources,
    }
