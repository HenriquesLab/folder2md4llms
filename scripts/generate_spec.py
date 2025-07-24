#!/usr/bin/env python3
"""
Script to generate platform-specific PyInstaller spec files from the unified template.
This eliminates duplication and ensures consistency across all platforms.

Usage:
    python scripts/generate_spec.py --platform macos --arch x64 --output folder2md-macos-x64.spec
    python scripts/generate_spec.py --platform windows --arch x64 --output folder2md-windows-x64.spec
    python scripts/generate_spec.py --platform linux --arch x64 --output folder2md-linux-x64.spec
"""

import argparse
import sys
from pathlib import Path


def get_platform_config(platform: str, arch: str) -> dict[str, str]:
    """Get platform-specific configuration for the spec file."""

    # Determine binary name
    if platform == "macos":
        binary_name = f"folder2md-macos-{arch}"
    elif platform == "windows":
        binary_name = f"folder2md-windows-{arch}.exe"
    elif platform == "linux":
        binary_name = f"folder2md-linux-{arch}"
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    # Common entry point
    entry_point = 'str(project_root / "pyinstaller_entry.py")'

    # Source path configuration
    src_path = 'src_path = project_root / "src"'

    # Platform-specific hidden imports
    if platform == "windows":
        platform_imports = [
            "# Windows-specific imports",
            '"win32api",',
            '"win32con",',
        ]
    elif platform == "macos":
        platform_imports = [
            "# macOS-specific imports",
            '"Foundation",',
            '"AppKit",',
        ]
    elif platform == "linux":
        platform_imports = [
            "# Linux-specific imports",
            '"magic.libmagic",',
        ]
    else:
        platform_imports = []

    # Platform-specific excludes
    if platform == "windows":
        platform_excludes = [
            "# Windows-specific excludes",
            '"win32com",',
            '"pythoncom",',
        ]
    elif platform == "macos":
        platform_excludes = [
            "# macOS-specific excludes",
            '"AppKit",',  # Only if not using GUI features
        ]
    elif platform == "linux":
        platform_excludes = [
            "# Linux-specific excludes",
            '"gi",',  # GTK if not needed
            '"cairo",',  # Cairo if not needed
        ]
    else:
        platform_excludes = []

    # Platform-specific data files (empty list if no additional files)
    if platform == "windows":
        platform_datas = [
            "# Windows-specific data files",
            "# python-magic-bin should handle libmagic automatically",
        ]
    else:
        platform_datas = []

    return {
        "BINARY_NAME": binary_name,
        "ENTRY_POINT": entry_point,
        "SRC_PATH": src_path,
        "PLATFORM_HIDDENIMPORTS": ("\n        " + "\n        ".join(platform_imports))
        if platform_imports
        else "",
        "PLATFORM_EXCLUDES": ("\n        " + "\n        ".join(platform_excludes))
        if platform_excludes
        else "",
        "PLATFORM_DATAS": ("\n        " + "\n        ".join(platform_datas))
        if platform_datas
        else "",
        "PLATFORM_BINARIES": "",  # Always empty for auto-detection
    }


def generate_spec_file(
    template_path: Path, output_path: Path, platform: str, arch: str
) -> None:
    """Generate a platform-specific spec file from the template."""

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Read template content
    template_content = template_path.read_text(encoding="utf-8")

    # Get platform configuration
    config = get_platform_config(platform, arch)

    # Replace placeholders
    spec_content = template_content
    for placeholder, value in config.items():
        spec_content = spec_content.replace(f"{{{{{placeholder}}}}}", value)

    # Write output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(spec_content, encoding="utf-8")

    print(f"Generated {platform}-{arch} spec file: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate platform-specific PyInstaller spec files from template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --platform macos --arch x64 --output folder2md-macos-x64.spec
  %(prog)s --platform macos --arch arm64 --output folder2md-macos-arm64.spec
  %(prog)s --platform windows --arch x64 --output folder2md-windows-x64.spec
  %(prog)s --platform linux --arch x64 --output folder2md-linux-x64.spec
        """,
    )

    parser.add_argument(
        "--platform",
        choices=["macos", "windows", "linux"],
        required=True,
        help="Target platform",
    )

    parser.add_argument(
        "--arch", choices=["x64", "arm64"], required=True, help="Target architecture"
    )

    parser.add_argument(
        "--output", type=Path, required=True, help="Output spec file path"
    )

    parser.add_argument(
        "--template",
        type=Path,
        default=Path("folder2md.spec.template"),
        help="Template spec file path (default: folder2md.spec.template)",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated spec file by importing it",
    )

    args = parser.parse_args()

    try:
        # Generate spec file
        generate_spec_file(args.template, args.output, args.platform, args.arch)

        # Validate if requested
        if args.validate:
            try:
                # Try to compile the spec file to check for syntax errors
                with open(args.output) as f:
                    compile(f.read(), str(args.output), "exec")
                print(f"Spec file validation passed: {args.output}")
            except SyntaxError as e:
                print(f"Spec file validation failed: {e}")
                sys.exit(1)

        print(f"Successfully generated spec file for {args.platform}-{args.arch}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
