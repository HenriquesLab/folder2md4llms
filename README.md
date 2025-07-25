# folder2md4llms

[![Tests](https://github.com/henriqueslab/folder2md4llms/actions/workflows/test.yml/badge.svg)](https://github.com/henriqueslab/folder2md4llms/actions/workflows/test.yml)
[![Release](https://github.com/henriqueslab/folder2md4llms/actions/workflows/release.yml/badge.svg)](https://github.com/henriqueslab/folder2md4llms/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/folder2md4llms.svg)](https://pypi.org/project/folder2md4llms/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/folder2md4llms.svg)](https://pypi.org/project/folder2md4llms/)

`folder2md4llms` is a powerful and flexible tool that converts a repository's contents into a single, LLM-friendly Markdown file. It's designed to be fast, configurable, and easy to use, with a focus on producing high-quality, structured output.

## ✨ Key Features

- **Smart Condensing**: Automatically condenses code to fit within a specified token or character limit without crude truncation.
- **Document Conversion**: Converts PDF, DOCX, XLSX, and other document formats into text.
- **Binary File Analysis**: Provides intelligent descriptions for images, archives, and other binary files.
- **Highly Configurable**: Use a `folder2md.yaml` file or command-line options to customize the output.
- **Fast and Efficient**: Leverages multi-threading and efficient file processing to handle large repositories quickly.
- **Advanced Filtering**: Uses `.gitignore`-style patterns to exclude files and directories.

## 🚀 Quick Start

### Installation

Choose between Python package (recommended) or standalone binary installation:

#### 🐍 Python Package Installation (Recommended)
**Easiest installation - no security warnings, automatic updates**

> **⚠️ Important:** The package name is `folder2md4llms` but the command is `folder2md`

```bash
# Using uv (fastest and most reliable)
uv tool install folder2md4llms

# Using pip (traditional method)
pip install folder2md4llms

# Using pipx (isolated installation)
pipx install folder2md4llms

# One-time usage without installation
pipx run folder2md4llms
```

**Common Installation Error:**
```bash
# ❌ WRONG - This will fail
pipx run folder2md  # Error: No matching distribution found

# ✅ CORRECT - Use the full package name
pipx run folder2md4llms
```

#### 🚀 Binary Installation (Alternative)
**No Python required - standalone executable**

**macOS (Homebrew):**
```bash
# Add the tap first
brew tap henriqueslab/homebrew-folder2md4llms

# Binary version (cask)
brew install --cask folder2md4llms-binary
```

**Windows (Scoop - Recommended for Windows):**
```powershell
# Install Scoop first (if not already installed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Add the bucket
scoop bucket add folder2md4llms https://github.com/HenriquesLab/scoop-folder2md4llms

# Binary version (no Python required)
scoop install folder2md4llms-binary

# Verify installation
folder2md --help
```

**Manual Binary Installation:**
1. Download the appropriate binary from [GitHub Releases](https://github.com/henriqueslab/folder2md4llms/releases/latest):
   - **macOS**: `folder2md-macos-x64` (Intel) or `folder2md-macos-arm64` (Apple Silicon)
   - **Windows**: `folder2md-windows-x64.exe`
   - **Linux**: Coming soon
2. Make executable (macOS/Linux): `chmod +x folder2md-*`
3. Move to PATH:
   - **macOS/Linux**: `sudo mv folder2md-* /usr/local/bin/folder2md`
   - **Windows**:
     ```powershell
     # Option 1: Move to a directory already in PATH
     Move-Item folder2md-windows-x64.exe $env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\folder2md.exe

     # Option 2: Create a dedicated folder and add to PATH
     New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\bin"
     Move-Item folder2md-windows-x64.exe "$env:USERPROFILE\bin\folder2md.exe"
     # Then add $env:USERPROFILE\bin to your PATH in System Environment Variables
     ```

##### ⚠️ macOS Security Note (Binary Only)

When you first run the binary on macOS, you may see a security warning. This is normal for unsigned binaries. **Note:** Python package installation (pip/uv) avoids this entirely.

**Method 1: Right-click to open (Recommended)**
1. Right-click on the binary:
   - **Homebrew users**: `/opt/homebrew/bin/folder2md`
   - **Manual download**: `folder2md-macos-*` (wherever you placed it)
2. Select "Open" from the menu
3. Click "Open" in the security dialog
4. The binary will run normally from then on

**Method 2: System Settings**
1. Try to run the binary (it will be blocked)
2. Go to System Settings → Privacy & Security
3. Look for "folder2md-macos-* was blocked..."
4. Click "Allow Anyway"
5. Try running again and click "Open"

**Method 3: Command line (for advanced users)**
```bash
xattr -c folder2md-macos-*
```

**Why this happens:** macOS Gatekeeper blocks unsigned binaries by default. This is normal for open-source tools distributed as binaries.

#### Python Package vs Binary Comparison

| Feature | Python Package | Binary |
|---------|----------------|---------|
| **Installation** | ✅ Easy (pip/uv) | ⚠️ Security warnings on macOS |
| **Updates** | ✅ Automatic (pip/uv) | 🔄 Manual/Package Manager |
| **Python Required** | ✅ Yes (3.11+) | ❌ No |
| **Startup Time** | 🐌 Slower | ⚡ Fast |
| **File Size** | 📦 ~10MB | 📦 ~50MB |
| **Dependencies** | ✅ Managed by pip/uv | ✅ Self-contained |
| **Use Case** | ✅ Most users, developers | Environments without Python |

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

> **Note**: The package name is `folder2md4llms` but the command is `folder2md` for convenience.

## 🚨 Troubleshooting

### Common Installation Issues

#### "No matching distribution found for folder2md"

**Problem**: You're trying to install `folder2md` instead of the correct package name.

**Solution**: Use the full package name `folder2md4llms`:
```bash
# ❌ Wrong
pip install folder2md
pipx run folder2md

# ✅ Correct
pip install folder2md4llms
pipx run folder2md4llms
```

#### "Command 'folder2md' not found" (Windows)

**Problem**: The command isn't available in your PATH after installation.

**Solutions**:
```powershell
# Option 1: Use scoop (recommended for Windows)
scoop bucket add folder2md4llms https://github.com/HenriquesLab/scoop-folder2md4llms
scoop install folder2md4llms-binary

# Option 2: Refresh PATH after pip installation
pip install folder2md4llms
# Restart your terminal or run:
refreshenv  # If using chocolatey
# OR close and reopen PowerShell

# Option 3: Use full path
python -m folder2md4llms .
```

#### Installation with uv fails in existing project

**Problem**: uv tries to resolve project dependencies instead of installing the tool globally.

**Solution**: Use `uv tool install` instead of `uv add`:
```bash
# ❌ Wrong - tries to add to current project
uv add folder2md4llms

# ✅ Correct - installs as global tool
uv tool install folder2md4llms
```

### Platform-Specific Issues

#### Windows: PowerShell Execution Policy

```powershell
# If you get execution policy errors:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### macOS: Security Warnings for Binary

See the [macOS Security Note](#️-macos-security-note-binary-only) above for detailed solutions.

#### Linux: Permission Denied

```bash
# Make binary executable
chmod +x folder2md-linux-*
# Move to PATH with proper permissions
sudo mv folder2md-linux-* /usr/local/bin/folder2md
```

### Getting Help

- **Command help**: `folder2md --help`
- **Version check**: `folder2md --version`
- **Report issues**: [GitHub Issues](https://github.com/henriqueslab/folder2md4llms/issues)
- **Discussions**: [GitHub Discussions](https://github.com/henriqueslab/folder2md4llms/discussions)

## 🔧 Configuration

You can configure `folder2md4llms` by creating a `folder2md.yaml` file in your repository's root directory. This allows you to set advanced options and define custom behavior.

For more details, see the [Configuration Guide](docs/api.md#configuration).

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
- **Homebrew**: [henriqueslab/tap](https://github.com/HenriquesLab/homebrew-folder2md4llms) - macOS binary
- **Scoop**: [HenriquesLab bucket](https://github.com/HenriquesLab/scoop-folder2md4llms) - Windows binary

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
