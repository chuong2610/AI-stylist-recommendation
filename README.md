# AI Stylist

AI Stylist is a FastAPI service for fashion chat, product search, and outfit recommendations. The current pipeline uses Gemini, a JSON-backed fashion concept seed, Neo4j for fashion rules, Qdrant for concept and product vector search, and PostgreSQL for chat/session persistence.

## Runtime Pieces

- FastAPI API under `src/ai_stylist/main.py`
- LangGraph ReAct agent for chat messages
- Gemini for intent extraction, embeddings, search-term generation, and final outfit text
- Concept seed from `scripts/seeds/knowledge_graph.json`
- Qdrant concept vector index from `scripts/seeds/knowledge_graph.json`
- Neo4j knowledge graph for concepts, aliases, edges, and rules
- Qdrant product index from `scripts/seeds/products.json`: dense (Gemini embedding) + sparse (local BM25 via `fastembed`) vectors, fused server-side with RRF on every search
- Product Service client that calls the real Java `product-service` REST API (`GET /api/v1/products`, `/{id}`, `/api/v1/categories`) for product hydration/search and category-slug-based `slot` classification, falling back to the local seed when the service is unreachable
- PostgreSQL for sessions, messages, and LangGraph checkpoint/memory data

## Requirements

- Python 3.12+
- `uv`
- Docker and Docker Compose
- Gemini API key
- Firecrawl API key for blog URL ingestion

## Environment

Create a local env file:

```powershell
Copy-Item .env.example .env
```

Set at least:

```env
GEMINI_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5430
POSTGRES_DB=ai_stylist
POSTGRES_USER=stylist
POSTGRES_PASSWORD=stylist123
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
QDRANT_CONCEPT_COLLECTION=ai_stylist_concepts
QDRANT_PRODUCT_COLLECTION=ai_stylist_products
PRODUCT_SERVICE_BASE_URL=http://localhost:8083
```

## Start Infrastructure

Neo4j, Qdrant, and product-service are **not** started by this repo — they're the Java BE's
shared containers. Start those first, from the BE repo:

```powershell
docker compose -f docker-compose.infra.yml up -d
```

Then start this repo's own Postgres (chat sessions/messages only — a separate DB from Java's,
remapped to host port 5430 to avoid colliding with the Java stack's postgres on 5432):

```powershell
docker compose up -d
```

Services:

- API: `http://localhost:8000` after starting the app
- Postgres (this repo): `localhost:5430`
- Neo4j Browser (Java BE stack): `http://localhost:7474`
- Qdrant (Java BE stack): `http://localhost:6333`

## Initialize Data

Run these after infrastructure is healthy:

```powershell
uv run python scripts/init_concepts.py
uv run python scripts/init_graphdb.py --clear
uv run python scripts/init_qdrant.py --recreate
```

What they do:

- `init_concepts.py`: recreates the Qdrant concept collection from `knowledge_graph.json`
- `init_graphdb.py --clear`: recreates the Neo4j fashion KG from `knowledge_graph.json`
- `init_qdrant.py --recreate`: recreates the product collection (dense + BM25 sparse vectors) from `products.json` and creates payload indexes for `base_price` and `slot`. First run downloads the local `Qdrant/bm25` sparse-encoder model via `fastembed` (cached afterward, no LLM call).

Re-run concept init when concept text or aliases change. Re-run product Qdrant init when product text, price, category, or embedding logic changes. This is a breaking schema change if the collection predates the dense+sparse split — an old single-vector collection can't be upserted into without `--recreate`.

Product data (`scripts/seeds/products.json`) mirrors the real Java `product-service` catalog (50 products, `SM-PRD-001`..`050`) — see `src/ai_stylist/clients/product_client.py` for how it's fetched from the live service (with this seed as fallback) and `scripts/seeds/knowledge_graph.json` for the matching fashion rules.

## Run API

```powershell
uv run python scripts/serve.py
```

Alternative:

```powershell
uv run uvicorn ai_stylist.main:app --reload
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Main APIs

- `POST /api/v1/sessions`
- `POST /api/v1/sessions/{session_id}/messages`
- `POST /api/v1/knowledge/ingest`

The chat API routes user messages through the LangGraph agent, which calls the outfit recommendation pipeline as a tool (`recommend_outfit`, see Agent Tools below). There is no standalone recommendation endpoint outside the chat flow.

## Knowledge Ingestion API

Use this endpoint to ingest fashion blog text or blog URLs into a Postgres review draft. Blog URLs are scraped through Firecrawl and require `FIRECRAWL_API_KEY`. It does not write to Neo4j until the user approves the draft.

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/knowledge/ingest `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{
    "user_id": "demo-user",
    "title": "Old money basics",
    "texts": ["Phong cách old money ưu tiên blazer, sơ mi, quần âu và màu trung tính."],
    "urls": [],
    "locale": "vi-VN"
  }'
```

The service extracts a KG delta with `Concept`, fashion relations, and `Rule` rows, then stores the draft in `knowledge_sources`.

Approve a draft after review:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/knowledge/sources/{source_id}/approve -Method Post
```

Delete a draft or approved source:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/knowledge/sources/{source_id} -Method Delete
```

Approved sources are upserted into Neo4j and merged into the Qdrant concept collection. Deleting an approved source removes the KG rows tagged with that source and clears Qdrant concept vectors for concepts that no longer exist.

## Agent Tools

- `recommend_outfit`: extracts intent, resolves concepts, reads KG rules, searches product candidates, and returns a full outfit
- `search_products`: searches real products by query with optional `target`, `price_min`, and `price_max`
- `get_fashion_knowledge`: resolves fashion terms and returns KG rules
- `save_user_style_profile`: stores user style preferences in LangGraph long-term memory
- `get_user_style_profile`: reads saved user style preferences
- `get_outfit_history`: reads prior outfit recommendations

## Current Data Flow

1. User message enters the chat API.
2. Intent is extracted by Gemini into a structured `ExtractedIntent`.
3. Concepts are resolved semantically from the Qdrant concept collection.
4. Resolved concept IDs are used to read rules from Neo4j.
5. Gemini generates target-specific product search terms.
6. Qdrant retrieves product candidates via a single hybrid query (dense Gemini embedding + local BM25 sparse vector, fused with RRF), filtered by `slot` and `base_price`.
7. Product Service text search (substring match, no ranking of its own) is merged in as a secondary signal alongside the Qdrant candidates.
8. Gemini selects final outfit items from candidates and writes reasons.
9. Product Service batch fetch hydrates selected product details.
10. API returns summary, outfit items, images, and debug metadata.

## End-to-End Tests

`tests/` contains a pytest suite that exercises the real stack (Gemini + Neo4j + Qdrant + product-service, no mocks) across 16 recommendation/retrieval scenarios. Requires infrastructure running and seeded (see above).

```powershell
uv run pytest tests/ -v
```

Results (expected vs. actual per case) are rendered into `tests/test_cases.xlsx` automatically at the end of the run. See `tests/data/test_cases.py` for the test case matrix and `tests/test_recommendation_pipeline.py` for the assertions.

## Useful Checks

```powershell
uv run python -m compileall src scripts
```

Search product tool smoke test:

```powershell
$env:PYTHONPATH='src'
uv run python -c "import asyncio; from ai_stylist.services.agent.tools import search_products; print(asyncio.run(search_products.ainvoke({'query':'ao so mi linen trang','target':'top','price_max':250000})))"
```
