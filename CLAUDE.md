# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- `make setup`: Install development dependencies and setup environment
- `make fix`: Format code and fix lint issues
- `make check`: Run all checks (lint, format, type, test)
- `make test`: Run tests with coverage reporting
- `make run`: Execute the CLI application with args (e.g., `make run ARGS="--help"`)
- `make build`: Build package for distribution
- `make publish-test`: Publish to PyPI test environment
- `make docs`: Generate documentation
- `make clean`: Remove build artifacts and caches
- `make version`: Show or bump version (e.g., `make version BUMP=patch`)

### Running Single Tests
```bash
uv run pytest tests/test_specific_file.py::test_function_name -v
```

## Code Architecture

### Core Processing Pipeline
The application follows a clear data flow:
1. **Configuration Loading** (`utils/config.py`) - Loads YAML config files hierarchically
2. **File Scanning** (`processor.py`) - Recursively scans directories with ignore filtering
3. **File Classification** (`utils/file_utils.py`) - Categorizes files by type
4. **Content Processing** - Routes to appropriate converter/analyzer
5. **Output Generation** (`formatters/markdown.py`) - Formats results with syntax highlighting

### Key Components

**RepositoryProcessor** (`processor.py`): Main orchestrator that coordinates the entire processing pipeline. Manages file scanning, filtering, and processing workflow.

**SmartAntiTruncationEngine** (`engine/smart_engine.py`): Intelligent content processing system that minimizes truncation through:
- Token budget management with configurable strategies (balanced, priority-first, condensed)
- Priority analysis of content importance
- Progressive condensing for large files
- Smart allocation across different content types

**ConverterFactory** (`converters/converter_factory.py`): Factory pattern implementation for document conversion. Supports PDF, DOCX, XLSX, RTF, Jupyter notebooks (.ipynb), and PowerPoint (PPTX) with graceful fallback when dependencies are unavailable.

**BinaryAnalyzer** (`analyzers/binary_analyzer.py`): Intelligently analyzes non-text files including images, archives, and executables. Uses PIL for image metadata and handles platform-specific file detection.

**Config** (`utils/config.py`): Hierarchical configuration system supporting both CLI arguments and YAML files. Searches up directory tree for `folder2md.yaml` files.

### Cross-Platform Compatibility

**Platform Detection** (`utils/platform_utils.py`): Comprehensive platform detection with different magic library dependencies:
- Windows: Uses `python-magic-bin`
- macOS/Linux: Uses standard `python-magic`
- Graceful fallback when optional dependencies unavailable

**File System Handling**: Platform-specific path handling and permission management throughout the codebase.

### Ignore Pattern System

**Pattern Matching** (`utils/ignore_patterns.py`): Implements gitignore-style pattern matching with support for:
- Recursive patterns (`**/*`)
- Directory-specific patterns
- Custom `.folder2md_ignore` files
- Comprehensive default patterns for build artifacts, dependencies, OS files

### Extension Points

**Adding New Converters**: Extend `BaseConverter` in `converters/base.py` and register in `ConverterFactory`.

**Adding Binary Analysis**: Extend methods in `BinaryAnalyzer` for new file types.

**Output Formats**: Extend `MarkdownFormatter` or create new formatters following the same interface.

## Configuration

The tool supports hierarchical YAML configuration via `folder2md.yaml` files. Config files are searched from the current directory up to the repository root. CLI arguments override config file settings.

## Testing

Tests use pytest with comprehensive fixtures for different file types and scenarios. The test suite covers:
- File type detection and classification
- Document conversion with mock dependencies
- Binary file analysis
- Cross-platform compatibility
- Configuration loading and inheritance
- Ignore pattern matching

## Dependencies

**Core Dependencies**: rich-click (enhanced CLI), PyYAML (config), rich (progress/formatting)

**Optional Dependencies**:
- `python-magic`/`python-magic-bin` (file type detection)
- `pypdf` (PDF conversion)
- `python-docx` (Word conversion)
- `openpyxl` (Excel conversion)
- `striprtf` (RTF conversion)
- `nbconvert` (Jupyter notebook conversion)
- `python-pptx` (PowerPoint conversion)
- `Pillow` (image analysis)
- `psutil` (memory monitoring)

All optional dependencies have graceful fallback behavior when unavailable.

## Development Toolchain

**Package Management**: Uses `uv` (ultra-fast Python package manager) + `hatch` (modern Python project management)

**Code Quality**:
- `ruff` (fast Python linter and formatter)
- `mypy` (static type checking)
- `pytest` (testing framework with coverage reporting)

**CLI Framework**: `rich-click` provides enhanced command-line interface with better help formatting, argument grouping, and rich text styling.

## Git Submodules

The project includes package distribution repositories as git submodules in the `git_submodules/` directory:

**Initialize submodules** (after cloning):
```bash
git submodule update --init --recursive
```

**Update submodules** to latest versions:
```bash
git submodule update --remote
```

**Working with submodules**:
- Changes to submodules should be made in their respective repositories
- The main repository tracks specific commits of each submodule
- Use `git submodule foreach git pull origin main` to update all submodules simultaneously

## Package Distribution

The folder2md4llms project maintains a multi-repository structure for cross-platform package distribution:

### Repository Structure
- **Main Repository**: `/Users/paxcalpt/Documents/GitHub/folder2md4llms` - Core application and PyPI distribution
- **Scoop Repository**: `git_submodules/scoop-folder2md4llms` - Windows package manager (git submodule)
- **Homebrew Repository**: `git_submodules/homebrew-folder2md4llms` - macOS/Linux package manager (git submodule)

### Scoop Repository (Windows)
**Location**: `git_submodules/scoop-folder2md4llms`
**Purpose**: Windows package distribution via Scoop package manager

**GitHub Actions Workflows**:
- **Test Manifest** (`test-manifest.yml`): Comprehensive testing pipeline
  - Matrix testing across Windows versions and Python versions (3.11, 3.12, 3.13)
  - JSON validation, installation, and functionality testing
  - Runs on push, PR, and daily schedule
- **Update Manifest** (`update-manifest.yml`): Automated version monitoring and updates
  - Runs every 4 hours to check PyPI for new versions
  - Automatically updates Scoop manifest and creates PRs
  - Tests updated manifest before creating PR

**Package Manifest**: `bucket/folder2md4llms.json`
- Current version tracking and autoupdate configuration
- Pip-based installation with Python dependency management

### Homebrew Repository (macOS/Linux)
**Location**: `git_submodules/homebrew-folder2md4llms`
**Purpose**: macOS and Linux package distribution via Homebrew tap

**GitHub Actions Workflows**:
- **Test Formula** (`test-formula.yml`): Formula syntax and installation testing
  - Validates Homebrew formula syntax
  - Tests installation from source
- Matrix testing on macOS-13 and macOS-14
  - Comprehensive functionality testing including CLI commands, file conversion, configuration

**Formula File**: `Formula/folder2md4llms.rb`
- Python 3.11 based installation
- Comprehensive dependency management (40+ Python resources)
- Full test suite for installation verification

### Automated Maintenance
- **Version Synchronization**: Both repositories automatically track PyPI releases
- **Quality Assurance**: Comprehensive testing across all supported platforms
- **User Support**: Automated issue handling and response systems
- **Performance Monitoring**: Installation timing and performance metrics
