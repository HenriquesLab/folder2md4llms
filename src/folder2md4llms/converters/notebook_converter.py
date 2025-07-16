"""Jupyter notebook converter."""

import json
import logging
from pathlib import Path
from typing import Any

try:
    import nbformat
    from nbconvert import MarkdownExporter

    NOTEBOOK_AVAILABLE = True
except ImportError:
    NOTEBOOK_AVAILABLE = False

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)


class NotebookConverter(BaseConverter):
    """Converts Jupyter notebooks to markdown."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.max_cells = self.config.get("notebook_max_cells", 200)
        self.include_outputs = self.config.get("notebook_include_outputs", True)
        self.include_metadata = self.config.get("notebook_include_metadata", False)

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the given file."""
        return (
            NOTEBOOK_AVAILABLE
            and file_path.suffix.lower() == ".ipynb"
            and file_path.exists()
        )

    def convert(self, file_path: Path) -> str | None:
        """Convert Jupyter notebook to markdown."""
        if not NOTEBOOK_AVAILABLE:
            return "Jupyter notebook conversion not available. Install nbconvert: pip install nbconvert"

        try:
            # Read notebook
            with open(file_path, encoding="utf-8") as f:
                notebook_content = nbformat.read(f, as_version=4)

            # Check cell count
            cell_count = len(notebook_content.cells)
            if cell_count > self.max_cells:
                logger.warning(
                    f"Notebook has {cell_count} cells, limiting to {self.max_cells}"
                )
                notebook_content.cells = notebook_content.cells[: self.max_cells]

            # Convert to markdown
            if self.include_outputs:
                exporter = MarkdownExporter()
            else:
                exporter = MarkdownExporter(exclude_output=True)

            (body, resources) = exporter.from_notebook_node(notebook_content)

            # Format the output
            text_parts = []
            text_parts.append(f"Jupyter Notebook: {file_path.name}")
            text_parts.append(f"Total cells: {cell_count}")

            if cell_count > self.max_cells:
                text_parts.append(f"Showing first {self.max_cells} cells")

            # Add metadata if requested
            if self.include_metadata and hasattr(notebook_content, "metadata"):
                metadata = notebook_content.metadata
                if metadata:
                    text_parts.append(
                        f"Kernel: {metadata.get('kernelspec', {}).get('display_name', 'Unknown')}"
                    )
                    text_parts.append(
                        f"Language: {metadata.get('language_info', {}).get('name', 'Unknown')}"
                    )

            text_parts.append("=" * 50)
            text_parts.append("")
            text_parts.append(body)

            return "\n".join(text_parts)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in notebook {file_path}: {e}")
            raise ConversionError(f"Invalid notebook format: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error converting notebook {file_path}: {e}")
            raise ConversionError(f"Failed to convert notebook: {str(e)}") from e

    def get_supported_extensions(self) -> set:
        """Get the file extensions this converter supports."""
        return {".ipynb"}

    def get_document_info(self, file_path: Path) -> dict[str, Any]:
        """Get notebook-specific information."""
        info = self.get_file_info(file_path)

        if not NOTEBOOK_AVAILABLE:
            info["error"] = "Jupyter notebook library not available"
            return info

        try:
            with open(file_path, encoding="utf-8") as f:
                notebook_content = nbformat.read(f, as_version=4)

            cell_count = len(notebook_content.cells)
            code_cells = sum(
                1 for cell in notebook_content.cells if cell.cell_type == "code"
            )
            markdown_cells = sum(
                1 for cell in notebook_content.cells if cell.cell_type == "markdown"
            )

            info.update(
                {
                    "total_cells": cell_count,
                    "code_cells": code_cells,
                    "markdown_cells": markdown_cells,
                    "will_be_truncated": cell_count > self.max_cells,
                }
            )

            # Add kernel information
            if hasattr(notebook_content, "metadata"):
                metadata = notebook_content.metadata
                if metadata:
                    kernelspec = metadata.get("kernelspec", {})
                    language_info = metadata.get("language_info", {})

                    info.update(
                        {
                            "kernel_name": kernelspec.get("name", "Unknown"),
                            "kernel_display_name": kernelspec.get(
                                "display_name", "Unknown"
                            ),
                            "language": language_info.get("name", "Unknown"),
                            "language_version": language_info.get("version", "Unknown"),
                        }
                    )

        except Exception as e:
            info["error"] = str(e)

        return info
