"""
End-to-end tests for the recommendation pipeline against the REAL stack:
Gemini (LLM + embeddings), Neo4j (knowledge graph), Qdrant (product vectors),
and the Java product-service (product DB). No mocks.

Requires, before running:
    uv run python scripts/init_graphdb.py --clear
    uv run python scripts/init_qdrant.py --recreate
and the product-service / Neo4j / Qdrant containers running locally.

Run with:
    uv run pytest tests/test_recommendation_pipeline.py -m e2e -v
Results are captured into tests/test_cases.xlsx (see conftest.py).
"""
import pytest

from ai_stylist.clients.product_client import ProductServiceClient
from ai_stylist.services.llm.gemini_client import GeminiClient
from ai_stylist.services.llm.intent_extractor import IntentExtractor
from ai_stylist.services.llm.search_term_generator import TargetSearchTerms
from ai_stylist.services.product.hybrid_retriever import HybridProductRetriever
from ai_stylist.services.recommendation.pipeline import RecommendationPipeline

from tests.data.test_cases import PIPELINE_TEST_CASES, RETRIEVAL_TEST_CASES

pytestmark = pytest.mark.e2e


def _assert(assertions: list[dict], name: str, passed: bool, detail: str = "") -> None:
    assertions.append({"name": name, "passed": bool(passed), "detail": detail})


def _check_required_roles(items: list[dict], required_roles, assertions: list[dict]) -> None:
    all_categories: set[str] = set()
    for item in items:
        all_categories.update(item.get("categories", []))
    for role in required_roles:
        hit = any(cat in all_categories for cat in role["any_of"])
        _assert(
            assertions,
            f"required_role:{role['role']}",
            hit,
            f"expected one of {role['any_of']} in {sorted(all_categories)}",
        )


def _check_forbidden_categories(items: list[dict], forbidden: list[str], assertions: list[dict]) -> None:
    if not forbidden:
        return
    all_categories: set[str] = set()
    for item in items:
        all_categories.update(item.get("categories", []))
    offenders = all_categories.intersection(forbidden)
    _assert(
        assertions,
        "forbidden_categories_absent",
        not offenders,
        f"forbidden categories present: {sorted(offenders)}" if offenders else "none present",
    )


def _check_demographics(items: list[dict], allowed: list[str], assertions: list[dict]) -> None:
    offenders = [
        item["product_id"] for item in items
        if item.get("target_demographic") not in allowed
    ]
    _assert(
        assertions,
        "demographics_allowed",
        not offenders,
        f"products outside {allowed}: {offenders}" if offenders else "all items within allowed demographics",
    )


def _check_dress_only(days: list[dict], expect_dress_only: bool, assertions: list[dict]) -> None:
    if not expect_dress_only:
        return
    for day in days:
        items = day.get("items", [])
        has_dress = any("Đầm" in item.get("categories", []) for item in items)
        separates = [
            item for item in items
            if "Đầm" not in item.get("categories", [])
        ]
        _assert(
            assertions,
            f"dress_only_day{day.get('day')}",
            has_dress and not separates,
            f"has_dress={has_dress}, separate_items={[i['name'] for i in separates]}",
        )


def _check_budget(days: list[dict], budget_max: float | None, assertions: list[dict]) -> None:
    if budget_max is None:
        return
    for day in days:
        total = day.get("total_price")
        _assert(
            assertions,
            f"budget_day{day.get('day')}",
            total is not None and total <= budget_max,
            f"total_price={total}, budget_max={budget_max}",
        )


def _check_min_days(days: list[dict], min_days: int, assertions: list[dict]) -> None:
    _assert(
        assertions,
        "min_days",
        len(days) >= min_days,
        f"got {len(days)} day(s), expected >= {min_days}",
    )


@pytest.mark.parametrize("case", PIPELINE_TEST_CASES, ids=[c["id"] for c in PIPELINE_TEST_CASES])
@pytest.mark.asyncio
async def test_recommendation_case(case, record_result):
    gemini = GeminiClient()
    extractor = IntentExtractor(gemini)
    intent = await extractor.extract(case["message"])
    intent.required_output.number_of_days = case["number_of_days"]

    pipeline = RecommendationPipeline()
    result = await pipeline.run(intent, case["message"], budget_max=case.get("budget_max"))

    days = result.get("outfit_plan", [])
    all_items = [item for day in days for item in day.get("items", [])]

    assertions: list[dict] = []
    _assert(assertions, "outfit_plan_non_empty", bool(days), f"{len(days)} day(s) returned")
    _check_min_days(days, case["min_days"], assertions)
    _check_required_roles(all_items, case["required_roles"], assertions)
    _check_forbidden_categories(all_items, case["forbidden_categories"], assertions)
    _check_demographics(all_items, case["allowed_demographics"], assertions)
    _check_dress_only(days, case["expect_dress_only"], assertions)
    _check_budget(days, case.get("budget_max"), assertions)

    passed = all(a["passed"] for a in assertions)
    record_result(case["id"], {
        "summary": result.get("summary", ""),
        "days": days,
        "assertions": assertions,
        "passed": passed,
    })

    failed = [a for a in assertions if not a["passed"]]
    assert not failed, "Failed assertions: " + "; ".join(f"{a['name']} ({a['detail']})" for a in failed)


@pytest.mark.parametrize("case", RETRIEVAL_TEST_CASES, ids=[c["id"] for c in RETRIEVAL_TEST_CASES])
@pytest.mark.asyncio
async def test_retrieval_case(case, record_result):
    gemini = GeminiClient()
    product_client = ProductServiceClient()
    retriever = HybridProductRetriever(gemini, product_client)

    search_terms = [TargetSearchTerms(item=case["target"], display_name=case["target"], terms=[case["query"]])]
    candidates_by_target = await retriever.search(search_terms, limit_per_target=8)
    candidates = candidates_by_target.get(case["target"], [])
    product_ids = [c.product_id for c in candidates]
    products = await product_client.batch_fetch(product_ids)

    hits = [
        {"product_id": p.product_id, "name": p.name, "categories": p.category_names}
        for p in products
    ]

    assertions: list[dict] = []
    _assert(assertions, "has_hits", bool(hits), f"{len(hits)} hit(s)")
    matched = any(
        cat in case["expected_category_any_of"]
        for hit in hits for cat in hit["categories"]
    )
    _assert(
        assertions,
        "expected_category_present",
        matched,
        f"expected one of {case['expected_category_any_of']} among hit categories",
    )
    all_real = all(h["product_id"] for h in hits)
    _assert(assertions, "products_resolved_from_real_db", all_real, "all hits hydrated via product-service/seed")

    passed = all(a["passed"] for a in assertions)
    record_result(case["id"], {
        "hits": hits,
        "assertions": assertions,
        "passed": passed,
    })

    failed = [a for a in assertions if not a["passed"]]
    assert not failed, "Failed assertions: " + "; ".join(f"{a['name']} ({a['detail']})" for a in failed)
