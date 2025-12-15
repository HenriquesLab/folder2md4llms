"""Parse and extract information from CHANGELOG.md.

This module provides functionality to fetch, parse, and format changelog entries
for display in the changelog command.
"""

import re
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass
class ChangelogEntry:
    """Represents a complete changelog entry for a specific version."""

    version: str  # e.g., "0.5.13"
    date: str | None  # e.g., "2025-01-15"
    sections: dict[str, list[str]]  # Section title -> list of changes
    raw_content: str  # Original markdown content


# Regular expressions for parsing
VERSION_HEADER_PATTERN = re.compile(
    r"^## \[v?([\d.]+)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?", re.MULTILINE
)
SECTION_HEADER_PATTERN = re.compile(
    r"^### (Added|Changed|Fixed|Removed|Documentation|Deprecated|Security)",
    re.MULTILINE,
)
BREAKING_PATTERNS = [
    re.compile(r"\*\*BREAKING", re.IGNORECASE),
    re.compile(r"breaking change", re.IGNORECASE),
    re.compile(r"⚠️", re.MULTILINE),
    re.compile(r"### Migration", re.MULTILINE),
]

# Default changelog URL
DEFAULT_CHANGELOG_URL = (
    "https://raw.githubusercontent.com/henriqueslab/folder2md4llms/main/CHANGELOG.md"
)


def fetch_changelog(url: str = DEFAULT_CHANGELOG_URL, timeout: int = 5) -> str:
    """Fetch CHANGELOG.md content from URL.

    Args:
        url: URL to fetch changelog from
        timeout: Request timeout in seconds

    Returns:
        Raw changelog content as string

    Raises:
        URLError: If network request fails
        HTTPError: If HTTP request returns error status
    """
    req = Request(url, headers={"User-Agent": "folder2md4llms-changelog"})
    with urlopen(req, timeout=timeout) as response:  # nosec
        content: str = response.read().decode("utf-8")
        return content


def parse_version_entry(content: str, version: str) -> ChangelogEntry | None:
    """Parse a specific version's changelog entry.

    Args:
        content: Full CHANGELOG.md content
        version: Version to extract (e.g., "0.5.13" or "v0.5.13")

    Returns:
        ChangelogEntry if found, None otherwise
    """
    # Normalize version (remove 'v' prefix if present)
    version = version.lstrip("v")

    # Find all version headers
    version_matches = list(VERSION_HEADER_PATTERN.finditer(content))

    # Find the target version
    target_match = None
    next_match = None

    for i, match in enumerate(version_matches):
        if match.group(1) == version:
            target_match = match
            if i + 1 < len(version_matches):
                next_match = version_matches[i + 1]
            break

    if not target_match:
        return None

    # Extract content between this version and the next
    start_pos = target_match.end()
    end_pos = next_match.start() if next_match else len(content)
    entry_content = content[start_pos:end_pos].strip()

    # Parse sections
    sections: dict[str, list[str]] = {}
    section_matches = list(SECTION_HEADER_PATTERN.finditer(entry_content))

    for i, section_match in enumerate(section_matches):
        section_name = section_match.group(1)
        section_start = section_match.end()
        section_end = (
            section_matches[i + 1].start()
            if i + 1 < len(section_matches)
            else len(entry_content)
        )

        section_content = entry_content[section_start:section_end].strip()

        # Extract list items
        items = []
        for line in section_content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                items.append(line[2:].strip())
            elif line and items:
                # Continuation of previous item
                items[-1] += " " + line

        sections[section_name] = items

    return ChangelogEntry(
        version=version,
        date=target_match.group(2),
        sections=sections,
        raw_content=entry_content,
    )


def extract_highlights(entry: ChangelogEntry, limit: int = 10) -> list[tuple[str, str]]:
    """Extract highlights from changelog entry.

    Args:
        entry: ChangelogEntry to extract from
        limit: Maximum number of highlights

    Returns:
        List of (emoji, description) tuples
    """
    highlights: list[tuple[str, str]] = []

    # Section emoji mapping
    emojis = {
        "Added": "✨",
        "Changed": "🔄",
        "Fixed": "🐛",
        "Removed": "🗑️",
        "Documentation": "📚",
        "Deprecated": "⚠️",
        "Security": "🔒",
    }

    for section_name in [
        "Added",
        "Changed",
        "Fixed",
        "Security",
        "Removed",
        "Documentation",
        "Deprecated",
    ]:
        items = entry.sections.get(section_name, [])
        emoji = emojis.get(section_name, "•")

        for item in items:
            if len(highlights) >= limit:
                break
            highlights.append((emoji, item))

        if len(highlights) >= limit:
            break

    return highlights


def detect_breaking_changes(entry: ChangelogEntry) -> list[str]:
    """Detect breaking changes in changelog entry.

    Args:
        entry: ChangelogEntry to check

    Returns:
        List of breaking change descriptions
    """
    breaking = []

    for pattern in BREAKING_PATTERNS:
        if pattern.search(entry.raw_content):
            # Extract breaking change items
            for section_items in entry.sections.values():
                for item in section_items:
                    if any(p.search(item) for p in BREAKING_PATTERNS):
                        # Clean up the item
                        clean_item = item.replace("**BREAKING**:", "").strip()
                        breaking.append(clean_item)

    return breaking


def format_summary(
    entries: list[ChangelogEntry],
    show_breaking: bool = True,
    highlights_per_version: int = 3,
) -> str:
    """Format multiple changelog entries as a summary.

    Args:
        entries: List of ChangelogEntry objects
        show_breaking: Whether to show breaking changes
        highlights_per_version: Number of highlights per version

    Returns:
        Formatted summary string
    """
    lines = []

    for entry in entries:
        # Version header
        if entry.date:
            lines.append(
                f"[bold cyan]v{entry.version}[/bold cyan] [dim]({entry.date})[/dim]"
            )
        else:
            lines.append(f"[bold cyan]v{entry.version}[/bold cyan]")

        # Breaking changes
        if show_breaking:
            breaking = detect_breaking_changes(entry)
            if breaking:
                lines.append("[bold red]⚠️  BREAKING CHANGES:[/bold red]")
                for change in breaking:
                    lines.append(f"  • {change}")

        # Highlights
        highlights = extract_highlights(entry, limit=highlights_per_version)
        if highlights:
            for emoji, description in highlights:
                lines.append(f"  {emoji} {description}")

        lines.append("")  # Blank line between versions

    return "\n".join(lines)
