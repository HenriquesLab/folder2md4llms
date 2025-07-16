"""File utility functions."""

from pathlib import Path
from typing import Dict, Optional

# Language mapping for syntax highlighting
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".m": "matlab",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    ".html": "html",
    ".htm": "html",
    ".xml": "xml",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".sql": "sql",
    ".md": "markdown",
    ".rst": "rst",
    ".tex": "latex",
    ".dockerfile": "dockerfile",
    ".makefile": "makefile",
    ".mk": "makefile",
    ".gradle": "gradle",
    ".cmake": "cmake",
    ".vim": "vim",
    ".lua": "lua",
    ".pl": "perl",
    ".pm": "perl",
    ".clj": "clojure",
    ".cljs": "clojure",
    ".elm": "elm",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hrl": "erlang",
    ".hs": "haskell",
    ".lhs": "haskell",
    ".ml": "ocaml",
    ".mli": "ocaml",
    ".fs": "fsharp",
    ".fsi": "fsharp",
    ".fsx": "fsharp",
    ".dart": "dart",
    ".proto": "protobuf",
    ".thrift": "thrift",
    ".graphql": "graphql",
    ".gql": "graphql",
}


def get_language_from_extension(extension: str) -> Optional[str]:
    """Get the language identifier for syntax highlighting from file extension."""
    return LANGUAGE_EXTENSIONS.get(extension.lower())


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary by looking for null bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except (OSError, PermissionError, UnicodeError):
        return True
    except Exception:
        # Catch any other platform-specific errors
        return True


def is_text_file(file_path: Path) -> bool:
    """Check if a file is a text file."""
    return not is_binary_file(file_path)


def get_file_stats(file_path: Path) -> Dict:
    """Get statistics for a file."""
    try:
        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_binary": is_binary_file(file_path),
            "extension": file_path.suffix.lower(),
            "language": get_language_from_extension(file_path.suffix.lower()),
        }
    except OSError:
        return {
            "size": 0,
            "modified": 0,
            "created": 0,
            "is_binary": True,
            "extension": "",
            "language": None,
        }


def should_convert_file(file_path: Path) -> bool:
    """Check if a file should be converted to text."""
    convertible_extensions = {
        ".pdf",
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".pptx",
        ".ppt",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
        ".csv",
        ".tsv",
    }
    return file_path.suffix.lower() in convertible_extensions


def is_image_file(file_path: Path) -> bool:
    """Check if a file is an image."""
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",
        ".tiff",
        ".tif",
        ".ico",
        ".psd",
        ".raw",
        ".cr2",
        ".nef",
        ".arw",
        ".dng",
        ".orf",
        ".sr2",
        ".k25",
        ".kdc",
        ".dcr",
    }
    return file_path.suffix.lower() in image_extensions


def is_archive_file(file_path: Path) -> bool:
    """Check if a file is an archive."""
    archive_extensions = {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tar.gz",
        ".tar.bz2",
        ".tar.xz",
        ".tgz",
        ".tbz2",
    }
    return file_path.suffix.lower() in archive_extensions


def is_executable_file(file_path: Path) -> bool:
    """Check if a file is executable."""
    executable_extensions = {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".app",
        ".deb",
        ".rpm",
        ".msi",
        ".dmg",
        ".pkg",
        ".bin",
        ".run",
    }
    return file_path.suffix.lower() in executable_extensions


def get_file_category(file_path: Path) -> str:
    """Get the category of a file."""
    if is_text_file(file_path):
        return "text"
    elif should_convert_file(file_path):
        return "document"
    elif is_image_file(file_path):
        return "image"
    elif is_archive_file(file_path):
        return "archive"
    elif is_executable_file(file_path):
        return "executable"
    else:
        return "binary"


def read_file_safely(file_path: Path, max_size: int = 1024 * 1024) -> Optional[str]:
    """Read a file safely with size limit and encoding handling."""
    try:
        if file_path.stat().st_size > max_size:
            return None

        # Try different encodings
        encodings = ["utf-8", "utf-16", "latin-1", "ascii"]

        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except (OSError, PermissionError):
                break

        return None
    except (OSError, PermissionError):
        return None
    except Exception:
        # Catch any other platform-specific errors
        return None
