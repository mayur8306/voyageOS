"""Text splitter for VoyageOS RAG system."""

import logging
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextSplitter:
    """Split documents into chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to split on (in order of priority)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len
        )

    def split_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of dicts with 'content', 'source', 'page'
            
        Returns:
            List of chunked documents with metadata
        """
        if not documents:
            logger.warning("No documents to split")
            return []

        chunks = []

        for doc in documents:
            try:
                text_chunks = self.splitter.split_text(doc['content'])

                for i, chunk in enumerate(text_chunks):
                    chunks.append({
                        'content': chunk,
                        'source': doc['source'],
                        'page': doc['page'],
                        'chunk_id': i,
                        'total_chunks': len(text_chunks)
                    })

            except Exception as e:
                logger.error(f"Failed to split document {doc.get('source', 'unknown')}: {str(e)}")
                continue

        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks

    def get_splitter(self) -> RecursiveCharacterTextSplitter:
        """Return the underlying splitter instance."""
        return self.splitter