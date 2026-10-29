import hashlib
import math
from typing import Protocol

from app.config import settings
from app.rag.extraction import normalize_whitespace


class EmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]: ...


def preprocess_for_embedding(text: str) -> str:
    cleaned = normalize_whitespace(text)
    return cleaned if cleaned else "empty"


class DeterministicLocalMockEmbedder:
    """
    Deterministic token-hash embedding provider used for offline unit tests
    when SentenceTransformer model weights are mocked out.
    Produces 384-dimensional unit vectors with real lexical overlap similarity.
    """

    def __init__(self, model_name: str = "mock-all-MiniLM-L6-v2", dim: int = 384):
        self._model_name = model_name
        self._dim = dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def _encode_single(self, text: str) -> list[float]:
        processed = preprocess_for_embedding(text).lower()
        tokens = [t.strip(".,!?;:()[]\"'") for t in processed.split() if len(t.strip(".,!?;:()[]\"'")) > 1]
        vec = [0.0] * self._dim
        if not tokens:
            vec[0] = 1.0
            return vec
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [round(v / norm, 6) for v in vec]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._encode_single(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._encode_single(query)


class SentenceTransformerEmbedder:
    """Local Sentence Transformers embedding service."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        cleaned = [preprocess_for_embedding(t) for t in texts]
        model = self._load_model()
        embeddings = model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> list[float]:
        cleaned = preprocess_for_embedding(query)
        model = self._load_model()
        embedding = model.encode([cleaned], normalize_embeddings=True, show_progress_bar=False)[0]
        return embedding.tolist()


_active_embedder: EmbeddingProvider | None = None


def get_embedding_service() -> EmbeddingProvider:
    global _active_embedder
    if _active_embedder is None:
        _active_embedder = SentenceTransformerEmbedder(settings.EMBEDDING_MODEL)
    return _active_embedder


def set_embedding_service(embedder: EmbeddingProvider | None) -> None:
    global _active_embedder
    _active_embedder = embedder
