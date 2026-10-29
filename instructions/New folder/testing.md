
# Testing Instructions

## Framework
- Use pytest.
- Use FastAPI TestClient for API tests.
- Use temporary SQLite databases.
- Use fixtures and mocks for expensive dependencies.

## Required test areas
- Budget arithmetic and rounding.
- Budget overruns and remaining balances.
- Timeline deadlines and date boundaries.
- Request validation and API errors.
- PDF, TXT, CSV, and JSON extraction.
- Chunking and overlap.
- Stable chunk identifiers.
- Embedding interface behavior.
- Retrieval relevance and metadata filters.
- Empty retrieval.
- Citation traceability.
- Structured LLM output validation.
- Database persistence.
- Task status changes.
- Document deletion and re-indexing.

## RAG evaluation
Maintain a fixed dataset containing:
- User query.
- Expected relevant documents.
- Required facts.
- Expected constraints.
- Expected behavior when evidence is missing.

Measure retrieval quality separately from generation quality.

## Rules
- Unit tests must run without external network access.
- Tests must not require a running Ollama server.
- Mock AI dependencies in unit tests.
- Mark actual local-model tests as integration tests.
- Never silently skip failures.
- Do not use personal event data in fixtures.
- Report only checks that were actually run.
