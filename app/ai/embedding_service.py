from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Lazy load and catch the transformer model
    the model is loaded once per process and reused across request to avoid repeat cold start cost"""

    return SentenceTransformer("all-MiniLM-L6-v2")


class EmbeddingService:
    """Generte semantic embedding for log message"""

    def __init__(self):
        self.model = get_embedding_model()
        self.embedding_dimensions = settings.embedding_dimension

    def embed_text(self, text: str):
        """Generate a normalized embedding vector for a single text input"""

        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Text for embedding cannot be empty")

        vector = self.model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        embedding = vector.tolist()
        self._validate_dimensions(embedding)
        return embedding

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate a normalized embedding vector for a multiple text input"""

        cleaned_texts = [text.strip() for text in texts if text.strip()]
        if not cleaned_texts:
            return []

        vectors = self.model.encode(
            cleaned_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        embeddings = [vector.tolist() for vector in vectors]
        for embedding in embeddings:
            self._validate_dimensions(embedding)
        return embeddings

    def _validate_dimensions(self, embedding: list[float]):
        """Ensure model output matches configured vector size"""

        if len(embedding) != self.embedding_dimensions:
            raise ValueError(
                "Embedding dimensions mismatch :"
                f"expected {self.embedding_dimensions}, got {len(embedding)}"
            )
