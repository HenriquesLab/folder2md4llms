"""Command-line interface for folder2md4llms."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress

from .__about__ import __version__
from .processor import RepositoryProcessor
from .utils.config import Config

console = Console()


def _generate_ignore_template(target_path: Path) -> None:
    """Generate a .folder2md_ignore template file."""
    ignore_file = target_path / ".folder2md_ignore"

    if ignore_file.exists():
        console.print(
            f"⚠️  .folder2md_ignore already exists at {ignore_file}", style="yellow"
        )
        if not click.confirm("Overwrite existing file?"):
            console.print("❌ Operation cancelled", style="red")
            return

    template_content = """# folder2md4llms ignore patterns
# This file specifies patterns for files and directories to ignore
# during repository processing. Uses gitignore-style patterns.

# ============================================================================
# VERSION CONTROL
# ============================================================================
.git/
.svn/
.hg/
.bzr/
CVS/

# ============================================================================
# BUILD ARTIFACTS & DEPENDENCIES
# ============================================================================
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Python development tools
.mypy_cache/
.ruff_cache/
.tox/
.nox/
.black/
.isort.cfg
htmlcov/
.benchmarks/

# Virtual environments
venv/
env/
.venv/
.env/
virtualenv/

# UV package manager
uv.lock

# Testing & Coverage
.pytest_cache/
.coverage
.nyc_output/
htmlcov/
cov_html/
coverage_html/
.benchmarks/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache

# Java
*.class
*.war
*.ear
*.jar
target/

# C/C++
*.obj
*.o
*.a
*.lib
*.dll
*.exe

# Rust
target/
Cargo.lock

# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
go.sum

# .NET
bin/
obj/
*.dll
*.exe
*.pdb

# ============================================================================
# IDE & EDITOR FILES
# ============================================================================
.vscode/
.idea/
.claude/
.cursor/

# ============================================================================
# AI ASSISTANT FILES
# ============================================================================
.claude/
Claude.md
CLAUDE.md
claude.md

# ============================================================================
# BUILD & OUTPUT DIRECTORIES
# ============================================================================
build/
output/
outputs/
out/
results/
reports/

# ============================================================================
# CACHE DIRECTORIES
# ============================================================================
.cache/
cache/
.tmp/
tmp/
*.swp
*.swo
*~
.project
.classpath
.c9revisions/
*.sublime-project
*.sublime-workspace
.history/

# ============================================================================
# OS GENERATED FILES
# ============================================================================
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# ============================================================================
# LOGS & TEMPORARY FILES
# ============================================================================
*.log
*.tmp
*.temp
*.cache
*.pid
*.seed
*.pid.lock
.nyc_output
.grunt
.sass-cache
.node_repl_history

# ============================================================================
# DOCUMENTATION & MEDIA
# ============================================================================
# Large media files
*.mp4
*.avi
*.mov
*.wmv
*.flv
*.webm
*.mkv
*.m4v
*.3gp
*.3g2
*.rm
*.swf
*.vob

# Large images (keep smaller ones for analysis)
*.psd
*.ai
*.tiff
*.tif
*.bmp
*.ico
*.raw
*.cr2
*.nef
*.arw
*.dng
*.orf
*.sr2

# ============================================================================
# ARCHIVES & PACKAGES
# ============================================================================
*.zip
*.tar.gz
*.tgz
*.rar
*.7z
*.bz2
*.xz
*.Z
*.lz
*.lzma
*.cab
*.iso
*.dmg
*.pkg
*.deb
*.rpm
*.msi

# ============================================================================
# SECURITY & SECRETS
# ============================================================================
*.key
*.pem
*.p12
*.p7b
*.crt
*.der
*.cer
*.pfx
*.p7c
*.p7r
*.spc
.env
.env.*
*.secret
secrets/
.secrets/
.aws/
.ssh/

# ============================================================================
# DATABASES & DATA FILES
# ============================================================================
*.db
*.sqlite
*.sqlite3
*.db3
*.s3db
*.sl3
*.mdb
*.accdb

# ============================================================================
# CUSTOM PATTERNS
# ============================================================================
# Add your custom ignore patterns below:

# Example: Ignore specific directories
# my_private_dir/
# temp/
# cache/

