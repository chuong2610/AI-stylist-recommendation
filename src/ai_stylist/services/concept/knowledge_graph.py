from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from ai_stylist.config import settings
from ai_stylist.db.neo4j import get_driver
from ai_stylist.services.concept.embedding_service import ResolvedConcept


@dataclass
class FashionRules:
    style_rules: list[dict[str, Any]] = field(default_factory=list)
    body_rules: list[dict[str, Any]] = field(default_factory=list)
    occasion_rules: list[dict[str, Any]] = field(default_factory=list)
    modesty_rules: list[dict[str, Any]] = field(default_factory=list)
    preferred_item_types: list[str] = field(default_factory=list)
    avoided_item_types: list[str] = field(default_factory=list)
    preferred_colors: list[str] = field(default_factory=list)


class KnowledgeGraphService:
    """
    Stage 4: queries Neo4j to get fashion rules from resolved concept IDs.
    """

    async def get_rules(self, resolved_concepts: list[ResolvedConcept]) -> FashionRules:
        concept_ids = [c.concept_id for c in resolved_concepts]
        rules = FashionRules()

        try:
            neo4j_rules = await self._query_neo4j(concept_ids)
            _merge_neo4j_into_rules(neo4j_rules, rules)
        except Exception:
            pass

        seed_terms = concept_ids + [c.input_term for c in resolved_concepts] + [c.concept_name for c in resolved_concepts]
        _merge_seed_rules(seed_terms, rules)
        return rules

    async def get_rules_for_terms(self, terms: list[str]) -> FashionRules:
        rules = FashionRules()
        _merge_seed_rules(terms, rules)
        return rules

    async def _query_neo4j(self, concept_ids: list[str]) -> list[dict]:
        driver = await get_driver()
        query = """
        UNWIND $concept_ids AS cid
        MATCH (c:Concept {id: cid})-[r]->(target:Concept)
        RETURN c.id AS source, c.type AS source_type,
               type(r) AS relation, r.weight AS weight,
               target.id AS target_id, target.name AS target_name, target.type AS target_type
        ORDER BY r.weight DESC
        """
        async with driver.session() as neo_session:
            result = await neo_session.run(query, concept_ids=concept_ids)
            return [dict(record) async for record in result]


def _merge_neo4j_into_rules(neo4j_rows: list[dict], rules: FashionRules) -> None:
    for row in neo4j_rows:
        relation = row.get("relation", "").upper()
        target_id = row.get("target_id", "")
        source_type = row.get("source_type", "")
        weight = row.get("weight", 1.0)
        entry = {"rule": f"{relation} {target_id}", "source_concept": row.get("source"), "weight": weight}

        if relation == "PREFERS":
            if "ITEM_" in target_id:
                item = target_id.replace("ITEM_", "").lower()
                if item not in rules.preferred_item_types:
                    rules.preferred_item_types.append(item)
            elif "COLOR_" in target_id:
                color = target_id.replace("COLOR_", "").lower()
                if color not in rules.preferred_colors:
                    rules.preferred_colors.append(color)
        elif relation == "AVOIDS":
            if "ITEM_" in target_id:
                item = target_id.replace("ITEM_", "").lower()
                if item not in rules.avoided_item_types:
                    rules.avoided_item_types.append(item)

        if source_type == "style":
            rules.style_rules.append(entry)
        elif source_type == "body_context":
            rules.body_rules.append(entry)
        elif source_type == "occasion":
            rules.occasion_rules.append(entry)
        elif source_type == "preference":
            rules.modesty_rules.append(entry)


def _merge_seed_rules(terms: list[str], rules: FashionRules) -> None:
    if not terms:
        return

    normalized_terms = {_normalize(t) for t in terms if t}
    for entry in _load_seed_rules():
        match_terms = {_normalize(t) for t in entry.get("match_terms", [])}
        if not normalized_terms.intersection(match_terms):
            continue

        _extend_unique(rules.preferred_item_types, entry.get("preferred_item_types", []))
        _extend_unique(rules.avoided_item_types, entry.get("avoided_item_types", []))
        _extend_unique(rules.preferred_colors, entry.get("preferred_colors", []))
        rules.style_rules.extend(entry.get("style_rules", []))
        rules.occasion_rules.extend(entry.get("occasion_rules", []))
        rules.body_rules.extend(entry.get("body_rules", []))
        rules.modesty_rules.extend(entry.get("modesty_rules", []))


def _load_seed_rules() -> list[dict[str, Any]]:
    path = Path(settings.kg_rules_seed_path)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _extend_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)
