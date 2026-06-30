"""Vector store for VoyageOS RAG system using ChromaDB."""

import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class VectorStore:
    """Manage ChromaDB vector store for RAG."""

    def __init__(self, persist_directory: str = "database/chromadb"):
        """
        Initialize vector store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.collection = None
        self._initialize_store()

    def _initialize_store(self):
        """Initialize ChromaDB collection."""
        try:
            import chromadb
            from chromadb.config import Settings

            # Create directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="travel_documents",
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(f"Initialized ChromaDB at {self.persist_directory}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise

    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dicts with 'content', 'source', 'page'
            embeddings: List of embedding vectors
        """
        if not documents or not embeddings:
            logger.warning("No documents or embeddings to add")
            return

        if len(documents) != len(embeddings):
            logger.error("Documents and embeddings length mismatch")
            return

        try:
            ids = [f"doc_{i}_{hash(doc['content'][:50])}" for i, doc in enumerate(documents)]
            contents = [doc['content'] for doc in documents]
            metadatas = [
                {
                    'source': doc['source'],
                    'page': doc['page'],
                    'chunk_id': doc.get('chunk_id', 0)
                }
                for doc in documents
            ]

            self.collection.add(
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {str(e)}")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_source: Optional[str] = None
    ) -> Dict:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_source: Optional source filename to filter by
            
        Returns:
            Dictionary with 'documents', 'metadatas', 'distances'
        """
        if not query_embedding:
            return {"documents": [], "metadatas": [], "distances": []}

        try:
            where_filter = None
            if filter_source:
                where_filter = {"source": filter_source}

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0]
            }

        except Exception as e:
            logger.error(f"Failed to search vector store: {str(e)}")
            return {"documents": [], "metadatas": [], "distances": []}

    def get_collection_count(self) -> int:
        """Return the number of documents in the collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {str(e)}")
            return 0

    def reset(self):
        """Reset the vector store (delete all documents)."""
        try:
            self.client.delete_collection("travel_documents")
            self.collection = self.client.get_or_create_collection(
                name="travel_documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store reset")
        except Exception as e:
            logger.error(f"Failed to reset vector store: {str(e)}")