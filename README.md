# AI Stylist

AI Stylist is a FastAPI service for fashion chat, product search, and outfit recommendations. The current pipeline uses Gemini, a JSON-backed fashion concept seed, Neo4j for fashion rules, Qdrant for product vector search, and PostgreSQL for chat/session persistence.

## Runtime Pieces

- FastAPI API under `src/ai_stylist/main.py`
- LangGraph ReAct agent for chat messages
- Gemini for intent extraction, embeddings, search-term generation, and final outfit text
- Concept seed from `scripts/seeds/knowledge_graph.json`
- Local concept embedding cache at `.cache/concept_embeddings.json`
- Neo4j knowledge graph for concepts, aliases, edges, and rules
- Qdrant product vector index from `scripts/seeds/products.json`
- Product Service client with local seed fallback for product hydration/search
- PostgreSQL for sessions, messages, and LangGraph checkpoint/memory data

## Requirements

- Python 3.12+
- `uv`
- Docker and Docker Compose
- Gemini API key

## Environment

Create a local env file:

```powershell
Copy-Item .env.example .env
```

Set at least:

```env
GEMINI_API_KEY=your_key_here
DATABASE_URL=postgresql+asyncpg://stylist:stylist123@localhost:5432/ai_stylist
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=stylist123
QDRANT_URL=http://localhost:6333
```

## Start Infrastructure

```powershell
docker compose up -d
```

Services:

- API: `http://localhost:8000` after starting the app
- Postgres: `localhost:5432`
- Neo4j Browser: `http://localhost:7474`
- Qdrant: `http://localhost:6333`

## Initialize Data

Run these after infrastructure is healthy:

```powershell
uv run python scripts/init_concepts.py
uv run python scripts/init_graphdb.py --clear
uv run python scripts/init_qdrant.py --recreate
```

What they do:

- `init_concepts.py`: builds `.cache/concept_embeddings.json` from `knowledge_graph.json`
- `init_graphdb.py --clear`: recreates the Neo4j fashion KG from `knowledge_graph.json`
- `init_qdrant.py --recreate`: recreates product vectors from `products.json` and creates payload indexes for `price` and `category`

Re-run Qdrant init when product text, product price, product category, or embedding logic changes.

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
- `POST /api/v1/recommendations/outfit`

The chat API routes user messages through the LangGraph agent. The direct recommendation API runs the outfit pipeline without the chat tool loop.

## Agent Tools

- `recommend_outfit`: extracts intent, resolves concepts, reads KG rules, searches product candidates, and returns a full outfit
- `search_products`: searches real products by query with optional `target`, `price_min`, and `price_max`
- `get_fashion_knowledge`: resolves fashion terms and returns KG rules
- `save_user_style_profile`: stores user style preferences in LangGraph long-term memory
- `get_user_style_profile`: reads saved user style preferences
- `get_outfit_history`: reads prior outfit recommendations

## Current Data Flow

1. User message enters the chat API or direct recommendation API.
2. Intent is extracted by Gemini into a structured `ExtractedIntent`.
3. Concepts are resolved semantically from `.cache/concept_embeddings.json`.
4. Resolved concept IDs are used to read rules from Neo4j.
5. Gemini generates target-specific product search terms.
6. Qdrant vector search retrieves product candidates and can filter by `category` and `price`.
7. Product Service text search is merged with vector candidates.
8. Gemini selects final outfit items from candidates and writes reasons.
9. Product Service batch fetch hydrates selected product details.
10. API returns summary, outfit items, product URLs/images, and debug metadata.

## Useful Checks

```powershell
uv run python -m compileall src scripts
```

Search product tool smoke test:

```powershell
$env:PYTHONPATH='src'
uv run python -c "import asyncio; from ai_stylist.services.agent.tools import search_products; print(asyncio.run(search_products.ainvoke({'query':'ao so mi linen trang','target':'top','price_max':250000})))"
```
