"""
Initialize Neo4j from scripts/seeds/knowledge_graph.json.

Usage:
    uv run python scripts/init_graphdb.py --clear
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_stylist.config import settings
from ai_stylist.db.neo4j import close_driver, get_driver


_RELATION_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _load_kg(path_value: str) -> dict[str, Any]:
    path = Path(path_value)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path_value} must contain a JSON object")
    return data


async def _create_constraints(session) -> None:
    await session.run("CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE")
    await session.run("CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (r:Rule) REQUIRE r.id IS UNIQUE")


async def _clear_graph(session) -> None:
    await session.run("MATCH (node) DETACH DELETE node")


async def _upsert_concepts(session, concepts: list[dict[str, Any]]) -> None:
    query = """
    UNWIND $concepts AS concept
    MERGE (c:Concept {id: concept.id})
    SET c.name = concept.name,
        c.type = concept.type,
        c.description = concept.description,
        c.aliases = coalesce(concept.aliases, [])
    """
    await session.run(query, concepts=concepts)


async def _upsert_edges(session, edges: list[dict[str, Any]]) -> None:
    for edge in edges:
        relation = str(edge["relation"]).upper()
        if not _RELATION_RE.fullmatch(relation):
            raise ValueError(f"Invalid relation type: {relation}")

        query = f"""
        MATCH (source:Concept {{id: $source_id}})
        MATCH (target:Concept {{id: $target_id}})
        MERGE (source)-[rel:{relation}]->(target)
        SET rel.weight = $weight,
            rel.explanation = $explanation
        """
        await session.run(
            query,
            source_id=edge["source"],
            target_id=edge["target"],
            weight=float(edge.get("weight", 1.0)),
            explanation=edge.get("explanation"),
        )


async def _upsert_rules(session, rules: list[dict[str, Any]]) -> None:
    query = """
    UNWIND $rules AS rule
    MATCH (concept:Concept {id: rule.concept_id})
    MERGE (r:Rule {id: rule.id})
    SET r.type = rule.type,
        r.priority = rule.priority,
        r.payload_json = rule.payload_json
    MERGE (concept)-[:HAS_RULE]->(r)
    """
    rows = [
        {
            "id": rule["id"],
            "concept_id": rule["concept_id"],
            "type": rule["type"],
            "priority": float(rule.get("priority", 1.0)),
            "payload_json": json.dumps(rule.get("payload", {}), ensure_ascii=False),
        }
        for rule in rules
    ]
    await session.run(query, rules=rows)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=settings.kg_seed_path)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    kg = _load_kg(args.seed)
    concepts = kg.get("concepts", [])
    edges = kg.get("edges", [])
    rules = kg.get("rules", [])
    if not concepts:
        raise ValueError(f"No concepts found in {args.seed}")

    driver = await get_driver()
    async with driver.session() as session:
        await _create_constraints(session)
        if args.clear:
            await _clear_graph(session)
            await _create_constraints(session)
        await _upsert_concepts(session, concepts)
        await _upsert_edges(session, edges)
        await _upsert_rules(session, rules)

    await close_driver()
    print(
        "Initialized Neo4j graph with "
        f"{len(concepts)} concept(s), {len(edges)} edge(s), {len(rules)} rule(s)."
    )


if __name__ == "__main__":
    asyncio.run(main())
