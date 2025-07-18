"""Code analyzer for extracting signatures and docstrings from Python files."""

import ast
import textwrap
from pathlib import Path
from typing import Any


class PythonCodeAnalyzer:
    """Analyzer for Python code that extracts signatures, docstrings, and structure."""

    def __init__(self, condense_mode: str = "signatures"):
        """Initialize the Python code analyzer.

        Args:
            condense_mode: How to condense the code
                - "signatures": Function/class signatures only
                - "signatures_with_docstrings": Signatures plus docstrings
                - "structure": Full structure with docstrings and type hints
        """
        self.condense_mode = condense_mode

    def analyze_file(self, file_path: Path) -> str | None:
        """Analyze a Python file and return condensed content.

        Args:
            file_path: Path to the Python file

        Returns:
            Condensed Python code content or None if analysis failed
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return self.analyze_code(content, str(file_path))
        except (OSError, UnicodeDecodeError) as e:
            return f"# Error reading file: {e}"

    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        """Analyze Python code content and return condensed version.

        Args:
            content: Python source code
            filename: Filename for error reporting

        Returns:
            Condensed code content or None if parsing failed
        """
        try:
            tree = ast.parse(content, filename)
            return self._extract_structure(tree, content)
        except SyntaxError as e:
            return f"# Syntax Error in {filename}: {e.msg} (line {e.lineno})"
        except Exception as e:
            return f"# Error parsing {filename}: {e}"

    def _extract_structure(self, tree: ast.AST, original_content: str) -> str:
        """Extract the condensed structure from AST.

        Args:
            tree: Parsed AST tree
            original_content: Original source code for line extraction

        Returns:
            Condensed code structure
        """
        lines = original_content.splitlines()
        result = []

        # Extract module-level docstring
        module_docstring = (
            ast.get_docstring(tree) if isinstance(tree, ast.Module) else None
        )
        if module_docstring:
            result.append(f'"""Module docstring:\n{module_docstring}\n"""')
            result.append("")

        # Process top-level imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                imports.append(self._get_source_segment(lines, node))

        if imports:
            result.extend(imports[:10])  # Limit to first 10 imports
            if len(imports) > 10:
                result.append(f"# ... and {len(imports) - 10} more imports")
            result.append("")

        # Process classes and functions
        if hasattr(tree, "body"):
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    result.extend(self._extract_class(node, lines))
                    result.append("")
                elif isinstance(node, ast.FunctionDef):
                    result.extend(self._extract_function(node, lines))
                    result.append("")
                elif isinstance(node, ast.AsyncFunctionDef):
                    result.extend(self._extract_async_function(node, lines))
                    result.append("")

        return "\n".join(result)

    def _extract_class(self, node: ast.ClassDef, lines: list[str]) -> list[str]:
        """Extract class signature and structure.

        Args:
            node: Class AST node
            lines: Source code lines

        Returns:
            List of condensed class representation lines
        """
        result = []

        # Class signature with decorators
        decorators = [
            self._get_source_segment(lines, dec) for dec in node.decorator_list
        ]
        result.extend(decorators)

        # Class definition line
        class_line = f"class {node.name}"
        if node.bases:
            bases = [self._get_source_segment(lines, base) for base in node.bases]
            class_line += f"({', '.join(bases)})"
        class_line += ":"
        result.append(class_line)

        # Class docstring
        docstring = ast.get_docstring(node)
        if docstring and self.condense_mode in [
            "signatures_with_docstrings",
            "structure",
        ]:
            indented_docstring = self._indent_text(f'"""{docstring}"""', 4)
            result.append(indented_docstring)

        # Class methods and attributes
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_lines = self._extract_function(item, lines, indent=4)
                methods.extend(method_lines)
            elif isinstance(item, ast.AsyncFunctionDef):
                method_lines = self._extract_async_function(item, lines, indent=4)
                methods.extend(method_lines)
            elif isinstance(item, ast.Assign) and self.condense_mode == "structure":
                # Class variables
                attr_line = self._get_source_segment(lines, item)
                methods.append(self._indent_text(attr_line, 4))

        if methods:
            result.extend(methods)
        else:
            result.append("    pass")

        return result

    def _extract_function(
        self, node: ast.FunctionDef, lines: list[str], indent: int = 0
    ) -> list[str]:
        """Extract function signature and docstring.

        Args:
            node: Function AST node
            lines: Source code lines
            indent: Indentation level

        Returns:
            List of condensed function representation lines
        """
        result = []

        # Function decorators
        decorators = [
            self._get_source_segment(lines, dec) for dec in node.decorator_list
        ]
        result.extend([self._indent_text(dec, indent) for dec in decorators])

        # Function signature
        func_line = f"def {node.name}("

        # Arguments
        args = []

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_source_segment(lines, arg.annotation)}"
            args.append(arg_str)

        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_str += (
                    f": {self._get_source_segment(lines, node.args.vararg.annotation)}"
                )
            args.append(vararg_str)

        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_str += (
                    f": {self._get_source_segment(lines, node.args.kwarg.annotation)}"
                )
            args.append(kwarg_str)

        func_line += ", ".join(args)
        func_line += ")"

        # Return annotation
        if node.returns:
            func_line += f" -> {self._get_source_segment(lines, node.returns)}"

        func_line += ":"
        result.append(self._indent_text(func_line, indent))

        # Function docstring
        docstring = ast.get_docstring(node)
        if docstring and self.condense_mode in [
            "signatures_with_docstrings",
            "structure",
        ]:
            indented_docstring = self._indent_text(f'"""{docstring}"""', indent + 4)
            result.append(indented_docstring)

        # Add pass or ellipsis
        if self.condense_mode == "signatures":
            result.append(self._indent_text("...", indent + 4))
        else:
            result.append(self._indent_text("pass", indent + 4))

        return result

    def _extract_async_function(
        self, node: ast.AsyncFunctionDef, lines: list[str], indent: int = 0
    ) -> list[str]:
        """Extract async function signature and docstring.

        Args:
            node: Async function AST node
            lines: Source code lines
            indent: Indentation level

        Returns:
            List of condensed async function representation lines
        """
        # Convert to regular function node for processing
        regular_func = ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

        result = self._extract_function(regular_func, lines, indent)

        # Convert "def" to "async def"
        for i, line in enumerate(result):
            if "def " in line:
                result[i] = line.replace("def ", "async def ")
                break

        return result

    def _get_source_segment(self, lines: list[str], node: ast.AST) -> str:
        """Get source code segment for an AST node.

        Args:
            lines: Source code lines
            node: AST node

        Returns:
            Source code segment
        """
        if not hasattr(node, "lineno"):
            return str(node)

        try:
            # Simple single-line extraction
            line_idx = node.lineno - 1
            if 0 <= line_idx < len(lines):
                return str(lines[line_idx].strip())
            return str(node)
        except (AttributeError, IndexError):
            return str(node)

    def _indent_text(self, text: str, spaces: int) -> str:
        """Indent text by specified number of spaces.

        Args:
            text: Text to indent
            spaces: Number of spaces to indent

        Returns:
            Indented text
        """
        indent = " " * spaces
        return textwrap.indent(text, indent)

    def get_stats(self) -> dict[str, Any]:
        """Get analysis statistics.

        Returns:
            Dictionary with analysis statistics
        """
        return {
            "condense_mode": self.condense_mode,
            "analyzer_type": "python_ast",
        }
