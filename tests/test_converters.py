"""Comprehensive tests for all document converters."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from folder2md4llms.converters.base import BaseConverter, ConversionError
from folder2md4llms.converters.code_converter import CodeConverter
from folder2md4llms.converters.converter_factory import ConverterFactory
from folder2md4llms.converters.docx_converter import DOCXConverter
from folder2md4llms.converters.notebook_converter import NotebookConverter
from folder2md4llms.converters.pdf_converter import PDFConverter
from folder2md4llms.converters.pptx_converter import PPTXConverter
from folder2md4llms.converters.python_converter import PythonConverter
from folder2md4llms.converters.rtf_converter import RTFConverter
from folder2md4llms.converters.smart_python_converter import SmartPythonConverter
from folder2md4llms.converters.xlsx_converter import XLSXConverter


class ConcreteConverter(BaseConverter):
    """Concrete implementation of BaseConverter for testing."""

    def can_convert(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".test"

    def convert(self, file_path: Path) -> str | None:
        return f"Converted: {file_path.name}"

    def get_supported_extensions(self) -> set:
        return {".test"}


class TestBaseConverter:
    """Test the base converter class."""

    def test_init(self):
        """Test base converter initialization."""
        converter = ConcreteConverter()
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test base converter initialization with config."""
        config = {"key": "value"}
        converter = ConcreteConverter(config)
        assert converter.config == config

    def test_get_file_info_success(self):
        """Test getting file info for existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)

        try:
            converter = ConcreteConverter()
            info = converter.get_file_info(temp_path)
            assert "size" in info
            assert "modified" in info
            assert "extension" in info
            assert "name" in info
            assert info["size"] > 0
        finally:
            os.unlink(temp_path)

    def test_get_file_info_nonexistent(self):
        """Test getting file info for non-existent file."""
        converter = ConcreteConverter()
        info = converter.get_file_info(Path("nonexistent.txt"))
        assert info["size"] == 0
        assert info["modified"] == 0
        assert info["extension"] == ""
        assert info["name"] == "nonexistent.txt"

    def test_conversion_error(self):
        """Test ConversionError exception."""
        error = ConversionError("Test error")
        assert str(error) == "Test error"


class TestConverterFactory:
    """Test the converter factory."""

    def test_init(self):
        """Test factory initialization."""
        factory = ConverterFactory({})
        assert factory is not None
        assert factory.config == {}

    def test_init_with_config(self):
        """Test factory initialization with config."""
        config = {"key": "value"}
        factory = ConverterFactory(config)
        assert factory.config == config

    def test_get_converters(self):
        """Test getting all converters."""
        factory = ConverterFactory({})
        converters = factory._get_converters()
        assert len(converters) > 0
        assert all(isinstance(c, BaseConverter) for c in converters)

    def test_get_converter_unknown(self):
        """Test getting converter for unknown file type."""
        factory = ConverterFactory({})
        converter = factory.get_converter(Path("test.unknown"))
        assert converter is None

    def test_can_convert_unknown(self):
        """Test can_convert for unknown file type."""
        factory = ConverterFactory({})
        assert factory.can_convert(Path("test.unknown")) is False

    def test_convert_file_no_converter(self):
        """Test conversion when no converter available."""
        factory = ConverterFactory({})
        result = factory.convert_file(Path("test.unknown"))
        assert result is None

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        factory = ConverterFactory({})
        extensions = factory.get_supported_extensions()
        assert isinstance(extensions, set)
        assert len(extensions) > 0

    def test_get_file_info_unsupported(self):
        """Test getting file info for unsupported file."""
        with tempfile.NamedTemporaryFile(suffix=".unknown", delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)

        try:
            factory = ConverterFactory({})
            info = factory.get_file_info(temp_path)
            assert info["supported"] is False
            assert info["size"] > 0
        finally:
            os.unlink(temp_path)

    def test_get_file_info_nonexistent(self):
        """Test getting file info for non-existent file."""
        factory = ConverterFactory({})
        info = factory.get_file_info(Path("nonexistent.unknown"))
        assert info["supported"] is False
        assert info["size"] == 0


class TestPDFConverter:
    """Test PDF converter."""

    def test_init(self):
        """Test PDF converter initialization."""
        converter = PDFConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test PDF converter initialization with config."""
        config = {"pdf_max_pages": 100}
        converter = PDFConverter(config)
        assert converter.config == config
        assert converter.max_pages == 100

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = PDFConverter({})
        extensions = converter.get_supported_extensions()
        assert ".pdf" in extensions
        assert isinstance(extensions, set)

    @patch("folder2md4llms.converters.pdf_converter.PDF_AVAILABLE", True)
    def test_can_convert_pdf_available(self):
        """Test PDF file detection when pypdf is available."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"mock pdf content")
            temp_path = Path(f.name)

        try:
            converter = PDFConverter({})
            assert converter.can_convert(temp_path) is True
            assert converter.can_convert(Path("test.txt")) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.pdf_converter.PDF_AVAILABLE", False)
    def test_can_convert_pdf_unavailable(self):
        """Test PDF file detection when pypdf is not available."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"mock pdf content")
            temp_path = Path(f.name)

        try:
            converter = PDFConverter({})
            assert converter.can_convert(temp_path) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.pdf_converter.PDF_AVAILABLE", True)
    @patch("folder2md4llms.converters.pdf_converter.pypdf")
    def test_convert_success(self, mock_pypdf):
        """Test successful PDF conversion."""
        # Mock PyPDF2 objects
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF content"

        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pypdf.PdfReader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"mock pdf content")
            temp_path = Path(f.name)

        try:
            converter = PDFConverter({})
            result = converter.convert(temp_path)
            assert result is not None
            assert "Sample PDF content" in result
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.pdf_converter.PDF_AVAILABLE", False)
    def test_convert_unavailable(self):
        """Test PDF conversion when pypdf not available."""
        converter = PDFConverter({})
        result = converter.convert(Path("test.pdf"))
        assert (
            result == "PDF conversion not available. Install pypdf: pip install pypdf"
        )

    @patch("folder2md4llms.converters.pdf_converter.PDF_AVAILABLE", True)
    @patch("folder2md4llms.converters.pdf_converter.pypdf")
    def test_convert_exception(self, mock_pypdf):
        """Test PDF conversion when exception occurs."""
        mock_pypdf.PdfReader.side_effect = Exception("PDF parsing error")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"mock pdf content")
            temp_path = Path(f.name)

        try:
            converter = PDFConverter({})
            with pytest.raises(ConversionError):
                converter.convert(temp_path)
        finally:
            os.unlink(temp_path)


