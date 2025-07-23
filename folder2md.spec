# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for folder2md4llms
Generates standalone binaries for macOS distribution via Homebrew
"""

import sys
from pathlib import Path

# Define the project root and source paths
project_root = Path(SPECPATH)
src_path = project_root / "src"

# Analysis configuration
a = Analysis(
    # Entry point script - use the existing pyinstaller_entry.py
    [str(project_root / "pyinstaller_entry.py")],

    # Additional paths for module discovery
    pathex=[str(src_path)],

    # Binary dependencies (will be auto-detected for most cases)
    binaries=[],

    # Data files to include
    datas=[
        # Include all package data
        (str(src_path / "folder2md4llms"), "folder2md4llms"),
    ],

    # Hidden imports that PyInstaller might miss
    hiddenimports=[
        # Core dependencies
        "folder2md4llms",
        "folder2md4llms.cli",
        "folder2md4llms.processor",
        "folder2md4llms.converters",
        "folder2md4llms.analyzers",
        "folder2md4llms.engine",
        "folder2md4llms.formatters",
        "folder2md4llms.utils",

        # External dependencies that might be missed
        "tiktoken_ext.openai_public",
        "tiktoken_ext",
        "pypdf",
        "pypdf._reader",
        "pypdf._writer",
        "docx",
        "docx.shared",
        "openpyxl",
        "openpyxl.workbook",
        "PIL",
        "PIL.Image",
        "magic",
        "yaml",
        "rich",
        "rich.console",
        "rich.progress",
        "rich.table",
        "rich.text",
        "rich.panel",
        "click",
        "click.core",
        "markdown",
        "pygments",
        "pygments.lexers",
        "pygments.formatters",
        "nbconvert",
        "nbconvert.exporters",
        "striprtf",
        "striprtf.striprtf",
        "pptx",
        "psutil",
        "httpx",
        "pyperclip",

        # Platform-specific magic imports
        "magic.libmagic" if sys.platform != "win32" else "magic",
    ],

    # Hook directories
    hookspath=[],

    # Hook configuration
    hooksconfig={},

    # Runtime hooks
    runtime_hooks=[],

    # Modules to exclude
    excludes=[
        # Exclude test modules
        "tests",
        "test",
        "pytest",

        # Exclude development tools
        "mypy",
        "ruff",
        "black",
        "isort",

        # Exclude unnecessary GUI libraries
        "tkinter",
        "PySide2",
        "PySide6",
        "PyQt5",
        "PyQt6",

        # Exclude large optional dependencies if not needed
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "jupyter",
    ],

    # Don't create a zip archive
    noarchive=False,

    # Optimization level
    optimize=0,
)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],

    # Output binary name
    name="folder2md",

    # Debug options
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,

    # Compression
    upx=True,
    upx_exclude=[],

    # Runtime options
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,

    # macOS specific options - use current architecture to avoid fat binary issues
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # Bundle options
    onefile=True,
)

# macOS App bundle (optional, for future GUI versions)
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="folder2md.app",
        icon=None,
        bundle_identifier="org.henriqueslab.folder2md4llms",
        version="0.4.37",
        info_plist={
            "CFBundleName": "folder2md4llms",
            "CFBundleDisplayName": "Folder to Markdown for LLMs",
            "CFBundleVersion": "0.4.37",
            "CFBundleShortVersionString": "0.4.37",
            "CFBundleIdentifier": "org.henriqueslab.folder2md4llms",
            "NSHighResolutionCapable": True,
            "LSBackgroundOnly": False,
        },
    )
