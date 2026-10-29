import json
from pathlib import Path
from app.services.seed_service import seed_initial_data

EVAL_DATASET_PATH = Path(__file__).resolve().parent / "eval_dataset.json"


def test_rag_evaluation_dataset_retrieval_and_constraints(test_env):
    """
    Evaluate the RAG pipeline against the fixed evaluation dataset in eval_dataset.json.
    Measures:
    - Expected source document hit rate
    - Required facts coverage in retrieved passages
    - Missing-evidence acknowledgment when location/topic is absent
    - Comparison between RAG-enabled and RAG-disabled responses
    """
    db = test_env["db"]
    retrieval = test_env["retrieval"]
    generation = test_env["generation"]

    seed_initial_data(db)
    cases = json.loads(EVAL_DATASET_PATH.read_text(encoding="utf-8"))

    hits = 0
    total_with_expected_docs = 0

    for case in cases:
        citations, fallback_applied, fallback_reason = retrieval.retrieve(
            query=case["query"],
            event_type=case["event_type"],
            location=case["location"],
            top_k=5,
        )
        retrieved_filenames = {c.filename for c in citations}
        combined_text = " ".join(c.excerpt.lower() for c in citations)

        if case["expected_documents"]:
            total_with_expected_docs += 1
            matched_doc = any(exp in retrieved_filenames for exp in case["expected_documents"])
            if matched_doc:
                hits += 1
            assert matched_doc, f"Case {case['id']} did not retrieve expected docs {case['expected_documents']}"

            for fact in case["required_facts"]:
                norm_fact = fact.lower().replace(",", "")
                norm_combined = combined_text.replace(",", "")
                assert norm_fact in norm_combined, (
                    f"Case {case['id']} missing required fact '{fact}' in retrieved text"
                )
        else:
            # Missing location/topic case (Antarctica) must acknowledge fallback
            assert fallback_applied is True
            assert fallback_reason is not None
            assert "Antarctica" in fallback_reason

        # Compare RAG-enabled vs RAG-disabled generation
        rag_enabled_reply, rag_citations, _ = generation.generate_chat_reply(
            user_message=case["query"],
            event_context="Evaluation Context",
            conversation_history="",
            retrieved_chunks=citations,
            fallback_reason=fallback_reason,
        )
        rag_disabled_reply, disabled_citations, _ = generation.generate_chat_reply(
            user_message=case["query"],
            event_context="Evaluation Context",
            conversation_history="",
            retrieved_chunks=[],
            fallback_reason="RAG disabled for baseline comparison.",
        )

        if citations:
            assert len(rag_citations) >= 1
        assert len(disabled_citations) == 0
        assert "not contain enough supporting information" in rag_disabled_reply.missing_evidence_note.lower() or "rag disabled" in rag_disabled_reply.missing_evidence_note.lower()

    hit_rate = hits / total_with_expected_docs if total_with_expected_docs else 1.0
    assert hit_rate == 1.0
