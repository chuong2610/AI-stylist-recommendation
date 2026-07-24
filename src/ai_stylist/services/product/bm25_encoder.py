"""
Local BM25 sparse-vector encoding for Qdrant hybrid search.

Runs fully offline via fastembed (no LLM call, deterministic). Both
scripts/init_qdrant.py (indexing) and hybrid_retriever.py (querying) must use
this same encoder so term hashes and the query/document weighting scheme
line up; Qdrant applies the actual IDF weighting server-side via the
collection's sparse vector "idf" modifier (see docs/qdrant hybrid search).
"""
from fastembed import SparseTextEmbedding

_MODEL_NAME = "Qdrant/bm25"
_model: SparseTextEmbedding | None = None


def _get_model() -> SparseTextEmbedding:
    global _model
    if _model is None:
        _model = SparseTextEmbedding(model_name=_MODEL_NAME)
    return _model


def encode_documents(texts: list[str]) -> list[dict]:
    if not texts:
        return []
    return [
        {"indices": embedding.indices.tolist(), "values": embedding.values.tolist()}
        for embedding in _get_model().embed(texts)
    ]


def encode_query(text: str) -> dict:
    embedding = next(iter(_get_model().query_embed(text)))
    return {"indices": embedding.indices.tolist(), "values": embedding.values.tolist()}
