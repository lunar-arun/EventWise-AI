# Backend Development Instructions

## Stack
- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 + SQLite
- Ollama (local HTTP API)
- Sentence Transformers
- ChromaDB
- PyPDF

## Architecture
- `routes/`: HTTP endpoints and request/response validation.
- `schemas/`: Pydantic request and response models.
- `services/`: deterministic business logic and orchestration.
- `rag/`: document ingestion, extraction, chunking, embeddings, retrieval, and grounded generation.
- `database/`: SQLAlchemy models, session management, and repository helpers.
- `prompts/`: prompt templates for planning, RAG, and chat.
- `tests/`: unit, API, and RAG evaluation tests.

Keep HTTP handlers thin. Put business logic in services.

## API Design
- Validate every request with Pydantic schemas.
- Use consistent response schemas and error payloads.
- Return appropriate HTTP status codes (`200`, `201`, `400`, `404`, `413`, `422`, `500`, `503`).
- Document endpoints using FastAPI OpenAPI metadata.
- Handle missing records and invalid inputs cleanly.
- Do not expose internal stack traces or local filesystem paths.

## Business Logic
- Represent all monetary values in validated integer Indian Rupees (INR).
- Calculate budgets, allocations, actual expenses, emergency reserves, and remaining balances deterministically in Python.
- Detect budget overruns (`planned_total > total_budget` or `actual_total > total_budget`).
- Preserve user-approved budgets; never allow LLM responses to overwrite total budgets without user approval.
- Calculate deadlines relative to the event date, clamping past dates safely when events are scheduled soon or in the past.
- Support `pending`, `in_progress`, and `completed` task states.
- Persist events, budget categories, expenses, tasks, chat sessions, chat messages, and knowledge documents in SQLite.

## Ollama Integration
- Use only the locally configured Ollama service (`OLLAMA_BASE_URL`).
- Make model settings configurable (`OLLAMA_MODEL`).
- Handle missing models, timeouts, and server unavailability gracefully with deterministic fallback plans.
- Validate model output with Pydantic.
- Never trust generated JSON without validating its content.
- Never allow model output to bypass Python budget validation.

## Database
- Use explicit SQLAlchemy models and relationships.
- Use transactions for related writes.
- Keep schema initialization reproducible.
- Use temporary SQLite databases in tests.
- Keep persistent data out of version control.

## Security
- Validate uploads (extension, MIME type, content, and `MAX_UPLOAD_SIZE_MB`).
- Sanitize filenames and prevent path traversal.
- Never execute uploaded content.
- Keep CORS restricted to configured origins (`FRONTEND_ORIGIN`).
- Treat user input and retrieved content as untrusted data.

## Testing
- Test business logic independently.
- Mock local AI dependencies in unit tests.
- Test API validation and error handling.
- Test persistence and date calculations.
- Separate mocked unit tests from actual local-model integration tests (`@pytest.mark.integration`).
