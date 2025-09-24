# folder2md4llms

<img src="src/logo/logo-folder2md4llms.svg" align="right" width="200" style="margin-left: 20px;"/>

[![Tests](https://github.com/henriqueslab/folder2md4llms/actions/workflows/test.yml/badge.svg)](https://github.com/henriqueslab/folder2md4llms/actions/workflows/test.yml)
[![Release](https://github.com/henriqueslab/folder2md4llms/actions/workflows/release.yml/badge.svg)](https://github.com/henriqueslab/folder2md4llms/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/folder2md4llms.svg)](https://pypi.org/project/folder2md4llms/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/folder2md4llms.svg)](https://pypi.org/project/folder2md4llms/)

`folder2md4llms` is a configurable tool that converts a repository's contents into a single, LLM-friendly Markdown file. It supports various file formats and provides options for content condensing and filtering.

## ✨ Key Features

- **Smart Condensing**: Automatically condenses code to fit within a specified token or character limit without crude truncation.
- **Document Conversion**: Converts PDF, DOCX, XLSX, and other document formats into text.
- **Binary File Analysis**: Provides intelligent descriptions for images, archives, and other binary files.
- **Highly Configurable**: Use a `folder2md.yaml` file or command-line options to customize the output.
- **Parallel Processing**: Uses multi-threading for processing multiple files concurrently.
- **Advanced Filtering**: Uses `.gitignore`-style patterns to exclude files and directories.

## 🚀 Installation

```bash
# Using pipx (recommended)
pipx install folder2md4llms

# Or using pip
pip install folder2md4llms

# Verify installation
folder2md --help
```

> **Note:** Package name is `folder2md4llms`, command is `folder2md`


### Basic Usage

```bash
# Process the current directory and save to output.md
folder2md .

# Process a specific directory and set a token limit
folder2md /path/to/repo --limit 80000t

# Copy the output to the clipboard
folder2md /path/to/repo --clipboard

# Generate a .folder2md_ignore file
folder2md --init-ignore
```

For a full list of commands and options, see the [CLI Reference](docs/api.md) or run `folder2md --help`.

## 🚨 Troubleshooting

### Common Issues

**"No matching distribution found for folder2md"**
- Use the correct package name: `folder2md4llms` (not `folder2md`)

**"Command 'folder2md' not found"**
- Ensure pipx is installed: `pip install pipx`
- Try: `python -m folder2md4llms .`

### Platform-Specific Issues

#### Windows: Use WSL2 (Recommended)

For Windows users, we recommend using WSL2 (Windows Subsystem for Linux) for the best experience:

```bash
# Install WSL2 (run in PowerShell as Administrator)
wsl --install -d Ubuntu-22.04

# Then follow the Linux installation instructions in WSL2
```

This provides better compatibility and performance compared to native Windows installation.


### Getting Help

- **Command help**: `folder2md --help`
- **Version check**: `folder2md --version`
- **Alternative**: `python -m folder2md4llms --help` (works without installation)
- **Report issues**: [GitHub Issues](https://github.com/henriqueslab/folder2md4llms/issues)
- **Discussions**: [GitHub Discussions](https://github.com/henriqueslab/folder2md4llms/discussions)

## 🔧 Configuration

You can configure `folder2md4llms` by creating a `folder2md.yaml` file in your repository's root directory. This allows you to set advanced options and define custom behavior.

For more details, see the [CLI Reference](docs/api.md).

## 🛠️ Development

Interested in contributing? Get started with these simple steps:

```bash
# Clone the repository
git clone https://github.com/henriqueslab/folder2md4llms.git
cd folder2md4llms

# Set up the development environment
make setup

# See all available commands
make help
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For more information, see the [Contributing Guidelines](CONTRIBUTING.md).

## 📖 Documentation

- **[CLI Reference](docs/api.md)** - Complete command-line reference
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](CHANGELOG.md)** - Version history and changes

## 📦 Distribution Channels

- **PyPI**: [folder2md4llms](https://pypi.org/project/folder2md4llms/) - Python package

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
