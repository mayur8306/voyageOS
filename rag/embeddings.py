"""Embeddings for VoyageOS RAG system."""

import logging
from typing import List, Dict
import os

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manage embeddings for RAG system."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding manager.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to embed documents: {str(e)}")
            return []

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        if not text:
            return []

        try:
            embedding = self.model.encode([text], show_progress_bar=False)
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"Failed to embed query: {str(e)}")
            return []

    def get_model(self):
        """Return the underlying model instance."""
        return self.model