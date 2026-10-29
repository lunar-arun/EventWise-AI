from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import KnowledgeDocumentModel
from app.database.repository import KnowledgeRepository
from app.rag.chunking import chunk_document_text, generate_deterministic_doc_id
from app.rag.extraction import (
    DocumentExtractionError,
    extract_text_from_bytes,
    normalize_whitespace,
)
from app.rag.retrieval import ChromaRetrievalService, get_retrieval_service
from app.schemas.knowledge import KnowledgeEntryCreate, KnowledgeEntryUpdate


class KnowledgeIngestionService:
    def __init__(
        self,
        upload_dir: str | None = None,
        retrieval_service: ChromaRetrievalService | None = None,
    ):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIRECTORY).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._retrieval_service = retrieval_service

    @property
    def retrieval(self) -> ChromaRetrievalService:
        return self._retrieval_service or get_retrieval_service()

    def _safe_storage_path(self, doc_id: str, safe_filename: str) -> Path:
        candidate = (self.upload_dir / f"{doc_id}_{safe_filename}").resolve()
        if not str(candidate).startswith(str(self.upload_dir)):
            raise DocumentExtractionError("Unsafe storage path detected.")
        return candidate

    def ingest_file_bytes(
        self,
        db: Session,
        filename: str,
        content_bytes: bytes,
        content_type: Optional[str] = None,
        title: Optional[str] = None,
        event_type: str = "general",
        category: str = "general",
        location: str = "general",
        source_label: str = "Uploaded Knowledge Document (Illustrative)",
        is_illustrative: bool = True,
        save_to_disk: bool = True,
    ) -> KnowledgeDocumentModel:
        safe_name, file_type, extracted_text = extract_text_from_bytes(
            filename=filename,
            content_bytes=content_bytes,
            content_type=content_type,
        )
        doc_title = (title or Path(safe_name).stem.replace("_", " ").replace("-", " ").title()).strip()
        doc_id = generate_deterministic_doc_id(safe_name, source_label)

        stored_path_str: Optional[str] = None
        if save_to_disk:
            target_path = self._safe_storage_path(doc_id, safe_name)
            target_path.write_bytes(content_bytes)
            stored_path_str = str(target_path)

        return self._index_and_persist(
            db=db,
            doc_id=doc_id,
            title=doc_title,
            filename=safe_name,
            file_type=file_type,
            file_path=stored_path_str,
            raw_content=extracted_text,
            event_type=event_type.lower().strip(),
            category=category.lower().strip(),
            location=location.strip(),
            source_label=source_label.strip(),
            is_illustrative=is_illustrative,
        )

    def create_structured_entry(
        self,
        db: Session,
        entry: KnowledgeEntryCreate,
    ) -> KnowledgeDocumentModel:
        safe_slug = "".join(c if c.isalnum() else "_" for c in entry.title.lower()).strip("_")[:48] or "entry"
        filename = f"{safe_slug}.txt"
        doc_id = generate_deterministic_doc_id(filename, entry.title)
        formatted_text = normalize_whitespace(f"# {entry.title}\n\n{entry.content}")

        return self._index_and_persist(
            db=db,
            doc_id=doc_id,
            title=entry.title,
            filename=filename,
            file_type="entry",
            file_path=None,
            raw_content=formatted_text,
            event_type=entry.event_type.lower().strip(),
            category=entry.category.lower().strip(),
            location=entry.location.strip(),
            source_label=entry.source_label.strip(),
            is_illustrative=entry.is_illustrative,
        )

    def update_structured_entry(
        self,
        db: Session,
        document_id: str,
        update_data: KnowledgeEntryUpdate,
    ) -> KnowledgeDocumentModel:
        doc = KnowledgeRepository.get_document(db, document_id)
        if not doc:
            raise ValueError(f"Knowledge document '{document_id}' not found.")

        new_title = update_data.title if update_data.title is not None else doc.title
        new_content = update_data.content if update_data.content is not None else (doc.raw_content or "")
        new_event_type = update_data.event_type if update_data.event_type is not None else doc.event_type
        new_category = update_data.category if update_data.category is not None else doc.category
        new_location = update_data.location if update_data.location is not None else doc.location
        new_source_label = update_data.source_label if update_data.source_label is not None else doc.source_label
        new_illustrative = update_data.is_illustrative if update_data.is_illustrative is not None else doc.is_illustrative

        formatted_text = normalize_whitespace(new_content)
        if not formatted_text.startswith("#"):
            formatted_text = normalize_whitespace(f"# {new_title}\n\n{formatted_text}")

        return self._index_and_persist(
            db=db,
            doc_id=doc.id,
            title=new_title,
            filename=doc.filename,
            file_type=doc.file_type,
            file_path=doc.file_path,
            raw_content=formatted_text,
            event_type=new_event_type.lower().strip(),
            category=new_category.lower().strip(),
            location=new_location.strip(),
            source_label=new_source_label.strip(),
            is_illustrative=new_illustrative,
        )

    def reindex_document(self, db: Session, document_id: str) -> KnowledgeDocumentModel:
        doc = KnowledgeRepository.get_document(db, document_id)
        if not doc:
            raise ValueError(f"Knowledge document '{document_id}' not found.")

        text_to_index = doc.raw_content
        if not text_to_index and doc.file_path:
            disk_path = Path(doc.file_path)
            if disk_path.exists():
                _, _, text_to_index = extract_text_from_bytes(doc.filename, disk_path.read_bytes())

        if not text_to_index:
            doc.status = "failed"
            doc.error_message = "Document content unavailable for re-indexing."
            return KnowledgeRepository.upsert_document(db, doc)

        return self._index_and_persist(
            db=db,
            doc_id=doc.id,
            title=doc.title,
            filename=doc.filename,
            file_type=doc.file_type,
            file_path=doc.file_path,
            raw_content=text_to_index,
            event_type=doc.event_type,
            category=doc.category,
            location=doc.location,
            source_label=doc.source_label,
            is_illustrative=doc.is_illustrative,
        )

    def delete_document(self, db: Session, document_id: str) -> bool:
        doc = KnowledgeRepository.get_document(db, document_id)
        if not doc:
            return False

        self.retrieval.delete_document_vectors(document_id)
        if doc.file_path:
            try:
                disk_path = Path(doc.file_path).resolve()
                if str(disk_path).startswith(str(self.upload_dir)) and disk_path.exists():
                    disk_path.unlink()
            except Exception:
                pass
        KnowledgeRepository.delete_document(db, doc)
        return True

    def _index_and_persist(
        self,
        db: Session,
        doc_id: str,
        title: str,
        filename: str,
        file_type: str,
        file_path: Optional[str],
        raw_content: str,
        event_type: str,
        category: str,
        location: str,
        source_label: str,
        is_illustrative: bool,
    ) -> KnowledgeDocumentModel:
        base_metadata = {
            "title": title,
            "filename": filename,
            "file_type": file_type,
            "event_type": event_type,
            "category": category,
            "location": location,
            "source_label": source_label,
            "is_illustrative": is_illustrative,
        }
        try:
            chunks = chunk_document_text(
                document_id=doc_id,
                text=raw_content,
                base_metadata=base_metadata,
            )
            if not chunks:
                raise DocumentExtractionError("Document produced zero valid chunks after normalization.")
            indexed_count = self.retrieval.index_chunks(chunks)
            doc_model = KnowledgeDocumentModel(
                id=doc_id,
                title=title,
                filename=filename,
                file_type=file_type,
                file_path=file_path,
                raw_content=raw_content,
                event_type=event_type,
                category=category,
                location=location,
                source_label=source_label,
                is_illustrative=is_illustrative,
                status="indexed",
                chunk_count=indexed_count,
                error_message=None,
            )
            return KnowledgeRepository.upsert_document(db, doc_model)
        except Exception as exc:
            failed_model = KnowledgeDocumentModel(
                id=doc_id,
                title=title,
                filename=filename,
                file_type=file_type,
                file_path=file_path,
                raw_content=raw_content,
                event_type=event_type,
                category=category,
                location=location,
                source_label=source_label,
                is_illustrative=is_illustrative,
                status="failed",
                chunk_count=0,
                error_message=str(exc),
            )
            KnowledgeRepository.upsert_document(db, failed_model)
            raise


_active_ingestion_service: KnowledgeIngestionService | None = None


def get_ingestion_service() -> KnowledgeIngestionService:
    global _active_ingestion_service
    if _active_ingestion_service is None:
        _active_ingestion_service = KnowledgeIngestionService()
    return _active_ingestion_service


def set_ingestion_service(service: KnowledgeIngestionService | None) -> None:
    global _active_ingestion_service
    _active_ingestion_service = service
