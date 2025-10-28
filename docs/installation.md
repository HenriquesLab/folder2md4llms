# Installation Guide

> **Quick Install**: `pipx install folder2md4llms`

Requires Python 3.11+. Check your version: `python --version`

---

## 🐍 Python Package Installation

### Using pipx (Recommended)

```bash
# Install folder2md4llms
pipx install folder2md4llms

# Verify
folder2md --help
```

### Using pip

```bash
pip install folder2md4llms
folder2md --help
```

---

## 🖥️ Platform-Specific Notes

### Linux

```bash
# Ubuntu/Debian
sudo apt install python3-pip pipx
pipx install folder2md4llms

# Fedora/RHEL
sudo dnf install python3-pip
pip3 install pipx
pipx install folder2md4llms
```

### macOS

```bash
brew install pipx
pipx install folder2md4llms
```

### Windows

```bash
pip install pipx
pipx install folder2md4llms
```

---

## 🚨 Troubleshooting

### Command not found

Add pipx to your PATH:
```bash
# Linux/macOS
export PATH="$HOME/.local/bin:$PATH"

# Or use module directly
python -m folder2md4llms .
```

### Installation fails

```bash
# Try pip instead
pip install folder2md4llms

# Or update pipx
pip install --upgrade pipx
```

## Development Installation

```bash
git clone https://github.com/henriqueslab/folder2md4llms.git
cd folder2md4llms
pip install -e ".[dev]"
```

## Getting Help

- [GitHub Issues](https://github.com/henriqueslab/folder2md4llms/issues)
- [GitHub Discussions](https://github.com/henriqueslab/folder2md4llms/discussions)
