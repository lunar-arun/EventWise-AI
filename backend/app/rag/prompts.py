from pathlib import Path
from typing import Any

from app.schemas.knowledge import SourceCitation

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_template(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def format_retrieved_passages(citations: list[SourceCitation]) -> str:
    if not citations:
        return "NO RETRIEVED PASSAGES FOUND IN LOCAL KNOWLEDGE BASE."
    blocks: list[str] = []
    for idx, c in enumerate(citations, start=1):
        blocks.append(
            f"--- PASSAGE {idx} (UNTRUSTED DOCUMENT DATA) ---\n"
            f"chunk_id: {c.chunk_id}\n"
            f"document_id: {c.document_id}\n"
            f"title: {c.title}\n"
            f"filename: {c.filename}\n"
            f"category: {c.category} | event_type: {c.event_type} | location: {c.location}\n"
            f"source_label: {c.source_label} (Illustrative={c.is_illustrative})\n"
            f"content:\n{c.excerpt}\n"
            f"--- END PASSAGE {idx} ---"
        )
    return "\n\n".join(blocks)


def build_planner_prompt(event_details: dict[str, Any], citations: list[SourceCitation]) -> str:
    rag_header = _load_template("rag_prompt.txt")
    planner_template = _load_template("planner_prompt.txt")
    details_str = "\n".join(f"- {k}: {v}" for k, v in event_details.items())
    context_str = format_retrieved_passages(citations)
    body = planner_template.format(
        event_details=details_str,
        retrieved_context=context_str,
    )
    return f"{rag_header}\n\n{body}".strip()


def build_chat_prompt(
    event_context: str,
    conversation_history: str,
    citations: list[SourceCitation],
    user_message: str,
) -> str:
    rag_header = _load_template("rag_prompt.txt")
    chat_template = _load_template("chat_prompt.txt")
    context_str = format_retrieved_passages(citations)
    body = chat_template.format(
        event_context=event_context,
        conversation_history=conversation_history or "No prior messages in this session.",
        retrieved_context=context_str,
        user_message=user_message,
    )
    return f"{rag_header}\n\n{body}".strip()
