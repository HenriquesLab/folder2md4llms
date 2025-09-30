"""Configuration management for folder2md4llms."""

from pathlib import Path
from typing import Any

import yaml


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""

    pass


class Config:
    """Configuration management for folder2md4llms."""

    # Configuration constraints
    CONSTRAINTS = {
        "token_limit": {"min": 100, "max": 10000000},
        "char_limit": {"min": 100, "max": 50000000},
        "max_file_size": {"min": 1024, "max": 1073741824},  # 1KB to 1GB
        "max_workers": {"min": 1, "max": 32},
        "max_memory_mb": {"min": 128, "max": 65536},
        "pdf_max_pages": {"min": 1, "max": 10000},
        "xlsx_max_sheets": {"min": 1, "max": 1000},
        "notebook_max_cells": {"min": 1, "max": 10000},
        "update_check_interval": {"min": 3600, "max": 2592000},  # 1 hour to 30 days
    }

    VALID_STRATEGIES = ["conservative", "balanced", "aggressive"]
    VALID_TOKEN_METHODS = ["tiktoken", "average", "conservative", "optimistic"]
    VALID_OUTPUT_FORMATS = ["markdown", "html", "plain"]

    def __init__(self):
        # Default configuration
        self.output_format = "markdown"
        self.include_tree = True
        self.include_stats = True
        self.convert_docs = True
        self.describe_binaries = True
        self.condense_python = False
        self.python_condense_mode = "signatures_with_docstrings"
        self.condense_code = False
        self.code_condense_mode = "signatures_with_docstrings"
        self.condense_languages = ["js", "ts", "java", "json", "yaml"]
        self.max_file_size = 1024 * 1024  # 1MB
        self.verbose = False
        self.ignore_file: Path | None = None

        # Document conversion settings
        self.pdf_max_pages = 50
        self.xlsx_max_sheets = 10
        self.notebook_max_cells = 200
        self.notebook_include_outputs = True

        # Output settings
        self.syntax_highlighting = True
        self.file_size_limit = 1024 * 1024  # 1MB
        self.output_file: Path | None = None

        # Performance settings
        self.max_workers = 4
        self.progress_bar = True

        # Streaming and token management
        self.token_estimation_method = "average"  # noqa: S105  # conservative, average, optimistic
        self.max_memory_mb = 1024  # Memory limit in MB
        self.token_limit = None  # Optional token limit for LLM workflows
        self.char_limit = None  # Optional character limit for LLM workflows
        self.default_token_limit = 100000  # Default token limit when none specified
        self.use_gitignore = True  # Use .gitignore files for filtering

        # Smart condensing settings
        self.smart_condensing = False  # Enable smart anti-truncation engine
        self.token_budget_strategy = "balanced"  # conservative, balanced, aggressive
        self.priority_analysis = True  # Enable content priority analysis
        self.progressive_condensing = True  # Enable progressive condensing
        self.critical_files = []  # Patterns for files that should never be condensed
        self.token_counting_method = (
            "tiktoken"  # tiktoken, average, conservative, optimistic
        )
        self.target_model = "gpt-4"  # Target model for tiktoken encoding

        # Update checking settings
        self.update_check_enabled = True  # Enable automatic update checking
        self.update_check_interval = (
            24 * 60 * 60
        )  # Check interval in seconds (24 hours)

        # Output file detection settings
        self.auto_ignore_output = True  # Automatically detect and prompt to ignore existing folder2md output files

    @classmethod
    def load(
        cls, config_path: Path | None = None, repo_path: Path | None = None
    ) -> "Config":
        """Load configuration from file or create default."""
        config = cls()

        # Look for config file
        if config_path and config_path.exists():
            config._load_from_file(config_path)
        elif repo_path:
            # Look for config in repo directory
            config_file = repo_path / "folder2md.yaml"
            if config_file.exists():
                config._load_from_file(config_file)
            else:
                # Look for config in parent directories
                parent = repo_path.parent
                while parent != parent.parent:
                    config_file = parent / "folder2md.yaml"
                    if config_file.exists():
                        config._load_from_file(config_file)
                        break
                    parent = parent.parent

        return config

    def _load_from_file(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                return

            # Validate configuration before applying
            self._validate_config(data)

            # Load configuration values
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)

        except ConfigValidationError:
            raise  # Re-raise validation errors
        except (OSError, yaml.YAMLError):
            # If config file can't be loaded, use defaults
            pass

    def _validate_config(self, config_dict: dict[str, Any]) -> None:
        """Validate configuration values.

        Args:
            config_dict: Configuration dictionary to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        for key, value in config_dict.items():
            # Check numeric constraints
            if key in self.CONSTRAINTS and isinstance(value, int | float):
                constraints = self.CONSTRAINTS[key]
                if value < constraints["min"] or value > constraints["max"]:
                    raise ConfigValidationError(
                        f"{key} must be between {constraints['min']} and {constraints['max']}, got {value}"
                    )

            # Check string enums
            elif key == "token_budget_strategy" and value not in self.VALID_STRATEGIES:
                raise ConfigValidationError(
                    f"token_budget_strategy must be one of {self.VALID_STRATEGIES}, got '{value}'"
                )
            elif (
                key == "token_counting_method" and value not in self.VALID_TOKEN_METHODS
            ):
                raise ConfigValidationError(
                    f"token_counting_method must be one of {self.VALID_TOKEN_METHODS}, got '{value}'"
                )
            elif key == "output_format" and value not in self.VALID_OUTPUT_FORMATS:
                raise ConfigValidationError(
                    f"output_format must be one of {self.VALID_OUTPUT_FORMATS}, got '{value}'"
                )

            # Check boolean values
            elif key in [
                "include_tree",
                "include_stats",
                "convert_docs",
                "describe_binaries",
                "condense_python",
                "condense_code",
                "verbose",
                "smart_condensing",
                "priority_analysis",
                "progressive_condensing",
                "update_check_enabled",
                "notebook_include_outputs",
                "syntax_highlighting",
                "auto_ignore_output",
            ]:
                if not isinstance(value, bool):
                    raise ConfigValidationError(
                        f"{key} must be a boolean value, got {type(value).__name__}"
                    )

            # Check list values
            elif key in ["condense_languages", "critical_files"]:
                if not isinstance(value, list):
                    raise ConfigValidationError(
                        f"{key} must be a list, got {type(value).__name__}"
                    )

            # Check path values
            elif key in ["ignore_file", "output_file"] and value is not None:
                if not isinstance(value, str | Path):
                    raise ConfigValidationError(
                        f"{key} must be a string or Path, got {type(value).__name__}"
                    )

    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_dict = {
            "output_format": self.output_format,
            "include_tree": self.include_tree,
            "include_stats": self.include_stats,
            "convert_docs": self.convert_docs,
            "describe_binaries": self.describe_binaries,
            "condense_python": self.condense_python,
            "python_condense_mode": self.python_condense_mode,
            "condense_code": self.condense_code,
            "code_condense_mode": self.code_condense_mode,
            "condense_languages": self.condense_languages,
            "max_file_size": self.max_file_size,
            "verbose": self.verbose,
            "pdf_max_pages": self.pdf_max_pages,
            "xlsx_max_sheets": self.xlsx_max_sheets,
            "notebook_max_cells": self.notebook_max_cells,
            "notebook_include_outputs": self.notebook_include_outputs,
            "syntax_highlighting": self.syntax_highlighting,
            "file_size_limit": self.file_size_limit,
            "max_workers": self.max_workers,
            "progress_bar": self.progress_bar,
            "token_estimation_method": self.token_estimation_method,
            "max_memory_mb": self.max_memory_mb,
            "token_limit": self.token_limit,
            "char_limit": self.char_limit,
            "use_gitignore": self.use_gitignore,
            "smart_condensing": self.smart_condensing,
            "token_budget_strategy": self.token_budget_strategy,
            "priority_analysis": self.priority_analysis,
            "progressive_condensing": self.progressive_condensing,
            "critical_files": self.critical_files,
            "token_counting_method": self.token_counting_method,
            "target_model": self.target_model,
            "update_check_enabled": self.update_check_enabled,
            "update_check_interval": self.update_check_interval,
            "auto_ignore_output": self.auto_ignore_output,
        }

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=True)
        except OSError:
            pass

    def create_default_config(self, config_path: Path) -> None:
        """Create a default configuration file with comments."""
        config_content = """# folder2md4llms configuration file