class TestDOCXConverter:
    """Test DOCX converter."""

    def test_init(self):
        """Test DOCX converter initialization."""
        converter = DOCXConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test DOCX converter initialization with config."""
        config = {"docx_extract_images": True}
        converter = DOCXConverter(config)
        assert converter.config == config
        assert converter.extract_images is True

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = DOCXConverter({})
        extensions = converter.get_supported_extensions()
        assert ".docx" in extensions
        assert isinstance(extensions, set)

    @patch("folder2md4llms.converters.docx_converter.DOCX_AVAILABLE", True)
    def test_can_convert_docx_available(self):
        """Test DOCX file detection when python-docx is available."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"mock docx content")
            temp_path = Path(f.name)

        try:
            converter = DOCXConverter({})
            assert converter.can_convert(temp_path) is True
            assert converter.can_convert(Path("test.txt")) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.docx_converter.DOCX_AVAILABLE", False)
    def test_can_convert_docx_unavailable(self):
        """Test DOCX file detection when python-docx is not available."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"mock docx content")
            temp_path = Path(f.name)

        try:
            converter = DOCXConverter({})
            assert converter.can_convert(temp_path) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.docx_converter.DOCX_AVAILABLE", True)
    @patch("folder2md4llms.converters.docx_converter.Document")
    def test_convert_success(self, mock_document):
        """Test successful DOCX conversion."""
        # Mock document structure
        mock_paragraph = Mock()
        mock_paragraph.text = "Sample DOCX content"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []  # Empty tables list
        mock_document.return_value = mock_doc

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"mock docx content")
            temp_path = Path(f.name)

        try:
            converter = DOCXConverter({})
            result = converter.convert(temp_path)
            assert result is not None
            assert "Sample DOCX content" in result
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.docx_converter.DOCX_AVAILABLE", False)
    def test_convert_unavailable(self):
        """Test DOCX conversion when python-docx not available."""
        converter = DOCXConverter({})
        result = converter.convert(Path("test.docx"))
        assert "DOCX conversion not available" in result


class TestXLSXConverter:
    """Test XLSX converter."""

    def test_init(self):
        """Test XLSX converter initialization."""
        converter = XLSXConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test XLSX converter initialization with config."""
        config = {"xlsx_max_sheets": 5}
        converter = XLSXConverter(config)
        assert converter.config == config
        assert converter.max_sheets == 5

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = XLSXConverter({})
        extensions = converter.get_supported_extensions()
        assert ".xlsx" in extensions
        assert isinstance(extensions, set)

    @patch("folder2md4llms.converters.xlsx_converter.XLSX_AVAILABLE", True)
    def test_can_convert_xlsx_available(self):
        """Test XLSX file detection when openpyxl is available."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(b"mock xlsx content")
            temp_path = Path(f.name)

        try:
            converter = XLSXConverter({})
            assert converter.can_convert(temp_path) is True
            assert converter.can_convert(Path("test.txt")) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.xlsx_converter.XLSX_AVAILABLE", False)
    def test_can_convert_xlsx_unavailable(self):
        """Test XLSX file detection when openpyxl is not available."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(b"mock xlsx content")
            temp_path = Path(f.name)

        try:
            converter = XLSXConverter({})
            assert converter.can_convert(temp_path) is False
        finally:
            os.unlink(temp_path)


