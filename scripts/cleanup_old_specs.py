#!/usr/bin/env python3
"""
Cleanup script to remove old duplicate PyInstaller spec files after consolidation.
This should be run once after the consolidation is complete.
"""

from pathlib import Path


def main():
    """Remove old duplicate spec files."""
    project_root = Path(__file__).parent.parent

    # Old spec files to remove
    old_spec_files = [
        "folder2md.spec",  # Keep as documentation/reference, but it's superseded
        "folder2md-linux-x64.spec",  # Old Linux spec (will be regenerated)
        "folder2md-linux.spec.template",  # Old template (superseded by new template)
    ]

    print("Cleaning up old PyInstaller spec files...")

    removed_files = []
    for spec_file in old_spec_files:
        spec_path = project_root / spec_file
        if spec_path.exists():
            print(f"  Removing: {spec_file}")
            spec_path.unlink()
            removed_files.append(spec_file)
        else:
            print(f"  Not found: {spec_file}")

    if removed_files:
        print(f"\nRemoved {len(removed_files)} old spec files:")
        for file in removed_files:
            print(f"  - {file}")

        print("\nThe new consolidated system uses:")
        print("  - folder2md.spec.template (unified template)")
        print("  - scripts/generate_spec.py (spec generator)")
        print("  - Generated specs are created dynamically by CI/CD")

    else:
        print("\nNo old spec files found to remove")

    print("\nCleanup complete!")


if __name__ == "__main__":
    main()
