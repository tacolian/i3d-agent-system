# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

i3d-agent-system is a multi-agent retrieval system for 3D CAD models built with FastAPI and LangGraph. It uses RAG (Retrieval Augmented Generation) with hybrid search (BM25 + vector search) and supports multi-tenant isolation via PostgreSQL RLS.

**Core Technologies:**
- FastAPI for REST API
- LangGraph for multi-agent orchestration
- PostgreSQL with pgvector for vector storage
- Redis for caching
- RabbitMQ for async tasks
- LangSmith for observability

## Common Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run all tests
pytest backend/tests -v

# Run specific test directory
pytest backend/tests/unit -v
pytest backend/tests/integration -v

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Code Quality

```bash
# Format code (line length: 100)
black backend/

# Lint code
ruff check backend/

# Type checking
mypy backend/
```

### Docker Deployment

```bash
cd docker
docker-compose up -d
```

## Architecture

### Multi-Agent Workflow (LangGraph)

The system uses LangGraph to orchestrate 4 specialized agents:

1. **Search Agent** - Direct CAD model retrieval
2. **Analysis Agent** - Deep analysis of models/specifications
3. **Recommendation Agent** - Similar model suggestions
4. **QA Agent** - Question answering about models

**Flow:** `intent → retrieval → [agent] → synthesizer → response`

Key files:
- [backend/graph/workflow.py](backend/graph/workflow.py) - Main workflow orchestration
- [backend/graph/state.py](backend/graph/state.py) - Shared state between agents
- [backend/graph/nodes.py](backend/graph/nodes.py) - Node implementations
- [backend/agents/base.py](backend/agents/base.py) - Base agent class with LLM routing

### RAG Pipeline

Hybrid search combining:
- **BM25** (keyword) via `RAG_BM25_WEIGHT` (default: 0.3)
- **Vector search** (semantic) via `RAG_VECTOR_WEIGHT` (default: 0.7)
- **Reranker** to refine top-K results

Key files:
- [backend/rag/hybrid_search.py](backend/rag/hybrid_search.py) - Search orchestration
- [backend/rag/retriever.py](backend/rag/retriever.py) - Vector/BM25 retrieval
- [backend/rag/reranker.py](backend/rag/reranker.py) - Result reranking

### Multi-Tenancy

Tenant isolation via:
- PostgreSQL RLS (Row Level Security)
- Tenant-specific vector tables: `tenant_{tenant_id}_vectors`
- Tenant-specific MinIO buckets: `{tenant_id}-files`

Supported tenants (configurable via `SUPPORTED_TENANTS`): `shenfa`, `meidi`, `dongjiang`, `huabei`

API requests require `X-Tenant-ID` header.

## Configuration

Configuration via environment variables or `.env` file. Key settings:

- `DATABASE_URL` - PostgreSQL with asyncpg
- `REDIS_URL` - Redis for caching
- `RABBITMQ_URL` - RabbitMQ for tasks
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` - LLM providers
- `LANGCHAIN_API_KEY` - LangSmith tracing
- `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - Object storage

Model routing (automatic based on task complexity):
- `LLM_MODEL_FAST` - Claude Haiku for simple tasks
- `LLM_MODEL_PRIMARY` - Claude Sonnet for standard tasks
- `LLM_MODEL_COMPLEX` - Claude Opus for complex tasks

## Database

- PostgreSQL 15+ with pgvector extension
- Async SQLAlchemy 2.0 with asyncpg
- Alembic for migrations (if needed)

Connection pooling configured via `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`.

## Testing

Tests use pytest with asyncio mode set to `auto`. Fixtures defined in [backend/tests/conftest.py](backend/tests/conftest.py).

Test database: `i3d_test` (separate from dev/prod databases)
