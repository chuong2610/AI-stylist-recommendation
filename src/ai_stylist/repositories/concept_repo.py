from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.models.concept import Concept, ConceptAlias, ConceptEdge, ConceptRule


class ConceptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, concept_id: str) -> Concept | None:
        result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id).options(selectinload(Concept.aliases))
        )
        return result.scalar_one_or_none()

    async def find_by_alias(self, alias: str) -> list[ConceptAlias]:
        result = await self.db.execute(
            select(ConceptAlias)
            .where(ConceptAlias.alias.ilike(alias))
            .options(selectinload(ConceptAlias.concept))
        )
        return list(result.scalars().all())

    async def find_aliases_batch(self, aliases: list[str]) -> list[ConceptAlias]:
        """Match multiple aliases at once (case-insensitive)."""
        from sqlalchemy import func
        normalized = [a.lower() for a in aliases]
        result = await self.db.execute(
            select(ConceptAlias)
            .where(func.lower(ConceptAlias.alias).in_(normalized))
            .options(selectinload(ConceptAlias.concept))
        )
        return list(result.scalars().all())

    async def find_similar(
        self,
        embedding: list[float],
        k: int = 5,
        min_similarity: float = 0.65,
    ) -> list[tuple[Concept, float]]:
        """Return (concept, cosine_similarity) pairs ordered by similarity desc."""
        max_distance = 1.0 - min_similarity
        distance_col = Concept.embedding.cosine_distance(embedding)
        result = await self.db.execute(
            select(Concept, (1.0 - distance_col).label("similarity"))
            .where(Concept.embedding.is_not(None))
            .where(distance_col <= max_distance)
            .order_by(distance_col)
            .limit(k)
        )
        return [(row.Concept, float(row.similarity)) for row in result.all()]

    async def get_all_for_indexing(self) -> list[Concept]:
        """Load all concepts with aliases for embedding indexing."""
        result = await self.db.execute(
            select(Concept).options(selectinload(Concept.aliases))
        )
        return list(result.scalars().all())

    async def get_edges(self, source_concept_id: str, relation_type: str | None = None) -> list[ConceptEdge]:
        q = select(ConceptEdge).where(ConceptEdge.source_concept_id == source_concept_id)
        if relation_type:
            q = q.where(ConceptEdge.relation_type == relation_type)
        result = await self.db.execute(q.order_by(ConceptEdge.weight.desc()))
        return list(result.scalars().all())

    async def get_rules(self, concept_id: str) -> list[ConceptRule]:
        result = await self.db.execute(
            select(ConceptRule)
            .where(ConceptRule.concept_id == concept_id)
            .order_by(ConceptRule.priority.desc())
        )
        return list(result.scalars().all())

    async def get_rules_batch(self, concept_ids: list[str]) -> list[ConceptRule]:
        result = await self.db.execute(
            select(ConceptRule)
            .where(ConceptRule.concept_id.in_(concept_ids))
            .order_by(ConceptRule.priority.desc())
        )
        return list(result.scalars().all())
