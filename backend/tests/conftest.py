import io
from pathlib import Path
from typing import Any, Optional
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database.models import Base
from app.database.session import get_db
from app.main import app
from app.rag.embeddings import DeterministicLocalMockEmbedder, set_embedding_service
from app.rag.generation import (
    GeneratedChatPayload,
    GeneratedPlanPayload,
    filter_verified_citations,
    set_generation_service,
)
from app.rag.ingestion import KnowledgeIngestionService, set_ingestion_service
from app.rag.retrieval import ChromaRetrievalService, set_retrieval_service
from app.schemas.event import ThemeRecommendation
from app.schemas.knowledge import SourceCitation


class MockOfflineGenerationService:
    """Deterministic offline mock for local Ollama in unit tests."""

    def __init__(self, inject_fake_citation: bool = False):
        self.inject_fake_citation = inject_fake_citation

    def check_health(self) -> dict[str, Any]:
        return {
            "status": "online",
            "ollama_reachable": True,
            "configured_model": "mock-local-instruct",
            "configured_model_available": True,
            "available_models": ["mock-local-instruct"],
        }

    def generate_event_plan(
        self,
        event_details: dict[str, Any],
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> tuple[GeneratedPlanPayload, list[SourceCitation], str]:
        cited_ids = [c.chunk_id for c in retrieved_chunks[:2]]
        if self.inject_fake_citation:
            cited_ids.append("fake_invented_chunk_9999")

        missing_note = fallback_reason or ""
        if not retrieved_chunks:
            missing_note = "Knowledge base does not contain enough supporting information for this query."

        payload = GeneratedPlanPayload(
            summary=(
                f"Mocked local plan for {event_details.get('name')} ({event_details.get('event_type')}) "
                f"in {event_details.get('location')} with illustrative budget ₹{event_details.get('total_budget'):,} INR."
            ),
            theme_recommendations=[
                ThemeRecommendation(
                    title=str(event_details.get("preferred_theme") or "Star Kingdom Celebration"),
                    tagline="Playful retro celebration with warm lighting",
                    description="Uses reusable fabric backdrops and seasonal florals.",
                    decor_highlights=["Sky-blue drapes", "Coin-gold balloon garland", "LED fairy lights"],
                    catering_notes=f"Menu tailored for {event_details.get('dietary_requirements') or 'Standard'}",
                    estimated_tier="Illustrative Estimate",
                    source_Backed=bool(retrieved_chunks),
                )
            ],
            ai_suggestions=[
                "Book venue 3 weeks early (illustrative estimate).",
                "Preserve the Emergency Reserve for last-minute costs.",
            ],
            cited_chunk_ids=cited_ids,
            missing_evidence_note=missing_note,
        )
        verified = filter_verified_citations(payload.cited_chunk_ids, retrieved_chunks)
        return payload, verified, "mock_ollama"

    def generate_chat_reply(
        self,
        user_message: str,
        event_context: str,
        conversation_history: str,
        retrieved_chunks: list[SourceCitation],
        fallback_reason: Optional[str] = None,
    ) -> tuple[GeneratedChatPayload, list[SourceCitation], str]:
        cited_ids = [c.chunk_id for c in retrieved_chunks[:2]]
        if self.inject_fake_citation:
            cited_ids.append("hallucinated_chunk_id_123")

        missing_note = fallback_reason or ""
        if not retrieved_chunks:
            missing_note = "Knowledge base does not contain enough supporting information for this query."

        reply_str = (
            f"Grounded response for: '{user_message}'. All costs are illustrative estimates in INR."
            if retrieved_chunks
            else f"General suggestion (no matching knowledge base evidence found) for: '{user_message}'."
        )
        payload = GeneratedChatPayload(
            reply=reply_str,
            suggestions=["Keep 10-12% emergency reserve", "Verify vendor quotes in writing"],
            cited_chunk_ids=cited_ids,
            missing_evidence_note=missing_note,
        )
        verified = filter_verified_citations(payload.cited_chunk_ids, retrieved_chunks)
        return payload, verified, "mock_ollama"


@pytest.fixture()
def test_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "SEED_SAMPLE_DATA_ON_STARTUP", False)
    db_path = tmp_path / "test_eventwise.db"
    chroma_dir = tmp_path / "test_chroma"
    upload_dir = tmp_path / "test_uploads"

    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, conn_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    mock_embedder = DeterministicLocalMockEmbedder()
    set_embedding_service(mock_embedder)

    retrieval_svc = ChromaRetrievalService(
        persist_directory=str(chroma_dir),
        collection_name="test_collection",
        embedder=mock_embedder,
    )
    set_retrieval_service(retrieval_svc)

    ingestion_svc = KnowledgeIngestionService(
        upload_dir=str(upload_dir),
        retrieval_service=retrieval_svc,
    )
    set_ingestion_service(ingestion_svc)

    mock_gen = MockOfflineGenerationService()
    set_generation_service(mock_gen)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        db_session = TestingSessionLocal()
        try:
            yield {
                "client": client,
                "db": db_session,
                "retrieval": retrieval_svc,
                "ingestion": ingestion_svc,
                "embedder": mock_embedder,
                "generation": mock_gen,
                "tmp_path": tmp_path,
            }
        finally:
            db_session.close()

    app.dependency_overrides.clear()
    set_embedding_service(None)
    set_retrieval_service(None)
    set_ingestion_service(None)
    set_generation_service(None)


def build_minimal_pdf_bytes(text: str = "EventWise AI Sample PDF Guide for Birthday Planning") -> bytes:
    """Create a valid single-page PDF in memory using reportlab or raw PDF syntax."""
    try:
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(72, 720, text)
        c.showPage()
        c.save()
        return buf.getvalue()
    except Exception:
        # Minimal standard PDF 1.4 byte stream fallback
        stream_content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
        pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
            b"/MediaBox [0 0 612 792] /Contents 5 0 R >> endobj\n"
            b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
            + f"5 0 obj << /Length {len(stream_content)} >> stream\n".encode("latin-1")
            + stream_content
            + b"\nendstream endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
            b"0000000115 00000 n \n0000000229 00000 n \n0000000297 00000 n \n"
            b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n390\n%%EOF"
        )
        return pdf
