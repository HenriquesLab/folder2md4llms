"""Main repository processor for folder2md4llms."""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.progress import Progress, TaskID

from .analyzers.binary_analyzer import BinaryAnalyzer
from .converters.converter_factory import ConverterFactory
from .formatters.markdown import MarkdownFormatter
from .utils.config import Config
from .utils.file_utils import (
    get_language_from_extension,
    is_text_file,
    read_file_safely,
    should_convert_file,
)
from .utils.ignore_patterns import IgnorePatterns
from .utils.tree_generator import TreeGenerator

logger = logging.getLogger(__name__)


class RepositoryProcessor:
    """Main processor for converting repositories to markdown."""

    def __init__(self, config: Config):
        self.config = config

        # Initialize components
        self.ignore_patterns = self._load_ignore_patterns()
        self.tree_generator = TreeGenerator(self.ignore_patterns)
        self.converter_factory = ConverterFactory(config.__dict__)
        self.binary_analyzer = BinaryAnalyzer(config.__dict__)
        self.markdown_formatter = MarkdownFormatter(
            include_tree=config.include_tree, include_stats=config.include_stats
        )

    def _load_ignore_patterns(self) -> IgnorePatterns:
        """Load ignore patterns from file or use defaults."""
        if self.config.ignore_file and self.config.ignore_file.exists():
            return IgnorePatterns.from_file(self.config.ignore_file)
        else:
            # Look for .folder2md_ignore in current directory
            ignore_file = Path(".folder2md_ignore")
            return IgnorePatterns.from_file(ignore_file)

    def process(self, repo_path: Path, progress: Optional[Progress] = None) -> str:
        """Process a repository and return markdown output."""
        if not repo_path.exists() or not repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {repo_path}")

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

            # Generate output
            output = self.markdown_formatter.format_repository(
                repo_path=repo_path,
                tree_structure=tree_structure,
                file_contents=results["text_files"],
                file_stats=results["stats"],
                binary_descriptions=results["binary_files"],
                converted_docs=results["converted_docs"],
            )

            return output

        finally:
            if progress:
                progress.remove_task(scan_task)
                progress.remove_task(process_task)

    def _scan_repository(
        self, repo_path: Path, progress: Optional[Progress], task: Optional[TaskID]
    ) -> List[Path]:
        """Scan repository and return list of files to process."""
        files = []

        def scan_directory(path: Path):
            try:
                for item in path.iterdir():
                    if self.ignore_patterns.should_ignore(item, repo_path):
                        continue

                    if item.is_file():
                        files.append(item)
                        if progress and task:
                            progress.update(task, advance=1)
                    elif item.is_dir():
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
        file_list: List[Path],
        repo_path: Path,
        progress: Optional[Progress],
        task: Optional[TaskID],
    ) -> Dict[str, Any]:
        """Process all files and categorize them."""
        results = {
            "text_files": {},
            "converted_docs": {},
            "binary_files": {},
            "stats": defaultdict(int),
        }

        # Statistics
        stats = {
            "total_files": len(file_list),
            "text_files": 0,
            "binary_files": 0,
            "converted_docs": 0,
            "total_size": 0,
            "text_size": 0,
            "languages": defaultdict(int),
        }

        for file_path in file_list:
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

                # Determine file category and process accordingly
                if is_text_file(file_path):
                    content = read_file_safely(file_path, self.config.max_file_size)
                    if content is not None:
                        results["text_files"][rel_path] = content
                        stats["text_files"] += 1
                        stats["text_size"] += len(content.encode("utf-8"))

                        # Track language
                        language = get_language_from_extension(file_path.suffix.lower())
                        if language:
                            stats["languages"][language] += 1
                        else:
                            stats["languages"]["unknown"] += 1

                elif should_convert_file(file_path) and self.config.convert_docs:
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

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue

        results["stats"] = dict(stats)
        return results
