"""Main repository processor for folder2md4llms."""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from rich.progress import Progress, TaskID

from .analyzers.binary_analyzer import BinaryAnalyzer
from .converters.converter_factory import ConverterFactory
from .converters.smart_python_converter import SmartPythonConverter
from .engine.smart_engine import SmartAntiTruncationEngine
from .formatters.markdown import MarkdownFormatter
from .utils.config import Config
from .utils.file_strategy import ProcessingAction
from .utils.file_utils import (
    get_language_from_extension,
    is_data_file,
    is_text_file,
    should_condense_code_file,
    should_condense_python_file,
    should_convert_file,
)
from .utils.ignore_patterns import IgnorePatterns
from .utils.ignore_suggestions import IgnoreSuggester
from .utils.resource_manager import ResourceManager
from .utils.smart_budget_manager import BudgetStrategy
from .utils.streaming_processor import (
    MemoryMonitor,
    StreamingFileProcessor,
    optimize_file_processing_order,
)
from .utils.tree_generator import TreeGenerator

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for processing errors."""

    pass


class RepositoryProcessor:
    """Main processor for converting repositories to markdown."""

    config: Config
    smart_engine: SmartAntiTruncationEngine | None
    ignore_patterns: IgnorePatterns | None
    tree_generator: TreeGenerator | None
    converter_factory: ConverterFactory
    smart_python_converter: SmartPythonConverter | None
    binary_analyzer: BinaryAnalyzer
    markdown_formatter: MarkdownFormatter
    ignore_suggester: IgnoreSuggester | None

    def __init__(
        self, config: Config, additional_ignore_patterns: list[str] | None = None
    ):
        self.config = config
        self.additional_ignore_patterns = additional_ignore_patterns or []

        # Initialize smart engine if enabled
        self.smart_engine = None
        if getattr(config, "smart_condensing", False):
            # Determine token limit - use token_limit if available, otherwise convert char_limit
            token_limit = getattr(config, "token_limit", None)
            char_limit = getattr(config, "char_limit", None)

            if token_limit:
                total_token_limit = token_limit
            elif char_limit:
                # Convert char limit to approximate token limit (avg ~4 chars per token)
                total_token_limit = char_limit // 4
            else:
                # Use a reasonable default if no limit is specified
                total_token_limit = getattr(
                    config, "default_token_limit", 100000
                )  # ~25k words

            strategy_name = getattr(config, "token_budget_strategy", "balanced")
            try:
                strategy = getattr(BudgetStrategy, strategy_name.upper())
            except AttributeError:
                strategy = BudgetStrategy.BALANCED

            self.smart_engine = SmartAntiTruncationEngine(
                total_token_limit=total_token_limit,
                strategy=strategy,
                enable_priority_analysis=getattr(config, "priority_analysis", True),
                enable_progressive_condensing=getattr(
                    config, "progressive_condensing", True
                ),
                token_counting_method=getattr(
                    config, "token_counting_method", "tiktoken"
                ),
                target_model=getattr(config, "target_model", "gpt-4"),
            )

        # Initialize components (ignore_patterns will be loaded in process method)
        self.ignore_patterns = None
        self.tree_generator = None
        self.ignore_suggester = None
        self.converter_factory = ConverterFactory(config.__dict__)

        # Add smart Python converter if smart condensing is enabled
        if getattr(config, "smart_condensing", False):
            self.smart_python_converter = SmartPythonConverter(config.__dict__)
        else:
            self.smart_python_converter = None

        self.binary_analyzer = BinaryAnalyzer(config.__dict__)
        self.markdown_formatter = MarkdownFormatter(
            include_tree=config.include_tree,
            include_stats=config.include_stats,
            include_preamble=getattr(config, "include_preamble", True),
            token_limit=getattr(config, "token_limit", None),
            char_limit=getattr(config, "char_limit", None),
            token_estimation_method=getattr(
                config, "token_estimation_method", "average"
            ),
            smart_engine_active=self.smart_engine is not None,
        )

        # Initialize streaming processor
        self.streaming_processor = StreamingFileProcessor(
            max_file_size=getattr(config, "max_file_size", 10 * 1024 * 1024),
            max_workers=getattr(config, "max_workers", 4),
            token_estimation_method=getattr(
                config, "token_estimation_method", "average"
            ),
        )

        # Initialize memory monitor
        self.memory_monitor = MemoryMonitor(
            max_memory_mb=getattr(config, "max_memory_mb", 1024)
        )

        # Initialize resource manager
        self.resource_manager = ResourceManager(
            max_memory_mb=getattr(config, "max_memory_mb", 1024),
            max_file_handles=getattr(config, "max_file_handles", 1000),
        )

        # Initialize ignore suggester (will be updated with ignore patterns in process method)
        self.ignore_suggester = None

    def _load_ignore_patterns(self, repo_path: Path) -> IgnorePatterns:
        """Load ignore patterns from hierarchical files or use defaults."""
        # If custom ignore file is specified, use it exclusively
        if self.config.ignore_file and self.config.ignore_file.exists():
            ignore_patterns = IgnorePatterns.from_file(self.config.ignore_file)
        else:
            # Use hierarchical loading for better pattern management
            ignore_patterns = IgnorePatterns.from_hierarchical_files(repo_path)

            # If no .folder2md_ignore files found, check if gitignore integration is enabled
            if not ignore_patterns.loaded_files and getattr(
                self.config, "use_gitignore", True
            ):
                # Look for .gitignore files in the repository
                gitignore_file = repo_path / ".gitignore"
                if gitignore_file.exists():
                    ignore_patterns = IgnorePatterns.from_gitignore(
                        gitignore_file, include_defaults=True
                    )

        # Add any additional ignore patterns passed from CLI
        if self.additional_ignore_patterns:
            for pattern in self.additional_ignore_patterns:
                ignore_patterns.add_pattern(pattern)

        return ignore_patterns

    def process(self, repo_path: Path, progress: Progress | None = None) -> str:
        """Process a repository and return markdown output."""
        if not repo_path.exists() or not repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {repo_path}")

        # Resolve the path to handle symlinks and relative paths consistently
        repo_path = repo_path.resolve()

        # Load ignore patterns and initialize tree generator
        self.ignore_patterns = self._load_ignore_patterns(repo_path)
        if self.ignore_patterns is not None:
            self.tree_generator = TreeGenerator(self.ignore_patterns)

        # Initialize ignore suggester with loaded patterns
        if self.ignore_patterns is not None:
            self.ignore_suggester = IgnoreSuggester(
                min_file_size=getattr(self.config, "suggestion_min_file_size", 100_000),
                min_dir_size=getattr(self.config, "suggestion_min_dir_size", 1_000_000),
                ignore_patterns=self.ignore_patterns,
            )

        # Display loaded ignore files if verbose
        if (
            self.config.verbose
            and self.ignore_patterns
            and self.ignore_patterns.loaded_files
        ):
            from rich.console import Console

            console = Console()
            console.print()
            console.print("📁 [bold cyan]Using ignore files:[/bold cyan]")
            for file_info in self.ignore_patterns.loaded_files:
                console.print(f"  • {file_info}")
            console.print()

        # Initialize progress tracking
        scan_task: TaskID | None = None
        process_task: TaskID | None = None
        if progress:
            scan_task = progress.add_task("Scanning files...", total=None)
            process_task = progress.add_task("Processing files...", total=None)

        try:
            # Scan repository
            file_list = self._scan_repository(repo_path, progress, scan_task)

            if progress and scan_task is not None and process_task is not None:
                progress.update(scan_task, completed=True, total=len(file_list))
                progress.update(process_task, total=len(file_list))

            # Process files with smart engine if enabled
            if self.smart_engine:
                results = self._process_files_with_smart_engine(
                    file_list, repo_path, progress, process_task
                )
            else:
                results = self._process_files(
                    file_list, repo_path, progress, process_task
                )

            # Generate tree structure
            tree_structure = None
            if self.config.include_tree and self.tree_generator:
                tree_structure = self.tree_generator.generate_tree(repo_path)

            # Create processing stats for preamble
            processing_stats = {
                "file_count": len(file_list),
                "token_count": results["stats"].get("estimated_tokens", 0),
            }

            # Add smart condensing stats if smart engine was used
            if self.smart_engine and results["stats"].get("smart_engine_used", False):
                processing_stats.update(
                    {
                        "smart_engine_active": True,
                        "original_tokens": results["stats"].get(
                            "original_tokens_total", 0
                        ),
                        "condensed_tokens": results["stats"].get(
                            "condensed_tokens_total", 0
                        ),
                    }
                )

            # Generate output
            output = self.markdown_formatter.format_repository(
                repo_path=repo_path,
                tree_structure=tree_structure,
                file_contents=results["text_files"],
                file_stats=results["stats"],
                binary_descriptions=results["binary_files"],
                converted_docs=results["converted_docs"],
                processing_stats=processing_stats,
            )

            # Display ignore suggestions if enabled
            if self.config.verbose and self.ignore_suggester:
                output_file = Path(
                    getattr(self.config, "output_file", None) or "output.md"
                )
                self.ignore_suggester.display_suggestions(output_file)

            return output

        finally:
            if progress and scan_task is not None and process_task is not None:
                progress.remove_task(scan_task)
                progress.remove_task(process_task)

    def _scan_repository(
        self, repo_path: Path, progress: Progress | None, task: TaskID | None
    ) -> list[Path]:
        """Scan repository and return list of files to process."""
        files = []
        errors = []

        # Validate repo_path to prevent path traversal
        try:
            resolved_repo_path = repo_path.resolve()
            if not resolved_repo_path.exists():
                raise ProcessingError(f"Repository path does not exist: {repo_path}")
            if not resolved_repo_path.is_dir():
                raise ProcessingError(f"Path is not a directory: {repo_path}")
            # Use resolved path for processing
            repo_path = resolved_repo_path
        except (OSError, RuntimeError) as e:
            raise ProcessingError(f"Invalid repository path: {e}") from e

        def scan_directory(path: Path):
            try:
                # Ensure we're not escaping the repo root
                path.relative_to(repo_path)

                for item in path.iterdir():
                    # Additional safety check
                    try:
                        item.relative_to(repo_path)
                    except ValueError:
                        logger.warning(f"Skipping file outside repo: {item}")
                        continue

                    if self.ignore_patterns and self.ignore_patterns.should_ignore(
                        item, repo_path
                    ):
                        continue

                    if item.is_file():
                        files.append(item)
                        # Analyze files that will be processed for suggestions
                        if self.ignore_suggester:
                            self.ignore_suggester.analyze_path(item, repo_path)
                        if progress and task:
                            progress.update(task, advance=1)
                    elif item.is_dir():
                        # Analyze directories for suggestions
                        if self.ignore_suggester:
                            self.ignore_suggester.analyze_path(item, repo_path)
                        scan_directory(item)

            except (OSError, PermissionError) as e:
                error_msg = f"Error scanning directory {path}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
            except Exception as e:
                # Catch any other platform-specific errors
                error_msg = f"Unexpected error scanning directory {path}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

        scan_directory(repo_path)

        if errors and self.config.verbose:
            from rich.console import Console

            console = Console()
            console.print(
                f"[WARNING] Encountered {len(errors)} errors during scan",
                style="yellow",
            )

        return files

    def _process_files(
        self,
        file_list: list[Path],
        repo_path: Path,
        progress: Progress | None,
        task: TaskID | None,
    ) -> dict[str, Any]:
        """Process all files and categorize them using streaming and parallel processing."""
        results: dict[str, Any] = {
            "text_files": {},
            "converted_docs": {},
            "binary_files": {},
            "stats": defaultdict(int),
        }

        # Statistics
        stats: dict[str, Any] = {
            "total_files": len(file_list),
            "text_files": 0,
            "binary_files": 0,
            "converted_docs": 0,
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

        # Use centralized strategy to categorize files for processing
        text_files = []
        other_files = []
        file_strategies = []

        for file_path in optimized_files:
            strategy = self.converter_factory.get_processing_strategy(file_path)
            file_strategies.append((file_path, strategy))

            # Categorize based on processing strategy
            if strategy.action == ProcessingAction.READ_TEXT:
                text_files.append(file_path)
            elif strategy.action in {
                ProcessingAction.CONVERT,
                ProcessingAction.CONDENSE_PYTHON,
                ProcessingAction.CONDENSE_CODE,
                ProcessingAction.ANALYZE_BINARY,
            }:
                other_files.append(file_path)
            # ProcessingAction.SKIP files are not added to either list

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
                    estimated_tokens = result.get("estimated_tokens", 0)
                    stats["estimated_tokens"] += (
                        int(estimated_tokens)
                        if isinstance(estimated_tokens, str)
                        else estimated_tokens
                    )

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

                # Use centralized strategy for processing decisions
                strategy = self.converter_factory.get_processing_strategy(file_path)

                if strategy.action in {
                    ProcessingAction.CONVERT,
                    ProcessingAction.CONDENSE_PYTHON,
                    ProcessingAction.CONDENSE_CODE,
                } and (
                    (
                        strategy.action == ProcessingAction.CONVERT
                        and self.config.convert_docs
                    )
                    or strategy.action
                    in {
                        ProcessingAction.CONDENSE_PYTHON,
                        ProcessingAction.CONDENSE_CODE,
                    }
                ):
                    # Try to convert document or condense code
                    converted_content = self.converter_factory.convert_file(file_path)
                    if converted_content:
                        results["converted_docs"][rel_path] = converted_content
                        stats["converted_docs"] += 1

                elif (
                    strategy.action == ProcessingAction.ANALYZE_BINARY
                    and self.config.describe_binaries
                ):
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
                "streaming_skipped": streaming_stats["skipped_files"],
                "streaming_errors": streaming_stats["error_files"],
            }
        )

        results["stats"] = dict(stats)
        return results

    def _process_files_with_smart_engine(
        self,
        file_list: list[Path],
        repo_path: Path,
        progress: Progress | None,
        task: TaskID | None,
    ) -> dict[str, Any]:
        """Process files using the smart anti-truncation engine."""
        # First, analyze the repository to get priorities and estimates
        if self.smart_engine is None:
            raise ValueError("Smart engine is not initialized")
        (
            file_priorities,
            token_estimates,
            import_scores,
        ) = self.smart_engine.analyze_repository(file_list, repo_path)

        # Allocate budgets based on priorities
        budget_allocations = self.smart_engine.allocate_budgets(
            file_priorities, token_estimates, import_scores
        )

        # Process files normally but with smart engine enhancements
        results: dict[str, Any] = {
            "text_files": {},
            "converted_docs": {},
            "binary_files": {},
            "stats": defaultdict(int),
        }

        stats: dict[str, Any] = defaultdict(int)
        stats["total_files"] = len(file_list)
        stats["languages"] = defaultdict(int)

        # Track token counts for smart condensing stats
        original_tokens_total = 0
        condensed_tokens_total = 0

        # Optimize file processing order
        optimized_files = optimize_file_processing_order(file_list)

        # Separate files for different processing approaches
        text_files = []
        other_files = []

        for file_path in optimized_files:
            # Use existing categorization logic but with smart enhancements
            if should_convert_file(file_path):
                other_files.append(file_path)
            elif should_condense_python_file(file_path, self.config.condense_python):
                other_files.append(file_path)
            elif should_condense_code_file(
                file_path, self.config.condense_code, self.config.condense_languages
            ):
                other_files.append(file_path)
            elif is_data_file(file_path):
                other_files.append(file_path)
            elif is_text_file(file_path):
                text_files.append(file_path)
            else:
                other_files.append(file_path)

        # Process text files with smart engine
        if text_files:
            for file_path in text_files:
                try:
                    if progress and task:
                        progress.update(task, advance=1)

                    rel_path = str(file_path.relative_to(repo_path))

                    # Get budget allocation
                    allocation = budget_allocations.get(file_path)

                    # Read file content
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                    except (OSError, UnicodeDecodeError):
                        continue

                    # Process with smart engine
                    allocation_dict = None
                    if allocation and hasattr(allocation, "__dict__"):
                        allocation_dict = allocation.__dict__
                    elif allocation and isinstance(allocation, dict):
                        allocation_dict = allocation

                    (
                        processed_content,
                        processing_info,
                    ) = self.smart_engine.process_file_with_budget(
                        file_path, content, allocation_dict
                    )

                    results["text_files"][rel_path] = processed_content
                    stats["text_files"] += 1
                    stats["text_size"] += len(processed_content.encode("utf-8"))
                    if isinstance(processing_info, dict):
                        stats["estimated_tokens"] += processing_info.get(
                            "final_tokens", 0
                        )

                    # Track original and condensed tokens for smart condensing stats
                    if isinstance(processing_info, dict):
                        original_tokens = processing_info.get("original_tokens", 0)
                        final_tokens = processing_info.get("final_tokens", 0)
                    else:
                        original_tokens = 0
                        final_tokens = 0
                    original_tokens_total += original_tokens
                    condensed_tokens_total += final_tokens

                    # Track language
                    language = get_language_from_extension(file_path.suffix.lower())
                    if language:
                        stats["languages"][language] += 1
                    else:
                        stats["languages"]["unknown"] += 1

                    # Update smart engine stats
                    if self.smart_engine and hasattr(self.smart_engine, "stats"):
                        count = self.smart_engine.stats.get("files_processed", 0)
                        self.smart_engine.stats["files_processed"] = int(count) + 1

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue

        # Process other files (converted docs, binaries, etc.) with existing logic
        for file_path in other_files:
            try:
                if progress and task:
                    progress.update(task, advance=1)

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

                # Process with smart Python converter if available and applicable
                if self.smart_python_converter and should_condense_python_file(
                    file_path, self.config.condense_python
                ):
                    # Set budget allocation for smart converter
                    allocation = budget_allocations.get(file_path)
                    if allocation:
                        self.smart_python_converter.set_budget_allocation(
                            file_path, allocation
                        )

                    converted_content = self.smart_python_converter.convert(file_path)
                    if converted_content:
                        results["converted_docs"][rel_path] = converted_content
                        stats["converted_docs"] += 1
                        continue

                # Use centralized strategy for processing decisions
                strategy = self.converter_factory.get_processing_strategy(file_path)

                if strategy.action in {
                    ProcessingAction.CONVERT,
                    ProcessingAction.CONDENSE_PYTHON,
                    ProcessingAction.CONDENSE_CODE,
                } and (
                    (
                        strategy.action == ProcessingAction.CONVERT
                        and self.config.convert_docs
                    )
                    or strategy.action
                    in {
                        ProcessingAction.CONDENSE_PYTHON,
                        ProcessingAction.CONDENSE_CODE,
                    }
                ):
                    # Try to convert document or condense code
                    converted_content = self.converter_factory.convert_file(file_path)
                    if converted_content:
                        # Apply smart processing to converted content if enabled
                        if (
                            self.smart_engine and len(converted_content) > 1000
                        ):  # Only for substantial content
                            allocation = budget_allocations.get(file_path)
                            allocation_dict = None
                            if allocation and hasattr(allocation, "__dict__"):
                                allocation_dict = allocation.__dict__
                            elif allocation and isinstance(allocation, dict):
                                allocation_dict = allocation

                            (
                                processed_content,
                                processing_info,
                            ) = self.smart_engine.process_file_with_budget(
                                file_path, converted_content, allocation_dict
                            )
                            results["converted_docs"][rel_path] = processed_content

                            # Track tokens for smart condensing stats
                            if isinstance(processing_info, dict):
                                original_tokens = processing_info.get(
                                    "original_tokens", 0
                                )
                                final_tokens = processing_info.get("final_tokens", 0)
                            else:
                                original_tokens = 0
                                final_tokens = 0
                            original_tokens_total += original_tokens
                            condensed_tokens_total += final_tokens
                        else:
                            results["converted_docs"][rel_path] = converted_content

                            # Track tokens for files not processed by smart engine
                            from ..utils.token_utils import estimate_tokens_from_text

                            tokens = estimate_tokens_from_text(converted_content)
                            original_tokens_total += tokens
                            condensed_tokens_total += tokens
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

        # Add smart engine stats to results
        if self.smart_engine:
            smart_stats = self.smart_engine.get_budget_report()
            stats.update(
                {
                    "smart_engine_used": True,
                    "smart_files_processed": smart_stats.get("engine_stats", {}).get(
                        "files_processed", 0
                    ),
                    "smart_tokens_saved": smart_stats.get("engine_stats", {}).get(
                        "total_tokens_saved", 0
                    ),
                    "budget_compression_ratio": smart_stats.get(
                        "budget_report", {}
                    ).get("compression_ratio", 1.0),
                    "original_tokens_total": original_tokens_total,
                    "condensed_tokens_total": condensed_tokens_total,
                }
            )

        results["stats"] = dict(stats)
        return results
