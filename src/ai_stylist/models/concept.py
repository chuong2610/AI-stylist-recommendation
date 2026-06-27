import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_stylist.db.postgres import Base

EMBEDDING_DIM = 3072


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    aliases: Mapped[list["ConceptAlias"]] = relationship("ConceptAlias", back_populates="concept", cascade="all, delete-orphan")
    rules: Mapped[list["ConceptRule"]] = relationship("ConceptRule", back_populates="concept", cascade="all, delete-orphan")
    outgoing_edges: Mapped[list["ConceptEdge"]] = relationship("ConceptEdge", foreign_keys="ConceptEdge.source_concept_id", cascade="all, delete-orphan")


class ConceptAlias(Base):
    __tablename__ = "concept_aliases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[str] = mapped_column(String(100), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False)

    concept: Mapped["Concept"] = relationship("Concept", back_populates="aliases")


class ConceptEdge(Base):
    __tablename__ = "concept_edges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_concept_id: Mapped[str] = mapped_column(String(100), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    target_concept_id: Mapped[str] = mapped_column(String(100), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)


class ConceptRule(Base):
    __tablename__ = "concept_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[str] = mapped_column(String(100), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    priority: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    concept: Mapped["Concept"] = relationship("Concept", back_populates="rules")
