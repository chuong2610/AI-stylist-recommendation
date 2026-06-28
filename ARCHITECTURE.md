# AI Stylist — Architecture & Source Code Documentation

> Version 0.2.0 · LangGraph ReAct Agent + Outfit Recommendation Pipeline

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Database Schema](#4-database-schema)
5. [Memory Architecture](#5-memory-architecture)
6. [Source Code — File by File](#6-source-code--file-by-file)
7. [API Endpoints](#7-api-endpoints)
8. [Flow: Startup](#8-flow-startup)
9. [Flow: Chat Message — General Q&A](#9-flow-chat-message--general-qa)
10. [Flow: Chat Message — Outfit Recommendation](#10-flow-chat-message--outfit-recommendation)
11. [Flow: Long-term Memory Read/Write](#11-flow-long-term-memory-readwrite)
12. [Recommendation Pipeline — Stage by Stage](#12-recommendation-pipeline--stage-by-stage)
13. [Data Flow Diagram](#13-data-flow-diagram)

---

## 1. Overview

AI Stylist là service chatbot thời trang sử dụng **LangGraph ReAct agent** với **Gemini** làm LLM. Agent tự suy luận khi nào cần gọi tool (tìm outfit, tra cứu kiến thức thời trang, đọc/ghi profile) và khi nào chỉ cần chat thường — không có flow cố định.

**Hai chức năng chính:**
- **Chatbot hỏi đáp**: tư vấn thời trang, giải thích rule phối đồ, câu hỏi tự do
- **Outfit Recommendation**: chạy pipeline 10 stage để tìm outfit thật từ Product Service

---

## 2. Tech Stack

| Layer | Technology | Mục đích |
|---|---|---|
| Language | Python 3.12 | — |
| Package manager | `uv` | — |
| Web framework | FastAPI + uvicorn | Async API server |
| LLM | Google Gemini (`gemini-2.0-flash`) | Agent reasoning + structured output |
| Agent framework | LangGraph `create_react_agent` | ReAct loop, memory management |
| LLM SDK | `langchain-google-genai` | LangChain wrapper cho Gemini |
| Short-term memory | `AsyncPostgresSaver` (psycopg3) | Conversation state per session |
| Long-term memory | `AsyncPostgresStore` (psycopg3) | User profile, outfit history cross-session |
| Relational DB | PostgreSQL (asyncpg + SQLAlchemy 2.0) | Sessions, messages, knowledge graph |
| Graph DB | Neo4j Community (Docker) | Fashion Knowledge Graph traversal |
| HTTP client | `httpx` async | Gọi external Product Service |
| Schema validation | Pydantic v2 | Request/response + structured LLM output |
| Config | `pydantic-settings` | Đọc `.env` |

---

## 3. Project Structure

```
ai_stylist/
├── .env                          # Biến môi trường (không commit)
├── .env.example                  # Template
├── .python-version               # Python 3.12
├── pyproject.toml                # Dependencies + build config
├── docker-compose.yml            # PostgreSQL + Neo4j
├── ARCHITECTURE.md               # File này
│
├── scripts/
│   ├── init_concepts.py          # Sync KG JSON concepts → PostgreSQL semantic store
│   ├── init_graphdb.py           # Sync KG JSON → Neo4j
│   ├── init_qdrant.py            # Sync product JSON → Qdrant
│   └── seeds/                    # products.json + knowledge_graph.json
│
└── src/ai_stylist/
    ├── main.py                   # FastAPI app + lifespan
    ├── config.py                 # Settings từ .env
    │
    ├── db/
    │   ├── postgres.py           # SQLAlchemy async engine + get_db()
    │   └── neo4j.py              # Neo4j async driver singleton
    │
    ├── models/                   # SQLAlchemy ORM (6 bảng)
    │   ├── session.py            # ChatSession
    │   ├── message.py            # Message
    │   └── concept.py            # Concept, ConceptAlias, ConceptEdge, ConceptRule
    │
    ├── schemas/                  # Pydantic models
    │   ├── chat.py               # SessionCreate/Response, MessageCreate/Response, ChatResponse
    │   ├── recommendation.py     # OutfitRequest, OutfitItem, DayOutfit, OutfitRecommendationResponse
    │   └── product.py            # Product, ProductSearchQuery, SemanticSearchQuery
    │
    ├── repositories/             # Data access layer (async SQLAlchemy)
    │   ├── session_repo.py       # CRUD chat_sessions
    │   ├── message_repo.py       # CRUD messages
    │   └── concept_repo.py       # Read concepts, aliases, edges, rules
    │
    ├── clients/
    │   └── product_client.py     # HTTP client → Product Service metadata hydration
    │
    ├── services/
    │   │
    │   ├── agent/                # LangGraph agent layer
    │   │   ├── tools.py          # 5 LangChain tools (recommend, knowledge, memory CRUD)
    │   │   ├── graph.py          # create_react_agent() với checkpointer + store
    │   │   ├── checkpointer.py   # AsyncPostgresSaver setup (short-term memory)
    │   │   └── store.py          # AsyncPostgresStore setup (long-term memory)
    │   │
    │   ├── chat/
    │   │   ├── session_service.py  # CRUD session + messages facade
    │   │   └── agent_service.py    # Bridge FastAPI → LangGraph, extract results
    │   │
    │   ├── llm/
    │   │   ├── gemini_client.py    # Wrapper: chat() + generate_structured()
    │   │   ├── intent_extractor.py # Stage 2: message → ExtractedIntent (JSON schema)
    │   │   └── outfit_planner.py   # Stage 11: shortlist → outfit plan (JSON schema)
    │   │
    │   ├── concept/
    │   │   ├── resolver.py         # Stage 3: user terms → canonical concept IDs
    │   │   └── knowledge_graph.py  # Stage 4: Neo4j + SQL → FashionRules
    │   │
    │   ├── product/
    │   │   ├── hybrid_retriever.py # Stage 6: hybrid product search
    │   │   ├── filter_service.py   # Stage 8: loại vi phạm hard constraints
    │   │   └── ranking_service.py  # Stage 9: scoring + shortlist
    │   │
    │   └── recommendation/
    │       ├── pipeline.py         # Orchestrator Stage 3–12
    │       └── constraint_builder.py # Stage 5: intent + rules → OutfitConstraints
    │
    └── api/v1/
        ├── router.py               # Mount chat + recommendations routers
        ├── chat.py                 # /sessions/** endpoints
        └── recommendations.py      # /recommendations/outfit endpoint
```

---

## 4. Database Schema

### PostgreSQL — Application Tables (SQLAlchemy `create_all`)

#### `chat_sessions`
| Column | Type | Ghi chú |
|---|---|---|
| `id` | UUID PK | auto-generated |
| `user_id` | VARCHAR(100) | indexed |
| `title` | VARCHAR(255) | nullable, auto-set từ 60 chars đầu message đầu tiên |
| `created_at` | TIMESTAMPTZ | server default |
| `updated_at` | TIMESTAMPTZ | updated khi có message mới |

#### `messages`
| Column | Type | Ghi chú |
|---|---|---|
| `id` | UUID PK | |
| `session_id` | UUID FK | cascade delete |
| `role` | VARCHAR(20) | `user` / `assistant` |
| `content` | TEXT | nội dung hiển thị |
| `intent` | VARCHAR(50) | `outfit_recommendation` / `fashion_knowledge` / `profile_update` / `memory_lookup` / null |
| `metadata` | JSONB | `{outfit_plan: {...}}` hoặc null |
| `created_at` | TIMESTAMPTZ | |

#### `concepts`
| Column | Type | Ghi chú |
|---|---|---|
| `id` | VARCHAR(100) PK | e.g. `STYLE_KOREAN_CASUAL` |
| `name` | VARCHAR(255) | |
| `type` | VARCHAR(50) | `style` / `body_context` / `occasion` / `preference` / `material_property` / `color` / `fit` / `item_type` / `neckline` |
| `description` | TEXT | |

#### `concept_aliases`
| Column | Type | Ghi chú |
|---|---|---|
| `id` | UUID PK | |
| `concept_id` | FK → concepts | |
| `alias` | VARCHAR(255) | e.g. `"style Hàn"`, `"hơi thấp"` |
| `language` | VARCHAR(20) | `vi` / `en` / `ko` |

#### `concept_edges`
| Column | Type | Ghi chú |
|---|---|---|
| `id` | UUID PK | |
| `source_concept_id` | FK | |
| `target_concept_id` | FK | |
| `relation_type` | VARCHAR(50) | `prefers` / `avoids` / `compatible_with` / `suitable_for` |
| `weight` | FLOAT | 0.0–1.0 |
| `explanation` | TEXT | |

#### `concept_rules`
| Column | Type | Ghi chú |
|---|---|---|
| `id` | UUID PK | |
| `concept_id` | FK | |
| `rule_type` | VARCHAR(50) | `hard_constraint` / `soft_preference` |
| `rule_payload` | JSONB | e.g. `{"fabric_property": ["breathable"]}` |
| `priority` | FLOAT | 0.0–1.0 |

### PostgreSQL — LangGraph Internal Tables (auto-created bởi `setup_checkpointer` + `setup_store`)

| Table | Tạo bởi | Mục đích |
|---|---|---|
| `checkpoints` | `AsyncPostgresSaver.setup()` | Short-term: snapshot state mỗi turn |
| `checkpoint_blobs` | `AsyncPostgresSaver.setup()` | Large channel values |
| `checkpoint_writes` | `AsyncPostgresSaver.setup()` | Intermediate writes |
| `store` | `AsyncPostgresStore.setup()` | Long-term: user profile, outfit history |

### Neo4j Graph

```
(:Concept {id, name, type})
  -[:PREFERS     {weight: float}]->
  -[:AVOIDS      {weight: float}]->
  -[:COMPATIBLE_WITH {weight: float}]->
(:Concept)
```

---

## 5. Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Memory                              │
│                                                                  │
│  SHORT-TERM (per session)        LONG-TERM (per user)           │
│  ─────────────────────────       ──────────────────────         │
│  AsyncPostgresSaver               AsyncPostgresStore             │
│  Key: thread_id = session_id      Key: user_id                  │
│                                                                  │
│  Stores:                          Namespace pattern:             │
│  - Full message history           ("users", uid, "profile")     │
│  - AIMessages + ToolMessages      ("users", uid, "outfit_history")│
│  - Tool call/result pairs         ("users", uid, "summaries")   │
│                                                                  │
│  Trim: pre_model_hook             Access: InjectedStore()        │
│  → keep last 30 messages          → auto-injected into tools     │
│                                                                  │
│  Lifecycle: per session           Lifecycle: permanent (no TTL)  │
└─────────────────────────────────────────────────────────────────┘
```

### Short-term Memory — `AsyncPostgresSaver`

- **Scope**: 1 conversation thread (1 `session_id`)
- **Key**: `thread_id = str(session_id)`
- **Content**: tất cả LangChain messages trong session — HumanMessage, AIMessage, ToolMessage
- **Restore**: khi `graph.ainvoke()` được gọi với cùng `thread_id`, checkpointer tự load state cũ
- **Trim**: `pre_model_hook` trong `graph.py` dùng `trim_messages(strategy="last", max_tokens=30)` — giữ 30 messages gần nhất trước khi gửi LLM, tránh context overflow

### Long-term Memory — `AsyncPostgresStore`

- **Scope**: cross-thread, theo `user_id`
- **Key**: `user_id` (= `ChatSession.user_id`)
- **Access trong tools**: `InjectedStore()` annotation — LangGraph tự inject store vào tool khi graph có `store=` parameter

#### Namespaces

| Namespace | Key | Content |
|---|---|---|
| `("users", user_id, "profile")` | `"preferences"` | body_type, preferred_styles, preferred_colors, modesty_level, budget_range, notes |
| `("users", user_id, "outfit_history")` | `"outfit_YYYYMMDD_HHMMSS"` | request, summary, occasion, style, resolved_concepts, number_of_days |
| `("users", user_id, "summaries")` | key tùy | Conversation summaries (future use) |

#### Store Operations được dùng

```python
# Đọc profile
item = await store.aget(("users", user_id, "profile"), "preferences")
# item.value → dict

# Ghi profile
await store.aput(("users", user_id, "profile"), "preferences", {...})

# Lưu outfit history
await store.aput(("users", user_id, "outfit_history"), key, {...})

# Search history
items = await store.asearch(("users", user_id, "outfit_history"), limit=5)
# items → list[Item], mỗi item có .value, .key, .namespace
```

---

## 6. Source Code — File by File

### `config.py`

`pydantic-settings` đọc `.env`. Cung cấp `settings` singleton với tất cả biến môi trường. Property `postgres_dsn` build DSN cho SQLAlchemy asyncpg.

### `main.py`

FastAPI app với `lifespan`:
```
startup:  create_all_tables() → setup_checkpointer() → setup_store()
shutdown: close_store() → close_checkpointer() → close_db() → close_driver()
```
Middleware: CORS (allow all). Exception handlers: ValueError→400, Exception→500.

### `db/postgres.py`

- `engine`: AsyncEngine (asyncpg, pool 10/20, pre_ping)
- `AsyncSessionFactory`: async_sessionmaker
- `Base`: DeclarativeBase cho tất cả models
- `get_db()`: FastAPI dependency, yield AsyncSession
- `create_all_tables()`: import models → `metadata.create_all()`

### `db/neo4j.py`

Singleton `AsyncDriver`. `get_driver()` lazy init. `close_driver()` cleanup.

### `models/`

**session.py**: `ChatSession` — bảng `chat_sessions`. Relationship 1-N với `Message` (cascade delete).

**message.py**: `Message` — bảng `messages`. Role: `user`/`assistant`. Column `metadata_` mapped sang DB column `metadata` (JSONB).

**concept.py**: 4 models:
- `Concept` — node của knowledge graph
- `ConceptAlias` — ánh xạ ngôn ngữ tự nhiên → concept_id
- `ConceptEdge` — cạnh có hướng giữa 2 concepts (prefers/avoids/...)
- `ConceptRule` — rule payload dạng JSON (hard_constraint / soft_preference)

### `repositories/`

**session_repo.py**: `create`, `get`, `list_by_user` (sort updated_at DESC), `update_title`, `touch` (update updated_at), `delete`.

**message_repo.py**: `create`, `list_by_session` (ASC), `get_recent(n)` — query DESC LIMIT n rồi reverse để trả oldest-first.

**concept_repo.py**: `find_by_alias` (ILIKE), `find_aliases_batch`, `get_edges` (sort by weight DESC), `get_rules`, `get_rules_batch`.

### `schemas/`

**chat.py**: `SessionCreate`, `SessionResponse`, `MessageCreate`, `MessageResponse`, `ChatResponse`.
`ChatResponse = { message: MessageResponse, outfit_plan: dict | None }`.

**recommendation.py**: `OutfitRequest`, `OutfitItem`, `DayOutfit`, `OutfitRecommendationResponse`.

**product.py**: `Product` — full product model với tất cả tags + scoring fields. `ProductSearchQuery`, `SemanticSearchQuery` — params cho Product Service.

### `clients/product_client.py`

HTTP client gọi Product Service qua httpx để search text trong hybrid retrieval và hydrate metadata sau khi đã chọn product IDs. Khi chạy local không có Product Service, client đọc `scripts/seeds/products.json` để hydrate metadata, không tham gia product search.

Main method:
- `batch_fetch(product_ids)` → `POST /products/batch`

### `services/agent/checkpointer.py`

Setup `AsyncPostgresSaver` dùng `psycopg_pool.AsyncConnectionPool` (psycopg3, tách biệt với SQLAlchemy asyncpg pool):
```
AsyncConnectionPool(conninfo=psycopg3_dsn, max_size=10)
  → AsyncPostgresSaver(pool)
  → .setup()  # tạo checkpoint tables nếu chưa có
```
Singleton `_checkpointer`. `get_checkpointer()` dùng trong `agent_service.py`.

### `services/agent/store.py`

Setup `AsyncPostgresStore` cho long-term memory:
```
AsyncPostgresStore.from_conn_string(postgresql://...)
  → .__aenter__()
  → .setup()  # tạo store table nếu chưa có
```
Fallback sang `InMemoryStore` nếu lỗi. Singleton `_store`. `get_store()` dùng trong `agent_service.py`.

### `services/agent/graph.py`

Compile LangGraph ReAct agent:
```python
create_react_agent(
    model=ChatGoogleGenerativeAI(...),
    tools=ALL_TOOLS,            # 5 tools
    checkpointer=checkpointer,  # short-term
    store=store,                # long-term
    pre_model_hook=...,         # trim messages → max 30
    prompt=_SYSTEM_PROMPT,
)
```

`pre_model_hook` chạy trước mỗi LLM call: nếu `len(messages) > 30` → `trim_messages(strategy="last", max_tokens=30)`.

### `services/agent/tools.py`

5 LangChain tools:

| Tool | Memory | Mô tả |
|---|---|---|
| `recommend_outfit` | DB + Store (r/w) | Chạy full pipeline, đọc profile để enrich, lưu outfit history |
| `get_fashion_knowledge` | DB only | Query knowledge graph, trả rules |
| `save_user_style_profile` | Store (write) | Upsert user profile vào long-term memory |
| `get_user_style_profile` | Store (read) | Đọc user profile từ long-term memory |
| `get_outfit_history` | Store (read) | Lấy lịch sử outfit recommendations |

**Dependency injection pattern:**
- `config["configurable"]["db"]` → SQLAlchemy session (per-request)
- `config["configurable"]["user_id"]` → namespace cho Store
- `InjectedStore()` annotation → LangGraph auto-inject store instance

### `services/chat/session_service.py`

Facade cho `SessionRepository` + `MessageRepository`. Methods:
- `create_session`, `get_session`, `list_sessions`, `delete_session`
- `get_history(n=20)` → n messages recent, oldest-first
- `list_messages()` → tất cả messages ASC
- `save_user_message`, `save_assistant_message` (tự gọi `touch()`)

### `services/chat/agent_service.py`

Bridge FastAPI → LangGraph:
1. Check session tồn tại
2. Lưu user message vào `messages` table
3. `create_graph(checkpointer, store)` → compile graph
4. `graph.ainvoke({"messages": [HumanMessage]}, config={thread_id, user_id, db})`
5. Extract `reply_text` từ `result["messages"][-1].content`
6. `_extract_tool_result()` → scan ToolMessages để lấy `tool_used` + `outfit_plan`
7. Lưu assistant message
8. Auto-set session title từ message đầu tiên

### `services/llm/gemini_client.py`

Wrapper `google-genai` SDK:
- `chat(history, user_message, system_instruction?)` → multi-turn chat, trả `str`
- `generate_structured(prompt, response_schema, system_instruction?, temperature?)` → JSON output theo Pydantic schema

### `services/llm/intent_extractor.py`

Stage 2. Dùng `generate_structured(response_schema=ExtractedIntent, temperature=0.1)`:
```
"Tôi hơi thấp, đi Vũng Tàu 3 ngày..."
→ ExtractedIntent {
    intent: "outfit_recommendation",
    occasion: "beach_travel",
    destination: "Vũng Tàu",
    duration: {days:3, nights:2},
    style_preferences: ["korean_style"],
    body_context: {height_group: "short_or_petite"},
    modesty_level: "medium_high",
    comfort_needs: ["cool","breathable"],
    required_output: {number_of_days: 3}
  }
```

### `services/llm/outfit_planner.py`

Stage 11. `generate_structured(response_schema=OutfitPlanResult, temperature=0.4)`.
System prompt enforce: *"Only use products from shortlisted_products"*.
Input: intent dict + rules dict + shortlisted products dict. Output: `OutfitPlanResult {summary, outfit_plan: [DayPlan]}`.

### `services/concept/embedding_service.py`

Stage 3. Resolve user terms → canonical concept IDs bằng Gemini embeddings + pgvector cosine search.
Returns `ResolvedConcept {input_term, concept_id, concept_name, concept_type, confidence}`.

`resolve_from_intent(intent_dict)` — tự extract terms từ requested_items, style_preferences, occasion, destination, height_group, modesty_level, comfort_needs, raw_keywords.

### `services/concept/knowledge_graph.py`

Stage 4. Query fashion rules từ resolved concept IDs:
1. **Neo4j** (Cypher MATCH): traverse graph, collect relations
2. **Rule nodes**: `(:Concept)-[:HAS_RULE]->(:Rule)` payload từ `scripts/seeds/knowledge_graph.json`

Output `FashionRules {style_rules, body_rules, occasion_rules, modesty_rules, hard_constraints, soft_preferences, preferred_item_types, avoided_item_types, preferred_colors}`.

### `services/recommendation/constraint_builder.py`

Stage 5. Merge `ExtractedIntent` + `FashionRules` → `OutfitConstraints`:

**Hard constraints** (filter bắt buộc):
- `modesty_level=medium_high/high` → `coverage_level=[medium,high]`, `excluded_neckline=[deep_v,strapless]`
- `comfort_needs=[cool/breathable]` → `fabric_property=[breathable,lightweight]`, `excluded_fabric=[wool,leather,thick_denim]`

**Soft preferences** (boost score): colors, preferred_items, avoid_items, style_tags.

**Search queries**: LLM-generated product terms sent to Qdrant semantic search and Product Service text search.

### `services/product/hybrid_retriever.py`

Stage 6. Hybrid product search:
```python
embeddings = gemini.embed_texts(search_terms)
qdrant.search(collection, embeddings)
product_service.search_text(search_terms)
```
`_merge_and_deduplicate()`: sản phẩm trùng ID → merge scores, union sources list.

### `services/product/filter_service.py`

Stage 8. Loại sản phẩm vi phạm hard constraints. Checks (theo thứ tự):
1. `stock_status == in_stock`
2. `coverage_level` trong allowed list
3. `neckline` không trong excluded_neckline
4. `fabric_tags` không chứa excluded_fabric
5. `style_tags` không chứa excluded_style
6. `fabric_tags` chứa ít nhất 1 fabric trong `fabric_property` (chỉ top/bottom/dress)

### `services/product/ranking_service.py`

Stage 9. Công thức final_score:
```
final_score =
  0.30 × semantic_relevance   = max(semantic_score, structured_score×0.8, graph_score×0.7)
  0.25 × constraint_match     = % soft_preferences thỏa mãn (style, color, fit, items)
  0.20 × outfit_compatibility = neutral_color +0.15, preferred_color +0.10,
                                breathable_fabric +0.10, high_waist +0.10, korean_casual +0.05
  0.10 × quality              = (rating-1)/4 × 0.8 + min(review_count/500, 0.2)
  0.10 × personalization      = 0.5 (placeholder — user history chưa có)
  0.05 × business             = 0.5 (placeholder)
```
Group by category → sort DESC. `shortlist()`: top 8, bottom 8, dress 6, shoes 5, accessory 5.

### `services/recommendation/pipeline.py`

Orchestrator Stage 3–12:
```
input: ExtractedIntent + original_message
  → Stage 3: ConceptResolver.resolve_from_intent()
  → Stage 4: KnowledgeGraphService.get_rules()
  → Stage 5: SearchTermGenerator.generate()
  → Stage 6: HybridProductRetriever.search()
  → Stage 7: FinalResponseGenerator.generate()
  → Stage 8: ProductServiceClient.batch_fetch()
  → Stage 12: format_outfit_plan()  [enrich với price/image/url]
output: { summary, outfit_plan, resolved_concepts, debug }
```
Graceful degradation: nếu không có DB → bỏ qua Stage 3–4, chạy với intent-only constraints.

---

## 7. API Endpoints

Base: `/api/v1`

### Chat

| Method | Path | Request | Response | Ghi chú |
|---|---|---|---|---|
| `POST` | `/sessions` | `{user_id, title?}` | `SessionResponse` | 201 |
| `GET` | `/sessions/{id}` | — | `SessionResponse` | 404 nếu không tìm thấy |
| `DELETE` | `/sessions/{id}` | — | 204 | Cascade xóa messages |
| `GET` | `/sessions/{id}/messages` | — | `MessageResponse[]` | Sorted ASC |
| `POST` | `/sessions/{id}/messages` | `{content}` | `ChatResponse` | **Main endpoint** |

**`ChatResponse`:**
```json
{
  "message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Mình gợi ý...",
    "intent": "outfit_recommendation",
    "metadata": {"outfit_plan": {...}},
    "created_at": "2024-01-01T..."
  },
  "outfit_plan": {
    "summary": "...",
    "outfits": [...],
    "resolved_concepts": [...]
  }
}
```

### Recommendations (Stateless)

| Method | Path | Request | Response |
|---|---|---|---|
| `POST` | `/recommendations/outfit` | `{user_id, message, budget_max?, locale?}` | `OutfitRecommendationResponse` |

### Health

| Method | Path | Response |
|---|---|---|
| `GET` | `/health` | `{"status":"ok","service":"ai-stylist","version":"0.2.0"}` |

---

## 8. Flow: Startup

```
uvicorn main:app
  │
  ├─ lifespan() bắt đầu
  │
  ├─ create_all_tables()
  │    → import models.session, message, concept  (register SQLAlchemy metadata)
  │    → engine.begin() → conn.run_sync(Base.metadata.create_all)
  │    → Tạo 6 bảng nếu chưa có:
  │      chat_sessions, messages, concepts,
  │      concept_aliases, concept_edges, concept_rules
  │
  ├─ setup_checkpointer()
  │    → AsyncConnectionPool(psycopg3_dsn, max_size=10).open()
  │    → AsyncPostgresSaver(pool)
  │    → .setup() → tạo: checkpoints, checkpoint_blobs, checkpoint_writes
  │    → _checkpointer singleton set
  │
  ├─ setup_store()
  │    → AsyncPostgresStore.from_conn_string(postgresql_dsn)
  │    → .__aenter__()
  │    → .setup() → tạo: store table
  │    → _store singleton set
  │    (fallback: InMemoryStore nếu lỗi)
  │
  └─ App ready, serve requests
```

---

## 9. Flow: Chat Message — General Q&A

```
POST /api/v1/sessions/{session_id}/messages
Body: { "content": "Korean casual và minimalist khác nhau thế nào?" }

  │
  ├─ [chat.py] SessionService.get_session(session_id)
  │    → SELECT FROM chat_sessions WHERE id = ?
  │
  ├─ [chat.py] AgentService.handle(session_id, content, user_id=session.user_id)
  │
  ├─ [agent_service.py] SessionService.save_user_message()
  │    → INSERT INTO messages (role="user", content=...)
  │
  ├─ [agent_service.py] create_graph(checkpointer, store)
  │    → ChatGoogleGenerativeAI(gemini-2.0-flash)
  │    → create_react_agent(llm, tools=5, checkpointer, store, pre_model_hook)
  │
  ├─ [agent_service.py] graph.ainvoke(
  │    {"messages": [HumanMessage("Korean casual...")]},
  │    config={thread_id=session_id, user_id=..., db=...}
  │  )
  │
  │  ┌─ LangGraph ReAct loop ─────────────────────────────────┐
  │  │                                                         │
  │  │  1. Checkpointer load state từ PostgreSQL              │
  │  │     (previous messages của thread này nếu có)          │
  │  │                                                         │
  │  │  2. pre_model_hook:                                     │
  │  │     if len(messages) > 30: trim → keep last 30         │
  │  │                                                         │
  │  │  3. Gemini nhận: system_prompt + history + user_msg    │
  │  │     → suy luận: câu hỏi về kiến thức                   │
  │  │     → có thể gọi get_fashion_knowledge hoặc chat       │
  │  │       thẳng không cần tool                              │
  │  │                                                         │
  │  │  4. Gemini quyết định KHÔNG gọi tool                   │
  │  │     → AIMessage("Korean casual thiên về...")           │
  │  │     → loop kết thúc                                     │
  │  │                                                         │
  │  │  5. Checkpointer save state (+ new messages)           │
  │  └─────────────────────────────────────────────────────────┘
  │
  ├─ [agent_service.py] reply_text = result["messages"][-1].content
  │
  ├─ [agent_service.py] _extract_tool_result() → (None, None) — không có ToolMessage
  │
  ├─ [agent_service.py] SessionService.save_assistant_message()
  │    → INSERT INTO messages (role="assistant", content=reply, intent=None)
  │    → SessionRepository.touch() → UPDATE updated_at
  │
  └─ Response: { message: {..., intent: null}, outfit_plan: null }
```

---

## 10. Flow: Chat Message — Outfit Recommendation

```
POST /api/v1/sessions/{session_id}/messages
Body: { "content": "Tôi hơi thấp, đi Vũng Tàu 3 ngày 2 đêm, style Hàn, không quá hở vẫn mát" }

  │
  ├─ ... (check session, save user message, create_graph như trên)
  │
  ├─ graph.ainvoke(...)
  │
  │  ┌─ LangGraph ReAct loop ─────────────────────────────────┐
  │  │                                                         │
  │  │  1. Checkpointer load state                            │
  │  │  2. pre_model_hook: trim nếu cần                       │
  │  │                                                         │
  │  │  3. Gemini phân tích → cần recommend_outfit tool       │
  │  │     → AIMessage với tool_calls=[{                      │
  │  │         name: "recommend_outfit",                       │
  │  │         args: {                                         │
  │  │           user_request: "Tôi hơi thấp...",             │
  │  │           number_of_days: 3,                            │
  │  │           budget_max: null                              │
  │  │         }                                               │
  │  │       }]                                                │
  │  │                                                         │
  │  │  4. LangGraph execute tool recommend_outfit:           │
  │  │     ├─ _get_db(config) → SQLAlchemy session            │
  │  │     ├─ _get_user_id(config) → user_id                  │
  │  │     ├─ store.aget(("users",uid,"profile"),"pref")     │
  │  │     │   → đọc profile từ long-term store               │
  │  │     │                                                   │
  │  │     ├─ IntentExtractor.extract(user_request + profile)│
  │  │     │   → Gemini structured → ExtractedIntent          │
  │  │     │                                                   │
  │  │     ├─ RecommendationPipeline.run(intent, message)    │
  │  │     │   [xem chi tiết Section 12]                      │
  │  │     │                                                   │
  │  │     ├─ store.aput(("users",uid,"outfit_history"), key, │
  │  │     │             {request, summary, occasion, ...})   │
  │  │     │   → lưu vào long-term store                      │
  │  │     │                                                   │
  │  │     └─ return JSON string {summary, outfits:[...]}     │
  │  │                                                         │
  │  │  5. ToolMessage(content=json_string, name="recommend_outfit")│
  │  │                                                         │
  │  │  6. Gemini nhận ToolMessage → viết reply thân thiện   │
  │  │     → AIMessage("Mình đã chọn outfit cho 3 ngày...")   │
  │  │                                                         │
  │  │  7. Checkpointer save state                            │
  │  └─────────────────────────────────────────────────────────┘
  │
  ├─ _extract_tool_result():
  │    → scan messages, tìm ToolMessage với name="recommend_outfit"
  │    → json.loads(content) → outfit_plan dict
  │    → return ("outfit_recommendation", outfit_plan)
  │
  ├─ save_assistant_message(intent="outfit_recommendation",
  │                          metadata={outfit_plan: {...}})
  │
  └─ Response: {
       message: { role:"assistant", content:"Mình đã chọn...",
                  intent:"outfit_recommendation",
                  metadata:{outfit_plan:{...}} },
       outfit_plan: { summary, outfits:[...], resolved_concepts:[...] }
     }
```

---

## 11. Flow: Long-term Memory Read/Write

### Khi user cung cấp thông tin về bản thân

```
User: "Tôi dáng người đầy đặn, thích màu earth tone, ngân sách tầm trung"

  → Gemini quyết định gọi save_user_style_profile tool
  → args: { body_type:"curvy", preferred_colors:["earth tones"],
             budget_range:"mid_range" }

  → Tool execution:
      existing = await store.aget(("users",uid,"profile"), "preferences")
      updated = {**existing, body_type:"curvy", preferred_colors:[...], ...}
      await store.aput(("users",uid,"profile"), "preferences", updated)

  → Gemini: "Mình đã ghi nhớ thông tin của bạn rồi nhé!"
```

### Khi user hỏi outfit lần sau (cross-session)

```
Session mới (session_id khác, user_id giống):
User: "Gợi ý outfit đi làm cho mình"

  → recommend_outfit tool:
      profile_item = await store.aget(("users",uid,"profile"), "preferences")
      # profile_item.value = {body_type:"curvy", preferred_colors:["earth tones"],
      #                        budget_range:"mid_range"}
      profile_ctx = "User profile: {body_type: curvy, ...}"
      intent = await extractor.extract(user_request + profile_ctx)
      # Intent đã được enrich với profile context
```

### Khi user xem lại lịch sử

```
User: "Những lần trước mình đã được gợi ý outfit gì?"

  → Gemini gọi get_outfit_history tool
  → items = await store.asearch(("users",uid,"outfit_history"), limit=5)
  → Gemini format kết quả thân thiện
```

---

## 12. Recommendation Pipeline — Stage by Stage

```
INPUT: ExtractedIntent + original_message
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: ConceptResolver                                         │
│                                                                  │
│ Input terms (từ intent):                                         │
│   style_preferences, occasion, destination, height_group,       │
│   modesty_level, comfort_needs, raw_keywords                     │
│                                                                  │
│ Matching:                                                        │
│   1. Exact: SELECT FROM concept_aliases WHERE alias ILIKE term  │
│   2. Substring: tách words ≥3 chars, thử từng word              │
│                                                                  │
│ Output:                                                          │
│   [ResolvedConcept {input_term, concept_id, type, confidence}]  │
│   "style Hàn" → STYLE_KOREAN_CASUAL (0.95)                     │
│   "hơi thấp"  → BODY_PETITE (0.95)                             │
│   "beach_travel" → OCCASION_BEACH_TRAVEL (0.95)                 │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: KnowledgeGraphService                                   │
│                                                                  │
│ Neo4j (primary):                                                 │
│   MATCH (c:Concept {id: cid})-[r]->(target:Concept)            │
│   RETURN source, type(r), r.weight, target                      │
│                                                                  │
│ Neo4j rule nodes:                                                │
│   MATCH (concept)-[:HAS_RULE]->(rule)                           │
│   RETURN rule.type, rule.payload_json, rule.priority            │
│                                                                  │
│ Output: FashionRules {                                           │
│   hard_constraints: {                                            │
│     fabric_property: ["breathable","lightweight"],              │
│     excluded_neckline: ["deep_v","strapless"],                  │
│     coverage_level: ["medium","high"]                           │
│   },                                                             │
│   soft_preferences: {                                            │
│     style_tags: ["korean_casual","minimal"],                    │
│     color: ["white","beige","pastel_blue"]                      │
│   },                                                             │
│   preferred_item_types: ["wide_leg_pants","midi_skirt"],         │
│   avoided_item_types: ["oversized_shirt"],                       │
│   preferred_colors: ["neutral","pastel"]                         │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 5: ConstraintBuilder                                       │
│                                                                  │
│ Merge intent + rules → OutfitConstraints {                       │
│   hard_constraints: {...},                                       │
│   soft_preferences: {...},                                       │
│   structured_query: ProductSearchQuery {                         │
│     categories: [top,bottom,dress,shoes,accessory],             │
│     style_tags: ["korean_casual"],                               │
│     occasion_tags: ["travel","beach","casual"],                  │
│     fabric_tags: ["breathable","lightweight"],                   │
│     coverage_level: ["medium","high"],                           │
│     stock_status: "in_stock", limit: 40                         │
│   },                                                             │
│   semantic_query: SemanticSearchQuery {                          │
│     query: "korean_style beach_travel petite friendly            │
│             modest breathable travel outfit 3 days outfit"       │
│   },                                                             │
│   number_of_days: 3                                              │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 6: HybridProductRetriever                                  │
│                                                                  │
│ Embed LLM-generated product terms                                │
│ Query Qdrant product vector collection                           │
│ Query Product Service text search                                │
│ Merge candidates per target item                                 │
│                                                                  │
│ _merge_and_deduplicate():                                        │
│   - structured: dict[id→Product], structured_match_score=0.80  │
│   - semantic: merge scores, add "vector_db" to sources          │
│   - graph: merge scores, add "graph_expansion" to sources       │
│                                                                  │
│ Output: ~12 candidate Products với đầy đủ scores + sources      │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 8: ProductFilterService                                    │
│                                                                  │
│ Hard constraint checks (loại nếu vi phạm):                       │
│   ✗ stock_status != in_stock                                    │
│   ✗ coverage_level = low (required: medium/high)                │
│   ✗ neckline = deep_v (excluded)                                │
│   ✗ fabric = wool/leather/thick_denim (excluded)               │
│   ✗ style = formal (excluded)                                   │
│   ✗ fabric không có breathable/lightweight (top/bottom/dress)  │
│                                                                  │
│ Ví dụ bị loại:                                                  │
│   "Áo hai dây cổ sâu" → excluded_neckline_deep_v               │
│   "Áo khoác dạ dày"   → excluded_fabric_wool                   │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 9: ProductRankingService                                   │
│                                                                  │
│ final_score per product:                                         │
│   0.30 × semantic_relevance  (max của 3 search scores)          │
│   0.25 × constraint_match    (% soft prefs thỏa mãn)            │
│   0.20 × outfit_compatibility (neutral/preferred color, fabric) │
│   0.10 × quality             (rating, review_count)             │
│   0.10 × personalization     (0.5 placeholder)                  │
│   0.05 × business            (0.5 placeholder)                  │
│                                                                  │
│ Group by category → sort by final_score DESC                     │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 10: Shortlist                                              │
│                                                                  │
│   top: top 8     bottom: top 8    dress: top 6                  │
│   shoes: top 5   accessory: top 5                               │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 11: OutfitPlanner (Gemini structured output)               │
│                                                                  │
│ Prompt = intent + rules + shortlisted_products (tên + giá)      │
│ System: "ONLY use products from shortlisted_products"           │
│ Schema: OutfitPlanResult { summary, outfit_plan: [DayPlan] }    │
│                                                                  │
│ Gemini tạo outfit plan:                                          │
│   Day 1: context, items[{category, product_id, name}],          │
│           styling_reason, styling_tip, constraint_check          │
│   Day 2: ...                                                     │
│   Day 3: ...                                                     │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 12: Format Response                                        │
│                                                                  │
│ Enrich mỗi item với price, image_url, product_url từ shortlist  │
│ Output: {                                                        │
│   summary: "...",                                                │
│   outfit_plan: [{ day, context, items[{...+price+url}],         │
│                   styling_tip, styling_reason }],                │
│   resolved_concepts: ["STYLE_KOREAN_CASUAL", ...],              │
│   debug: { candidates_total, filtered_out, ranked_categories }  │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. Data Flow Diagram

```
┌──────────┐     POST /sessions/{id}/messages      ┌──────────────────┐
│  Client  │ ──────────────────────────────────── ▶ │   FastAPI API    │
└──────────┘                                        │   chat.py        │
                                                    └────────┬─────────┘
                                                             │ AgentService.handle()
                                                    ┌────────▼─────────┐
                                                    │  LangGraph Graph  │
                                                    │  ReAct Agent      │
                                                    │  (Gemini LLM)     │
                                                    └──┬──────────┬─────┘
                              Checkpointer (r/w)       │          │ Store (r/w)
                    ┌──────────────────────────────────▼┐  ┌──────▼──────────────┐
                    │     PostgreSQL                      │  │  PostgreSQL          │
                    │     checkpoints table               │  │  store table         │
                    │     (short-term memory)             │  │  (long-term memory)  │
                    └────────────────────────────────────┘  └──────────────────────┘
                                        │
                              Tool calls│
                    ┌───────────────────┼──────────────────────┐
                    │                   │                        │
          ┌─────────▼──────┐  ┌─────────▼──────┐  ┌───────────▼──────────┐
          │  recommend_    │  │ get_fashion_   │  │ save/get_user_       │
          │  outfit        │  │ knowledge      │  │ style_profile        │
          │  tool          │  │ tool           │  │ get_outfit_history   │
          └────────┬───────┘  └────────┬───────┘  └──────────────────────┘
                   │                   │
          ┌────────▼───────────────────▼──────┐
          │     RecommendationPipeline         │
          │     + ConceptResolver              │
          │     + KnowledgeGraphService        │
          └────┬──────────────────────┬────────┘
               │                      │
    ┌──────────▼──────┐    ┌──────────▼──────────┐
    │   PostgreSQL     │    │     Neo4j            │
    │   (concepts,     │    │   (Knowledge Graph   │
    │   aliases,       │    │    traversal)        │
    │   edges, rules)  │    └─────────────────────┘
    └──────────┬───────┘
               │ HybridProductRetriever
    ┌──────────▼──────────────────────┐
    │     Hybrid product search        │
    │     semantic search by LLM terms │
    │     Product Service hydrates IDs │
    └──────────────────────────────────┘
```

---

## Cách chạy

```bash
# 1. Copy và điền API key
cp .env.example .env
# Sửa GEMINI_API_KEY=your_key

# 2. Start local services
docker-compose up -d

# 3. Seed semantic concepts, graph rules, and product vectors
uv run python scripts/init_concepts.py --index
uv run python scripts/init_graphdb.py --clear
uv run python scripts/init_qdrant.py --recreate

# 4. Chạy app (tự tạo tables khi startup)
uv run uvicorn ai_stylist.main:app --reload --port 8000

# 5. Swagger UI
# http://localhost:8000/docs
```

---

*Document này phản ánh source code tại version 0.2.0. Mọi thay đổi trong code cần được cập nhật vào document này.*