class TestRTFConverter:
    """Test RTF converter."""

    def test_init(self):
        """Test RTF converter initialization."""
        converter = RTFConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test RTF converter initialization with config."""
        config = {"rtf_max_size": 5000000}
        converter = RTFConverter(config)
        assert converter.config == config
        assert converter.max_size == 5000000

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = RTFConverter({})
        extensions = converter.get_supported_extensions()
        assert ".rtf" in extensions
        assert isinstance(extensions, set)

    @patch("folder2md4llms.converters.rtf_converter.RTF_AVAILABLE", True)
    def test_can_convert_rtf_available(self):
        """Test RTF file detection when striprtf is available."""
        with tempfile.NamedTemporaryFile(suffix=".rtf", delete=False) as f:
            f.write(b"mock rtf content")
            temp_path = Path(f.name)

        try:
            converter = RTFConverter({})
            assert converter.can_convert(temp_path) is True
            assert converter.can_convert(Path("test.txt")) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.rtf_converter.RTF_AVAILABLE", False)
    def test_can_convert_rtf_unavailable(self):
        """Test RTF file detection when striprtf is not available."""
        with tempfile.NamedTemporaryFile(suffix=".rtf", delete=False) as f:
            f.write(b"mock rtf content")
            temp_path = Path(f.name)

        try:
            converter = RTFConverter({})
            assert converter.can_convert(temp_path) is False
        finally:
            os.unlink(temp_path)


class TestNotebookConverter:
    """Test Jupyter notebook converter."""

    def test_init(self):
        """Test notebook converter initialization."""
        converter = NotebookConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test notebook converter initialization with config."""
        config = {"notebook_max_cells": 50}
        converter = NotebookConverter(config)
        assert converter.config == config
        assert converter.max_cells == 50

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = NotebookConverter({})
        extensions = converter.get_supported_extensions()
        assert ".ipynb" in extensions
        assert isinstance(extensions, set)

    @patch("folder2md4llms.converters.notebook_converter.NOTEBOOK_AVAILABLE", True)
    def test_can_convert_notebook_available(self):
        """Test notebook file detection when nbformat is available."""
        with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False) as f:
            f.write(b"mock ipynb content")
            temp_path = Path(f.name)

        try:
            converter = NotebookConverter({})
            assert converter.can_convert(temp_path) is True
            assert converter.can_convert(Path("test.txt")) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.notebook_converter.NOTEBOOK_AVAILABLE", False)
    def test_can_convert_notebook_unavailable(self):
        """Test notebook file detection when nbformat is not available."""
        with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False) as f:
            f.write(b"mock ipynb content")
            temp_path = Path(f.name)

        try:
            converter = NotebookConverter({})
            assert converter.can_convert(temp_path) is False
        finally:
            os.unlink(temp_path)


