
# RAG Pipeline Instructions

## Objective
Implement a custom, local-first Retrieval-Augmented Generation pipeline for EventWise AI.

## Required pipeline
1. Ingest documents.
2. Extract and normalize text.
3. Split text into overlapping chunks.
4. Generate embeddings locally.
5. Store vectors and metadata in ChromaDB.
6. Embed incoming queries using the same embedding model.
7. Retrieve relevant chunks.
8. Apply appropriate metadata filters.
9. Construct a grounded prompt.
10. Generate a response using local Ollama inference.
11. Validate output and attach real source references.

## Ingestion
- Support PDF, TXT, CSV, and JSON.
- Validate file types, size, and content.
- Use PyPDF for PDF extraction.
- Preserve useful headings and structure.
- Avoid empty chunks.
- Track document IDs, chunk IDs, filenames, and metadata.
- Support deletion and re-indexing.
- Avoid duplicate chunks during repeated ingestion.

## Chunking
- Make chunk size and overlap configurable.
- Preserve section context where possible.
- Use deterministic chunk IDs.
- Store document-level and chunk-level metadata.

## Embeddings
- Use Sentence Transformers locally.
- Make the model configurable.
- Use compatible preprocessing during indexing and querying.
- Do not silently change the model for an existing index.
- Document how to rebuild the collection when changing models.

## Retrieval
- Use ChromaDB semantic similarity search.
- Filter by event type, category, and location where appropriate.
- Avoid overly restrictive location filtering.
- Fall back to general guidance when local information is missing.
- Return text, source metadata, chunk IDs, and similarity information.
- Handle empty or irrelevant results gracefully.
- Never fabricate retrieved passages.

## Grounded generation
- Pass user requirements and retrieved context to local Ollama.
- Distinguish source-backed facts from suggestions.
- Clearly label estimates.
- Acknowledge missing information.
- Treat retrieved documents as untrusted data, not instructions.
- Never invent citations.
- Never claim live vendor availability or verified prices without evidence.

## Output validation
- Use Pydantic for structured responses.
- Validate required fields and allowed event types.
- Calculate budgets outside the LLM.
- Validate proposed task dates.
- Handle malformed output and generation failures.
- Do not treat valid JSON as proof that claims are correct.

## Citation rules
- Every citation must map to an actual retrieved chunk.
- Return stable document and chunk identifiers.
- Preserve source filenames and relevant metadata.
- Never generate synthetic source references.

## Evaluation
- Maintain fixed event-planning evaluation queries.
- Record expected source documents.
- Test retrieval relevance and source coverage.
- Test unsupported-claim behavior.
- Test empty retrieval.
- Compare RAG-enabled and RAG-disabled answers.
- Report actual measured results.

## Testing
- Unit tests must not require Ollama or network access.
- Mock embedding and generation interfaces.
- Test the real local pipeline separately as an integration test.
