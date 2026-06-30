"""Retriever for VoyageOS RAG system."""

import logging
from typing import List, Dict, Optional
from rag.embeddings import EmbeddingManager
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieve relevant documents from vector store."""

    def __init__(
        self,
        embedding_manager: Optional[EmbeddingManager] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize retriever.
        
        Args:
            embedding_manager: EmbeddingManager instance
            vector_store: VectorStore instance
        """
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.vector_store = vector_store or VectorStore()

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter_source: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query string
            n_results: Number of results to return
            filter_source: Optional source filename to filter by
            
        Returns:
            List of relevant documents with content, source, page, and score
        """
        if not query or not query.strip():
            return []

        try:
            # Embed the query
            query_embedding = self.embedding_manager.embed_query(query)

            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []

            # Search vector store
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=n_results,
                filter_source=filter_source
            )

            # Format results
            documents = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results.get("documents", []),
                    results.get("metadatas", []),
                    results.get("distances", [])
                )
            ):
                documents.append({
                    'content': doc,
                    'source': metadata.get('source', 'Unknown'),
                    'page': metadata.get('page', 0),
                    'score': 1 - distance,  # Convert distance to similarity score
                    'rank': i + 1
                })

            logger.info(f"Retrieved {len(documents)} relevant documents for query")
            return documents

        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            return []

    def get_relevant_context(self, query: str, max_chars: int = 3000) -> str:
        """
        Get relevant context as a formatted string.
        
        Args:
            query: User query string
            max_chars: Maximum characters to return
            
        Returns:
            Formatted context string with source citations
        """
        documents = self.retrieve(query, n_results=5)

        if not documents:
            return ""

        context_parts = []
        total_chars = 0

        for doc in documents:
            # Add source citation
            source_info = f"[Source: {doc['source']}, Page {doc['page']}]"
            text = doc['content']

            # Check if adding this would exceed max_chars
            if total_chars + len(text) + len(source_info) > max_chars:
                # Truncate text to fit
                remaining = max_chars - total_chars - len(source_info) - 10
                if remaining > 100:
                    text = text[:remaining] + "..."
                else:
                    break

            context_parts.append(f"{text}\n{source_info}")
            total_chars += len(text) + len(source_info) + 1

            if total_chars >= max_chars:
                break

        return "\n\n---\n\n".join(context_parts)

    def has_relevant_documents(self, query: str, threshold: float = 0.5) -> bool:
        """
        Check if there are relevant documents for a query.
        
        Args:
            query: User query string
            threshold: Minimum similarity score (0-1)
            
        Returns:
            True if relevant documents exist
        """
        documents = self.retrieve(query, n_results=1)

        if not documents:
            return False

        return documents[0]['score'] >= threshold