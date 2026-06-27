from pydantic import BaseModel, Field

from ai_stylist.services.llm.intent_extractor import ExtractedIntent


class OutfitSearchTarget(BaseModel):
    item: str
    role: str  # main | support | optional
    required: bool = True
    search: bool = True
    context: list[str] = Field(default_factory=list)


class OutfitSearchPlan(BaseModel):
    targets: list[OutfitSearchTarget] = Field(default_factory=list)
    excluded_items: list[str] = Field(default_factory=list)


class OutfitSearchPlanBuilder:
    """
    Builds item-level search targets for outfit recommendation.

    This replaces the old category-first `_required_categories()` step. The
    plan is item-first: categories may exist later as product metadata, but
    they do not decide what search terms are generated.
    """

    def build(self, intent: ExtractedIntent, rules: dict) -> OutfitSearchPlan:
        requested = _requested_items(intent)
        occasion = intent.occasion or intent.destination
        context = [v for v in [occasion, *intent.style_preferences] if v]

        if not requested:
            requested = _fallback_main_items(intent, rules)

        targets: list[OutfitSearchTarget] = []
        excluded: list[str] = []

        for item in requested:
            normalized = _normalize_item(item)
            if not normalized:
                continue
            if normalized not in [t.item for t in targets]:
                targets.append(OutfitSearchTarget(
                    item=normalized,
                    role="main",
                    required=True,
                    context=context,
                ))

            supports, item_excluded = _support_items_for_main(normalized, rules)
            excluded.extend(item_excluded)
            for support_item, required in supports:
                if support_item not in [t.item for t in targets]:
                    targets.append(OutfitSearchTarget(
                        item=support_item,
                        role="support" if required else "optional",
                        required=required,
                        context=[f"phối với {normalized}", *context],
                    ))

        return OutfitSearchPlan(
            targets=targets,
            excluded_items=_unique(excluded),
        )


def _requested_items(intent: ExtractedIntent) -> list[str]:
    if intent.requested_items:
        return intent.requested_items

    raw = " ".join(intent.raw_keywords).lower()
    message_terms = [
        ("áo sơ mi", ["áo sơ mi", "shirt"]),
        ("váy", ["váy", "đầm", "dress"]),
        ("quần", ["quần", "pants", "short"]),
        ("giày", ["giày", "sandal", "heels", "sneaker"]),
        ("phụ kiện", ["phụ kiện", "clutch", "túi", "bông tai"]),
    ]
    return [item for item, aliases in message_terms if any(alias in raw for alias in aliases)]


def _fallback_main_items(intent: ExtractedIntent, rules: dict) -> list[str]:
    preferred = " ".join(rules.get("preferred_item_types", [])).lower()
    if any(term in preferred for term in ("dress", "đầm", "váy")):
        return ["váy"]
    if intent.occasion and any(term in intent.occasion.lower() for term in ("party", "tiệc")):
        return ["váy"]
    return ["outfit"]


def _normalize_item(item: str) -> str:
    value = item.strip().lower()
    if not value:
        return ""
    if any(term in value for term in ("áo sơ mi", "shirt")):
        return "áo sơ mi"
    if any(term in value for term in ("váy", "đầm", "dress")):
        return "váy"
    if any(term in value for term in ("quần", "pants", "short")):
        return "quần"
    if any(term in value for term in ("giày", "sandal", "heels", "sneaker")):
        return "giày"
    if any(term in value for term in ("phụ kiện", "clutch", "túi", "bông tai", "earring")):
        return "phụ kiện"
    return value


def _support_items_for_main(item: str, rules: dict) -> tuple[list[tuple[str, bool]], list[str]]:
    preferred = [_normalize_item(v) for v in rules.get("preferred_item_types", [])]

    if item == "váy":
        supports = [("giày", True), ("phụ kiện", False)]
        if "phụ kiện" not in preferred and "giày" not in preferred:
            return supports, ["áo", "quần"]
        return supports, ["áo", "quần"]

    if item == "áo sơ mi":
        return [("quần", True), ("giày", False)], ["váy"]

    if item == "quần":
        return [("áo", True), ("giày", False)], ["váy"]

    return [], []


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
