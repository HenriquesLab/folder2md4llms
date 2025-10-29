"""
Homebrew update checker for folder2md4llms.

Checks if a newer version is available via Homebrew.

Note: Before upgrading with Homebrew, always run 'brew update' first to fetch
the latest formulae. The install_detector module includes this in upgrade commands.
"""

import re
import subprocess  # nosec B404
from urllib.request import Request, urlopen

# Homebrew formula information
HOMEBREW_TAP = "HenriquesLab/homebrew-folder2md4llms"
FORMULA_NAME = "folder2md4llms"
FORMULA_URL = "https://raw.githubusercontent.com/HenriquesLab/homebrew-folder2md4llms/main/Formula/folder2md4llms.rb"


def check_brew_outdated(
    package: str = FORMULA_NAME, timeout: int = 5
) -> tuple[str, str] | None:
    """
    Check if package is outdated using `brew outdated` command.

    Args:
        package: Package name to check
        timeout: Command timeout in seconds

    Returns:
        Tuple of (current_version, latest_version) if outdated, None otherwise
        Returns None if brew is not installed or command fails
    """
    try:
        # Run: brew outdated --verbose <package>
        # Output format: "folder2md4llms (0.2.1) < 0.2.2"
        result = subprocess.run(  # nosec B603, B607
            ["brew", "outdated", "--verbose", package],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            # Package is up to date or not installed
            return None

        # Parse output: "folder2md4llms (0.2.1) < 0.2.2"
        output = result.stdout.strip()
        match = re.search(r"\(([\d.]+)\)\s*<\s*([\d.]+)", output)
        if match:
            current_version = match.group(1)
            latest_version = match.group(2)
            return (current_version, latest_version)

        return None

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # brew not installed or command failed
        return None


def check_formula_github(
    formula_url: str = FORMULA_URL, timeout: int = 5
) -> str | None:
    """
    Check the latest version from the GitHub formula file.

    Args:
        formula_url: URL to the formula Ruby file
        timeout: Request timeout in seconds

    Returns:
        Latest version string if found, None otherwise
    """
    try:
        req = Request(formula_url, headers={"User-Agent": "folder2md4llms"})
        with urlopen(req, timeout=timeout) as response:  # nosec B310
            if response.status != 200:
                return None

            content = response.read().decode("utf-8")

            # Parse version from formula
            # Look for: version "0.2.2"
            version_match = re.search(r'version\s+"([\d.]+)"', content)
            if version_match:
                return version_match.group(1)

            # Alternative: parse from url line
            # url "https://files.pythonhosted.org/.../folder2md4llms-0.2.2.tar.gz"
            url_match = re.search(
                r'url\s+"[^"]*folder2md4llms[/-]([\d.]+)\.tar\.gz"', content
            )
            if url_match:
                return url_match.group(1)

            return None

    except Exception:
        return None


def check_homebrew_update(current_version: str) -> tuple[bool, str] | None:
    """
    Check if a Homebrew update is available.

    Tries brew outdated command first, falls back to GitHub formula.

    Args:
        current_version: Current installed version

    Returns:
        Tuple of (has_update, latest_version) if check succeeds, None on failure
    """
    # Try brew outdated command first (most reliable)
    brew_result = check_brew_outdated()
    if brew_result is not None:
        _current, latest = brew_result
        has_update = latest != current_version
        return (has_update, latest)

    # Fall back to checking GitHub formula
    formula_version = check_formula_github()
    if formula_version is not None:
        has_update = formula_version != current_version
        return (has_update, formula_version)

    # Both methods failed
    return None
