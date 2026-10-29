from pathlib import Path
import pytest

from app.rag.embeddings import SentenceTransformerEmbedder
from app.rag.generation import OllamaGenerationService
from app.rag.retrieval import ChromaRetrievalService
from app.rag.chunking import chunk_document_text


@pytest.mark.integration
def test_real_sentence_transformer_and_chromadb_integration(tmp_path: Path):
    """Integration test using actual local SentenceTransformer embeddings and ChromaDB."""
    embedder = SentenceTransformerEmbedder("sentence-transformers/all-MiniLM-L6-v2")
    retrieval = ChromaRetrievalService(
        persist_directory=str(tmp_path / "live_chroma"),
        collection_name="live_eval",
        embedder=embedder,
    )
    chunks = chunk_document_text(
        document_id="doc_live_01",
        text=(
            "# Birthday Budget Guide\n\n"
            "For a ₹25,000 birthday celebration in Chennai, allocate ₹5,000 for Venue, "
            "₹8,000 for Food and beverages, and ₹3,000 for Emergency reserve."
        ),
        base_metadata={
            "title": "Live Birthday Guide",
            "filename": "live_bday.txt",
            "event_type": "birthday",
            "category": "budget",
            "location": "Chennai",
            "source_label": "Integration Test Guide",
            "is_illustrative": True,
        },
    )
    count = retrieval.index_chunks(chunks)
    assert count >= 1

    results, _, _ = retrieval.retrieve(
        query="What is the ₹25,000 birthday venue and food allocation?",
        event_type="birthday",
        top_k=2,
    )
    assert len(results) >= 1
    assert "5,000" in results[0].excerpt


@pytest.mark.integration
def test_local_ollama_health_check_integration():
    """Verify the Ollama health check returns a structured status dictionary."""
    svc = OllamaGenerationService()
    health = svc.check_health()
    assert "ollama_reachable" in health
    assert "configured_model" in health