# Example: Ignore specific file types
# *.backup
# *.old
# *.orig
"""

    try:
        ignore_file.write_text(template_content, encoding="utf-8")
        console.print(
            f"✅ Generated .folder2md_ignore template at {ignore_file}", style="green"
        )
        console.print(
            "📝 Edit the file to customize ignore patterns for your project",
            style="cyan",
        )
    except Exception as e:
        console.print(f"❌ Error creating ignore template: {e}", style="red")
        sys.exit(1)


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path (default: output.md)",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path",
)
@click.option(
    "--ignore-file",
    type=click.Path(exists=True, path_type=Path),
    help="Custom ignore file path (default: .folder2md_ignore)",
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "html", "plain"]),
    default="markdown",
    help="Output format",
)
@click.option(
    "--include-tree/--no-tree",
    default=True,
    help="Include folder structure tree",
)
@click.option(
    "--include-stats/--no-stats",
    default=True,
    help="Include file statistics",
)
@click.option(
    "--include-preamble/--no-preamble",
    default=True,
    help="Include explanatory preamble in output",
)
@click.option(
    "--convert-docs/--no-convert-docs",
    default=True,
    help="Convert documents (PDF, DOCX, etc.)",
)
@click.option(
    "--describe-binaries/--no-describe-binaries",
    default=True,
    help="Describe binary files",
)
@click.option(
    "--max-file-size",
    type=int,
    default=1024 * 1024,  # 1MB
    help="Maximum file size to process (bytes)",
)
@click.option(
    "--token-limit",
    type=int,
    help="Maximum tokens to include in output (for LLM workflows)",
)
@click.option(
    "--char-limit",
    type=int,
    help="Maximum characters to include in output (for LLM workflows)",
)
@click.option(
    "--max-tokens-per-chunk",
    type=int,
    default=8000,
    help="Maximum tokens per chunk for large files",
)
@click.option(
    "--token-estimation-method",
    type=click.Choice(["conservative", "average", "optimistic"]),
    default="average",
    help="Method for estimating token counts",
)
@click.option(
    "--max-workers",
    type=int,
    default=4,
    help="Maximum number of parallel workers",
)
@click.option(
    "--use-gitignore/--no-gitignore",
    default=True,
    help="Use .gitignore files for filtering",
)
@click.option(
    "--clipboard",
    is_flag=True,
    help="Copy output to clipboard",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "--init-ignore",
    is_flag=True,
    help="Generate .folder2md_ignore template file",
)
@click.version_option(version=__version__)
def main(
    path: Path,
    output: Optional[Path],
    config: Optional[Path],
    ignore_file: Optional[Path],
    format: str,
    include_tree: bool,
    include_stats: bool,
    include_preamble: bool,
    convert_docs: bool,
    describe_binaries: bool,
    max_file_size: int,
    token_limit: Optional[int],
    char_limit: Optional[int],
    max_tokens_per_chunk: int,
    token_estimation_method: str,
    max_workers: int,
    use_gitignore: bool,
    clipboard: bool,
    verbose: bool,
    init_ignore: bool,
) -> None:
    """Convert a folder structure to markdown format for LLM consumption.

    PATH: Directory to process (default: current directory)
    """
    try:
        # Handle init-ignore flag
        if init_ignore:
            _generate_ignore_template(path)
            return
        # Load configuration
        config_obj = Config.load(config_path=config, repo_path=path)

        # Override config with command line options
        if ignore_file:
            config_obj.ignore_file = ignore_file
        config_obj.output_format = format
        config_obj.include_tree = include_tree
        config_obj.include_stats = include_stats
        config_obj.include_preamble = include_preamble
        config_obj.convert_docs = convert_docs
        config_obj.describe_binaries = describe_binaries
        config_obj.max_file_size = max_file_size
        config_obj.verbose = verbose

        # Set streaming and token management options
        if token_limit:
            config_obj.token_limit = token_limit
        if char_limit:
            config_obj.char_limit = char_limit
        config_obj.max_tokens_per_chunk = max_tokens_per_chunk
        config_obj.token_estimation_method = token_estimation_method
        config_obj.max_workers = max_workers
        config_obj.use_gitignore = use_gitignore

        # Set output file
        if not output:
            output = Path("output.md")

        # Store output file in config for suggestions
        config_obj.output_file = output

        # Initialize processor
        processor = RepositoryProcessor(config_obj)

        # Process repository
        with Progress(console=console, disable=not verbose) as progress:
            result = processor.process(path, progress)

        # Write output
        output.write_text(result, encoding="utf-8")

        # Copy to clipboard if requested
        if clipboard:
            try:
                import pyperclip

                pyperclip.copy(result)
                console.print("✅ Output copied to clipboard", style="green")
            except ImportError:
                console.print(
                    "⚠️  pyperclip not available for clipboard support", style="yellow"
                )

        console.print(f"✅ Repository processed successfully: {output}", style="green")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
