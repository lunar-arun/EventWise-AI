from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.repository import KnowledgeRepository
from app.database.session import get_db
from app.rag.extraction import DocumentExtractionError
from app.rag.ingestion import get_ingestion_service
from app.rag.retrieval import get_retrieval_service
from app.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeEntryCreate,
    KnowledgeEntryUpdate,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base Manager"])


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
def list_knowledge_documents(
    db: Session = Depends(get_db),
) -> list[KnowledgeDocumentResponse]:
    docs = KnowledgeRepository.list_documents(db)
    return [KnowledgeDocumentResponse.model_validate(d) for d in docs]


@router.post("/upload", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    event_type: str = Form(default="general"),
    category: str = Form(default="general"),
    location: str = Form(default="general"),
    source_label: str = Form(default="Uploaded Knowledge Document (Illustrative)"),
    is_illustrative: bool = Form(default=True),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")
    content_bytes = await file.read()
    try:
        doc = get_ingestion_service().ingest_file_bytes(
            db=db,
            filename=file.filename,
            content_bytes=content_bytes,
            content_type=file.content_type,
            title=title,
            event_type=event_type,
            category=category,
            location=location,
            source_label=source_label,
            is_illustrative=is_illustrative,
        )
        return KnowledgeDocumentResponse.model_validate(doc)
    except DocumentExtractionError as exc:
        msg = str(exc)
        code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if "maximum allowed size" in msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=msg) from exc


@router.post("/entries", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_entry(
    payload: KnowledgeEntryCreate,
    db: Session = Depends(get_db),
) -> KnowledgeDocumentResponse:
    try:
        doc = get_ingestion_service().create_structured_entry(db, payload)
        return KnowledgeDocumentResponse.model_validate(doc)
    except DocumentExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/entries/{document_id}", response_model=KnowledgeDocumentResponse)
def update_knowledge_entry(
    document_id: str,
    payload: KnowledgeEntryUpdate,
    db: Session = Depends(get_db),
) -> KnowledgeDocumentResponse:
    try:
        doc = get_ingestion_service().update_structured_entry(db, document_id, payload)
        return KnowledgeDocumentResponse.model_validate(doc)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge_base(
    payload: KnowledgeSearchRequest,
) -> KnowledgeSearchResponse:
    citations, fallback_applied, fallback_reason = get_retrieval_service().retrieve(
        query=payload.query,
        top_k=payload.top_k,
        event_type=payload.event_type,
        category=payload.category,
        location=payload.location,
    )
    return KnowledgeSearchResponse(
        query=payload.query,
        results=citations,
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
        total_found=len(citations),
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
def delete_knowledge_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    deleted = get_ingestion_service().delete_document(db, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document '{document_id}' not found.",
        )
    return {"status": "deleted", "document_id": document_id}


@router.post("/documents/{document_id}/reindex", response_model=KnowledgeDocumentResponse)
def reindex_knowledge_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> KnowledgeDocumentResponse:
    try:
        doc = get_ingestion_service().reindex_document(db, document_id)
        return KnowledgeDocumentResponse.model_validate(doc)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
