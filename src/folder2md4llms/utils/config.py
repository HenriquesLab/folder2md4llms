"""Configuration management for folder2md4llms."""

from pathlib import Path

import yaml


class Config:
    """Configuration management for folder2md4llms."""

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
        self.docx_extract_images = False
        self.xlsx_max_sheets = 10
        self.rtf_max_size = 10 * 1024 * 1024  # 10MB
        self.notebook_max_cells = 200
        self.notebook_include_outputs = True
        self.notebook_include_metadata = False
        self.pptx_max_slides = 100
        self.pptx_include_notes = True
        self.pptx_include_slide_numbers = True

        # Binary file analysis settings
        self.image_extract_metadata = True
        self.archive_list_contents = True
        self.executable_basic_info = True

        # Output settings
        self.markdown_toc = True
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

            # Load configuration values
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)

        except (OSError, yaml.YAMLError):
            # If config file can't be loaded, use defaults
            pass

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
            "docx_extract_images": self.docx_extract_images,
            "xlsx_max_sheets": self.xlsx_max_sheets,
            "rtf_max_size": self.rtf_max_size,
            "notebook_max_cells": self.notebook_max_cells,
            "notebook_include_outputs": self.notebook_include_outputs,
            "notebook_include_metadata": self.notebook_include_metadata,
            "pptx_max_slides": self.pptx_max_slides,
            "pptx_include_notes": self.pptx_include_notes,
            "pptx_include_slide_numbers": self.pptx_include_slide_numbers,
            "image_extract_metadata": self.image_extract_metadata,
            "archive_list_contents": self.archive_list_contents,
            "executable_basic_info": self.executable_basic_info,
            "markdown_toc": self.markdown_toc,
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
docx_extract_images: false
xlsx_max_sheets: 10
rtf_max_size: 10485760  # 10MB
notebook_max_cells: 200
notebook_include_outputs: true
notebook_include_metadata: false
pptx_max_slides: 100
pptx_include_notes: true
pptx_include_slide_numbers: true

# Binary file analysis settings
image_extract_metadata: true
archive_list_contents: true
executable_basic_info: true

# Markdown output settings
markdown_toc: true
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
"""

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
        except OSError:
            pass
