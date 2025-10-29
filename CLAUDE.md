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
just test

# Format code and fix lint issues
just fix

# Run all static analysis (format, lint, types)
just check

# Build package
just build
```

### Testing
- Tests use pytest with parallel execution
- Mock heavy operations (file I/O, network)
- Test cross-platform compatibility
- Coverage target: >80%

## 🐛 Known Issues & TODOs

### High Priority
1. **Test Coverage**: Increase coverage from 67% to >80%
2. **Error Handling**: Improve error messages and recovery
3. **Performance**: Optimize for large repositories

### Medium Priority
- Add support for more file formats
- Implement custom token counting models
- Add progress bars for long operations

### Documentation
- Keep docs simple and focused
- Avoid unnecessary complexity in installation guides
- Focus on common use cases, not edge cases

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
5. Update Homebrew formula (see below)

### Homebrew Formula Updates

folder2md4llms is distributed via PyPI and Homebrew. After the PyPI release is live, update the Homebrew formula.

#### Homebrew Formula Location

The Homebrew formula is maintained in a separate repository located at `../homebrew-formulas`:
- **Repository**: `../homebrew-formulas/`
- **Formula file**: `Formula/folder2md4llms.rb`
- **Automation**: Managed via justfile commands

#### Commands

After the PyPI release is live and verified at https://pypi.org/project/folder2md4llms/:

```bash
cd ../homebrew-formulas

# Option 1: Full automated release workflow (recommended)
# This will update, test, commit, and push in one command
just release folder2md4llms

# Option 2: Manual step-by-step workflow
just update folder2md4llms           # Updates to latest PyPI version
just test folder2md4llms             # Tests the formula installation
just commit folder2md4llms VERSION   # Commits with standardized message
git push                             # Push to remote

# Utility commands
just list                            # List all formulas with current versions
just check-updates                   # Check for available PyPI updates
just sha256 folder2md4llms VERSION   # Get SHA256 for a specific version
```

#### Workflow Notes

- **Always verify PyPI first**: The formula update pulls package info from PyPI, so the release must be live
- **Automatic metadata**: The `just update` command automatically fetches the version, download URL, and SHA256 checksum from PyPI
- **Full automation**: The `just release` command runs the complete workflow: update → test → commit → push
- **Standardized commits**: Formula updates use consistent commit message format
- **Testing**: The `just test` command uninstalls and reinstalls the formula to verify it works correctly

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
- Simplified documentation across all channels
- Removed legacy version support references
- Streamlined installation instructions (Python package only)
- Reduced troubleshooting complexity
- Enhanced document converters with binary content validation
- Improved error handling in converters

## 📊 Project Stats
- Supports 15+ document formats
- Multi-language AST parsing capabilities
- Configurable token/character limits
- Smart condensing with priority analysis
