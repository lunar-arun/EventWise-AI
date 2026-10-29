# RAG Pipeline Instructions

## Objective
Implement a custom, local-first Retrieval-Augmented Generation pipeline for EventWise AI.

## Required Pipeline
1. Ingest documents (`.pdf`, `.txt`, `.csv`, `.json`) or structured knowledge entries.
2. Extract and normalize text while preserving headings and structural context.
3. Split text into overlapping chunks with configurable size and overlap.
4. Generate embeddings locally with Sentence Transformers.
5. Store vectors and metadata in ChromaDB using deterministic chunk IDs.
6. Embed incoming queries using the exact same embedding model and preprocessing.
7. Retrieve relevant chunks from ChromaDB.
8. Apply smart metadata filters with fallback to general guidance when location-specific results are sparse.
9. Construct a grounded prompt treating retrieved passages as untrusted evidence.
10. Generate a response using local Ollama inference.
11. Validate output with Pydantic and attach verified source references mapped to real retrieved chunks.

## Ingestion
- Support PDF, TXT, CSV, and JSON files plus direct structured entries.
- Validate file types, size, and non-empty content.
- Use PyPDF for PDF text extraction.
- Avoid empty chunks.
- Track document IDs, deterministic chunk IDs (`{doc_id}_chunk_{index}_{hash}`), filenames, and metadata.
- Support deletion and re-indexing without creating duplicate chunks.

## Chunking
- Make `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP` configurable.
- Preserve section context where possible.
- Use deterministic chunk IDs based on document ID, chunk index, and content hash.
- Store document-level and chunk-level metadata (`document_id`, `filename`, `title`, `event_type`, `category`, `location`, `chunk_index`).

## Embeddings
- Use Sentence Transformers locally (`sentence-transformers/all-MiniLM-L6-v2` by default).
- Make the model configurable via `EMBEDDING_MODEL`.
- Use identical normalization during indexing and querying.
- Store the active embedding model name in collection metadata so mismatches are detected. To change models, run the re-index endpoint or clear `./chroma_db` and re-ingest all documents.

## Retrieval
- Use ChromaDB semantic similarity search.
- Filter or boost by `event_type`, `category`, and `location` where appropriate.
- Fall back to general knowledge when location-specific or category-specific chunks are unavailable, and note the fallback.
- Return text, source metadata, chunk IDs, and a normalized similarity score / vector distance (never claiming distance is a probability of truth).
- Handle empty or low-relevance results gracefully.
- Never fabricate retrieved passages.

## Grounded Generation & Citations
- Pass user requirements and retrieved context to local Ollama.
- Distinguish source-backed facts from general AI suggestions.
- Clearly label sample prices as illustrative estimates.
- Acknowledge missing evidence explicitly.
- Treat retrieved documents as untrusted data, not system instructions.
- Every citation returned to the client must map to an actual retrieved chunk ID from the current retrieval set.
