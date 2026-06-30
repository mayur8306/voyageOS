"""PDF document loader for VoyageOS RAG system."""

import os
import logging
from pathlib import Path
from typing import List, Dict
import pypdf

logger = logging.getLogger(__name__)


class PDFLoader:
    """Load PDF documents from the data directory."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.documents = []

    def load_all_pdfs(self) -> List[Dict]:
        """
        Load all PDF files from the data directory.
        
        Returns:
            List of dictionaries with 'content', 'source', and 'page'
        """
        self.documents = []

        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return self.documents

        pdf_files = list(self.data_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {self.data_dir}")
            return self.documents

        logger.info(f"Found {len(pdf_files)} PDF files in {self.data_dir}")

        for pdf_file in pdf_files:
            try:
                self._load_pdf(pdf_file)
            except Exception as e:
                logger.error(f"Failed to load {pdf_file}: {str(e)}")
                continue

        logger.info(f"Loaded {len(self.documents)} document chunks from {len(pdf_files)} PDFs")
        return self.documents

    def _load_pdf(self, pdf_path: Path):
        """Load a single PDF file and extract text."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                logger.info(f"Loading {pdf_path.name}: {num_pages} pages")

                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    try:
                        text = page.extract_text()

                        if text and text.strip():
                            self.documents.append({
                                'content': text.strip(),
                                'source': pdf_path.name,
                                'page': page_num,
                                'total_pages': num_pages
                            })
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num} from {pdf_path.name}: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Failed to open {pdf_path}: {str(e)}")
            raise

    def get_documents(self) -> List[Dict]:
        """Return loaded documents."""
        return self.documents

    def get_sources(self) -> List[str]:
        """Return list of unique source filenames."""
        return list(set(doc['source'] for doc in self.documents))