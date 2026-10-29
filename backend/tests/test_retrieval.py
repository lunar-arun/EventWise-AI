from app.rag.generation import filter_verified_citations
from app.schemas.knowledge import KnowledgeEntryCreate


def test_empty_retrieval_handled_gracefully(test_env):
    retrieval = test_env["retrieval"]
    results, fallback_applied, reason = retrieval.retrieve(
        query="birthday party decoration ideas",
        event_type="birthday",
    )
    assert results == []
    assert fallback_applied is True
    assert reason is not None
    assert "no indexed documents" in reason.lower()


def test_retrieval_relevance_and_location_fallback(test_env):
    db = test_env["db"]
    ingestion = test_env["ingestion"]
    retrieval = test_env["retrieval"]

    ingestion.create_structured_entry(
        db,
        KnowledgeEntryCreate(
            title="Birthday Balloon and Fairy Light Decor Guide",
            content=(
                "Use reusable fabric drapes, warm LED fairy lights, and seasonal marigold garlands "
                "to keep birthday decoration within an illustrative ₹3,000 INR allocation."
            ),
            event_type="birthday",
            category="decoration",
            location="Chennai",
            source_label="Decor Guide",
            is_illustrative=True,
        ),
    )
    ingestion.create_structured_entry(
        db,
        KnowledgeEntryCreate(
            title="Wedding Mandap & Sadhya Feast Guide",
            content=(
                "Traditional wedding preparation includes Kalyana Mandapam booking, floral stage arch, "
                "and multi-course banana leaf Sadhya catering for 200 guests."
            ),
            event_type="wedding",
            category="planning",
            location="Madurai",
            source_label="Wedding Guide",
            is_illustrative=True,
        ),
    )

    # Query for birthday decoration in Chennai
    bday_results, fb_applied, _ = retrieval.retrieve(
        query="birthday balloon fairy light decoration 3000 INR",
        event_type="birthday",
        category="decoration",
        location="Chennai",
        top_k=2,
    )
    assert len(bday_results) >= 1
    assert bday_results[0].event_type == "birthday"
    assert "Birthday Balloon" in bday_results[0].title

    # Query for a city not in the KB ("Guwahati") -> falls back to general/available birthday guidance and notes limitation
    loc_results, loc_fallback, loc_reason = retrieval.retrieve(
        query="birthday decoration fairy lights",
        event_type="birthday",
        location="Guwahati",
        top_k=2,
    )
    assert len(loc_results) >= 1
    assert loc_fallback is True
    assert loc_reason is not None
    assert "Guwahati" in loc_reason


def test_citation_traceability_strips_fabricated_chunk_ids(test_env):
    db = test_env["db"]
    ingestion = test_env["ingestion"]
    retrieval = test_env["retrieval"]

    doc = ingestion.create_structured_entry(
        db,
        KnowledgeEntryCreate(
            title="Community Event Sound and PA Checklist",
            content=(
                "Community gatherings require dual PA speakers, cordless microphones, drinking water stations, "
                "and waste segregation bins every 25 meters."
            ),
            event_type="community",
            category="planning",
            location="General India",
            source_label="Community Guide",
            is_illustrative=True,
        ),
    )
    retrieved, _, _ = retrieval.retrieve("community PA speakers microphones", event_type="community")
    assert len(retrieved) >= 1
    real_chunk_id = retrieved[0].chunk_id

    verified = filter_verified_citations(
        ["fabricated_chunk_001", real_chunk_id, "hallucinated_source_999"],
        retrieved,
    )
    assert len(verified) == 1
    assert verified[0].chunk_id == real_chunk_id
    assert verified[0].document_id == doc.id