class TestPPTXConverter:
    """Test PPTX converter."""

    def test_init(self):
        """Test PPTX converter initialization."""
        converter = PPTXConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test PPTX converter initialization with config."""
        config = {"pptx_max_slides": 20}
        converter = PPTXConverter(config)
        assert converter.config == config
        assert converter.max_slides == 20

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = PPTXConverter({})
        extensions = converter.get_supported_extensions()
        assert ".pptx" in extensions
        assert isinstance(extensions, set)

    @patch("folder2md4llms.converters.pptx_converter.PPTX_AVAILABLE", True)
    def test_can_convert_pptx_available(self):
        """Test PPTX file detection when python-pptx is available."""
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            f.write(b"mock pptx content")
            temp_path = Path(f.name)

        try:
            converter = PPTXConverter({})
            assert converter.can_convert(temp_path) is True
            assert converter.can_convert(Path("test.txt")) is False
        finally:
            os.unlink(temp_path)

    @patch("folder2md4llms.converters.pptx_converter.PPTX_AVAILABLE", False)
    def test_can_convert_pptx_unavailable(self):
        """Test PPTX file detection when python-pptx is not available."""
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            f.write(b"mock pptx content")
            temp_path = Path(f.name)

        try:
            converter = PPTXConverter({})
            assert converter.can_convert(temp_path) is False
        finally:
            os.unlink(temp_path)


class TestPythonConverter:
    """Test Python converter."""

    def test_init(self):
        """Test Python converter initialization."""
        converter = PythonConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test Python converter initialization with config."""
        config = {"condense_python": True}
        converter = PythonConverter(config)
        assert converter.config == config

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = PythonConverter({})
        extensions = converter.get_supported_extensions()
        assert ".py" in extensions
        assert isinstance(extensions, set)

    def test_can_convert_python(self):
        """Test Python file detection."""
        converter = PythonConverter({"condense_python": True})
        assert converter.can_convert(Path("test.py")) is True
        assert converter.can_convert(Path("test.PY")) is True
        assert converter.can_convert(Path("test.txt")) is False

        # Test with condense_python=False
        converter_no_condense = PythonConverter({"condense_python": False})
        assert converter_no_condense.can_convert(Path("test.py")) is False

    def test_convert_success(self):
        """Test successful Python conversion."""
        python_code = '''
def hello_world():
    """Print hello world."""
    print("Hello, World!")
    return True

class TestClass:
    """Test class."""

    def method(self):
        """Test method."""
        pass
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            converter = PythonConverter({"condense_python": True})
            result = converter.convert(temp_path)
            assert result is not None
            assert "def hello_world():" in result or "hello_world" in result
        finally:
            os.unlink(temp_path)

    def test_convert_invalid_python(self):
        """Test conversion of invalid Python code."""
        invalid_code = "def invalid syntax here"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_path = Path(f.name)

        try:
            converter = PythonConverter({"condense_python": True})
            result = converter.convert(temp_path)
            # Should return something even for invalid syntax
            assert result is not None
        finally:
            os.unlink(temp_path)


class TestCodeConverter:
    """Test code converter for various languages."""

    def test_init(self):
        """Test code converter initialization."""
        converter = CodeConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test code converter initialization with config."""
        config = {"condense_code": True}
        converter = CodeConverter(config)
        assert converter.config == config

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = CodeConverter({"condense_code": True})
        extensions = converter.get_supported_extensions()
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".java" in extensions
        assert isinstance(extensions, set)

    def test_can_convert_javascript(self):
        """Test JavaScript file detection."""
        converter = CodeConverter({"condense_code": True})
        assert converter.can_convert(Path("test.js")) is True
        assert converter.can_convert(Path("test.JS")) is True
        assert converter.can_convert(Path("test.txt")) is False

    def test_can_convert_typescript(self):
        """Test TypeScript file detection."""
        converter = CodeConverter({"condense_code": True})
        assert converter.can_convert(Path("test.ts")) is True
        assert converter.can_convert(Path("test.tsx")) is True

    def test_can_convert_java(self):
        """Test Java file detection."""
        converter = CodeConverter({"condense_code": True})
        assert converter.can_convert(Path("test.java")) is True
        assert converter.can_convert(Path("test.JAVA")) is True

    def test_convert_javascript_success(self):
        """Test successful JavaScript conversion."""
        js_code = """
function helloWorld() {
    console.log("Hello, World!");
    return true;
}

class TestClass {
    constructor() {
        this.value = 42;
    }

    method() {
        return this.value;
    }
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            temp_path = Path(f.name)

        try:
            converter = CodeConverter({"condense_code": True})
            result = converter.convert(temp_path)
            assert result is not None
            assert "function helloWorld()" in result or "helloWorld" in result
        finally:
            os.unlink(temp_path)

    def test_convert_unsupported_language(self):
        """Test conversion of unsupported language."""
        converter = CodeConverter({"condense_code": True})
        result = converter.convert(Path("test.unknown"))
        assert result is None


class TestSmartPythonConverter:
    """Test smart Python converter."""

    def test_init(self):
        """Test smart Python converter initialization."""
        converter = SmartPythonConverter({})
        assert converter is not None
        assert converter.config == {}

    def test_init_with_config(self):
        """Test smart Python converter initialization with config."""
        config = {"condense_python": True}
        converter = SmartPythonConverter(config)
        assert converter.config == config

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        converter = SmartPythonConverter({})
        extensions = converter.get_supported_extensions()
        assert ".py" in extensions
        assert isinstance(extensions, set)

    def test_can_convert_python(self):
        """Test Python file detection."""
        converter = SmartPythonConverter({"condense_python": True})
        assert converter.can_convert(Path("test.py")) is True
        assert converter.can_convert(Path("test.PY")) is True
        assert converter.can_convert(Path("test.txt")) is False

        # Test with condense_python=False
        converter_no_condense = SmartPythonConverter({"condense_python": False})
        assert converter_no_condense.can_convert(Path("test.py")) is False

    def test_convert_success(self):
        """Test successful smart Python conversion."""
        python_code = '''
import os
import sys

def hello_world():
    """Print hello world with smart features."""
    print("Hello, World!")
    return True

class SmartClass:
    """Smart test class."""

    def __init__(self):
        self.value = 42

    def smart_method(self):
        """Smart method with complex logic."""
        if self.value > 0:
            return self.value * 2
        return 0
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            converter = SmartPythonConverter({"condense_python": True})
            result = converter.convert(temp_path)
            assert result is not None
            assert "def hello_world():" in result or "hello_world" in result
        finally:
            os.unlink(temp_path)

    def test_set_budget_allocation(self):
        """Test setting budget allocation."""
        converter = SmartPythonConverter({})
        test_path = Path("test.py")

        # Mock allocation object
        mock_allocation = Mock()
        mock_allocation.allocated_tokens = 100
        mock_allocation.priority = "high"

        # Should not raise exception
        converter.set_budget_allocation(test_path, mock_allocation)

        # Verify allocation is stored
        assert test_path in converter.budget_allocations
        assert converter.budget_allocations[test_path] == mock_allocation

    def test_convert_nonexistent_file(self):
        """Test conversion of non-existent file."""
        converter = SmartPythonConverter({})
        result = converter.convert(Path("nonexistent.py"))
        assert result is None


# Additional test coverage comments
