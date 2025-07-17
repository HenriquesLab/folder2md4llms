# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Simplified and streamlined the command-line interface (CLI) for a more intuitive user experience.
- Simplified the `Makefile` with fewer, more logical commands for easier development.

## [0.4.0] - 2025-01-17

### Added
- **🚀 Smart Anti-Truncation Engine**: Revolutionary system to eliminate crude content truncation
  - **Priority-based File Classification**: Automatically categorizes files by importance (CRITICAL/HIGH/MEDIUM/LOW)
  - **Dynamic Token Budget Allocation**: Intelligent distribution of token budget based on content priority
  - **Progressive Condensing**: 5-level adaptive compression system (none → light → moderate → heavy → maximum)
  - **Context-aware Chunking**: Preserves semantic boundaries and never breaks functions mid-implementation
  - **AST-based Code Analysis**: Deep understanding of Python, JavaScript, and Java code structures
  - **Import Graph Analysis**: Determines dependency importance for better prioritization
  - **Multi-language Support**: Extensible architecture for different programming languages
  - **Budget Optimization**: Maximizes information density within token constraints
- **Enhanced CLI Options**: New smart condensing flags
  - `--smart-condensing`: Enable intelligent content condensing
  - `--token-budget-strategy`: Choose allocation strategy (conservative/balanced/aggressive)
  - `--priority-analysis`: Control priority classification behavior
- **Streaming File Processing**: Handle large files without loading entire content into memory
- **Parallel Processing**: Multi-threaded file analysis using ThreadPoolExecutor for improved performance
- **File Chunking**: Split very large files into configurable chunks with token/size limits
- **Memory Usage Monitoring**: Track and warn about memory usage during large processing jobs
- **Token Counting**: Configurable token limits for different LLM models with estimation methods
- **Enhanced Document Support**: Added support for RTF, Jupyter notebooks (.ipynb), and PowerPoint (.pptx) files
- **Full .gitignore Compatibility**: Complete gitignore-style pattern matching including negation patterns
- **CLI Enhancements**: New options including `--token-limit`, `--char-limit`, `--max-tokens-per-chunk`, `--use-gitignore`
- **Ignore Template Generation**: `--init-ignore` flag to generate comprehensive .folder2md_ignore template
- **Cross-platform Compatibility**: Enhanced support for Windows, macOS, and Linux with platform-specific dependencies
- **GitHub Actions Workflows**: Automated testing and PyPI publishing workflows
- **Tag-based Versioning**: Integrated hatch-vcs for automatic version management from git tags
- **Update Checker**: Optional automatic update notifications with caching support

### Changed
- **BREAKING**: Minimum Python version requirement raised from 3.8 to 3.11
- **PDF Processing**: Upgraded from PyPDF2 to pypdf for better text extraction and performance
- **Configuration System**: Enhanced hierarchical YAML configuration with more options
- **File Type Detection**: Improved cross-platform file type detection using python-magic/python-magic-bin
- **CLI Interface**: More intuitive command-line options with better help text and validation
- **Error Handling**: Better cross-platform file system error handling and user feedback
- **Dependencies**: Updated to use modern, actively maintained libraries

### Fixed
- **Virtual Environment Filtering**: Properly exclude .venv directories in ignore patterns
- **Platform-specific Issues**: Resolved Windows compatibility issues with file paths and permissions
- **Memory Leaks**: Fixed memory issues when processing large repositories
- **Pattern Matching**: Corrected gitignore-style pattern matching edge cases

### Removed
- **Deprecated Dependencies**: Removed PyPDF2 in favor of pypdf
- **Legacy Python Support**: Dropped support for Python 3.8, 3.9, and 3.10
- **Redundant Workflows**: Removed build workflow in favor of streamlined testing and release workflows

## [0.2.0] - 2024-XX-XX

### Added
- Initial enhanced version with core functionality
- Basic document conversion support (PDF, DOCX, XLSX)
- File type detection and binary analysis
- Configurable ignore patterns
- Rich CLI interface with progress bars
- Basic cross-platform support

### Changed
- Complete rewrite of the processing pipeline
- Improved output formatting with syntax highlighting
- Better error handling and user feedback

## [0.1.0] - 2024-XX-XX

### Added
- Initial release
- Basic folder-to-markdown conversion
- Simple file filtering
- Command-line interface

---

## Development Notes

### Version 0.2.1+ Features

This version introduces significant performance and scalability improvements:

- **Streaming Architecture**: Files are processed in chunks rather than loaded entirely into memory
- **Parallel Processing**: Multiple files can be processed simultaneously using ThreadPoolExecutor
- **Token Management**: Built-in token counting and estimation for LLM workflows
- **Enhanced Document Support**: Support for RTF, Jupyter notebooks, and PowerPoint files
- **Production Ready**: Comprehensive testing, automated releases, and professional documentation

### Breaking Changes in 0.2.1+

- **Python 3.11+ Required**: The minimum Python version has been raised to 3.11
- **Configuration Changes**: Some configuration options have been renamed or restructured
- **Dependency Updates**: Several dependencies have been updated to newer versions

### Migration Guide

To upgrade from version 0.2.0 to 0.2.1+:

1. **Update Python**: Ensure you're running Python 3.11 or later
2. **Update Dependencies**: Run `pip install --upgrade folder2md4llms`
3. **Review Configuration**: Check your `folder2md.yaml` files for any deprecated options
4. **Test Functionality**: Run the tool with `--verbose` flag to ensure all features work as expected

### Development Commands

- `make dev`: Install development dependencies
- `make test`: Run tests with coverage
- `make lint`: Run linting checks
- `make format`: Format code
- `make check`: Run all checks
- `make build`: Build package
- `make docs`: Generate documentation

### Contributing

This project uses:
- **Hatch** for project management and building
- **Ruff** for linting and formatting
- **pytest** for testing
- **GitHub Actions** for CI/CD
- **Semantic versioning** for releases

For detailed contribution guidelines, see the project documentation.
