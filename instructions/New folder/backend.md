
# Backend Development Instructions

## Stack
- Python.
- FastAPI.
- Pydantic.
- SQLite.
- Ollama.
- Sentence Transformers.
- ChromaDB.
- PyPDF.

## Architecture
- routes/: HTTP endpoints and validation.
- schemas/: Pydantic request and response models.
- services/: business logic.
- rag/: retrieval and generation pipeline.
- database/: persistence and repositories.
- prompts/: prompt templates.
- tests/: unit and integration tests.

Keep HTTP handlers thin. Put business logic in services.

## API design
- Validate every request.
- Use consistent response schemas.
- Return appropriate HTTP status codes.
- Document endpoints using OpenAPI.
- Handle missing records and invalid inputs.
- Do not expose internal stack traces.

## Business logic
- Calculate budgets in Python.
- Detect budget overruns.
- Track planned and actual spending.
- Preserve user-approved budgets.
- Calculate deadlines relative to the event date.
- Support pending, in_progress, and completed task states.
- Persist events, expenses, tasks, and chat history.

## Ollama integration
- Use only the locally configured Ollama service.
- Make model settings configurable.
- Handle missing models, timeouts, and server failures.
- Validate model output with Pydantic.
- Never trust generated JSON without validating its content.
- Never allow model output to bypass budget validation.

## Database
- Use explicit models and relationships.
- Use transactions for related writes.
- Keep schema changes reproducible.
- Use temporary databases in tests.
- Keep persistent data out of version control.

## Security
- Validate uploads and restrict file sizes.
- Prevent path traversal.
- Never execute uploaded content.
- Keep CORS restricted to configured origins.
- Do not expose private file paths.
- Treat user input and retrieved content as untrusted.

## Testing
- Test business logic independently.
- Mock local AI dependencies in unit tests.
- Test API validation and error handling.
- Test persistence and date calculations.
- Separate mocked tests from actual local-model integration tests.
