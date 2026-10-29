import hashlib
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.rag.extraction import normalize_whitespace


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]


def generate_deterministic_doc_id(filename: str, source_label: str = "") -> str:
    seed = f"{filename.strip().lower()}::{source_label.strip().lower()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"doc_{digest}"


def generate_deterministic_chunk_id(document_id: str, chunk_index: int, chunk_text: str) -> str:
    content_hash = hashlib.sha256(chunk_text.strip().encode("utf-8")).hexdigest()[:10]
    return f"{document_id}_chunk_{chunk_index:04d}_{content_hash}"


def chunk_document_text(
    document_id: str,
    text: str,
    base_metadata: dict[str, Any],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """
    Split normalized text into overlapping chunks while preserving section headers
    and line/paragraph boundaries. Uses deterministic chunk IDs so re-indexing is idempotent.
    """
    target_size = chunk_size if chunk_size is not None else settings.RAG_CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else settings.RAG_CHUNK_OVERLAP

    if target_size <= 50:
        raise ValueError("chunk_size must be greater than 50 characters.")
    if overlap < 0 or overlap >= target_size:
        raise ValueError("chunk_overlap must be non-negative and strictly less than chunk_size.")

    cleaned = normalize_whitespace(text)
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    raw_chunks: list[str] = []
    current_heading = ""
    current_buffer = ""

    for para in paragraphs:
        first_line = para.split("\n", 1)[0].strip()
        if first_line.startswith("#"):
            current_heading = first_line.lstrip("#").strip()

        heading_prefix = f"[{current_heading}]\n" if current_heading else ""
        para_with_heading = (
            para if (not current_heading or current_heading in para) else f"{heading_prefix}{para}"
        )

        # If adding this paragraph fits in target_size, accumulate it
        candidate = f"{current_buffer}\n\n{para}".strip() if current_buffer else para_with_heading
        if len(candidate) <= target_size:
            current_buffer = candidate
            continue

        # Flush existing buffer before handling the new paragraph
        if current_buffer:
            raw_chunks.append(current_buffer)
            overlap_tail = current_buffer[-overlap:].strip() if overlap > 0 else ""
            current_buffer = ""
        else:
            overlap_tail = ""

        # If the paragraph itself (with heading/overlap) fits in target_size, put it in current_buffer
        seeded_para = (
            f"{heading_prefix}{overlap_tail}\n{para}".strip()
            if overlap_tail and not para.startswith(heading_prefix.strip())
            else para_with_heading
        )
        if len(seeded_para) <= target_size:
            current_buffer = seeded_para
            continue

        # Otherwise split the large paragraph along lines/words with overlap while keeping heading
        work_text = para
        while len(work_text) > 0:
            avail = max(60, target_size - len(heading_prefix))
            if len(work_text) <= avail:
                piece = f"{heading_prefix}{work_text}".strip()
                current_buffer = piece
                break
            slice_part = work_text[:avail]
            # Prefer breaking at newline or space
            last_nl = slice_part.rfind("\n")
            last_sp = slice_part.rfind(" ")
            break_pos = last_nl if last_nl > avail // 2 else (last_sp if last_sp > avail // 2 else avail)
            chunk_piece = f"{heading_prefix}{work_text[:break_pos].strip()}".strip()
            if chunk_piece:
                raw_chunks.append(chunk_piece)
            step = max(1, break_pos - overlap)
            work_text = work_text[step:].strip()

    if current_buffer.strip():
        raw_chunks.append(current_buffer.strip())

    chunks: list[DocumentChunk] = []
    for idx, chunk_str in enumerate(raw_chunks):
        if not chunk_str.strip():
            continue
        cid = generate_deterministic_chunk_id(document_id, idx, chunk_str)
        meta = {
            **base_metadata,
            "document_id": document_id,
            "chunk_index": idx,
        }
        chunks.append(
            DocumentChunk(
                chunk_id=cid,
                document_id=document_id,
                chunk_index=idx,
                text=chunk_str,
                metadata=meta,
            )
        )
    return chunks
