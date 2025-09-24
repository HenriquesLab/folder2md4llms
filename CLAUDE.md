# folder2md4llms Development Guide

## 🎯 Project Overview
folder2md4llms converts folder structures and file contents into LLM-friendly Markdown files. It's designed to help developers share codebases with AI assistants like Claude.

## 🏗️ Architecture

### Core Components
1. **CLI (`cli.py`)**: Entry point using rich-click for enhanced help
2. **Processor (`processor.py`)**: Main orchestrator for repository processing
3. **Analyzers**: Code analysis and condensing logic
4. **Converters**: Document format conversion (PDF, DOCX, etc.)
5. **Engine**: Smart anti-truncation engine for token management
6. **Utils**: File handling, patterns, and configuration

### Key Design Decisions
- **Streaming Processing**: Handles large files efficiently with parallel processing
- **Smart Condensing**: Progressive condensing based on token budgets
- **Hierarchical Ignore Patterns**: Supports .folder2md_ignore at multiple levels
- **Platform Agnostic**: Uses python-magic-bin on Windows, python-magic elsewhere

## 📦 Package Structure
```
src/folder2md4llms/
├── cli.py                 # Command-line interface
├── processor.py           # Main processing logic
├── analyzers/            # Code analysis modules
│   ├── priority_analyzer.py    # File importance scoring
│   ├── progressive_condenser.py # Smart code condensing
│   └── binary_analyzer.py      # Binary file analysis
├── converters/           # Document converters
│   ├── converter_factory.py    # Central converter registry
│   └── [format]_converter.py   # Format-specific converters
├── engine/               # Smart processing engine
│   └── smart_engine.py         # Token budget management
├── formatters/           # Output formatting
│   └── markdown.py            # Markdown generation
└── utils/                # Utilities
    ├── config.py              # Configuration management
    ├── file_strategy.py       # File processing strategies
    ├── streaming_processor.py # Parallel file processing
    └── token_utils.py         # Token counting
```

## 🚀 Development Workflow

### Setup
```bash
# Clone and navigate
git clone https://github.com/henriqueslab/folder2md4llms
cd folder2md4llms

# Install with uv (recommended)
uv sync --all-extras

# Or traditional pip
pip install -e ".[dev]"
```

### Common Tasks
```bash
# Run tests with coverage
make test

# Format code and fix lint issues
make fix

# Run all static analysis (format, lint, types)
make check

# Build package
make build
```

### Testing
- Tests use pytest with parallel execution
- Mock heavy operations (file I/O, network)
- Test cross-platform compatibility
- Coverage target: >80%

## 🐛 Known Issues & TODOs

### High Priority
1. **Test Coverage**: Increase coverage from 67% to >80%
   - Focus on converters and analyzers with lower coverage
   - Add integration tests for smart engine

2. **Error Handling**: Improve error messages and recovery
   - Better handling of corrupted files
   - Clearer user messages for common issues

3. **Performance**: Optimize for large repositories
   - Implement incremental processing
   - Add caching for repeated runs

### Medium Priority
- Add support for more file formats
- Implement custom token counting models
- Add progress bars for long operations
- Create better ignore pattern suggestions

### Low Priority
- Add telemetry (opt-in)
- Create GUI version
- Add cloud storage support

## 🔧 Configuration

### Key Config Options
- `token_limit`: Maximum tokens for output (e.g., 80000)
- `smart_condensing`: Enable intelligent code condensing
- `condense_languages`: Languages to condense
- `max_file_size`: Skip files larger than this
- `token_budget_strategy`: How to allocate tokens (balanced/aggressive/conservative)

### Environment Variables
- `FOLDER2MD_CONFIG`: Path to custom config file
- `FOLDER2MD_UPDATE_CHECK`: Disable update checks

## 📝 Code Style
- Python 3.11+ with type hints
- Ruff for linting and formatting
- Line length: 88 characters
- Docstrings for public APIs
- NO comments unless necessary

## 🚢 Release Process
1. Update version in `__version__.py`
2. Update CHANGELOG.md
3. Create PR to main
4. Tag release triggers PyPI publication

## 🔐 Security Considerations
- Sanitize file paths to prevent traversal
- Limit file sizes to prevent DoS
- No execution of analyzed code
- Safe handling of binary files

## 💡 Tips for Contributors
1. **Adding File Formats**: Extend `converter_factory.py`
2. **New Analyzers**: Inherit from `BaseCodeAnalyzer`
3. **Token Counting**: Use `token_utils.py` for consistency
4. **Cross-platform**: Test on Windows, macOS, Linux

## 📊 Metrics & Monitoring
- GitHub Actions for CI/CD
- Coverage reports with codecov
- Performance benchmarks in tests
- Error tracking via GitHub issues

## 🤝 Integration Points
- **Package Managers**: PyPI, pipx
- **IDEs**: VS Code extension planned
- **CI/CD**: GitHub Actions examples
- **Cloud**: AWS Lambda, Google Cloud Functions

## 📚 Resources
- [API Documentation](docs/api.md)
- [User Guide](README.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Architecture Decisions](docs/architecture.md) (TODO)

## 🎯 Project Goals
1. **Comprehensive**: Process diverse file types and formats
2. **Intelligent**: Use AST parsing and smart analysis for quality output
3. **Configurable**: Extensive options for different use cases
4. **Reliable**: Consistent output across platforms
5. **LLM-Friendly**: Optimized for AI consumption

## 🔄 Recent Changes
- Removed binary distribution in favor of Python package only
- Added Gemini AI workflows for automated code review and triage
- Enhanced document converters with binary content validation
- Improved error handling in PDF, DOCX, PPTX, and RTF converters
- Streamlined CLI with simplified help text
- Added comprehensive installation documentation

## 📊 Project Stats
- Supports 15+ document formats
- Multi-language AST parsing capabilities
- Configurable token/character limits
- Smart condensing with priority analysis
