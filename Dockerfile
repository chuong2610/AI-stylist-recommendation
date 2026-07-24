FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY scripts/ scripts/

RUN uv sync --frozen --no-dev

RUN uv run python -c "from fastembed import SparseTextEmbedding; SparseTextEmbedding(model_name='Qdrant/bm25')"

EXPOSE 8000

ENTRYPOINT ["uv", "run", "python", "scripts/serve.py"]
