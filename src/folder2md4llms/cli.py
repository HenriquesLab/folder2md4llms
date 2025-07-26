"""Command-line interface for folder2md4llms."""

import sys
from pathlib import Path

import rich_click as click
from rich.console import Console

from .__version__ import __version__
from .processor import RepositoryProcessor
from .utils.config import Config
from .utils.logging_config import setup_logging
from .utils.update_checker import check_for_updates

# Configure rich-click for better help formatting
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.STYLE_METAVAR = "bold yellow"
click.rich_click.STYLE_OPTION = "bold green"
click.rich_click.STYLE_ARGUMENT = "bold blue"
click.rich_click.STYLE_COMMAND = "bold cyan"
click.rich_click.STYLE_SWITCH = "bold magenta"
click.rich_click.STYLE_HELPTEXT = "dim"
click.rich_click.STYLE_USAGE = "yellow"
click.rich_click.STYLE_USAGE_COMMAND = "bold"
click.rich_click.STYLE_HELP_HEADER = "bold blue"
click.rich_click.STYLE_FOOTER_TEXT = "dim"
click.rich_click.OPTION_GROUPS = {
    "folder2md4llms": [
        {
            "name": "Output Options",
            "options": ["-o", "--output", "--clipboard"],
        },
        {
            "name": "Processing Options",
            "options": ["--limit", "--condense", "-c", "--config"],
        },
        {
            "name": "Utility Options",
            "options": ["--init-ignore", "--disable-update-check", "-v", "--verbose"],
        },
        {
            "name": "Help & Version",
            "options": ["--help", "--version"],
        },
    ]
}

console = Console()


def _get_template_content() -> str:
    """Load the .folder2md_ignore template content from the package."""
    try:
        # Try to get template from package data
        import importlib.resources as resources

        try:
            # For Python 3.9+
            template_files = resources.files("folder2md4llms") / "templates"
            template_file = template_files / "folder2md_ignore.template"
            return template_file.read_text(encoding="utf-8")
        except AttributeError:
            # Fallback for older Python versions
            with resources.open_text(
                "folder2md4llms.templates", "folder2md_ignore.template"
            ) as f:
                return f.read()

    except (ImportError, FileNotFoundError):
        # Fallback: try to read from file system (development environment)
        try:
            template_path = (
                Path(__file__).parent / "templates" / "folder2md_ignore.template"
            )
            return template_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Last resort: return a minimal template
            return """# folder2md4llms ignore patterns
# Add your ignore patterns below (gitignore-style syntax)

# Common patterns
.git/
__pycache__/
*.pyc
node_modules/
.vscode/
.idea/
*.log
*.tmp

# Add your custom patterns here:
"""


