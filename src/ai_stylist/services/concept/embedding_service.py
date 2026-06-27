from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.config import settings
from ai_stylist.models.concept import Concept
from ai_stylist.repositories.concept_repo import ConceptRepository
from ai_stylist.services.llm.gemini_client import GeminiClient


@dataclass
class ResolvedConcept:
    input_term: str
    concept_id: str
    concept_name: str
    concept_type: str
    confidence: float


class EmbeddingService:
    """Semantic concept lookup via Gemini text-embedding-004 + pgvector."""

    def __init__(self, gemini: GeminiClient):
        self._gemini = gemini

    async def embed_terms(self, terms: list[str]) -> list[list[float]]:
        return await self._gemini.embed_texts(terms)

    def concept_text(self, concept: Concept) -> str:
        alias_str = " ".join(a.alias for a in concept.aliases)
        return f"{concept.name} {concept.type} {concept.description or ''} {alias_str}".strip()

    async def resolve_terms(self, terms: list[str], db: AsyncSession) -> list[ResolvedConcept]:
        """Embed terms and find the closest concept for each via cosine similarity."""
        if not terms:
            return []

        embeddings = await self.embed_terms(terms)
        repo = ConceptRepository(db)
        results: list[ResolvedConcept] = []
        seen_ids: set[str] = set()

        for term, embedding in zip(terms, embeddings):
            matches = await repo.find_similar(embedding, k=1, min_similarity=settings.concept_similarity_threshold)
            if matches:
                concept, similarity = matches[0]
                if concept.id not in seen_ids:
                    seen_ids.add(concept.id)
                    results.append(ResolvedConcept(
                        input_term=term,
                        concept_id=concept.id,
                        concept_name=concept.name,
                        concept_type=concept.type,
                        confidence=round(similarity, 3),
                    ))

        return results

    async def resolve_from_intent(self, intent: dict, db: AsyncSession) -> list[ResolvedConcept]:
        return await self.resolve_terms(_extract_intent_terms(intent), db)

    async def index_all(self, db: AsyncSession) -> int:
        """Embed every concept and persist the vectors. Returns number indexed."""
        repo = ConceptRepository(db)
        concepts = await repo.get_all_for_indexing()
        if not concepts:
            return 0

        texts = [self.concept_text(c) for c in concepts]
        embeddings = await self._gemini.embed_texts(texts)

        for concept, embedding in zip(concepts, embeddings):
            concept.embedding = embedding

        await db.commit()
        return len(concepts)


def _extract_intent_terms(intent: dict) -> list[str]:
    terms: list[str] = []
    if style_prefs := intent.get("style_preferences", []):
        terms.extend(style_prefs)
    if requested_items := intent.get("requested_items", []):
        terms.extend(requested_items)
    if occasion := intent.get("occasion"):
        terms.append(occasion)
    if destination := intent.get("destination"):
        terms.append(destination)
    if body_ctx := intent.get("body_context", {}):
        if h := body_ctx.get("height_group"):
            terms.append(h)
    if modesty := intent.get("modesty_level"):
        terms.append(modesty)
    if comfort := intent.get("comfort_needs", []):
        terms.extend(comfort)
    if raw := intent.get("raw_keywords", []):
        terms.extend(raw)
    return terms
