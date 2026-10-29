# Testing Instructions

## Framework
- Use `pytest`.
- Use FastAPI `TestClient` for API endpoint tests.
- Use temporary SQLite databases and temporary ChromaDB/upload directories per test fixture.
- Use fixtures and deterministic mocks for local AI dependencies in unit tests.

## Required Test Areas
- Budget arithmetic, integer INR validation, and rounding behavior.
- Budget overruns, emergency reserves, and remaining balances.
- Timeline deadlines, event scale adjustments, and past/near-date boundary handling.
- Request validation and API error responses.
- PDF, TXT, CSV, and JSON text extraction.
- Text chunking, overlap, and deterministic chunk identifiers.
- Embedding interface behavior.
- Retrieval relevance, metadata filtering, and fallback behavior.
- Empty retrieval handling.
- Citation traceability (verifying fake citations are stripped).
- Structured LLM output validation and fallback behavior when Ollama is unavailable or returns invalid JSON.
- Database persistence for events, budgets, expenses, tasks, chat, and documents.
- Task status transitions (`pending` -> `in_progress` -> `completed`).
- Document deletion and re-indexing.

## RAG Evaluation
Maintain a fixed evaluation dataset in `backend/tests/evaluation/` containing:
- User query and event context.
- Expected relevant source documents.
- Required facts and constraints.
- Unsupported-claim and missing-evidence behavior.
- Comparison between RAG-enabled and RAG-disabled responses.

## Rules
- Unit tests must run offline without external network access or a running Ollama server.
- Mark tests that invoke the live local Ollama server or full SentenceTransformer model download with `@pytest.mark.integration`.
- Never silently skip failures in unit tests.
- Do not use personal event data in fixtures.
