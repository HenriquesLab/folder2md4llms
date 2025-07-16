<!-- markdownlint-disable -->

# API Overview

## Core Components

### CLI Module (`cli.py`)
- **main()**: Main command-line interface function
- **_generate_ignore_template()**: Generate .folder2md_ignore template file

### Processor Module (`processor.py`)
- **RepositoryProcessor**: Main processor class for converting repositories to markdown

### Configuration Module (`utils/config.py`)
- **Config**: Configuration management class

### File Utils Module (`utils/file_utils.py`)
- **is_binary_file()**: Check if file is binary
- **is_text_file()**: Check if file is text
- **get_file_category()**: Get file category (text, document, image, etc.)
- **read_file_safely()**: Safe file reading with encoding detection

### Platform Utils Module (`utils/platform_utils.py`)
- **is_windows()**: Check if running on Windows
- **is_macos()**: Check if running on macOS
- **is_linux()**: Check if running on Linux
- **get_platform_name()**: Get standardized platform name

### Ignore Patterns Module (`utils/ignore_patterns.py`)
- **IgnorePatterns**: Manage file/directory ignore patterns

### Converters
- **ConverterFactory**: Factory for document converters
- **PDFConverter**: PDF to text conversion
- **DOCXConverter**: DOCX to text conversion
- **XLSXConverter**: XLSX to markdown conversion

### Analyzers
- **BinaryAnalyzer**: Binary file analysis and description

### Formatters
- **MarkdownFormatter**: Markdown output formatting

---

_This file was manually updated to reflect the current API structure._
