"""Main repository processor for folder2md4llms."""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from rich.progress import Progress, TaskID

from .analyzers.binary_analyzer import BinaryAnalyzer
from .converters.converter_factory import ConverterFactory
from .formatters.markdown import MarkdownFormatter
from .utils.config import Config
from .utils.file_utils import (
    get_language_from_extension,
    is_text_file,
    should_convert_file,
)
from .utils.ignore_patterns import IgnorePatterns
from .utils.ignore_suggestions import IgnoreSuggester
from .utils.streaming_processor import (
    MemoryMonitor,
    StreamingFileProcessor,
    optimize_file_processing_order,
)
from .utils.tree_generator import TreeGenerator

logger = logging.getLogger(__name__)


class RepositoryProcessor:
    """Main processor for converting repositories to markdown."""

    def __init__(self, config: Config):
        self.config = config

        # Initialize components (ignore_patterns will be loaded in process method)
        self.ignore_patterns = None
        self.tree_generator = None
        self.converter_factory = ConverterFactory(config.__dict__)
        self.binary_analyzer = BinaryAnalyzer(config.__dict__)
        self.markdown_formatter = MarkdownFormatter(
            include_tree=config.include_tree,
            include_stats=config.include_stats,
            include_preamble=getattr(config, "include_preamble", True),
        )

        # Initialize streaming processor
        self.streaming_processor = StreamingFileProcessor(
            max_file_size=getattr(config, "max_file_size", 10 * 1024 * 1024),
            max_tokens_per_chunk=getattr(config, "max_tokens_per_chunk", 8000),
            max_workers=getattr(config, "max_workers", 4),
            token_estimation_method=getattr(
                config, "token_estimation_method", "average"
            ),
        )

        # Initialize memory monitor
        self.memory_monitor = MemoryMonitor(
            max_memory_mb=getattr(config, "max_memory_mb", 1024)
        )

        # Initialize ignore suggester (will be updated with ignore patterns in process method)
        self.ignore_suggester = None

    def _load_ignore_patterns(self, repo_path: Path) -> IgnorePatterns:
        """Load ignore patterns from hierarchical files or use defaults."""
        # If custom ignore file is specified, use it exclusively
        if self.config.ignore_file and self.config.ignore_file.exists():
            return IgnorePatterns.from_file(self.config.ignore_file)

        # Use hierarchical loading for better pattern management
        ignore_patterns = IgnorePatterns.from_hierarchical_files(repo_path)

        # If no .folder2md_ignore files found, check if gitignore integration is enabled
        if not ignore_patterns.loaded_files and getattr(
            self.config, "use_gitignore", True
        ):
            # Look for .gitignore files in the repository
            gitignore_file = repo_path / ".gitignore"
            if gitignore_file.exists():
                return IgnorePatterns.from_gitignore(
                    gitignore_file, include_defaults=True
                )

        return ignore_patterns

    def process(self, repo_path: Path, progress: Progress | None = None) -> str:
        """Process a repository and return markdown output."""
        if not repo_path.exists() or not repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {repo_path}")

        # Load ignore patterns and initialize tree generator
        self.ignore_patterns = self._load_ignore_patterns(repo_path)
        self.tree_generator = TreeGenerator(self.ignore_patterns)

        # Initialize ignore suggester with loaded patterns
        self.ignore_suggester = IgnoreSuggester(
            min_file_size=getattr(self.config, "suggestion_min_file_size", 100_000),
            min_dir_size=getattr(self.config, "suggestion_min_dir_size", 1_000_000),
            ignore_patterns=self.ignore_patterns,
        )

        # Display loaded ignore files if verbose
        if self.config.verbose and self.ignore_patterns.loaded_files:
            from rich.console import Console

            console = Console()
            console.print()
            console.print("📁 [bold cyan]Using ignore files:[/bold cyan]")
            for file_info in self.ignore_patterns.loaded_files:
                console.print(f"  • {file_info}")
            console.print()

        # Initialize progress tracking
        if progress:
            scan_task = progress.add_task("Scanning files...", total=None)
            process_task = progress.add_task("Processing files...", total=None)
        else:
            scan_task = process_task = None

        try:
            # Scan repository
            file_list = self._scan_repository(repo_path, progress, scan_task)

            if progress:
                progress.update(scan_task, completed=True, total=len(file_list))
                progress.update(process_task, total=len(file_list))

            # Process files
            results = self._process_files(file_list, repo_path, progress, process_task)

            # Generate tree structure
            tree_structure = None
            if self.config.include_tree:
                tree_structure = self.tree_generator.generate_tree(repo_path)

            # Create processing stats for preamble
            processing_stats = {
                "file_count": len(file_list),
                "token_count": results["stats"].get("total_tokens", 0),
            }

            # Generate output
            output = self.markdown_formatter.format_repository(
                repo_path=repo_path,
                tree_structure=tree_structure,
                file_contents=results["text_files"],
                file_stats=results["stats"],
                binary_descriptions=results["binary_files"],
                converted_docs=results["converted_docs"],
                chunked_files=results["chunked_files"],
                processing_stats=processing_stats,
            )

            # Display ignore suggestions if enabled
            if self.config.verbose:
                output_file = Path(getattr(self.config, "output_file", "output.md"))
                self.ignore_suggester.display_suggestions(output_file)

            return output

        finally:
            if progress:
                progress.remove_task(scan_task)
                progress.remove_task(process_task)

    def _scan_repository(
        self, repo_path: Path, progress: Progress | None, task: TaskID | None
    ) -> list[Path]:
        """Scan repository and return list of files to process."""
        files = []

        def scan_directory(path: Path):
            try:
                for item in path.iterdir():
                    if self.ignore_patterns.should_ignore(item, repo_path):
                        continue

                    if item.is_file():
                        files.append(item)
                        # Analyze files that will be processed for suggestions
                        self.ignore_suggester.analyze_path(item, repo_path)
                        if progress and task:
                            progress.update(task, advance=1)
                    elif item.is_dir():
                        # Analyze directories for suggestions
                        self.ignore_suggester.analyze_path(item, repo_path)
                        scan_directory(item)

            except (OSError, PermissionError) as e:
                logger.warning(f"Error scanning directory {path}: {e}")
            except Exception as e:
                # Catch any other platform-specific errors
                logger.warning(f"Unexpected error scanning directory {path}: {e}")

        scan_directory(repo_path)
        return files

    def _process_files(
        self,
        file_list: list[Path],
        repo_path: Path,
        progress: Progress | None,
        task: TaskID | None,
    ) -> dict[str, Any]:
        """Process all files and categorize them using streaming and parallel processing."""
        results = {
            "text_files": {},
            "converted_docs": {},
            "binary_files": {},
            "chunked_files": {},
            "stats": defaultdict(int),
        }

        # Statistics
        stats = {
            "total_files": len(file_list),
            "text_files": 0,
            "binary_files": 0,
            "converted_docs": 0,
            "chunked_files": 0,
            "total_size": 0,
            "text_size": 0,
            "languages": defaultdict(int),
            "estimated_tokens": 0,
        }

        # Check memory usage before processing
        memory_mb, over_limit = self.memory_monitor.check_memory_usage()
        if over_limit:
            logger.warning(f"High memory usage detected: {memory_mb:.1f}MB")

        # Optimize file processing order
        optimized_files = optimize_file_processing_order(file_list)

        # Separate text files for streaming processing
        text_files = []
        other_files = []

        for file_path in optimized_files:
            if is_text_file(file_path):
                text_files.append(file_path)
            else:
                other_files.append(file_path)

        # Process text files with streaming processor
        if text_files:
            streaming_results = self.streaming_processor.process_files_parallel(
                text_files
            )

            for file_path_str, result in streaming_results.items():
                file_path = Path(file_path_str)
                rel_path = str(file_path.relative_to(repo_path))

                if result["status"] == "processed":
                    results["text_files"][rel_path] = result["content"]
                    stats["text_files"] += 1
                    stats["text_size"] += len(result["content"].encode("utf-8"))
                    stats["estimated_tokens"] += result.get("estimated_tokens", 0)

                    # Track language
                    language = get_language_from_extension(file_path.suffix.lower())
                    if language:
                        stats["languages"][language] += 1
                    else:
                        stats["languages"]["unknown"] += 1

                elif result["status"] == "chunked":
                    results["chunked_files"][rel_path] = result["chunks"]
                    stats["chunked_files"] += 1
                    stats["estimated_tokens"] += result.get("estimated_tokens", 0)

                    # Track language
                    language = get_language_from_extension(file_path.suffix.lower())
                    if language:
                        stats["languages"][language] += 1
                    else:
                        stats["languages"]["unknown"] += 1

        # Process non-text files with traditional approach
        for file_path in other_files:
            try:
                # Update progress
                if progress and task:
                    progress.update(task, advance=1)

                # Get relative path for output
                rel_path = str(file_path.relative_to(repo_path))

                # Get file stats
                try:
                    file_size = file_path.stat().st_size
                    stats["total_size"] += file_size

                    # Skip files that are too large
                    if file_size > self.config.max_file_size:
                        logger.info(
                            f"Skipping large file: {rel_path} ({file_size} bytes)"
                        )
                        continue

                except OSError:
                    continue

                # Process document files
                if should_convert_file(file_path) and self.config.convert_docs:
                    # Try to convert document
                    converted_content = self.converter_factory.convert_file(file_path)
                    if converted_content:
                        results["converted_docs"][rel_path] = converted_content
                        stats["converted_docs"] += 1

                elif self.config.describe_binaries:
                    # Analyze binary file
                    description = self.binary_analyzer.analyze_file(file_path)
                    if description:
                        results["binary_files"][rel_path] = description
                        stats["binary_files"] += 1

                # Check memory usage periodically
                if len(results["binary_files"]) % 50 == 0:
                    self.memory_monitor.check_memory_usage()

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue

        # Add streaming processor stats
        streaming_stats = self.streaming_processor.get_stats()
        stats.update(
            {
                "streaming_processed": streaming_stats["processed_files"],
                "streaming_chunked": streaming_stats["chunked_files"],
                "streaming_chunks": streaming_stats["total_chunks"],
                "streaming_skipped": streaming_stats["skipped_files"],
                "streaming_errors": streaming_stats["error_files"],
            }
        )

        results["stats"] = dict(stats)
        return results
