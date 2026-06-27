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

    # Concept semantic search
    concept_similarity_threshold: float = 0.65

    # Product Service
    product_service_base_url: str = "http://localhost:8001"
    product_service_timeout: int = 10
    product_catalog_seed_path: str = "scripts/seeds/product_catalog_seed.json"

    # Local AI-managed retrieval seeds (BM25 + vector mock)
    product_bm25_seed_path: str = "scripts/seeds/product_bm25_seed.json"
    product_vector_seed_path: str = "scripts/seeds/product_vector_seed.json"
    kg_rules_seed_path: str = "scripts/seeds/kg_rules_seed.json"
    hybrid_search_limit_per_target: int = 8

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
