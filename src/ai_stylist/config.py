from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_stylist"
    postgres_user: str = "stylist"
    postgres_password: str = "stylist123"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "stylist123"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # Firecrawl blog ingestion
    firecrawl_api_key: str = ""
    firecrawl_base_url: str = "https://api.firecrawl.dev/v2"
    firecrawl_timeout: int = 120

    # Concept semantic search
    concept_similarity_threshold: float = 0.65
    qdrant_concept_collection: str = "ai_stylist_concepts"

    # Product Service
    product_service_base_url: str = "http://localhost:8001"
    product_service_timeout: int = 10
    product_service_text_search_path: str = "/products/search"

    # Seed JSON used only by init scripts and local metadata hydration.
    product_seed_path: str = "scripts/seeds/products.json"
    kg_seed_path: str = "scripts/seeds/knowledge_graph.json"

    # Qdrant product vector search
    qdrant_url: str = "http://localhost:6333"
    qdrant_product_collection: str = "ai_stylist_products"
    qdrant_timeout: int = 10
    qdrant_score_threshold: float = 0.25
    hybrid_search_limit_per_target: int = 8
    hybrid_vector_weight: float = 0.65
    hybrid_text_weight: float = 0.35
    hybrid_multi_source_bonus: float = 0.1

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
