from dataclasses import dataclass, field
import json
from typing import Any

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
    preferred_targets: list[dict[str, Any]] = field(default_factory=list)
    excluded_items: list[dict[str, Any]] = field(default_factory=list)
    pairing_rules: list[dict[str, Any]] = field(default_factory=list)


class KnowledgeGraphService:
    """
    Queries Neo4j for fashion rules from semantic-resolved concept IDs.
    """

    async def get_rules(self, resolved_concepts: list[ResolvedConcept]) -> FashionRules:
        concept_ids = [c.concept_id for c in resolved_concepts]
        rules = FashionRules()
        if not concept_ids:
            return rules

        edges = await self._query_edges(concept_ids)
        rule_rows = await self._query_rules(concept_ids)
        _merge_edges_into_rules(edges, rules)
        _merge_rule_rows_into_rules(rule_rows, rules)
        return rules

    async def _query_edges(self, concept_ids: list[str]) -> list[dict[str, Any]]:
        driver = await get_driver()
        query = """
        MATCH (source:Concept)-[rel]->(target:Concept)
        WHERE source.id IN $concept_ids
        RETURN source.id AS source,
               source.type AS source_type,
               type(rel) AS relation,
               coalesce(rel.weight, 1.0) AS weight,
               rel.explanation AS explanation,
               target.id AS target_id,
               target.name AS target_name,
               target.type AS target_type
        ORDER BY weight DESC
        """
        async with driver.session() as neo_session:
            result = await neo_session.run(query, concept_ids=concept_ids)
            return [dict(record) async for record in result]

    async def _query_rules(self, concept_ids: list[str]) -> list[dict[str, Any]]:
        driver = await get_driver()
        query = """
        MATCH (concept:Concept)-[:HAS_RULE]->(rule:Rule)
        WHERE concept.id IN $concept_ids
        RETURN concept.id AS concept_id,
               concept.type AS source_type,
               rule.type AS rule_type,
               rule.payload_json AS payload_json,
               coalesce(rule.priority, 1.0) AS priority
        ORDER BY priority DESC
        """
        async with driver.session() as neo_session:
            result = await neo_session.run(query, concept_ids=concept_ids)
            return [dict(record) async for record in result]


def _merge_edges_into_rules(rows: list[dict[str, Any]], rules: FashionRules) -> None:
    for row in rows:
        relation = str(row.get("relation", "")).upper()
        target_id = str(row.get("target_id") or "")
        target_type = str(row.get("target_type") or "")
        weight = float(row.get("weight") or 1.0)
        entry = {
            "relation": relation.lower(),
            "target_id": target_id,
            "target_name": row.get("target_name"),
            "source_concept": row.get("source"),
            "weight": weight,
            "explanation": row.get("explanation"),
        }

        if relation == "PREFERS":
            _append_preferred_target(rules, target_id, target_type)
        elif relation == "AVOIDS":
            _append_avoided_target(rules, target_id, target_type)
        elif relation in {"PAIRS_WITH", "COMPATIBLE_WITH"}:
            _extend_unique_dicts(rules.pairing_rules, [{
                "from": row.get("source"),
                "to": target_id,
                "relation": relation.lower(),
                "weight": weight,
            }])

        _append_rule_entry_by_source_type(rules, str(row.get("source_type") or ""), entry)


def _merge_rule_rows_into_rules(rows: list[dict[str, Any]], rules: FashionRules) -> None:
    for row in rows:
        payload = _parse_payload(row.get("payload_json"))
        if not isinstance(payload, dict):
            continue

        payload = {
            **payload,
            "source_concept": row.get("concept_id"),
            "priority": float(row.get("priority") or 1.0),
        }
        rule_type = str(row.get("rule_type") or "").lower()
        source_type = str(row.get("source_type") or "")

        if rule_type == "style_rule":
            rules.style_rules.append(payload)
        elif rule_type == "body_rule":
            rules.body_rules.append(payload)
        elif rule_type == "occasion_rule":
            rules.occasion_rules.append(payload)
        elif rule_type == "modesty_rule":
            rules.modesty_rules.append(payload)
        elif rule_type == "preferred_item_types":
            _extend_unique(rules.preferred_item_types, _as_string_list(payload.get("items")))
        elif rule_type == "avoided_item_types":
            _extend_unique(rules.avoided_item_types, _as_string_list(payload.get("items")))
        elif rule_type == "preferred_colors":
            _extend_unique(rules.preferred_colors, _as_string_list(payload.get("colors")))
        elif rule_type == "preferred_targets":
            _extend_unique_dicts(rules.preferred_targets, _as_dict_list(payload.get("targets")))
        elif rule_type == "excluded_items":
            _extend_unique_dicts(rules.excluded_items, _as_dict_list(payload.get("items")))
        elif rule_type == "pairing_rules":
            _extend_unique_dicts(rules.pairing_rules, _as_dict_list(payload.get("rules")))
        else:
            _append_rule_entry_by_source_type(rules, source_type, payload)

        _extend_unique(rules.preferred_item_types, _as_string_list(payload.get("prefer_items")))
        _extend_unique(rules.preferred_item_types, _as_string_list(payload.get("preferred_item_types")))
        _extend_unique(rules.avoided_item_types, _as_string_list(payload.get("avoid_items")))
        _extend_unique(rules.avoided_item_types, _as_string_list(payload.get("avoided_item_types")))
        _extend_unique(rules.preferred_colors, _as_string_list(payload.get("color")))
        _extend_unique(rules.preferred_colors, _as_string_list(payload.get("colors")))


def _append_preferred_target(rules: FashionRules, target_id: str, target_type: str) -> None:
    if target_type == "item_type" or target_id.startswith("ITEM_"):
        item = _concept_key(target_id, "ITEM_")
        if item not in rules.preferred_item_types:
            rules.preferred_item_types.append(item)
    elif target_type == "color" or target_id.startswith("COLOR_"):
        color = _concept_key(target_id, "COLOR_")
        if color not in rules.preferred_colors:
            rules.preferred_colors.append(color)


def _append_avoided_target(rules: FashionRules, target_id: str, target_type: str) -> None:
    if target_type == "item_type" or target_id.startswith("ITEM_"):
        item = _concept_key(target_id, "ITEM_")
        if item not in rules.avoided_item_types:
            rules.avoided_item_types.append(item)


def _append_rule_entry_by_source_type(rules: FashionRules, source_type: str, entry: dict[str, Any]) -> None:
    if source_type == "style":
        rules.style_rules.append(entry)
    elif source_type == "body_context":
        rules.body_rules.append(entry)
    elif source_type == "occasion":
        rules.occasion_rules.append(entry)
    elif source_type == "preference":
        rules.modesty_rules.append(entry)


def _parse_payload(payload_json: Any) -> dict[str, Any] | None:
    if isinstance(payload_json, dict):
        return payload_json
    if not isinstance(payload_json, str):
        return None
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _concept_key(concept_id: str, prefix: str) -> str:
    return concept_id.removeprefix(prefix).lower()


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _extend_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _extend_unique_dicts(target: list[dict[str, Any]], values: list[dict[str, Any]]) -> None:
    for value in values:
        if value not in target:
            target.append(value)
