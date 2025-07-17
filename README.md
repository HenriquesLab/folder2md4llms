# folder2md4llms

[![Tests](https://github.com/henriqueslab/folder2md4llms/actions/workflows/test.yml/badge.svg)](https://github.com/henriqueslab/folder2md4llms/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Enhanced tool to concatenate folder contents into markdown format for LLM consumption, inspired by gpt-repository-loader with significant improvements.

## ✨ Features

- **📝 Markdown-first output** - Professional formatting with table of contents, syntax highlighting, and structured sections
- **📁 Folder structure visualization** - ASCII tree representation of directory structure
- **📊 Repository statistics** - File counts, sizes, and language breakdown
- **📄 Document conversion** - PDF, DOCX, XLSX files converted to text/markdown
- **🔧 Binary file analysis** - Intelligent descriptions for images, archives, and executables
- **⚙️ Highly configurable** - YAML configuration files and comprehensive CLI options
- **🚀 Fast and efficient** - Multi-threaded processing with progress tracking
- **🔍 Smart filtering** - Advanced ignore patterns with glob support and template generation
- **📋 Multiple output formats** - Markdown, HTML, and plain text support
- **🌍 Cross-platform compatibility** - Works seamlessly on Windows, macOS, and Linux

## 🚀 Quick Start

### Installation

```bash
# Install using uv (recommended)
uv add folder2md4llms

# Or using pip
pip install folder2md4llms
```

### Basic Usage

```bash
# Process current directory
folder2md .

# Process specific directory with custom output
folder2md /path/to/repo --output analysis.md

# Skip tree generation and copy to clipboard
folder2md /path/to/repo --no-tree --clipboard

# Smart condensing with token limit (fits content under 50k tokens)
folder2md /path/to/repo --smart-condensing --token-limit 50000

# Smart condensing with character limit (fits content under 200k chars)
folder2md /path/to/repo --smart-condensing --char-limit 200000

# Smart condensing with aggressive budget strategy
folder2md /path/to/repo --smart-condensing --token-limit 30000 --token-budget-strategy aggressive

# Generate ignore template file
folder2md --init-ignore
```

## 📖 Documentation

- **[API Documentation](docs/api.md)** - Complete API reference
- **[Configuration Guide](docs/api.md#configuration)** - Configuration options and examples
- **[File Type Support](docs/api.md#supported-file-types)** - Supported file formats

## 🛠️ Development

### Setup

```bash
# Clone the repository
git clone https://github.com/henriqueslab/folder2md4llms.git
cd folder2md4llms

# Create virtual environment and install dependencies
uv venv
uv sync --dev

# Install pre-commit hooks
make install-hooks
```

### Development Commands

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run tests with coverage
make test-cov

# Run all checks
make check

# Run pre-commit on all files
make pre-commit
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_cli.py

# Run with coverage
uv run pytest --cov=folder2md4llms --cov-report=term-missing
```

## 🎯 Use Cases

- **AI/ML Projects** - Prepare codebases for LLM analysis and code review
- **Documentation** - Generate comprehensive project overviews
- **Code Analysis** - Create structured summaries for large repositories
- **Knowledge Management** - Convert project structures into searchable markdown
- **Team Onboarding** - Provide new team members with project overviews

## 🧠 Smart Condensing

The smart condensing feature uses an intelligent anti-truncation engine to fit large repositories within token or character limits while preserving the most important content.

### How It Works

1. **Priority Analysis** - Automatically categorizes files by importance (CRITICAL/HIGH/MEDIUM/LOW)
2. **Dynamic Budget Allocation** - Distributes available tokens based on content priority
3. **Progressive Condensing** - Applies 5 levels of adaptive compression (none → light → moderate → heavy → maximum)
4. **Context-Aware Chunking** - Preserves semantic boundaries and never breaks functions mid-implementation

### Usage

```bash
# Enable smart condensing with token limit
folder2md . --smart-condensing --token-limit 50000

# Enable smart condensing with character limit
folder2md . --smart-condensing --char-limit 200000

# Use aggressive budget strategy for maximum compression
folder2md . --smart-condensing --token-limit 30000 --token-budget-strategy aggressive

# Protect critical files from condensing
folder2md . --smart-condensing --token-limit 40000 --critical-files "README.md,main.py"
```

### Budget Strategies

- **Conservative** - Preserves more content, less aggressive condensing
- **Balanced** - Good balance between content preservation and compression (default)
- **Aggressive** - Maximum compression to fit more files within limits

### Configuration

```yaml
# Enable smart condensing
smart_condensing: true
token_limit: 50000
token_budget_strategy: balanced
critical_files: ["README.md", "main.py"]
```

## 🔧 Configuration

### Basic Configuration

Create a `folder2md.yaml` file in your repository:

```yaml
# Output settings
output_format: markdown
include_tree: true
include_stats: true

# Processing options
convert_docs: true
describe_binaries: true
max_file_size: 1048576  # 1MB

# Document conversion
pdf_max_pages: 50
xlsx_max_sheets: 10
```

### Ignore Patterns

#### Quick Start with Template

Generate a comprehensive ignore template:

```bash
folder2md --init-ignore
```

This creates a `.folder2md_ignore` file with common patterns for:
- Version control systems (git, svn, etc.)
- Build artifacts and dependencies
- IDE and editor files
- OS-generated files
- Security-sensitive files
- Large media files
- Custom patterns section

#### Manual Creation

You can also create a `.folder2md_ignore` file manually:

```
# Version control
.git/
.svn/

# Build artifacts
__pycache__/
*.pyc
node_modules/
build/
dist/

# IDE files
.vscode/
.idea/

# Custom patterns
*.secret
temp/
```

## 📊 Output Format

The generated markdown includes:

1. **📑 Table of Contents** - Navigation links to all sections
2. **📁 Folder Structure** - ASCII tree representation
3. **📊 Repository Statistics** - File counts, sizes, and language breakdown
4. **📄 Source Code** - Syntax-highlighted code blocks
5. **📋 Documents** - Converted document content
6. **🔧 Binary Files & Assets** - Descriptions of non-text files

## 🔄 Improvements over gptrepo

- **Enhanced Output**: Markdown formatting with table of contents and syntax highlighting
- **Document Conversion**: PDF, DOCX, XLSX files automatically converted
- **Binary Analysis**: Intelligent descriptions for images, archives, and executables
- **Advanced Filtering**: Glob patterns and hierarchical ignore rules with template generation
- **Configuration**: YAML configuration files and extensive CLI options
- **Performance**: Multi-threaded processing with progress tracking
- **Cross-platform**: Native support for Windows, macOS, and Linux
- **Extensibility**: Modular architecture for easy extension

## 🌍 Cross-Platform Support

folder2md4llms works seamlessly across different operating systems:

- **Windows**: Full support with automatic dependency management
- **macOS**: Optimized for Apple Silicon and Intel processors
- **Linux**: Compatible with all major distributions

### Platform-Specific Features

- **File Type Detection**: Automatic fallback when python-magic is unavailable
- **Path Handling**: Consistent behavior across different file systems
- **Dependencies**: Platform-specific package management (python-magic vs python-magic-bin)
- **Error Handling**: Robust handling of platform-specific file system quirks

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [gpt-repository-loader](https://github.com/mpoon/gpt-repository-loader) by mpoon
- Built with modern Python tooling: [uv](https://github.com/astral-sh/uv), [ruff](https://github.com/astral-sh/ruff), [pytest](https://pytest.org)

## 👤 Author

**Ricardo Henriques** - [@ricardohenriques](https://github.com/ricardohenriques)

Email: ricardo@henriqueslab.org
