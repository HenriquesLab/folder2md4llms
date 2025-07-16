"""PDF document converter."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)


class PDFConverter(BaseConverter):
    """Converts PDF files to text."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_pages = self.config.get("pdf_max_pages", 50)

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the given file."""
        return (
            PDF_AVAILABLE and file_path.suffix.lower() == ".pdf" and file_path.exists()
        )

    def convert(self, file_path: Path) -> Optional[str]:
        """Convert PDF to text."""
        if not PDF_AVAILABLE:
            return "PDF conversion not available. Install PyPDF2: pip install PyPDF2"

        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                # Get document info
                num_pages = len(reader.pages)
                pages_to_process = min(num_pages, self.max_pages)

                # Extract text from pages
                text_parts = []
                text_parts.append(f"PDF Document: {file_path.name}")
                text_parts.append(f"Total pages: {num_pages}")

                if pages_to_process < num_pages:
                    text_parts.append(f"Showing first {pages_to_process} pages")

                text_parts.append("=" * 50)
                text_parts.append("")

                for page_num in range(pages_to_process):
                    try:
                        page = reader.pages[page_num]
                        page_text = page.extract_text()

                        if page_text.strip():
                            text_parts.append(f"--- Page {page_num + 1} ---")
                            text_parts.append(page_text.strip())
                            text_parts.append("")

                    except Exception as e:
                        text_parts.append(f"--- Page {page_num + 1} (Error) ---")
                        text_parts.append(f"Error extracting text: {str(e)}")
                        text_parts.append("")

                return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error converting PDF {file_path}: {e}")
            raise ConversionError(f"Failed to convert PDF: {str(e)}") from e

    def get_supported_extensions(self) -> set:
        """Get the file extensions this converter supports."""
        return {".pdf"}

    def get_document_info(self, file_path: Path) -> Dict[str, Any]:
        """Get PDF-specific information."""
        info = self.get_file_info(file_path)

        if not PDF_AVAILABLE:
            info["error"] = "PDF library not available"
            return info

        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                info.update(
                    {
                        "pages": len(reader.pages),
                        "encrypted": reader.is_encrypted,
                    }
                )

                # Try to get metadata
                if reader.metadata:
                    metadata = reader.metadata
                    info.update(
                        {
                            "title": metadata.get("/Title", ""),
                            "author": metadata.get("/Author", ""),
                            "subject": metadata.get("/Subject", ""),
                            "creator": metadata.get("/Creator", ""),
                            "producer": metadata.get("/Producer", ""),
                            "creation_date": metadata.get("/CreationDate", ""),
                            "modification_date": metadata.get("/ModDate", ""),
                        }
                    )

        except Exception as e:
            info["error"] = str(e)

        return info
