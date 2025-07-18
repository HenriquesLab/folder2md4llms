"""PDF document converter."""

import logging
from pathlib import Path
from typing import Any

try:
    import pypdf

    PDF_AVAILABLE = True
except ImportError:
    try:
        import PyPDF2 as pypdf  # type: ignore[no-redef]

        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)


class PDFConverter(BaseConverter):
    """Converts PDF files to text."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.max_pages = self.config.get("pdf_max_pages", 50)

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the given file."""
        return (
            PDF_AVAILABLE and file_path.suffix.lower() == ".pdf" and file_path.exists()
        )

    def convert(self, file_path: Path) -> str | None:
        """Convert PDF to text."""
        if not PDF_AVAILABLE:
            return "PDF conversion not available. Install pypdf: pip install pypdf"

        try:
            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)

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

                        # Try improved text extraction with pypdf
                        try:
                            # Use improved text extraction if available
                            if hasattr(page, "extract_text"):
                                page_text = page.extract_text()
                            else:
                                # Fallback for older PyPDF2
                                page_text = page.extract_text()
                        except Exception:
                            # Final fallback
                            page_text = str(page)

                        # Clean up the text
                        page_text = self._clean_pdf_text(page_text)

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

    def get_document_info(self, file_path: Path) -> dict[str, Any]:
        """Get PDF-specific information."""
        info = self.get_file_info(file_path)

        if not PDF_AVAILABLE:
            info["error"] = "PDF library not available"
            return info

        try:
            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)

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

    def _clean_pdf_text(self, text: str) -> str:
        """Clean up extracted PDF text."""
        if not text:
            return ""

        # Remove excessive whitespace
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Remove excessive spaces
            line = " ".join(line.split())

            cleaned_lines.append(line)

        # Join lines back together
        result = "\n".join(cleaned_lines)

        # Remove excessive newlines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result
