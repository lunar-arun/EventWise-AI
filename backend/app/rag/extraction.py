import csv
import io
import json
import re
from pathlib import Path
from typing import Any
from pypdf import PdfReader

from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".json"}
ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".csv": {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel", "application/octet-stream"},
    ".json": {"application/json", "text/json", "text/plain", "application/octet-stream"},
}


class DocumentExtractionError(ValueError):
    """Raised when a document fails validation or text extraction."""


def sanitize_filename(filename: str) -> str:
    if not filename or "\x00" in filename:
        raise DocumentExtractionError("Invalid filename.")
    # Prevent path traversal by rejecting explicit '..' path segments
    normalized = filename.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    if ".." in parts:
        raise DocumentExtractionError("Path traversal sequences are not allowed in filenames.")
    base = Path(normalized).name
    cleaned = re.sub(r"[^A-Za-z0-9._\- ]+", "_", base).strip(" .")
    if not cleaned:
        raise DocumentExtractionError("Filename contains no valid characters.")
    ext = Path(cleaned).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentExtractionError(
            f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return cleaned


def validate_upload(
    filename: str,
    content_bytes: bytes,
    content_type: str | None = None,
    max_bytes: int | None = None,
) -> tuple[str, str]:
    safe_name = sanitize_filename(filename)
    ext = Path(safe_name).suffix.lower()
    limit = max_bytes if max_bytes is not None else settings.max_upload_bytes

    if len(content_bytes) == 0:
        raise DocumentExtractionError("Uploaded file is empty.")
    if len(content_bytes) > limit:
        raise DocumentExtractionError(
            f"File exceeds maximum allowed size of {limit // (1024 * 1024)} MB."
        )

    if content_type:
        base_mime = content_type.split(";")[0].strip().lower()
        allowed_mimes = ALLOWED_MIME_TYPES.get(ext, set())
        if base_mime and base_mime not in allowed_mimes:
            raise DocumentExtractionError(
                f"MIME type '{base_mime}' does not match extension '{ext}'."
            )

    return safe_name, ext.lstrip(".")


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned_lines: list[str] = []
    blank_streak = 0
    for line in lines:
        if not line:
            blank_streak += 1
            if blank_streak <= 1:
                cleaned_lines.append("")
        else:
            blank_streak = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def extract_text_from_pdf(content_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content_bytes))
        pages_text: list[str] = []
        for idx, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            if extracted.strip():
                pages_text.append(f"## Page {idx}\n{extracted.strip()}")
        full_text = normalize_whitespace("\n\n".join(pages_text))
        if not full_text:
            raise DocumentExtractionError("PDF contains no extractable text.")
        return full_text
    except DocumentExtractionError:
        raise
    except Exception as exc:
        raise DocumentExtractionError(f"Failed to extract text from PDF: {exc}") from exc


def extract_text_from_txt(content_bytes: bytes) -> str:
    try:
        decoded = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            decoded = content_bytes.decode("latin-1")
        except Exception as exc:
            raise DocumentExtractionError("Unable to decode text file encoding.") from exc
    normalized = normalize_whitespace(decoded)
    if not normalized:
        raise DocumentExtractionError("Text file contains no readable content.")
    return normalized


def extract_text_from_csv(content_bytes: bytes) -> str:
    try:
        decoded = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentExtractionError("CSV file must be UTF-8 encoded.") from exc

    stream = io.StringIO(decoded)
    reader = csv.reader(stream)
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        raise DocumentExtractionError("CSV file contains no non-empty rows.")

    headers = [h.strip() for h in rows[0]]
    formatted_rows: list[str] = [f"# CSV Dataset Columns: {', '.join(headers)}"]
    for idx, row in enumerate(rows[1:], start=1):
        pairs = []
        for col_idx, cell in enumerate(row):
            col_name = headers[col_idx] if col_idx < len(headers) else f"Column_{col_idx + 1}"
            val = cell.strip()
            if val:
                pairs.append(f"{col_name}: {val}")
        if pairs:
            formatted_rows.append(f"Row {idx} — " + " | ".join(pairs))

    result = normalize_whitespace("\n".join(formatted_rows))
    if not result:
        raise DocumentExtractionError("CSV file yielded no usable text.")
    return result


def _flatten_json_to_markdown(data: Any, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            heading = f"{prefix}{key}"
            if isinstance(value, (dict, list)):
                lines.append(f"## {heading}")
                lines.extend(_flatten_json_to_markdown(value, prefix=""))
            else:
                lines.append(f"- {key}: {value}")
    elif isinstance(data, list):
        for idx, item in enumerate(data, start=1):
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or item.get("category") or f"Item {idx}"
                lines.append(f"### {title}")
                for k, v in item.items():
                    lines.append(f"- {k}: {v}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append(str(data))
    return lines


def extract_text_from_json(content_bytes: bytes) -> str:
    try:
        decoded = content_bytes.decode("utf-8-sig")
        parsed = json.loads(decoded)
    except Exception as exc:
        raise DocumentExtractionError(f"Invalid JSON content: {exc}") from exc

    lines = _flatten_json_to_markdown(parsed)
    normalized = normalize_whitespace("\n".join(lines))
    if not normalized:
        raise DocumentExtractionError("JSON file contains no extractable text.")
    return normalized


def extract_text_from_bytes(
    filename: str,
    content_bytes: bytes,
    content_type: str | None = None,
    max_bytes: int | None = None,
) -> tuple[str, str, str]:
    """
    Validate file and extract normalized text.
    Returns (safe_filename, file_type, extracted_text).
    """
    safe_name, file_type = validate_upload(filename, content_bytes, content_type, max_bytes=max_bytes)
    if file_type == "pdf":
        text = extract_text_from_pdf(content_bytes)
    elif file_type == "txt":
        text = extract_text_from_txt(content_bytes)
    elif file_type == "csv":
        text = extract_text_from_csv(content_bytes)
    elif file_type == "json":
        text = extract_text_from_json(content_bytes)
    else:
        raise DocumentExtractionError(f"Unsupported file type: {file_type}")
    return safe_name, file_type, text
