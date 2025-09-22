# Complete Installation Guide

This guide covers platform-specific installation instructions for folder2md4llms.

> **👋 Quick Install?** For most users, `pipx install folder2md4llms` is all you need. This guide is for users who need platform-specific setup or encounter installation issues.

---

## 🐍 Python Package Installation

### Recommended Method: pipx

pipx is the recommended way to install Python command-line tools as it creates isolated environments for each tool:

```bash
# Install pipx if you don't have it
pip install pipx

# Install folder2md4llms
pipx install folder2md4llms

# Verify installation
folder2md --help
```

### Alternative: pip with --user

```bash
# Install to user directory
pip install --user folder2md4llms

# Verify installation
folder2md --help
```

### Alternative: System-wide pip (not recommended)

```bash
# Install system-wide (may require sudo on Linux/macOS)
pip install folder2md4llms

# Verify installation
folder2md --help
```

---

## 🖥️ Platform-Specific Setup

### Linux

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pipx
sudo apt install python3-pip pipx

# Install folder2md4llms
pipx install folder2md4llms

# Verify installation
folder2md --help
```

#### Red Hat/CentOS/Fedora

```bash
# Install Python and pip
sudo dnf install python3-pip

# Install pipx
python3 -m pip install --user pipx

# Add pipx to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Install folder2md4llms
pipx install folder2md4llms

# Verify installation
folder2md --help
```

#### Arch Linux

```bash
# Install Python and pipx
sudo pacman -S python-pip python-pipx

# Install folder2md4llms
pipx install folder2md4llms

# Verify installation
folder2md --help
```

### macOS

```bash
# Install pipx
brew install pipx

# Install folder2md4llms
pipx install folder2md4llms

# Verify installation
folder2md --help
```

**Alternative (using system Python):**
```bash
# Install pipx using pip
pip3 install pipx

# Add pipx to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"

# Install folder2md4llms
pipx install folder2md4llms
```

### Windows

#### Windows WSL2 (Recommended)

```bash
# Install WSL2 (PowerShell as Administrator)
wsl --install -d Ubuntu-22.04

# In Ubuntu WSL:
sudo apt update
sudo apt install python3-pip pipx

# Install folder2md4llms
pipx install folder2md4llms

# Verify installation
folder2md --help
```

---

## 🚨 Troubleshooting

### Command not found after installation

**Issue**: `folder2md: command not found`

**Solutions**:
1. **Check if pipx bin directory is in PATH**:
   ```bash
   # Linux/macOS
   echo $PATH | grep -o $HOME/.local/bin

   # Windows
   echo $env:PATH | Select-String "$env:USERPROFILE\.local\bin"
   ```

2. **Add pipx bin directory to PATH**:
   ```bash
   # Linux/macOS (add to ~/.bashrc or ~/.zshrc)
   export PATH="$HOME/.local/bin:$PATH"

   # Windows (add to user environment variables)
   # Add %USERPROFILE%\.local\bin to your PATH
   ```

3. **Use full path temporarily**:
   ```bash
   # Linux/macOS
   ~/.local/bin/folder2md --help

   # Windows
   %USERPROFILE%\.local\bin\folder2md.exe --help
   ```

### pipx installation fails

**Issue**: `pipx install` command fails

**Solutions**:
1. **Update pipx**:
   ```bash
   pip install --upgrade pipx
   ```

2. **Reinstall pipx**:
   ```bash
   pip uninstall pipx
   pip install pipx
   ```

3. **Use pip instead**:
   ```bash
   pip install --user folder2md4llms
   ```

### Permission denied on Linux/macOS

**Issue**: Permission errors during installation

**Solutions**:
1. **Use --user flag**:
   ```bash
   pip install --user folder2md4llms
   ```

2. **Fix permissions**:
   ```bash
   # Make sure ~/.local/bin exists and is writable
   mkdir -p ~/.local/bin
   chmod 755 ~/.local/bin
   ```

### Python version compatibility

**Issue**: Incompatible Python version

**Requirements**: Python 3.11 or higher

**Solutions**:
1. **Check Python version**:
   ```bash
   python --version
   python3 --version
   ```

2. **Install compatible Python**:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3.11

   # macOS: Download from python.org or use system package manager

   # Windows: Download from python.org
   ```

---

## 🔗 Alternative Installation Methods

### From Source (Development)

```bash
# Clone repository
git clone https://github.com/henriqueslab/folder2md4llms.git
cd folder2md4llms

# Install in development mode
pip install -e .

# Verify installation
folder2md --help
```


---

## 🆘 Getting Help

If you're still having issues:

1. **Check our troubleshooting guide**: See main [README.md](../README.md#-troubleshooting)
2. **Search existing issues**: [GitHub Issues](https://github.com/henriqueslab/folder2md4llms/issues)
3. **Ask for help**: [GitHub Discussions](https://github.com/henriqueslab/folder2md4llms/discussions)
4. **Report a bug**: [New Issue](https://github.com/henriqueslab/folder2md4llms/issues/new)

When reporting issues, please include:
- Your operating system and version
- Python version (`python --version`)
- Installation method attempted
- Complete error message

---

*This installation guide is designed to get folder2md4llms running on any system. For most users, `pipx install folder2md4llms` is the simplest and most reliable method.*
