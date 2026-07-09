"""
Shared fixtures for the real-stack recommendation pipeline tests.

These tests call the actual Gemini API, Neo4j knowledge graph, Qdrant, and
the Java product-service (no mocks) — see tests/test_recommendation_pipeline.py.
Results are collected as they run and, at session end, rendered into
tests/test_cases.xlsx (expected vs. actual) via generate_test_case_workbook.
"""
import asyncio
import json
import sys
from pathlib import Path

import pytest

if sys.platform == "win32":
    # ProactorEventLoop breaks the Neo4j async bolt driver (and psycopg3) when a
    # single driver/connection is reused across the test session; must be set
    # before any event loop is created. Mirrors the fix in ai_stylist.main.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
RESULTS_PATH = ARTIFACTS_DIR / "actual_results.json"

_results: dict[str, dict] = {}


@pytest.fixture
def record_result():
    """Test cases call this to attach their captured actual-output to the report."""
    def _record(case_id: str, data: dict) -> None:
        _results[case_id] = data
    return _record


def pytest_sessionfinish(session, exitstatus):
    if not _results:
        return
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(_results, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    try:
        from tests.generate_test_case_workbook import build_workbook
        build_workbook(actual_results=_results)
    except Exception as exc:  # pragma: no cover - reporting must never fail the test run
        print(f"[conftest] Failed to render tests/test_cases.xlsx: {exc}")
