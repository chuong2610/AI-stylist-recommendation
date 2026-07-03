import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, model_validator


class KnowledgeIngestRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=255)
    texts: list[str] = Field(default_factory=list)
    urls: list[HttpUrl] = Field(default_factory=list)
    locale: str = "vi-VN"
    max_concepts: int = Field(default=50, ge=1, le=120)
    max_edges: int = Field(default=100, ge=1, le=240)
    max_rules: int = Field(default=100, ge=1, le=240)

    @model_validator(mode="after")
    def require_source(self):
        if not self.texts and not self.urls:
            raise ValueError("At least one text or url is required")
        return self


class IngestedConcept(BaseModel):
    id: str
    name: str
    type: str
    description: str = ""
    aliases: list[str] = Field(default_factory=list)


class IngestedEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float


class IngestedRule(BaseModel):
    id: str
    concept_id: str
    type: str
    priority: float


class KnowledgeIngestResponse(BaseModel):
    source_id: uuid.UUID
    status: str
    concepts_upserted: int
    edges_upserted: int
    rules_upserted: int
    concept_vectors_upserted: int
    concepts: list[IngestedConcept]
    edges: list[IngestedEdge]
    rules: list[IngestedRule]
    sources: list[str]


class KnowledgeSourceSummary(BaseModel):
    id: uuid.UUID
    user_id: str
    title: str | None = None
    status: str
    sources: list[str]
    concepts_count: int
    edges_count: int
    rules_count: int
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None


class KnowledgeSourceDetail(KnowledgeSourceSummary):
    source_text: str
    concepts: list[IngestedConcept]
    edges: list[IngestedEdge]
    rules: list[IngestedRule]
