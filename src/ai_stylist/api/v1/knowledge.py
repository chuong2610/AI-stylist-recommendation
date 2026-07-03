import uuid

from fastapi import APIRouter
from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.db.postgres import get_db
from ai_stylist.models.knowledge_source import KnowledgeSource
from ai_stylist.schemas.knowledge import (
    IngestedConcept,
    IngestedEdge,
    IngestedRule,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeSourceDetail,
    KnowledgeSourceSummary,
)
from ai_stylist.services.concept.ingestion import KnowledgeIngestionService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ingest", response_model=KnowledgeIngestResponse)
async def ingest_knowledge(body: KnowledgeIngestRequest, db: AsyncSession = Depends(get_db)):
    svc = KnowledgeIngestionService()
    try:
        source = await svc.create_draft(
            db=db,
            user_id=body.user_id,
            title=body.title,
            texts=body.texts,
            urls=[str(url) for url in body.urls],
            locale=body.locale,
            max_concepts=body.max_concepts,
            max_edges=body.max_edges,
            max_rules=body.max_rules,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _source_response(source, concept_vectors_upserted=0)


@router.get("/sources", response_model=list[KnowledgeSourceSummary])
async def list_knowledge_sources(
    user_id: str = Query(..., min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    svc = KnowledgeIngestionService()
    return [_source_summary(source) for source in await svc.list_sources(db, user_id=user_id)]


@router.get("/sources/{source_id}", response_model=KnowledgeSourceDetail)
async def get_knowledge_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = KnowledgeIngestionService()
    source = await svc.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    return _source_detail(source)


@router.post("/sources/{source_id}/approve", response_model=KnowledgeIngestResponse)
async def approve_knowledge_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = KnowledgeIngestionService()
    result = await svc.approve_source(db, source_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    source, concept_vectors_upserted = result
    return _source_response(source, concept_vectors_upserted=concept_vectors_upserted)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = KnowledgeIngestionService()
    if not await svc.delete_source(db, source_id):
        raise HTTPException(status_code=404, detail="Knowledge source not found")


def _source_response(source: KnowledgeSource, concept_vectors_upserted: int) -> KnowledgeIngestResponse:
    extraction = _extraction(source)
    return KnowledgeIngestResponse(
        source_id=source.id,
        status=source.status,
        concepts_upserted=len(extraction["concepts"]) if source.status == "approved" else 0,
        edges_upserted=len(extraction["edges"]) if source.status == "approved" else 0,
        rules_upserted=len(extraction["rules"]) if source.status == "approved" else 0,
        concept_vectors_upserted=concept_vectors_upserted,
        concepts=_concepts(extraction),
        edges=_edges(extraction),
        rules=_rules(extraction),
        sources=source.sources,
    )


def _source_summary(source: KnowledgeSource) -> KnowledgeSourceSummary:
    extraction = _extraction(source)
    return KnowledgeSourceSummary(
        id=source.id,
        user_id=source.user_id,
        title=source.title,
        status=source.status,
        sources=source.sources,
        concepts_count=len(extraction["concepts"]),
        edges_count=len(extraction["edges"]),
        rules_count=len(extraction["rules"]),
        created_at=source.created_at,
        updated_at=source.updated_at,
        approved_at=source.approved_at,
    )


def _source_detail(source: KnowledgeSource) -> KnowledgeSourceDetail:
    summary = _source_summary(source)
    extraction = _extraction(source)
    return KnowledgeSourceDetail(
        **summary.model_dump(),
        source_text=source.source_text,
        concepts=_concepts(extraction),
        edges=_edges(extraction),
        rules=_rules(extraction),
    )


def _extraction(source: KnowledgeSource) -> dict:
    return {
        "concepts": source.extraction.get("concepts", []),
        "edges": source.extraction.get("edges", []),
        "rules": source.extraction.get("rules", []),
    }


def _concepts(extraction: dict) -> list[IngestedConcept]:
    return [
        IngestedConcept(
            id=c["id"],
            name=c["name"],
            type=c["type"],
            description=c.get("description", ""),
            aliases=c.get("aliases", []),
        )
        for c in extraction["concepts"]
    ]


def _edges(extraction: dict) -> list[IngestedEdge]:
    return [
        IngestedEdge(source=e["source"], target=e["target"], relation=e["relation"], weight=e["weight"])
        for e in extraction["edges"]
    ]


def _rules(extraction: dict) -> list[IngestedRule]:
    return [
        IngestedRule(id=r["id"], concept_id=r["concept_id"], type=r["type"], priority=r["priority"])
        for r in extraction["rules"]
    ]
