import pytest
from app.rag.chunking import (
    chunk_document_text,
    generate_deterministic_chunk_id,
    generate_deterministic_doc_id,
)
from app.rag.extraction import (
    DocumentExtractionError,
    extract_text_from_bytes,
    sanitize_filename,
)
from app.schemas.knowledge import KnowledgeEntryCreate
from tests.conftest import build_minimal_pdf_bytes


def test_extract_txt_csv_json_and_pdf():
    # TXT
    fname, ftype, txt = extract_text_from_bytes(
        "guide.txt", b"# Birthday Guide\n\nVenue: Rs 5000\nFood: Rs 8000", "text/plain"
    )
    assert fname == "guide.txt"
    assert ftype == "txt"
    assert "Venue: Rs 5000" in txt

    # CSV
    csv_bytes = b"category,amount_inr\nVenue,5000\nFood,8000\n"
    _, ftype_csv, txt_csv = extract_text_from_bytes("costs.csv", csv_bytes, "text/csv")
    assert ftype_csv == "csv"
    assert "category: Venue | amount_inr: 5000" in txt_csv

    # JSON
    json_bytes = b'{"event_type": "birthday", "items": [{"name": "Cake", "cost": 2000}]}'
    _, ftype_json, txt_json = extract_text_from_bytes("data.json", json_bytes, "application/json")
    assert ftype_json == "json"
    assert "Cake" in txt_json

    # PDF
    pdf_bytes = build_minimal_pdf_bytes("Wedding Checklist Mandap and Catering Guide")
    _, ftype_pdf, txt_pdf = extract_text_from_bytes("wedding.pdf", pdf_bytes, "application/pdf")
    assert ftype_pdf == "pdf"
    assert "Wedding Checklist" in txt_pdf


def test_reject_unsafe_filenames_and_oversized_uploads():
    with pytest.raises(DocumentExtractionError):
        sanitize_filename("../../etc/passwd")
    with pytest.raises(DocumentExtractionError):
        sanitize_filename("malicious.exe")
    with pytest.raises(DocumentExtractionError):
        extract_text_from_bytes("empty.txt", b"", "text/plain")
    with pytest.raises(DocumentExtractionError):
        extract_text_from_bytes("huge.txt", b"a" * 2048, "text/plain", max_bytes=1024)


def test_chunking_overlap_and_deterministic_ids():
    doc_id_1 = generate_deterministic_doc_id("birthday_guide.txt", "Curated")
    doc_id_2 = generate_deterministic_doc_id("birthday_guide.txt", "Curated")
    assert doc_id_1 == doc_id_2

    sample_text = (
        "# Section 1: Budget\n\n"
        + ("Birthday budget allocation details with illustrative INR amounts. " * 12)
        + "\n\n# Section 2: Timeline\n\n"
        + ("Three weeks before finalize guest list and venue selection. " * 12)
    )
    chunks_a = chunk_document_text(
        document_id=doc_id_1,
        text=sample_text,
        base_metadata={"title": "Guide"},
        chunk_size=300,
        chunk_overlap=60,
    )
    chunks_b = chunk_document_text(
        document_id=doc_id_1,
        text=sample_text,
        base_metadata={"title": "Guide"},
        chunk_size=300,
        chunk_overlap=60,
    )
    assert len(chunks_a) >= 3
    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]
    assert generate_deterministic_chunk_id(doc_id_1, 0, chunks_a[0].text) == chunks_a[0].chunk_id


def test_ingestion_reindex_and_delete_idempotency(test_env):
    db = test_env["db"]
    ingestion = test_env["ingestion"]
    retrieval = test_env["retrieval"]

    entry = KnowledgeEntryCreate(
        title="Chennai Vegetarian Catering Guide",
        content=(
            "Pure vegetarian wedding and birthday catering in Chennai typically includes "
            "welcome lime mint cooler, paneer starter, sambar, rasam, vegetable biryani, "
            "and payasam. Illustrative estimate is ₹180 to ₹350 per plate."
        ),
        event_type="birthday",
        category="catering",
        location="Chennai",
        source_label="Illustrative Catering Entry",
        is_illustrative=True,
    )
    doc1 = ingestion.create_structured_entry(db, entry)
    count_after_first = retrieval.get_collection().count()
    assert doc1.chunk_count >= 1
    assert count_after_first == doc1.chunk_count

    # Re-indexing the same document must NOT duplicate vectors
    doc_reindexed = ingestion.reindex_document(db, doc1.id)
    assert retrieval.get_collection().count() == count_after_first
    assert doc_reindexed.id == doc1.id

    # Deleting removes both SQLite record and ChromaDB vectors
    deleted = ingestion.delete_document(db, doc1.id)
    assert deleted is True
    assert retrieval.get_collection().count() == 0
