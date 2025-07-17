"""Smart chunker for context-aware content splitting that preserves code structure."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from ..analyzers.priority_analyzer import PriorityLevel
from .token_utils import estimate_tokens_from_text


@dataclass
class Chunk:
    """Represents a chunk of content with metadata."""

    content: str
    chunk_id: int
    total_chunks: int
    start_line: int | None = None
    end_line: int | None = None
    context_info: str | None = None
    continuation_from: int | None = None
    continues_to: int | None = None
    estimated_tokens: int | None = None
    chunk_type: str = "content"  # content, header, footer, context


@dataclass
class ChunkingStrategy:
    """Configuration for chunking behavior."""

    preserve_functions: bool = True
    preserve_classes: bool = True
    include_context_headers: bool = True
    overlap_functions: bool = True  # Include function signatures in multiple chunks
    max_context_lines: int = 5
    min_chunk_size: int = 100  # Minimum tokens per chunk


class SmartChunker:
    """Context-aware chunker that preserves code structure and relationships."""

    def __init__(self, strategy: ChunkingStrategy | None = None):
        """Initialize the smart chunker.

        Args:
            strategy: Chunking strategy configuration
        """
        self.strategy = strategy or ChunkingStrategy()
        self.stats = {
            "files_chunked": 0,
            "total_chunks_created": 0,
            "context_preservations": 0,
            "function_overlaps": 0,
        }

    def chunk_with_context(
        self,
        content: str,
        file_path: Path,
        max_tokens: int,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        preserve_functions: bool = True,
    ) -> list[Chunk]:
        """Chunk content while preserving context and code structure.

        Args:
            content: Content to chunk
            file_path: Path to the source file
            max_tokens: Maximum tokens per chunk
            priority: Priority level of the content
            preserve_functions: Whether to preserve function boundaries

        Returns:
            List of chunks with context information
        """
        if not content.strip():
            return []

        # Estimate total tokens
        total_tokens = estimate_tokens_from_text(content)

        # If content fits in one chunk, return it as-is
        if total_tokens <= max_tokens:
            chunk = Chunk(
                content=content,
                chunk_id=1,
                total_chunks=1,
                estimated_tokens=total_tokens,
            )
            return [chunk]

        # Determine chunking approach based on file type
        file_extension = file_path.suffix.lower()

        if file_extension == ".py":
            chunks = self._chunk_python_content(content, max_tokens, priority)
        elif file_extension in [".js", ".ts", ".jsx", ".tsx"]:
            chunks = self._chunk_javascript_content(content, max_tokens, priority)
        elif file_extension == ".java":
            chunks = self._chunk_java_content(content, max_tokens, priority)
        else:
            chunks = self._chunk_generic_content(content, max_tokens)

        # Add continuation context between chunks
        if self.strategy.include_context_headers:
            chunks = self.add_continuation_context(chunks, file_path)

        # Update statistics
        self.stats["files_chunked"] += 1
        self.stats["total_chunks_created"] += len(chunks)

        return chunks

    def add_continuation_context(
        self, chunks: list[Chunk], file_path: Path
    ) -> list[Chunk]:
        """Add context headers and footers to chunks for better continuity.

        Args:
            chunks: List of chunks to enhance
            file_path: Path to the source file

        Returns:
            Enhanced chunks with context information
        """
        if len(chunks) <= 1:
            return chunks

        enhanced_chunks = []

        for i, chunk in enumerate(chunks):
            enhanced_content = []

            # Add header with context information
            if i > 0:
                header = (
                    f"# Continuation of {file_path.name} (Part {i + 1}/{len(chunks)})\n"
                )
                if chunk.continuation_from:
                    header += f"# Continued from Part {chunk.continuation_from}\n"
                enhanced_content.append(header)
            else:
                header = f"# {file_path.name} (Part {i + 1}/{len(chunks)})\n"
                enhanced_content.append(header)

            # Add the actual content
            enhanced_content.append(chunk.content)

            # Add footer with continuation info
            if i < len(chunks) - 1:
                footer = f"\n# Continues in Part {i + 2}/{len(chunks)}..."
                enhanced_content.append(footer)

            # Create enhanced chunk
            enhanced_chunk = Chunk(
                content="\n".join(enhanced_content),
                chunk_id=chunk.chunk_id,
                total_chunks=chunk.total_chunks,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                context_info=f"Part {i + 1} of {len(chunks)}",
                continuation_from=chunk.continuation_from,
                continues_to=chunk.continues_to,
                estimated_tokens=estimate_tokens_from_text("\n".join(enhanced_content)),
                chunk_type=chunk.chunk_type,
            )

            enhanced_chunks.append(enhanced_chunk)
            self.stats["context_preservations"] += 1

        return enhanced_chunks

    def _chunk_python_content(
        self, content: str, max_tokens: int, priority: PriorityLevel
    ) -> list[Chunk]:
        """Chunk Python content preserving function and class boundaries."""
        try:
            tree = ast.parse(content)
            lines = content.split("\n")

            # Find function and class boundaries
            boundaries = self._find_python_boundaries(tree, lines)

            # Create chunks respecting boundaries
            chunks = self._create_chunks_with_boundaries(
                content, lines, boundaries, max_tokens, priority
            )

            return chunks

        except SyntaxError:
            # Fall back to generic chunking if parsing fails
            return self._chunk_generic_content(content, max_tokens)

    def _find_python_boundaries(
        self, tree: ast.AST, lines: list[str]
    ) -> list[tuple[int, int, str, str]]:
        """Find natural boundaries in Python code (functions, classes).

        Returns:
            List of (start_line, end_line, boundary_type, name) tuples
        """
        boundaries = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                start_line = node.lineno - 1  # Convert to 0-based
                end_line = getattr(node, "end_lineno", len(lines)) - 1
                boundaries.append((start_line, end_line, "function", node.name))

            elif isinstance(node, ast.ClassDef):
                start_line = node.lineno - 1
                end_line = getattr(node, "end_lineno", len(lines)) - 1
                boundaries.append((start_line, end_line, "class", node.name))

                # Also find methods within the class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        method_start = item.lineno - 1
                        method_end = getattr(item, "end_lineno", end_line) - 1
                        boundaries.append(
                            (
                                method_start,
                                method_end,
                                "method",
                                f"{node.name}.{item.name}",
                            )
                        )

        return sorted(boundaries, key=lambda x: x[0])

    def _create_chunks_with_boundaries(
        self,
        content: str,
        lines: list[str],
        boundaries: list[tuple[int, int, str, str]],
        max_tokens: int,
        priority: PriorityLevel,
    ) -> list[Chunk]:
        """Create chunks that respect code boundaries."""
        chunks = []
        current_chunk_lines = []
        current_tokens = 0
        chunk_id = 1
        last_line_processed = 0

        # Group boundaries by logical units
        i = 0
        while i < len(lines):
            # Find if current line starts a boundary
            boundary = None
            for start, end, btype, name in boundaries:
                if start == i:
                    boundary = (start, end, btype, name)
                    break

            if boundary:
                start, end, btype, name = boundary

                # Get the complete boundary content
                boundary_lines = lines[start : end + 1]
                boundary_content = "\n".join(boundary_lines)
                boundary_tokens = estimate_tokens_from_text(boundary_content)

                # If boundary fits in current chunk, add it
                if current_tokens + boundary_tokens <= max_tokens:
                    current_chunk_lines.extend(boundary_lines)
                    current_tokens += boundary_tokens
                    i = end + 1

                # If boundary is too large, handle specially
                elif boundary_tokens > max_tokens:
                    # Save current chunk if it has content
                    if current_chunk_lines:
                        chunks.append(
                            self._create_chunk(
                                current_chunk_lines,
                                chunk_id,
                                priority,
                                last_line_processed,
                                last_line_processed + len(current_chunk_lines) - 1,
                            )
                        )
                        chunk_id += 1
                        current_chunk_lines = []
                        current_tokens = 0
                        last_line_processed = i

                    # Split the large boundary into sub-chunks
                    sub_chunks = self._split_large_boundary(
                        boundary_lines, max_tokens, chunk_id, btype, name, start
                    )
                    chunks.extend(sub_chunks)
                    chunk_id += len(sub_chunks)
                    i = end + 1
                    last_line_processed = i

                # If boundary doesn't fit, start new chunk
                else:
                    # Save current chunk
                    if current_chunk_lines:
                        chunks.append(
                            self._create_chunk(
                                current_chunk_lines,
                                chunk_id,
                                priority,
                                last_line_processed,
                                last_line_processed + len(current_chunk_lines) - 1,
                            )
                        )
                        chunk_id += 1
                        last_line_processed = i

                    # Start new chunk with boundary
                    current_chunk_lines = boundary_lines[:]
                    current_tokens = boundary_tokens
                    i = end + 1

            else:
                # Regular line, add if it fits
                line = lines[i]
                line_tokens = estimate_tokens_from_text(line)

                if current_tokens + line_tokens <= max_tokens:
                    current_chunk_lines.append(line)
                    current_tokens += line_tokens
                else:
                    # Start new chunk
                    if current_chunk_lines:
                        chunks.append(
                            self._create_chunk(
                                current_chunk_lines,
                                chunk_id,
                                priority,
                                last_line_processed,
                                last_line_processed + len(current_chunk_lines) - 1,
                            )
                        )
                        chunk_id += 1
                        last_line_processed = i

                    current_chunk_lines = [line]
                    current_tokens = line_tokens

                i += 1

        # Add final chunk if there's content
        if current_chunk_lines:
            chunks.append(
                self._create_chunk(
                    current_chunk_lines,
                    chunk_id,
                    priority,
                    last_line_processed,
                    last_line_processed + len(current_chunk_lines) - 1,
                )
            )

        # Update chunk metadata
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total_chunks

        # Add function signature overlaps if enabled
        if self.strategy.overlap_functions:
            chunks = self._add_function_overlaps(chunks, boundaries)

        return chunks

    def _split_large_boundary(
        self,
        boundary_lines: list[str],
        max_tokens: int,
        start_chunk_id: int,
        boundary_type: str,
        name: str,
        start_line: int,
    ) -> list[Chunk]:
        """Split a large function or class into multiple chunks."""
        sub_chunks = []
        current_lines = []
        current_tokens = 0
        chunk_id = start_chunk_id

        # Always include the signature in the first chunk
        signature_line = boundary_lines[0] if boundary_lines else ""
        current_lines.append(signature_line)
        current_tokens = estimate_tokens_from_text(signature_line)

        for _i, line in enumerate(boundary_lines[1:], 1):
            line_tokens = estimate_tokens_from_text(line)

            if current_tokens + line_tokens <= max_tokens:
                current_lines.append(line)
                current_tokens += line_tokens
            else:
                # Create chunk with current content
                chunk_content = "\n".join(current_lines)
                chunk = Chunk(
                    content=chunk_content,
                    chunk_id=chunk_id,
                    total_chunks=0,  # Will be updated later
                    start_line=start_line,
                    context_info=f"{boundary_type} {name} (part {chunk_id - start_chunk_id + 1})",
                    estimated_tokens=current_tokens,
                )
                sub_chunks.append(chunk)
                chunk_id += 1

                # Start new chunk with signature for context
                current_lines = [signature_line, line]
                current_tokens = estimate_tokens_from_text(signature_line) + line_tokens

        # Add final chunk
        if current_lines:
            chunk_content = "\n".join(current_lines)
            chunk = Chunk(
                content=chunk_content,
                chunk_id=chunk_id,
                total_chunks=0,  # Will be updated later
                start_line=start_line,
                context_info=f"{boundary_type} {name} (part {chunk_id - start_chunk_id + 1})",
                estimated_tokens=estimate_tokens_from_text(chunk_content),
            )
            sub_chunks.append(chunk)

        return sub_chunks

    def _add_function_overlaps(
        self, chunks: list[Chunk], boundaries: list[tuple[int, int, str, str]]
    ) -> list[Chunk]:
        """Add function signatures to multiple chunks for context."""
        enhanced_chunks = []

        for chunk in chunks:
            enhanced_content = chunk.content
            overlapping_functions = []

            # Find functions that span across chunk boundaries
            for start, end, btype, name in boundaries:
                if btype in ["function", "method"]:
                    # Check if function signature should be included for context
                    if (
                        chunk.start_line
                        and start < chunk.start_line
                        and end >= chunk.start_line
                    ):
                        # Function starts before this chunk but continues into it
                        overlapping_functions.append(
                            f"# Continued from: def {name}(...)"
                        )
                    elif (
                        chunk.end_line
                        and start <= chunk.end_line
                        and end > chunk.end_line
                    ):
                        # Function starts in this chunk but continues beyond
                        overlapping_functions.append(f"# Continues: def {name}(...)")

            # Add context information
            if overlapping_functions:
                context_header = "\n".join(overlapping_functions) + "\n\n"
                enhanced_content = context_header + enhanced_content
                self.stats["function_overlaps"] += 1

            enhanced_chunk = Chunk(
                content=enhanced_content,
                chunk_id=chunk.chunk_id,
                total_chunks=chunk.total_chunks,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                context_info=chunk.context_info,
                continuation_from=chunk.continuation_from,
                continues_to=chunk.continues_to,
                estimated_tokens=estimate_tokens_from_text(enhanced_content),
                chunk_type=chunk.chunk_type,
            )
            enhanced_chunks.append(enhanced_chunk)

        return enhanced_chunks

    def _chunk_javascript_content(
        self, content: str, max_tokens: int, priority: PriorityLevel
    ) -> list[Chunk]:
        """Chunk JavaScript/TypeScript content preserving function boundaries."""
        lines = content.split("\n")

        # Find function boundaries using regex
        function_patterns = [
            r"^\s*function\s+\w+",
            r"^\s*async\s+function\s+\w+",
            r"^\s*const\s+\w+\s*=\s*\(",
            r"^\s*export\s+function\s+\w+",
            r"^\s*export\s+const\s+\w+\s*=",
            r"^\s*class\s+\w+",
        ]

        boundaries = []
        for i, line in enumerate(lines):
            for pattern in function_patterns:
                if re.match(pattern, line):
                    # Find the end of this function/class (simple heuristic)
                    end_line = self._find_js_block_end(lines, i)
                    boundaries.append((i, end_line, "function", "js_function"))
                    break

        return self._create_chunks_with_boundaries(
            content, lines, boundaries, max_tokens, priority
        )

    def _chunk_java_content(
        self, content: str, max_tokens: int, priority: PriorityLevel
    ) -> list[Chunk]:
        """Chunk Java content preserving class and method boundaries."""
        lines = content.split("\n")

        # Find Java boundaries
        boundaries = []
        brace_stack = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Count braces
            brace_stack.extend(["{"] * line.count("{"))
            brace_stack = brace_stack[: -line.count("}")]

            # Detect method/class declarations
            if re.match(
                r"^\s*(public|private|protected)?\s*(static\s+)?(class|interface|\w+\s+\w+\s*\()",
                stripped,
            ):
                # Find end of this declaration
                end_line = self._find_java_block_end(lines, i)
                boundaries.append((i, end_line, "declaration", "java_declaration"))

        return self._create_chunks_with_boundaries(
            content, lines, boundaries, max_tokens, priority
        )

    def _chunk_generic_content(self, content: str, max_tokens: int) -> list[Chunk]:
        """Generic chunking for unknown file types."""
        lines = content.split("\n")
        chunks = []
        current_lines = []
        current_tokens = 0
        chunk_id = 1

        for i, line in enumerate(lines):
            line_tokens = estimate_tokens_from_text(line)

            if current_tokens + line_tokens <= max_tokens:
                current_lines.append(line)
                current_tokens += line_tokens
            else:
                # Create chunk
                if current_lines:
                    chunk_content = "\n".join(current_lines)
                    chunk = Chunk(
                        content=chunk_content,
                        chunk_id=chunk_id,
                        total_chunks=0,  # Will be updated
                        start_line=i - len(current_lines),
                        end_line=i - 1,
                        estimated_tokens=current_tokens,
                    )
                    chunks.append(chunk)
                    chunk_id += 1

                # Start new chunk
                current_lines = [line]
                current_tokens = line_tokens

        # Add final chunk
        if current_lines:
            chunk_content = "\n".join(current_lines)
            chunk = Chunk(
                content=chunk_content,
                chunk_id=chunk_id,
                total_chunks=0,
                start_line=len(lines) - len(current_lines),
                end_line=len(lines) - 1,
                estimated_tokens=estimate_tokens_from_text(chunk_content),
            )
            chunks.append(chunk)

        # Update total chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        return chunks

    def _create_chunk(
        self,
        lines: list[str],
        chunk_id: int,
        priority: PriorityLevel,
        start_line: int,
        end_line: int,
    ) -> Chunk:
        """Create a chunk from lines with metadata."""
        content = "\n".join(lines)
        estimated_tokens = estimate_tokens_from_text(content)

        return Chunk(
            content=content,
            chunk_id=chunk_id,
            total_chunks=0,  # Will be updated later
            start_line=start_line,
            end_line=end_line,
            estimated_tokens=estimated_tokens,
        )

    def _find_js_block_end(self, lines: list[str], start: int) -> int:
        """Find the end of a JavaScript function or class block."""
        brace_count = 0
        in_block = False

        for i in range(start, len(lines)):
            line = lines[i]

            for char in line:
                if char == "{":
                    brace_count += 1
                    in_block = True
                elif char == "}":
                    brace_count -= 1
                    if in_block and brace_count == 0:
                        return i

        return len(lines) - 1

    def _find_java_block_end(self, lines: list[str], start: int) -> int:
        """Find the end of a Java method or class block."""
        return self._find_js_block_end(lines, start)  # Same logic for braces

    def get_chunking_stats(self) -> dict:
        """Get statistics about chunking operations."""
        return self.stats.copy()

    def estimate_optimal_chunk_size(
        self,
        content: str,
        file_path: Path,
        total_token_budget: int,
        target_chunks: int = 3,
    ) -> int:
        """Estimate optimal chunk size for given content and constraints.

        Args:
            content: Content to analyze
            file_path: Path to source file
            total_token_budget: Total available tokens
            target_chunks: Desired number of chunks

        Returns:
            Recommended tokens per chunk
        """
        total_tokens = estimate_tokens_from_text(content)

        # If content fits in budget, no chunking needed
        if total_tokens <= total_token_budget:
            return total_tokens

        # Calculate base chunk size
        base_chunk_size = total_token_budget // target_chunks

        # Adjust based on file type
        file_extension = file_path.suffix.lower()
        if file_extension == ".py":
            # Python functions tend to be longer, prefer larger chunks
            return min(int(base_chunk_size * 1.2), total_token_budget // 2)
        elif file_extension in [".js", ".ts", ".jsx", ".tsx"]:
            # JavaScript can be more modular, smaller chunks work well
            return max(int(base_chunk_size * 0.8), 500)
        else:
            return base_chunk_size
