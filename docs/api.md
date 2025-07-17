# API Documentation

## Overview

folder2md4llms is a command-line tool that converts folder structures to markdown format for LLM consumption. It provides enhanced features compared to the original gptrepo tool.

## Command Line Interface

### Basic Usage

```bash
folder2md /path/to/repository
```

### Options

- `--output, -o`: Output file path (default: output.md)
- `--config, -c`: Configuration file path
- `--ignore-file`: Custom ignore file path (default: .folder2md_ignore)
- `--format`: Output format (markdown, html, plain) - default: markdown
- `--include-tree/--no-tree`: Include folder structure tree (default: true)
- `--include-stats/--no-stats`: Include repository statistics (default: true)
- `--convert-docs/--no-convert-docs`: Convert documents (PDF, DOCX, etc.) (default: true)
- `--describe-binaries/--no-describe-binaries`: Describe binary files (default: true)
- `--max-file-size`: Maximum file size to process in bytes (default: 1MB)
- `--clipboard`: Copy output to clipboard
- `--verbose, -v`: Verbose output
- `--init-ignore`: Generate .folder2md_ignore template file
- `--smart-condensing`: Enable smart anti-truncation engine with priority-aware condensing
- `--token-budget-strategy`: Token budget allocation strategy (conservative/balanced/aggressive)
- `--critical-files`: Comma-separated patterns for files that should never be condensed
- `--version`: Show version information
- `--help`: Show help message

### Examples

```bash
# Basic usage
folder2md .

# With custom output file
folder2md /path/to/repo --output analysis.md

# Skip tree generation and copy to clipboard
folder2md /path/to/repo --no-tree --clipboard

# Verbose mode with custom settings
folder2md /path/to/repo --verbose --max-file-size 2097152 --no-convert-docs

# Use custom ignore file
folder2md /path/to/repo --ignore-file my_custom_ignore

# Smart condensing with token limit
folder2md /path/to/repo --smart-condensing --token-limit 50000

# Smart condensing with character limit
folder2md /path/to/repo --smart-condensing --char-limit 200000

# Generate ignore template file
folder2md --init-ignore
```

## Configuration

### Configuration File

Create a `folder2md.yaml` file in your repository or specify with `--config`:

```yaml
# Output format (markdown, html, plain)
output_format: markdown

# Include folder structure tree
include_tree: true

# Include repository statistics
include_stats: true

# Convert documents (PDF, DOCX, etc.)
convert_docs: true

# Describe binary files
describe_binaries: true

# Maximum file size to process (bytes)
max_file_size: 1048576  # 1MB

# Document conversion settings
pdf_max_pages: 50
docx_extract_images: false
xlsx_max_sheets: 10

# Binary file analysis settings
image_extract_metadata: true
archive_list_contents: true
executable_basic_info: true

# Markdown output settings
markdown_toc: true
syntax_highlighting: true
file_size_limit: 1048576  # 1MB
chunk_large_files: true

# Performance settings
max_workers: 4
progress_bar: true

# Smart condensing settings
smart_condensing: true
token_limit: 50000
char_limit: 200000
token_budget_strategy: balanced  # conservative, balanced, aggressive
critical_files: ["README.md", "main.py"]
```

### Ignore Patterns

#### Template Generation

Generate a comprehensive ignore template with common patterns:

```bash
folder2md --init-ignore
```

This creates a `.folder2md_ignore` file with pre-configured patterns for:
- Version control systems (.git, .svn, .hg, etc.)
- Build artifacts and dependencies (node_modules, __pycache__, dist, etc.)
- IDE and editor files (.vscode, .idea, *.swp, etc.)
- OS-generated files (.DS_Store, Thumbs.db, etc.)
- Security-sensitive files (*.key, *.pem, .env, etc.)
- Large media and archive files
- Custom patterns section for project-specific needs

#### Manual Creation

You can also create a `.folder2md_ignore` file manually to specify files and directories to ignore:

```
# Version control
.git/
.svn/
.hg/

# Build artifacts
__pycache__/
*.pyc
build/
dist/
*.egg-info/
node_modules/
target/

# IDE files
.vscode/
.idea/
*.sublime-*

# OS files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.log
*~

# Custom patterns
my_secret_dir/
*.backup
```

## Core Components

### RepositoryProcessor

The main processor that orchestrates the conversion process.

```python
from folder2md4llms.processor import RepositoryProcessor
from folder2md4llms.utils.config import Config

config = Config()
processor = RepositoryProcessor(config)
result = processor.process(Path("/path/to/repo"))
```

### Configuration Management

```python
from folder2md4llms.utils.config import Config

# Load from file
config = Config.load(config_path=Path("config.yaml"))

# Load from repository directory
config = Config.load(repo_path=Path("/path/to/repo"))

# Save configuration
config.save(Path("config.yaml"))
```

### File Processing

```python
from folder2md4llms.utils.file_utils import (
    is_binary_file, is_text_file, get_file_category,
    should_convert_file, read_file_safely
)

# Check file types
is_binary = is_binary_file(file_path)
is_text = is_text_file(file_path)
category = get_file_category(file_path)  # text, document, image, archive, executable, binary

# Safe file reading
content = read_file_safely(file_path, max_size=1024*1024)
```

### Document Conversion

```python
from folder2md4llms.converters.converter_factory import ConverterFactory

factory = ConverterFactory()
converter = factory.get_converter(file_path)
if converter:
    content = converter.convert(file_path)
```

### Binary File Analysis

```python
from folder2md4llms.analyzers.binary_analyzer import BinaryAnalyzer

analyzer = BinaryAnalyzer()
description = analyzer.analyze_file(file_path)
```

### Ignore Patterns

```python
from folder2md4llms.utils.ignore_patterns import IgnorePatterns

# Load from file
patterns = IgnorePatterns.from_file(Path(".folder2md_ignore"))

# Check if should ignore
should_ignore = patterns.should_ignore(file_path, base_path)

# Add custom patterns
patterns.add_pattern("*.tmp")
patterns.remove_pattern("*.log")
```

### Tree Generation

```python
from folder2md4llms.utils.tree_generator import TreeGenerator

generator = TreeGenerator(ignore_patterns)
tree = generator.generate_tree(repo_path)
counts = generator.count_items(repo_path)
```

## Supported File Types

### Text Files
- Source code files (Python, JavaScript, Java, C++, etc.)
- Configuration files (JSON, YAML, TOML, etc.)
- Documentation files (Markdown, reStructuredText, etc.)
- Web files (HTML, CSS, etc.)

### Document Conversion
- **PDF**: Text extraction using pypdf
- **DOCX**: Text and table extraction using python-docx
- **XLSX**: Spreadsheet to markdown table conversion using openpyxl
- **CSV**: Automatic markdown table formatting

### Binary File Analysis
- **Images**: Metadata extraction (dimensions, format, EXIF data)
- **Archives**: Contents listing for ZIP files
- **Executables**: Basic file information and type detection

## Output Format

The generated markdown includes:

1. **Table of Contents**: Navigation links to all sections
2. **Folder Structure**: ASCII tree representation
3. **Repository Statistics**: File counts, sizes, and language breakdown
4. **Source Code**: Syntax-highlighted code blocks
5. **Documents**: Converted document content
6. **Binary Files & Assets**: Descriptions of non-text files

## Performance Features

- **Parallel Processing**: Multi-threaded file processing
- **Progress Tracking**: Real-time progress bars
- **Memory Efficient**: Streaming file processing
- **Size Limits**: Configurable file size limits
- **Caching**: Efficient file type detection

## Error Handling

The tool gracefully handles:
- Permission errors
- Corrupted files
- Large files
- Binary files
- Network timeouts
- Missing dependencies

## Extensions

The tool is designed to be extensible:
- Add new document converters
- Implement custom binary analyzers
- Create new output formatters
- Add custom ignore patterns
