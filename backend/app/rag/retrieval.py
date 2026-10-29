from pathlib import Path
from typing import Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.rag.chunking import DocumentChunk
from app.rag.embeddings import EmbeddingProvider, get_embedding_service
from app.schemas.knowledge import SourceCitation


class EmbeddingModelMismatchError(RuntimeError):
    """Raised when an existing ChromaDB collection was indexed with a different embedding model."""


class ChromaRetrievalService:
    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str | None = None,
        embedder: EmbeddingProvider | None = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self._embedder = embedder
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    @property
    def embedder(self) -> EmbeddingProvider:
        return self._embedder or get_embedding_service()

    def get_collection(self):
        active_model = self.embedder.model_name
        collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine", "embedding_model": active_model},
        )
        stored_model = (collection.metadata or {}).get("embedding_model")
        if stored_model and stored_model != active_model and collection.count() > 0:
            raise EmbeddingModelMismatchError(
                f"ChromaDB collection '{self.collection_name}' was built with embedding model "
                f"'{stored_model}', but current EMBEDDING_MODEL is '{active_model}'. "
                "Rebuild or re-index the collection before querying."
            )
        return collection

    def reset_collection(self) -> None:
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.get_collection()

    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0
        collection = self.get_collection()
        doc_id = chunks[0].document_id
        # Remove any previous chunks for this document_id before upserting so re-indexing never leaves stale chunks
        self.delete_document_vectors(doc_id)

        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        embeddings = self.embedder.embed_texts(texts)

        sanitized_metadatas: list[dict[str, Any]] = []
        for c in chunks:
            meta: dict[str, Any] = {}
            for k, v in c.metadata.items():
                if v is None:
                    meta[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            sanitized_metadatas.append(meta)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=sanitized_metadatas,
        )
        return len(chunks)

    def delete_document_vectors(self, document_id: str) -> None:
        collection = self.get_collection()
        try:
            collection.delete(where={"document_id": document_id})
        except Exception:
            pass

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        event_type: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        max_distance: float = 1.65,
    ) -> tuple[list[SourceCitation], bool, Optional[str]]:
        """
        Retrieve relevant passages with intelligent metadata filtering and automatic
        fallback to general guidance when location-specific or strict category filters
        yield sparse results.
        Returns (citations, fallback_applied, fallback_reason).
        """
        k = top_k or settings.RAG_TOP_K
        collection = self.get_collection()
        total_in_store = collection.count()
        if total_in_store == 0:
            return [], True, "The local knowledge base currently contains no indexed documents."

        query_embedding = self.embedder.embed_query(query)
        fallback_applied = False
        fallback_reason: Optional[str] = None

        # Build progressive filter candidates:
        # 1. Event type + category (if specified)
        # 2. Event type or 'general'
        # 3. Unfiltered semantic search
        filter_attempts: list[tuple[Optional[dict[str, Any]], Optional[str]]] = []

        norm_event = event_type.strip().lower() if event_type and event_type.strip().lower() not in ("all", "") else None
        norm_cat = category.strip().lower() if category and category.strip().lower() not in ("all", "general", "") else None
        norm_loc = location.strip().lower() if location and location.strip().lower() not in ("all", "general", "") else None

        if norm_event and norm_cat:
            filter_attempts.append(
                (
                    {
                        "$and": [
                            {"event_type": {"$in": [norm_event, "general"]}},
                            {"category": norm_cat},
                        ]
                    },
                    None,
                )
            )
        if norm_event:
            filter_attempts.append(
                (
                    {"event_type": {"$in": [norm_event, "general"]}},
                    f"Broadened category filter to include all '{norm_event}' and general planning knowledge." if norm_cat else None,
                )
            )
        filter_attempts.append(
            (
                None,
                "Used general event planning knowledge across all categories.",
            )
        )

        collected: dict[str, SourceCitation] = {}

        for where_clause, reason_if_used in filter_attempts:
            try:
                n_results = min(max(k * 2, 6), total_in_store)
                query_kwargs: dict[str, Any] = {
                    "query_embeddings": [query_embedding],
                    "n_results": n_results,
                    "include": ["documents", "metadatas", "distances"],
                }
                if where_clause is not None:
                    query_kwargs["where"] = where_clause

                raw = collection.query(**query_kwargs)
            except Exception:
                continue

            ids_list = (raw.get("ids") or [[]])[0]
            docs_list = (raw.get("documents") or [[]])[0]
            metas_list = (raw.get("metadatas") or [[]])[0]
            dists_list = (raw.get("distances") or [[]])[0]

            for cid, doc_text, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
                if not cid or not doc_text:
                    continue
                float_dist = float(dist) if dist is not None else 1.0
                if float_dist > max_distance:
                    continue

                # Slight boost if location matches user location
                doc_loc = str((meta or {}).get("location", "general")).lower()
                adjusted_dist = float_dist
                if norm_loc and norm_loc in doc_loc:
                    adjusted_dist = max(0.0, float_dist - 0.08)

                # Convert cosine distance [0, 2] to a bounded similarity score [0, 1]
                sim_score = round(max(0.0, min(1.0, 1.0 - (adjusted_dist / 2.0))), 4)

                if cid not in collected:
                    collected[cid] = SourceCitation(
                        document_id=str((meta or {}).get("document_id", "unknown")),
                        chunk_id=str(cid),
                        title=str((meta or {}).get("title", "Knowledge Guide")),
                        filename=str((meta or {}).get("filename", "guide.txt")),
                        category=str((meta or {}).get("category", "general")),
                        event_type=str((meta or {}).get("event_type", "general")),
                        location=str((meta or {}).get("location", "general")),
                        source_label=str((meta or {}).get("source_label", "Curated EventWise Guide")),
                        is_illustrative=bool((meta or {}).get("is_illustrative", True)),
                        excerpt=str(doc_text),
                        distance=round(float_dist, 4),
                        similarity_score=sim_score,
                    )

            if len(collected) >= k:
                if reason_if_used and not fallback_reason:
                    fallback_applied = True
                    fallback_reason = reason_if_used
                break
            elif reason_if_used:
                fallback_applied = True
                fallback_reason = reason_if_used

        sorted_results = sorted(
            collected.values(),
            key=lambda item: (-item.similarity_score, item.distance, item.chunk_id),
        )[:k]

        if norm_loc and sorted_results:
            has_loc_match = any(
                norm_loc in c.location.lower() or norm_loc in c.excerpt.lower()
                for c in sorted_results
            )
            if not has_loc_match:
                fallback_applied = True
                loc_msg = (
                    f"No location-specific documents for '{location}' were found in the knowledge base; "
                    "using general India/illustrative event planning guidance."
                )
                fallback_reason = f"{fallback_reason} {loc_msg}".strip() if fallback_reason else loc_msg

        if not sorted_results:
            return (
                [],
                True,
                "No sufficiently relevant passages were found in the knowledge base for this query.",
            )

        return sorted_results, fallback_applied, fallback_reason


_active_retrieval_service: ChromaRetrievalService | None = None


def get_retrieval_service() -> ChromaRetrievalService:
    global _active_retrieval_service
    if _active_retrieval_service is None:
        _active_retrieval_service = ChromaRetrievalService()
    return _active_retrieval_service


def set_retrieval_service(service: ChromaRetrievalService | None) -> None:
    global _active_retrieval_service
    _active_retrieval_service = service
