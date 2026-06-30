"""RAG pipeline for VoyageOS."""

import logging
from typing import List, Dict, Optional
from rag.loader import PDFLoader
from rag.splitter import TextSplitter
from rag.embeddings import EmbeddingManager
from rag.vector_store import VectorStore
from rag.retriever import Retriever

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline for travel knowledge assistant."""

    def __init__(self, data_dir: str = "data", persist_directory: str = "database/chromadb"):
        """
        Initialize RAG pipeline.
        
        Args:
            data_dir: Directory containing PDF files
            persist_directory: Directory for ChromaDB persistence
        """
        self.data_dir = data_dir
        self.persist_directory = persist_directory
        
        # Initialize components
        self.loader = PDFLoader(data_dir)
        self.splitter = TextSplitter()
        self.embedding_manager = None
        self.vector_store = None
        self.retriever = None
        
        # Track if documents have been ingested
        self.is_ingested = False
        self.initialization_error = None

    def ingest_documents(self, force_reload: bool = False) -> bool:
        """
        Load, split, embed, and store all PDF documents.
        
        Args:
            force_reload: If True, reset and reload all documents
            
        Returns:
            True if successful, False otherwise
        """
        if self.is_ingested and not force_reload:
            logger.info("Documents already ingested")
            return True

        try:
            logger.info("========== VoyageOS Startup ==========")
            
            # Reset if force reload
            if force_reload:
                logger.info("Force reloading documents")
                if self.vector_store:
                    self.vector_store.reset()
            
            # Initialize embedding manager
            logger.info("Loading embedding model...")
            self.embedding_manager = EmbeddingManager()
            
            # Initialize vector store
            logger.info("Loading ChromaDB...")
            self.vector_store = VectorStore(self.persist_directory)
            
            # Initialize retriever
            self.retriever = Retriever(self.embedding_manager, self.vector_store)
            
            # Check if documents already exist
            existing_count = self.vector_store.get_collection_count()
            if existing_count > 0 and not force_reload:
                logger.info(f"Knowledge Base Ready - {existing_count} documents loaded")
                logger.info("=====================================")
                self.is_ingested = True
                return True

            # Load PDFs
            logger.info(f"Scanning {self.data_dir} for PDFs...")
            documents = self.loader.load_all_pdfs()
            
            if not documents:
                logger.warning("No PDF documents found in data directory")
                logger.info("=====================================")
                return False

            # Split documents
            logger.info("Splitting documents into chunks...")
            chunks = self.splitter.split_documents(documents)
            
            if not chunks:
                logger.warning("No chunks created from documents")
                logger.info("=====================================")
                return False

            # Embed documents
            logger.info("Creating embeddings...")
            texts = [chunk['content'] for chunk in chunks]
            embeddings = self.embedding_manager.embed_documents(texts)
            
            if not embeddings:
                logger.error("Failed to generate embeddings")
                logger.info("=====================================")
                return False

            # Store in vector database
            logger.info("Storing in vector database...")
            self.vector_store.add_documents(chunks, embeddings)
            
            self.is_ingested = True
            logger.info(f"Knowledge Base Ready - {len(chunks)} chunks from {len(documents)} pages")
            logger.info("=====================================")
            return True

        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Failed to initialize RAG: {str(e)}")
            logger.info("=====================================")
            return False

    def query(self, question: str, n_results: int = 5) -> Dict:
        """
        Query the RAG system.
        
        Args:
            question: User question
            n_results: Number of results to retrieve
            
        Returns:
            Dictionary with 'context', 'sources', and 'has_answer'
        """
        if not self.is_ingested or not self.retriever:
            return {
                "context": "",
                "sources": [],
                "has_answer": False
            }

        try:
            # Get relevant context
            context = self.retriever.get_relevant_context(question, max_chars=3000)
            
            # Get source documents
            documents = self.retriever.retrieve(question, n_results=n_results)
            sources = list(set(doc['source'] for doc in documents))
            
            has_answer = len(context) > 0 and self.retriever.has_relevant_documents(question)
            
            return {
                "context": context,
                "sources": sources,
                "has_answer": has_answer
            }

        except Exception as e:
            logger.error(f"Failed to query RAG: {str(e)}")
            return {
                "context": "",
                "sources": [],
                "has_answer": False
            }

    def get_sources(self) -> List[str]:
        """Return list of available document sources."""
        try:
            return self.loader.get_sources()
        except Exception as e:
            logger.error(f"Failed to get sources: {str(e)}")
            return []

    def get_document_count(self) -> int:
        """Return number of documents in vector store."""
        try:
            if self.vector_store:
                return self.vector_store.get_collection_count()
            return 0
        except Exception as e:
            logger.error(f"Failed to get document count: {str(e)}")
            return 0

    def get_status(self) -> Dict:
        """Return RAG system status."""
        return {
            "initialized": self.is_ingested,
            "document_count": self.get_document_count(),
            "sources": self.get_sources(),
            "error": self.initialization_error
        }

    def reset(self):
        """Reset the RAG pipeline."""
        if self.vector_store:
            self.vector_store.reset()
        self.is_ingested = False
        self.initialization_error = None
        logger.info("RAG pipeline reset")