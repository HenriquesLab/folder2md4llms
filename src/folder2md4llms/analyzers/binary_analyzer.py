"""Binary file analyzer for describing non-text files."""

import logging
from pathlib import Path
from typing import Any

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import magic

    MAGIC_AVAILABLE = True
    # Test if magic is working properly
    try:
        magic.from_file(__file__)
    except Exception:
        MAGIC_AVAILABLE = False
except ImportError:
    MAGIC_AVAILABLE = False

from ..utils.file_utils import (
    get_file_category,
)
from ..utils.platform_utils import (
    is_windows,
)

logger = logging.getLogger(__name__)


class BinaryAnalyzer:
    """Analyzes and describes binary files."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.extract_image_metadata = self.config.get("image_extract_metadata", True)
        self.list_archive_contents = self.config.get("archive_list_contents", True)
        self.analyze_executables = self.config.get("executable_basic_info", True)

    def analyze_file(self, file_path: Path) -> str:
        """Analyze a binary file and return a description."""
        if not file_path.exists():
            return f"File not found: {file_path}"

        try:
            category = get_file_category(file_path)

            if category == "image":
                return self._analyze_image(file_path)
            elif category == "archive":
                return self._analyze_archive(file_path)
            elif category == "executable":
                return self._analyze_executable(file_path)
            else:
                return self._analyze_generic_binary(file_path)

        except Exception as e:
            logger.error(f"Error analyzing binary file {file_path}: {e}")
            return f"Error analyzing file: {str(e)}"

    def _analyze_image(self, file_path: Path) -> str:
        """Analyze an image file."""
        parts = [f"**Image File**: {file_path.name}"]

        # Basic file info
        try:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            parts.append(f"**Size**: {size_mb:.2f} MB")
        except OSError:
            pass

        # Image-specific info
        if PIL_AVAILABLE and self.extract_image_metadata:
            try:
                with Image.open(file_path) as img:
                    parts.append(f"**Dimensions**: {img.width}x{img.height} pixels")
                    parts.append(f"**Format**: {img.format}")
                    parts.append(f"**Mode**: {img.mode}")

                    # EXIF data for JPEG images
                    if hasattr(img, "_getexif") and img._getexif():
                        exif = img._getexif()
                        if exif:
                            parts.append("**EXIF Data**:")
                            for key, value in exif.items():
                                if key in [306, 272, 271]:  # DateTime, Make, Model
                                    parts.append(f"  - {key}: {value}")

            except Exception as e:
                parts.append(f"**Error reading image**: {str(e)}")

        else:
            parts.append("*PIL not available for detailed image analysis*")

        return "\n".join(parts)

    def _analyze_archive(self, file_path: Path) -> str:
        """Analyze an archive file."""
        parts = [f"**Archive File**: {file_path.name}"]

        # Basic file info
        try:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            parts.append(f"**Size**: {size_mb:.2f} MB")
        except OSError:
            pass

        # Archive type
        ext = file_path.suffix.lower()
        archive_types = {
            ".zip": "ZIP Archive",
            ".rar": "RAR Archive",
            ".7z": "7-Zip Archive",
            ".tar": "TAR Archive",
            ".gz": "GZIP Archive",
            ".bz2": "BZIP2 Archive",
            ".xz": "XZ Archive",
            ".tgz": "TAR.GZ Archive",
            ".tbz2": "TAR.BZ2 Archive",
        }

        archive_type = archive_types.get(ext, "Unknown Archive")
        parts.append(f"**Type**: {archive_type}")

        # Try to list contents (basic implementation)
        if self.list_archive_contents:
            if ext == ".zip":
                contents = self._list_zip_contents(file_path)
                if contents:
                    parts.append("**Contents**:")
                    parts.extend(contents)

        return "\n".join(parts)

    def _list_zip_contents(self, file_path: Path) -> list:
        """List contents of a ZIP file."""
        try:
            import zipfile

            with zipfile.ZipFile(file_path, "r") as zip_file:
                contents = []
                for info in zip_file.infolist()[:20]:  # Limit to first 20 files
                    size_kb = info.file_size / 1024
                    contents.append(f"  - {info.filename} ({size_kb:.1f} KB)")

                if len(zip_file.infolist()) > 20:
                    contents.append(
                        f"  ... and {len(zip_file.infolist()) - 20} more files"
                    )

                return contents

        except Exception as e:
            return [f"  Error listing contents: {str(e)}"]

    def _analyze_executable(self, file_path: Path) -> str:
        """Analyze an executable file."""
        parts = [f"**Executable File**: {file_path.name}"]

        # Basic file info
        try:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            parts.append(f"**Size**: {size_mb:.2f} MB")

            # Check if file is executable (Unix-like systems only)
            if not is_windows():
                if stat.st_mode & 0o111:
                    parts.append("**Permissions**: Executable")
                else:
                    parts.append("**Permissions**: Not executable")
            else:
                # On Windows, check if it's a known executable extension
                if file_path.suffix.lower() in {".exe", ".bat", ".cmd", ".com", ".msi"}:
                    parts.append("**Permissions**: Executable")

        except OSError:
            pass

        # File type detection
        if MAGIC_AVAILABLE:
            try:
                file_type = magic.from_file(str(file_path))
                parts.append(f"**Type**: {file_type}")
            except Exception as e:
                logger.warning(f"Magic failed for {file_path}: {e}")
                parts.append(f"**Type**: {self._get_fallback_type(file_path)}")
        else:
            ext = file_path.suffix.lower()
            exe_types = {
                ".exe": "Windows Executable",
                ".dll": "Windows Dynamic Library",
                ".so": "Linux Shared Object",
                ".dylib": "macOS Dynamic Library",
                ".app": "macOS Application Bundle",
                ".deb": "Debian Package",
                ".rpm": "RPM Package",
                ".msi": "Windows Installer Package",
                ".dmg": "macOS Disk Image",
                ".pkg": "macOS Package",
            }
            parts.append(f"**Type**: {exe_types.get(ext, 'Unknown Executable')}")

        return "\n".join(parts)

    def _analyze_generic_binary(self, file_path: Path) -> str:
        """Analyze a generic binary file."""
        parts = [f"**Binary File**: {file_path.name}"]

        # Basic file info
        try:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            parts.append(f"**Size**: {size_mb:.2f} MB")
        except OSError:
            pass

        # File type detection
        if MAGIC_AVAILABLE:
            try:
                file_type = magic.from_file(str(file_path))
                parts.append(f"**Type**: {file_type}")
            except Exception as e:
                logger.warning(f"Magic failed for {file_path}: {e}")
                parts.append(f"**Type**: {self._get_fallback_type(file_path)}")
        else:
            parts.append(f"**Type**: {self._get_fallback_type(file_path)}")

        # Try to detect if it's a text file with unusual extension
        try:
            with open(file_path, "rb") as f:
                sample = f.read(1024)
                if b"\0" not in sample:
                    # Might be a text file
                    try:
                        sample.decode("utf-8")
                        parts.append("**Note**: File appears to contain text data")
                    except UnicodeDecodeError:
                        pass
        except OSError:
            pass

        return "\n".join(parts)

    def _get_fallback_type(self, file_path: Path) -> str:
        """Get file type without python-magic dependency."""
        ext = file_path.suffix.lower()

        # Common file type mappings
        type_mappings = {
            ".txt": "Plain text",
            ".log": "Log file",
            ".json": "JSON data",
            ".xml": "XML document",
            ".html": "HTML document",
            ".css": "CSS stylesheet",
            ".js": "JavaScript source",
            ".py": "Python source",
            ".java": "Java source",
            ".c": "C source",
            ".cpp": "C++ source",
            ".h": "C header",
            ".md": "Markdown document",
            ".pdf": "PDF document",
            ".doc": "Microsoft Word document",
            ".docx": "Microsoft Word document",
            ".xls": "Microsoft Excel spreadsheet",
            ".xlsx": "Microsoft Excel spreadsheet",
            ".ppt": "Microsoft PowerPoint presentation",
            ".pptx": "Microsoft PowerPoint presentation",
            ".zip": "ZIP archive",
            ".tar": "TAR archive",
            ".gz": "GZIP compressed data",
            ".jpg": "JPEG image",
            ".jpeg": "JPEG image",
            ".png": "PNG image",
            ".gif": "GIF image",
            ".bmp": "BMP image",
            ".svg": "SVG image",
            ".mp3": "MP3 audio",
            ".wav": "WAV audio",
            ".mp4": "MP4 video",
            ".avi": "AVI video",
            ".mov": "QuickTime video",
        }

        if ext in type_mappings:
            return type_mappings[ext]
        elif ext:
            return f"File with {ext} extension"
        else:
            return "Unknown file type"
