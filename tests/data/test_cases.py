"""
Single source of truth for the recommendation-pipeline test case matrix.

Each case is checked against the real stack (Gemini + Neo4j knowledge graph +
Qdrant + Java product-service) — see tests/test_recommendation_pipeline.py.
tests/generate_test_case_workbook.py renders this data (plus captured actual
results) into tests/test_cases.xlsx.
"""
from typing import Any, TypedDict


class RequiredRole(TypedDict):
    role: str
    any_of: list[str]


class TestCase(TypedDict, total=False):
    id: str
    group: str
    message: str
    expected_gender: str | None
    expected_occasion_keywords: list[str]
    budget_max: float | None
    number_of_days: int
    required_roles: list[RequiredRole]
    forbidden_categories: list[str]
    allowed_demographics: list[str]
    expect_dress_only: bool
    min_days: int
    notes: str


PIPELINE_TEST_CASES: list[TestCase] = [
    {
        "id": "TC01",
        "group": "Office",
        "message": "Gợi ý outfit đi làm công sở cho nam, ngân sách dưới 1.3 triệu",
        "expected_gender": "male",
        "expected_occasion_keywords": ["công sở", "office"],
        "budget_max": 1_300_000,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo sơ mi", "Áo polo"]},
            {"role": "bottom", "any_of": ["Quần dài", "Quần kaki"]},
        ],
        "forbidden_categories": ["Áo hoodie", "Áo tank top", "Quần short", "Đầm", "Chân váy"],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Office wear for a male user must stay formal and within budget.",
    },
    {
        "id": "TC02",
        "group": "Office",
        "message": "Gợi ý outfit đi làm công sở cho nữ, cần chỉn chu lịch sự",
        "expected_gender": "female",
        "expected_occasion_keywords": ["công sở", "office"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo sơ mi", "Áo blouse"]},
            {"role": "bottom", "any_of": ["Quần dài", "Chân váy"]},
        ],
        "forbidden_categories": ["Áo hoodie", "Áo tank top", "Quần short"],
        "allowed_demographics": ["FEMALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Office wear for a female user: shirt/blouse + dress pants/skirt.",
    },
    {
        "id": "TC03",
        "group": "Sport",
        "message": "Gợi ý đồ tập gym cho nam, cần thoải mái vận động",
        "expected_gender": "male",
        "expected_occasion_keywords": ["thể thao", "gym", "sport"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun", "Áo tank top"]},
            {"role": "bottom", "any_of": ["Quần jogger", "Quần short"]},
        ],
        "forbidden_categories": ["Quần dài", "Áo sơ mi", "Đầm"],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Workout outfit should be breathable/casual, not office wear.",
    },
    {
        "id": "TC04",
        "group": "Sport",
        "message": "Gợi ý đồ tập yoga cho nữ",
        "expected_gender": "female",
        "expected_occasion_keywords": ["thể thao", "yoga", "sport"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo tank top", "Áo thun"]},
            {"role": "bottom", "any_of": ["Quần legging", "Quần jogger", "Quần short"]},
        ],
        "forbidden_categories": ["Quần dài", "Đầm"],
        "allowed_demographics": ["FEMALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Yoga outfit should favor leggings/tank top.",
    },
    {
        "id": "TC05",
        "group": "Homewear",
        "message": "Gợi ý đồ mặc ở nhà thoải mái, unisex cũng được",
        "expected_gender": None,
        "expected_occasion_keywords": ["mặc nhà", "ở nhà", "loungewear"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun", "Áo tank top"]},
            {"role": "bottom", "any_of": ["Quần jogger", "Quần short"]},
        ],
        "forbidden_categories": ["Quần dài", "Áo sơ mi", "Đầm"],
        "allowed_demographics": ["MALE", "FEMALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Home/loungewear should stay soft and relaxed; no tailored office pieces.",
    },
    {
        "id": "TC06",
        "group": "Daily",
        "message": "Gợi ý outfit đi chơi hằng ngày cho nam, phong cách basic dễ mặc",
        "expected_gender": "male",
        "expected_occasion_keywords": ["hằng ngày", "basic", "daily"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun", "Áo polo"]},
            {"role": "bottom", "any_of": ["Quần jeans", "Quần kaki"]},
        ],
        "forbidden_categories": ["Đầm", "Chân váy", "Áo blouse"],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Everyday casual male outfit: t-shirt/polo + jeans/kaki.",
    },
    {
        "id": "TC07",
        "group": "Daily",
        "message": "Gợi ý outfit đi chơi hằng ngày cho nữ, phong cách basic dễ mặc",
        "expected_gender": "female",
        "expected_occasion_keywords": ["hằng ngày", "basic", "daily"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun", "Áo polo", "Áo blouse"]},
            {"role": "bottom", "any_of": ["Quần jeans", "Chân váy", "Quần kaki"]},
        ],
        "forbidden_categories": [],
        "allowed_demographics": ["FEMALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Everyday casual female outfit.",
    },
    {
        "id": "TC08",
        "group": "Party",
        "message": "Gợi ý outfit đi tiệc sinh nhật cho nữ",
        "expected_gender": "female",
        "expected_occasion_keywords": ["tiệc", "party"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "dress", "any_of": ["Đầm"]},
        ],
        "forbidden_categories": [],
        "allowed_demographics": ["FEMALE", "UNISEX"],
        "expect_dress_only": True,
        "min_days": 1,
        "notes": "Party outfit should center on a dress, not separate top+bottom.",
    },
    {
        "id": "TC09",
        "group": "MainItem",
        "message": "Lên outfit với quần jeans cho nam",
        "expected_gender": "male",
        "expected_occasion_keywords": [],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "bottom", "any_of": ["Quần jeans"]},
        ],
        "forbidden_categories": ["Đầm", "Chân váy"],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "outfit_with_main_item around explicit 'quần jeans' must include a jeans product.",
    },
    {
        "id": "TC10",
        "group": "MainItem",
        "message": "Tìm đầm đi tiệc cho nữ",
        "expected_gender": "female",
        "expected_occasion_keywords": ["tiệc"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "dress", "any_of": ["Đầm"]},
        ],
        "forbidden_categories": [],
        "allowed_demographics": ["FEMALE", "UNISEX"],
        "expect_dress_only": True,
        "min_days": 1,
        "notes": "outfit_with_main_item around explicit 'đầm' must include a dress product.",
    },
    {
        "id": "TC11",
        "group": "Budget",
        "message": "Gợi ý áo thun và quần kaki cho nam, ngân sách dưới 900 nghìn",
        "expected_gender": "male",
        "expected_occasion_keywords": [],
        "budget_max": 900_000,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun"]},
            {"role": "bottom", "any_of": ["Quần kaki"]},
        ],
        "forbidden_categories": [],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Tight budget: total day price must stay under 900,000 VND.",
    },
    {
        "id": "TC12",
        "group": "Body",
        "message": "Nam 1m70 80kg, gợi ý outfit đi làm công sở form rộng thoải mái",
        "expected_gender": "male",
        "expected_occasion_keywords": ["công sở"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo sơ mi", "Áo polo"]},
            {"role": "bottom", "any_of": ["Quần dài", "Quần kaki"]},
        ],
        "forbidden_categories": ["Đầm", "Chân váy"],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Stocky male body context: summary/reason text must not use 'curvy' wording.",
    },
    {
        "id": "TC13",
        "group": "Body",
        "message": "Nữ hơi thấp, gợi ý outfit đi chơi hằng ngày",
        "expected_gender": "female",
        "expected_occasion_keywords": ["hằng ngày"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun", "Áo polo", "Áo blouse"]},
            {"role": "bottom", "any_of": ["Quần jeans", "Chân váy", "Quần kaki"]},
        ],
        "forbidden_categories": [],
        "allowed_demographics": ["FEMALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Petite female body context, daily casual outfit.",
    },
    {
        "id": "TC14",
        "group": "Modesty",
        "message": "Gợi ý outfit mặc nhà nhưng kín đáo, không mặc quần short hay áo tank top",
        "expected_gender": None,
        "expected_occasion_keywords": ["mặc nhà"],
        "budget_max": None,
        "number_of_days": 1,
        "required_roles": [
            {"role": "top", "any_of": ["Áo thun", "Áo hoodie", "Áo len"]},
            {"role": "bottom", "any_of": ["Quần jogger", "Quần jeans", "Quần kaki"]},
        ],
        "forbidden_categories": ["Quần short", "Áo tank top"],
        "allowed_demographics": ["MALE", "FEMALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 1,
        "notes": "Explicit modest request must exclude shorts and tank tops.",
    },
    {
        "id": "TC15",
        "group": "MultiDay",
        "message": "Gợi ý outfit đi làm công sở cho nam trong 2 ngày",
        "expected_gender": "male",
        "expected_occasion_keywords": ["công sở"],
        "budget_max": None,
        "number_of_days": 2,
        "required_roles": [
            {"role": "top", "any_of": ["Áo sơ mi", "Áo polo"]},
            {"role": "bottom", "any_of": ["Quần dài", "Quần kaki"]},
        ],
        "forbidden_categories": ["Đầm", "Chân váy"],
        "allowed_demographics": ["MALE", "UNISEX"],
        "expect_dress_only": False,
        "min_days": 2,
        "notes": "Multi-day request must return at least 2 day plans.",
    },
]


class RetrievalTestCase(TypedDict):
    id: str
    group: str
    query: str
    target: str
    expected_category_any_of: list[str]


RETRIEVAL_TEST_CASES: list[RetrievalTestCase] = [
    {
        "id": "TC16",
        "group": "SearchTool",
        "query": "Áo Polo nam",
        "target": "top",
        "expected_category_any_of": ["Áo polo"],
    },
]


def all_case_ids() -> list[str]:
    return [c["id"] for c in PIPELINE_TEST_CASES] + [c["id"] for c in RETRIEVAL_TEST_CASES]
