from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Represents the result of an embedding operation."""

    embeddings: List[List[float]]
    model: str
    usage: Optional[Dict[str, Any]] = None  # Token usage, cost, etc.
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_text(self, text: str, **kwargs) -> List[float]:
        """
        Generate embeddings for a single text.

        Args:
            text: Text to embed
            **kwargs: Provider-specific parameters

        Returns:
            List of embedding values
        """
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str], **kwargs) -> EmbeddingResult:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            **kwargs: Provider-specific parameters

        Returns:
            EmbeddingResult with embeddings and metadata
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this provider.

        Returns:
            Embedding dimension
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.

        Returns:
            Dictionary with model information
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration parameters for this provider.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def embed_query(self, query: str, **kwargs) -> List[float]:
        """
        Generate embeddings for a search query.
        Some providers may optimize differently for queries vs documents.

        Args:
            query: Query text to embed
            **kwargs: Provider-specific parameters

        Returns:
            List of embedding values
        """
        return self.embed_text(query, **kwargs)

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        import math

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(a * a for a in embedding2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize an embedding to unit length.

        Args:
            embedding: Embedding vector to normalize

        Returns:
            Normalized embedding vector
        """
        import math

        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude == 0:
            return embedding

        return [x / magnitude for x in embedding]

    def batch_embed_with_progress(
        self, texts: List[str], batch_size: int = 100, show_progress: bool = False
    ) -> List[List[float]]:
        """
        Embed a large number of texts in batches with optional progress tracking.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            show_progress: Whether to show progress information

        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_result = self.embed_documents(batch_texts)
            all_embeddings.extend(batch_result.embeddings)

            if show_progress:
                batch_num = (i // batch_size) + 1
                print(f"Processed batch {batch_num}/{total_batches}")

        return all_embeddings

    @abstractmethod
    def get_max_input_length(self) -> int:
        """
        Get the maximum input length supported by this provider.

        Returns:
            Maximum number of tokens/characters supported
        """
        pass

    def truncate_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Truncate text to fit within provider limits.

        Args:
            text: Text to potentially truncate
            max_length: Maximum length (uses provider default if None)

        Returns:
            Truncated text
        """
        if max_length is None:
            max_length = self.get_max_input_length()

        if len(text) <= max_length:
            return text

        # Simple character-based truncation
        # More sophisticated implementations might consider word boundaries
        return text[:max_length]
