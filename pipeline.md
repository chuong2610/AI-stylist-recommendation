# Current Pipeline

This document describes the current runtime pipeline. The older Postgres concept tables and pgvector concept search are no longer part of the active flow.

## Chat Pipeline

1. `POST /api/v1/sessions/{session_id}/messages` receives the user message.
2. `AgentService` loads the session and saves the user message.
3. LangGraph runs the ReAct agent with the available tools.
4. The agent chooses one or more tools:
   - `recommend_outfit` for full outfit planning.
   - `search_products` for direct product search.
   - `get_fashion_knowledge` for style/body/occasion rule lookup.
   - Memory tools for profile and outfit history.
5. `AgentService` extracts structured tool results when available.
6. The assistant message and extracted result are saved to Postgres.
7. The API returns the assistant text plus optional structured recommendation/product-search payload.

## Outfit Recommendation Pipeline

Input:

- `ExtractedIntent`
- original user message
- optional `budget_max`

Steps:

1. `EmbeddingService.resolve_from_intent`
   - Reads concept embeddings from `.cache/concept_embeddings.json`.
   - Embeddings are initialized from `scripts/seeds/knowledge_graph.json`.
   - Resolves intent fields such as style, occasion, body type, modesty, and constraints to concept IDs.
   - Resolves by expected concept type where the intent field implies a type.

2. `KnowledgeGraphService.get_rules`
   - Uses resolved concept IDs to query Neo4j.
   - Reads concept rules, preferred items, avoided items, colors, targets, exclusions, and pairings.
   - Output is normalized into a dict for LLM prompts.

3. `SearchTermGenerator.generate`
   - Uses intent plus KG rules.
   - Produces target-specific search terms such as `top`, `bottom`, `dress`, `shoes`, `bag`, or `accessory`.
   - KG influences terms and constraints, but does not directly pick final product IDs.

4. `HybridProductRetriever.search`
   - Searches Qdrant product vectors for semantic matches.
   - Applies Qdrant payload filters for `category` and `price` when available.
   - Also calls Product Service text search.
   - Merges vector and text candidates by product ID.
   - Output is `dict[target, list[ProductSearchCandidate]]`.

5. `FinalResponseGenerator.generate`
   - Uses intent, KG rules, generated search terms, and product candidates.
   - Decides the final outfit items.
   - Writes item reasons, styling tips, styling reasons, and constraint checks.

6. `ProductServiceClient.batch_fetch`
   - Fetches full product data for selected IDs.
   - The local seed fallback is used when the external Product Service is not reachable.

7. `RecommendationPipeline._format_outfit_plan`
   - Joins final LLM-selected item IDs with fetched product details.
   - Computes total price.
   - Returns API-ready outfit data.

Output:

- `summary`
- `outfit_plan`
- `resolved_concepts`
- debug metadata:
  - generated search terms
  - candidate count per target
  - selected product IDs
  - fetched product count

## Direct Product Search Pipeline

Tool: `search_products`

Input:

- `query`
- optional `target`
- optional `limit`
- optional `price_min`
- optional `price_max`

Steps:

1. The tool wraps the query into one `TargetSearchTerms` object.
2. `HybridProductRetriever.search` searches Qdrant and Product Service.
3. Qdrant filters by:
   - `category` from target mapping
   - `price >= price_min`
   - `price <= price_max`
4. Product Service/text candidates are post-filtered by price and target category.
5. Matching product IDs are hydrated by `ProductServiceClient.batch_fetch`.
6. The tool returns product details and retrieval scores.

Output:

- `query`
- `target`
- `price_filter`
- `products`

Each product contains ID, name, description, category, brand, colors, sizes, material, price, URLs, stock/rating metadata, matched text, retrieval score, and source flags.

## Knowledge Graph Data

Source file:

- `scripts/seeds/knowledge_graph.json`

Runtime stores:

- `.cache/concept_embeddings.json` for semantic concept resolution.
- Neo4j for graph traversal and rule lookup.

Current KG content:

- concepts: style, body type, occasion, modesty, color, item type, material, constraint, and related fashion concepts.
- aliases: alternate terms used to resolve user language to a concept.
- edges: concept relationships such as preferred item, avoided item, pairing, color, material, or target relation.
- rules: human-readable styling guidance attached to concepts.

Current non-goals:

- No active SQL `Concept`, `ConceptAlias`, `ConceptEdge`, or `ConceptRule` tables.
- No active pgvector concept search.
- No final product decision made by KG alone. KG narrows and guides the prompt; final outfit item selection is done by the LLM from retrieved product candidates.

## Product Vector Index

Source file:

- `scripts/seeds/products.json`

Runtime store:

- Qdrant collection configured in settings.

Indexed vector text includes product-facing searchable text such as name, category, description, brand, material, color, style tags, occasions, and search keywords.

Payload fields used by filters include:

- `product_id`
- `name`
- `category`
- `price`

`scripts/init_qdrant.py --recreate` should be run when product seed data, indexed text, payload fields, or embeddings change.
