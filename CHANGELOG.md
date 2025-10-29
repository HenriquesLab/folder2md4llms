# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.12] - 2025-10-29

### Added
- **Installation Method Detection**: New `install_detector.py` utility that detects how folder2md4llms was installed (Homebrew, pipx, uv, pip, dev) and provides context-aware upgrade commands
- **Homebrew Update Checker**: New `homebrew_checker.py` utility that checks for Homebrew updates via `brew outdated` or GitHub formula
- **Encoding Utilities**: New `encoding.py` module with centralized file reading, encoding fallback, and Unicode surrogate character handling
- **Community Health Files**: Added comprehensive community files to improve GitHub community health score from 50% to 100%
  - CONTRIBUTING.md with complete contribution guidelines
  - CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
  - Issue templates (bug report, feature request)

### Developer Experience
- New utilities prepare for enhanced version checking and user-friendly upgrade instructions
- Comprehensive test coverage: 94% for homebrew_checker, 79% for install_detector

## [0.5.11] - 2025-10-29

### Added
- **Changelog Validation in Release Workflow**: Automated verification that CHANGELOG.md is updated before releases
  - Verifies CHANGELOG entry exists for the release version
  - Validates date format (YYYY-MM-DD)
  - Checks for duplicate tags
  - Fails release early if validation fails (before tests/build/publish)
  - Inspired by TaskRepo's proven pattern

### Changed
- **Migrated from Makefile to justfile** for improved developer experience
  - All 12 development commands converted to justfile recipes
  - Python-based implementations for complex logic (check-release, version)
  - Cleaner syntax: `just test -v` vs `make test ARGS="-v"`
  - Better argument passing with variadic parameters
  - Built-in help with `just --list`
  - No .PHONY declarations needed
  - Cross-platform consistency
- Updated all documentation (README.md, CLAUDE.md) to use `just` commands
- Removed Makefile after comprehensive dependency audit

### Developer Experience
- Contributors should now use `just` instead of `make`
- Installation: `brew install just` (macOS) or `cargo install just`
- Migration is straightforward: `make test` → `just test`, `make setup` → `just setup`

## [0.5.10] - 2025-01-17

### Added
- **Interactive File Analysis and Ignore Suggestions**: Automatically analyzes files during processing and provides interactive suggestions for files that should be ignored
  - Detects binary data files (.cif, .h5, .hdf5, .npy, .mat, etc.) regardless of size
  - Identifies media files (images, videos, audio) that don't add LLM value
  - Flags build artifacts (compiled code, minified JS/CSS, etc.)
  - Detects large files exceeding configurable threshold (default: 10MB)
  - Interactive prompts allow users to add suggested patterns to `.folder2md_ignore`
  - Category-by-category selection with file size summaries
  - Skips prompts in non-interactive environments (CI/CD)
- CLI option `--no-suggestions` to disable file analysis and suggestions
- Configuration options:
  - `enable_ignore_suggestions`: Enable/disable the feature (default: true)
  - `interactive_suggestions`: Use interactive prompts vs display-only (default: true)
  - `large_file_threshold`: Size threshold for flagging large files (default: 10MB)

### Changed
- Ignore pattern suggestions now run automatically by default (previously only with `--verbose`)
- Enhanced `IgnoreSuggester` with smart detection for multiple file categories
- Improved suggestion output with emojis and organized categories

## [0.5.9] - 2025-01-17

### Fixed
- Fixed Unicode encoding error when using `--clipboard` flag with files containing invalid UTF-8 byte sequences
- Added comprehensive surrogate character handling throughout the processing pipeline
- Improved error handling for files with mixed or corrupted encodings
- Added `errors="surrogateescape"` and `errors="replace"` strategies for robust file reading
- Enhanced document converters (PDF, DOCX, PPTX, RTF) to handle encoding issues gracefully

### Changed
- File reading now uses surrogate-aware encoding strategies with immediate cleaning
- Markdown formatter cleans all input content of surrogates before processing
- Added multiple layers of surrogate detection and cleaning for robustness
- Improved error messages for Unicode-related issues

## [0.5.8] - 2025-01-16

### Fixed
- Corrected upgrade instructions in update notification message
- Updated documentation to reflect accurate package manager commands

## [0.5.7] - 2025-01-02

### Added
- Prominent Python 3.11+ requirement notice in README installation section
- Python version troubleshooting guide in README
- Runtime Python version check with friendly error message in CLI
- Migration path documentation for Python 3.8-3.10 users (use v0.2.0)

### Changed
- Moved Python version requirements to top of installation.md for better visibility
- Enhanced installation documentation with clear version compatibility guidance

## [0.5.6] - 2025-01-02

### Fixed
- Removed incorrect `.doc` (legacy Word format) support from DOCXConverter - only `.docx` is supported by python-docx library
- Fixed "File is not a zip file" error when encountering `.doc` files
- Added `~$*` pattern to ignore Microsoft Office temporary files

### Changed
- DOCXConverter now only handles `.docx` files (XML-based format)
- Legacy `.doc` files are no longer advertised as convertible

### Added
- Simplified and streamlined the command-line interface (CLI) for a more intuitive user experience.
- Simplified the `Makefile` with fewer, more logical commands for easier development.

## [0.4.0] - 2025-01-17

### Added
- **🚀 Smart Anti-Truncation Engine**: Intelligent system to eliminate crude content truncation
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