def _generate_ignore_template(target_path: Path, force: bool = False) -> None:
    """Generate a .folder2md_ignore template file."""
    ignore_file = target_path / ".folder2md_ignore"

    if ignore_file.exists():
        console.print(
            f"[WARNING] .folder2md_ignore already exists at {ignore_file}",
            style="yellow",
        )
        if not force:
            # Handle non-interactive environment
            if not sys.stdin.isatty():
                console.print(
                    "[ERROR] File exists and --force not specified in non-interactive environment",
                    style="red",
                )
                return
            if not click.confirm("Overwrite existing file?"):
                console.print("[ERROR] Operation cancelled", style="red")
                return

    try:
        template_content = _get_template_content()
        ignore_file.write_text(template_content, encoding="utf-8")
        console.print(
            f"[SUCCESS] Generated .folder2md_ignore template at {ignore_file}",
            style="green",
        )
        console.print(
            "[NOTE] Edit the file to customize ignore patterns for your project",
            style="cyan",
        )
    except Exception as e:
        console.print(f"[ERROR] Error creating ignore template: {e}", style="red")
        sys.exit(1)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path. Defaults to 'output.md'.",
)
@click.option(
    "--limit",
    type=str,
    help="Set a size limit for the output. Automatically enables smart condensing. "
    "Examples: '80000t' for tokens, '200000c' for characters.",
)
@click.option(
    "--condense",
    is_flag=True,
    help="Enable code condensing for supported languages. Uses defaults from config.",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Custom configuration file path.",
)
@click.option(
    "--clipboard", is_flag=True, help="Copy the final output to the clipboard."
)
@click.option(
    "--init-ignore",
    is_flag=True,
    help="Generate a .folder2md_ignore template file in the target directory.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite existing files when using --init-ignore.",
)
@click.option(
    "--disable-update-check",
    is_flag=True,
    help="Disable the automatic check for new versions.",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging.")
@click.version_option(version=__version__, prog_name="folder2md4llms")
def main(
    path: Path,
    output: Path | None,
    limit: str | None,
    condense: bool,
    config: Path | None,
    clipboard: bool,
    init_ignore: bool,
    force: bool,
    disable_update_check: bool,
    verbose: bool,
) -> None:
    """
    **folder2md4llms** converts a folder's structure and file contents into a single
    Markdown file, optimized for consumption by Large Language Models (LLMs).

    **PATH**: The directory to process. Defaults to the current directory.

    ## Examples

    **Get help:**
    ```
    $ folder2md --help
    ```

    **Basic usage (process current directory):**
    ```
    $ folder2md
    ```

    **Process a specific directory and save to a custom file:**
    ```
    $ folder2md ./my-project -o my-project.md
    ```

    **Set a token limit to automatically condense files:**
    ```
    $ folder2md PATH --limit 80000t
    ```

    **Copy the output to the clipboard:**
    ```
    $ folder2md PATH --clipboard
    ```

    **Generate ignore template:**
    ```
    $ folder2md PATH --init-ignore
    ```
    """
    try:
        # Validate path argument
        try:
            path = path.resolve()
            if not path.exists():
                console.print(f"[ERROR] Path does not exist: {path}", style="red")
                sys.exit(1)
            if not path.is_dir():
                console.print(f"[ERROR] Path is not a directory: {path}", style="red")
                sys.exit(1)
        except (OSError, RuntimeError) as e:
            console.print(f"[ERROR] Invalid path: {e}", style="red")
            sys.exit(1)

        if init_ignore:
            _generate_ignore_template(path, force=force)
            return

        # Setup logging
        log_file = None
        if verbose:
            # Create a log file in the output directory
            log_dir = Path.cwd() / ".folder2md_logs"
            log_dir.mkdir(exist_ok=True)
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"folder2md_{timestamp}.log"

        setup_logging(verbose=verbose, log_file=log_file)

        config_obj = Config.load(config_path=config, repo_path=path)

        if not disable_update_check and getattr(
            config_obj, "update_check_enabled", True
        ):
            check_for_updates(
                enabled=True,
                force=False,
                show_notification=True,
                check_interval=getattr(
                    config_obj, "update_check_interval", 24 * 60 * 60
                ),
            )

        # --- Override config with CLI options ---
        if output:
            config_obj.output_file = output
        if verbose:
            config_obj.verbose = verbose
        if condense:
            config_obj.condense_code = True

        if limit:
            config_obj.smart_condensing = True

            # Validate limit format
            if not limit or len(limit) < 2:
                console.print(
                    "[ERROR] Invalid limit format. Use <number>t for tokens or <number>c for characters.",
                    style="red",
                )
                sys.exit(1)

            limit_val_str = limit[:-1]
            limit_unit = limit[-1].lower()

            if not limit_val_str.isdigit() or limit_unit not in ["t", "c"]:
                console.print(
                    "[ERROR] Invalid limit format. Use <number>t for tokens or <number>c for characters.",
                    style="red",
                )
                sys.exit(1)

            limit_value = int(limit_val_str)
            if limit_value <= 0:
                console.print("[ERROR] Limit must be a positive number.", style="red")
                sys.exit(1)

            # Add reasonable upper bounds
            if limit_unit == "t" and limit_value > 10000000:
                console.print(
                    "[ERROR] Token limit too large (maximum: 10,000,000).", style="red"
                )
                sys.exit(1)
            elif limit_unit == "c" and limit_value > 50000000:
                console.print(
                    "[ERROR] Character limit too large (maximum: 50,000,000).",
                    style="red",
                )
                sys.exit(1)

            if limit_unit == "t":
                config_obj.token_limit = limit_value
                if limit_value < 100:
                    console.print(
                        "[WARNING] Token limit is very small (< 100).", style="yellow"
                    )
            elif limit_unit == "c":
                config_obj.char_limit = limit_value
                if limit_value < 500:
                    console.print(
                        "[WARNING] Character limit is very small (< 500).",
                        style="yellow",
                    )

        # --- Initialize and run the processor ---
        processor = RepositoryProcessor(config_obj)
        result = processor.process(path)

        # --- Handle output ---
        output_file = Path(getattr(config_obj, "output_file", None) or "output.md")
        output_file.write_text(result, encoding="utf-8")

        console.print(
            f"[SUCCESS] Repository processed successfully: {output_file}", style="green"
        )

        if clipboard:
            try:
                import pyperclip

                pyperclip.copy(result)
                console.print("[SUCCESS] Output copied to clipboard.", style="green")
            except ImportError:
                console.print(
                    "[WARNING] 'pyperclip' is not installed. Cannot copy to clipboard.",
                    style="yellow",
                )

    except Exception as e:
        console.print(f"[ERROR] An unexpected error occurred: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
