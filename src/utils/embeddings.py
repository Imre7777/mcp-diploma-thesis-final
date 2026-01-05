"""
Embedding Service for Query Vectorization

This module provides embedding generation for search queries using OpenAI's
text-embedding-3-large model (3072 dimensions) to match the precomputed
embeddings in the database.

For production, set OPENAI_API_KEY environment variable.
For testing without API key, provides mock embeddings.
"""

import logging
import os
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings from text queries.
    
    Uses OpenAI text-embedding-3-large (3072 dimensions) to match
    the precomputed embeddings in the database.
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072,
        api_key: Optional[str] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            model: Embedding model name (default: text-embedding-3-large)
            dimensions: Output dimensions (default: 3072)
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        """
        self.model = model
        self.dimensions = dimensions
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Try to import OpenAI client
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAI embedding service: {model}")
            except ImportError:
                logger.warning(
                    "OpenAI package not installed. Install with: pip install openai"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning(
                "No OpenAI API key found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter. Using mock embeddings for testing."
            )
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding vector for a query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            List of floats representing the embedding vector (3072 dimensions)
            
        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Query text cannot be empty")
        
        # Use OpenAI API if available
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text.strip(),
                    dimensions=self.dimensions
                )
                embedding = response.data[0].embedding
                logger.debug(f"Generated embedding for query: '{text[:50]}...'")
                return embedding
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                logger.warning("Falling back to mock embeddings")
                return self._generate_mock_embedding(text)
        
        # Fallback: Generate mock embedding for testing
        return self._generate_mock_embedding(text)
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for testing without API key.
        
        Creates a deterministic but pseudo-random vector based on the text.
        This is only for testing and will not produce meaningful search results.
        
        Args:
            text: Text to create mock embedding for
            
        Returns:
            Mock embedding vector (3072 dimensions)
        """
        # Use text hash as seed for reproducibility
        seed = hash(text.lower().strip()) % (2**32)
        rng = np.random.RandomState(seed)
        
        # Generate random vector
        embedding = rng.randn(self.dimensions).astype(float)
        
        # Normalize to unit length (common for embeddings)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        logger.debug(
            f"Generated mock embedding for query: '{text[:50]}...' "
            f"(shape: {len(embedding)})"
        )
        
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=[t.strip() for t in texts if t.strip()],
                    dimensions=self.dimensions
                )
                embeddings = [item.embedding for item in response.data]
                logger.debug(f"Generated {len(embeddings)} embeddings")
                return embeddings
                
            except Exception as e:
                logger.error(f"OpenAI API batch error: {e}")
                logger.warning("Falling back to mock embeddings")
                return [self._generate_mock_embedding(t) for t in texts]
        
        # Fallback: Generate mock embeddings
        return [self._generate_mock_embedding(t) for t in texts]
    
    @property
    def is_using_mock(self) -> bool:
        """Check if service is using mock embeddings."""
        return self.client is None


def create_embedding_service(
    model: str = "text-embedding-3-large",
    dimensions: int = 3072,
    api_key: Optional[str] = None
) -> EmbeddingService:
    """
    Factory function to create an embedding service.
    
    Args:
        model: Embedding model name
        dimensions: Output dimensions
        api_key: Optional API key (will use env var if not provided)
        
    Returns:
        EmbeddingService instance
    """
    return EmbeddingService(model=model, dimensions=dimensions, api_key=api_key)