# This file controls how your repository is processed

# Output format (markdown, html, plain)
output_format: markdown

# Include folder structure tree
include_tree: true

# Include repository statistics
include_stats: true

# Convert documents (PDF, DOCX, etc.)
convert_docs: true

# Describe binary files
describe_binaries: true

# Condense Python files to signatures and docstrings
condense_python: false

# Python condensing mode (signatures, signatures_with_docstrings, structure)
python_condense_mode: signatures_with_docstrings

# Condense code files (JS, TS, Java, etc.) to signatures
condense_code: false

# Code condensing mode (signatures, signatures_with_docstrings, structure)
code_condense_mode: signatures_with_docstrings

# Languages to condense (js, ts, java, json, yaml, or "all")
condense_languages: [js, ts, java, json, yaml]

# Maximum file size to process (bytes)
max_file_size: 1048576  # 1MB

# Document conversion settings
pdf_max_pages: 50
xlsx_max_sheets: 10
notebook_max_cells: 200
notebook_include_outputs: true

# Output settings
syntax_highlighting: true
file_size_limit: 1048576  # 1MB
# Performance settings
max_workers: 4
progress_bar: true

# Streaming and token management
token_estimation_method: average  # conservative, average, optimistic
max_memory_mb: 1024
token_limit: null  # Optional token limit for LLM workflows
char_limit: null   # Optional character limit for LLM workflows
use_gitignore: true  # Use .gitignore files for filtering

# Smart anti-truncation engine settings
smart_condensing: false  # Enable intelligent content processing
token_budget_strategy: balanced  # conservative, balanced, aggressive
priority_analysis: true  # Analyze content priority automatically
progressive_condensing: true  # Apply condensing based on available budget
critical_files: []  # Patterns for files that should never be condensed

# Token counting settings
token_counting_method: tiktoken  # tiktoken, average, conservative, optimistic
target_model: gpt-4  # Target model for tiktoken encoding

# Update checking settings
update_check_enabled: true  # Enable automatic update checking
update_check_interval: 86400  # Check interval in seconds (24 hours)

# Output file detection settings
auto_ignore_output: true  # Automatically detect and prompt to ignore existing folder2md output files
"""

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
        except OSError:
            pass
