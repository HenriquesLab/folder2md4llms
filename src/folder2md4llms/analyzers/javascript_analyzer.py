"""JavaScript and TypeScript code analyzer."""

import re
from pathlib import Path
from typing import Any

from .base_code_analyzer import RegexBasedAnalyzer


class JavaScriptAnalyzer(RegexBasedAnalyzer):
    """Analyzer for JavaScript and TypeScript files."""

    def __init__(self, condense_mode: str = "signatures_with_docstrings"):
        super().__init__(condense_mode)
        self._compile_patterns()

    def get_supported_extensions(self) -> set[str]:
        """Get supported file extensions."""
        return {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}

    def _compile_patterns(self) -> None:
        """Compile regex patterns for JavaScript/TypeScript."""
        # Function patterns (various forms)
        self.function_pattern = re.compile(
            r"(?:^|\n)\s*(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|"
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|"
            r"(\w+)\s*\([^)]*\)\s*\{)",
            re.MULTILINE,
        )

        # Class patterns
        self.class_pattern = re.compile(
            r"(?:^|\n)\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )

        # Interface patterns (TypeScript)
        self.interface_pattern = re.compile(
            r"(?:^|\n)\s*(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )

        # Type patterns (TypeScript)
        self.type_pattern = re.compile(
            r"(?:^|\n)\s*(?:export\s+)?type\s+(\w+)\s*=", re.MULTILINE
        )

        # Enum patterns (TypeScript)
        self.enum_pattern = re.compile(
            r"(?:^|\n)\s*(?:export\s+)?enum\s+(\w+)\s*\{", re.MULTILINE
        )

        # Import patterns
        self.import_pattern = re.compile(
            r'(?:^|\n)\s*(?:import\s+.+?from\s+[\'"].+?[\'"]|'
            r'import\s+[\'"].+?[\'"]|'
            r'const\s+.+?\s*=\s*require\([\'"].+?[\'"]\))',
            re.MULTILINE,
        )

        # Export patterns
        self.export_pattern = re.compile(
            r'(?:^|\n)\s*export\s+(?:default\s+)?(?:\{[^}]+\}|.+?)(?:\s+from\s+[\'"].+?[\'"])?',
            re.MULTILINE,
        )

        # JSDoc comment pattern
        self.jsdoc_pattern = re.compile(
            r"/\*\*\s*\n((?:\s*\*.*\n)*)\s*\*/", re.MULTILINE
        )

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import and require statements."""
        imports = []

        if self.import_pattern:
            for match in self.import_pattern.finditer(content):
                import_line = match.group().strip()
                # Clean up multiline imports
                import_line = re.sub(r"\s+", " ", import_line)
                imports.append(import_line)

        return imports[:15]  # Limit to first 15 imports

    def _extract_functions(self, content: str) -> list[dict[str, Any]]:
        """Extract function definitions."""
        functions = []

        # Find all function-like constructs
        patterns = [
            # Regular function declarations
            r"(?:^|\n)(\s*)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{",
            # Arrow functions
            r"(?:^|\n)(\s*)(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)(?:\s*:\s*([^=]+?))?\s*=>\s*\{",
            # Method definitions in classes
            r"(?:^|\n)(\s*)(?:async\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                indent = match.group(1) if len(match.groups()) >= 1 else ""
                name = match.group(2) if len(match.groups()) >= 2 else "anonymous"
                params = match.group(3) if len(match.groups()) >= 3 else ""
                return_type = match.group(4) if len(match.groups()) >= 4 else None

                # Extract JSDoc if available
                start_pos = match.start()
                preceding_content = content[:start_pos]
                jsdoc = self._extract_preceding_jsdoc(preceding_content)

                functions.append(
                    {
                        "name": name,
                        "params": params.strip(),
                        "return_type": return_type.strip() if return_type else None,
                        "jsdoc": jsdoc,
                        "indent": len(indent),
                        "line": content[:start_pos].count("\n") + 1,
                    }
                )

        return functions

    def _extract_classes(self, content: str) -> list[dict[str, Any]]:
        """Extract class definitions."""
        classes = []

        if self.class_pattern:
            for match in self.class_pattern.finditer(content):
                class_name = match.group(1)
                start_pos = match.start()

                # Extract JSDoc if available
                preceding_content = content[:start_pos]
                jsdoc = self._extract_preceding_jsdoc(preceding_content)

                # Find class methods
                class_start = match.end()
                class_end = self._find_matching_brace(content, class_start - 1)
                class_body = content[class_start:class_end] if class_end else ""

                methods = self._extract_class_methods(class_body)

                classes.append(
                    {
                        "name": class_name,
                        "jsdoc": jsdoc,
                        "methods": methods,
                        "line": content[:start_pos].count("\n") + 1,
                    }
                )

        return classes

    def _extract_interfaces(self, content: str) -> list[dict[str, Any]]:
        """Extract TypeScript interface definitions."""
        interfaces = []

        if hasattr(self, "interface_pattern") and self.interface_pattern:
            for match in self.interface_pattern.finditer(content):
                interface_name = match.group(1)
                start_pos = match.start()

                # Extract JSDoc if available
                preceding_content = content[:start_pos]
                jsdoc = self._extract_preceding_jsdoc(preceding_content)

                interfaces.append(
                    {
                        "name": interface_name,
                        "jsdoc": jsdoc,
                        "line": content[:start_pos].count("\n") + 1,
                    }
                )

        return interfaces

    def _extract_types(self, content: str) -> list[dict[str, Any]]:
        """Extract TypeScript type definitions."""
        types = []

        if hasattr(self, "type_pattern") and self.type_pattern:
            for match in self.type_pattern.finditer(content):
                type_name = match.group(1)
                start_pos = match.start()

                types.append(
                    {"name": type_name, "line": content[:start_pos].count("\n") + 1}
                )

        return types

    def _extract_class_methods(self, class_body: str) -> list[dict[str, Any]]:
        """Extract methods from a class body."""
        methods = []

        # Method pattern within class
        method_pattern = re.compile(
            r"(?:^|\n)(\s*)(?:static\s+)?(?:async\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{",
            re.MULTILINE,
        )

        for match in method_pattern.finditer(class_body):
            indent = match.group(1)
            name = match.group(2)
            params = match.group(3)
            return_type = match.group(4)

            methods.append(
                {
                    "name": name,
                    "params": params.strip(),
                    "return_type": return_type.strip() if return_type else None,
                    "indent": len(indent),
                }
            )

        return methods

    def _extract_preceding_jsdoc(self, preceding_content: str) -> str | None:
        """Extract JSDoc comment that precedes the current position."""
        if not self.jsdoc_pattern or not self._should_include_docstring():
            return None

        # Look for JSDoc in the last few lines before the current position
        lines = preceding_content.split("\n")

        # Work backwards to find JSDoc
        jsdoc_lines: list[str] = []
        in_jsdoc = False

        for line in reversed(lines[-10:]):  # Check last 10 lines
            line = line.strip()
            if line.endswith("*/"):
                in_jsdoc = True
                jsdoc_lines.insert(0, line)
            elif in_jsdoc:
                jsdoc_lines.insert(0, line)
                if line.startswith("/**"):
                    break
            elif line and not line.startswith("//"):
                # Hit non-comment line, stop looking
                break

        if jsdoc_lines and jsdoc_lines[0].startswith("/**"):
            # Clean up JSDoc
            cleaned = []
            for line in jsdoc_lines[1:-1]:  # Skip /** and */
                line = re.sub(r"^\s*\*\s?", "", line)
                if line.strip():
                    cleaned.append(line)
            return "\n".join(cleaned) if cleaned else None

        return None

    def _find_matching_brace(self, content: str, start_pos: int) -> int | None:
        """Find the matching closing brace for an opening brace."""
        if start_pos >= len(content) or content[start_pos] != "{":
            return None

        brace_count = 1
        pos = start_pos + 1

        while pos < len(content) and brace_count > 0:
            char = content[pos]
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            pos += 1

        return pos - 1 if brace_count == 0 else None

    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        """Analyze JavaScript/TypeScript code and return condensed version."""
        try:
            content = self._clean_content(content)
            result = []

            # Determine if this is TypeScript
            is_typescript = any(ext in filename.lower() for ext in [".ts", ".tsx"])
            language = "TypeScript" if is_typescript else "JavaScript"

            # Add header
            result.append(self._format_header(Path(filename), language))

            # Extract imports
            imports = self._extract_imports(content)
            if imports:
                result.extend(self._truncate_list(imports, 10, "imports"))
                result.append("")

            # Extract TypeScript-specific constructs
            if is_typescript:
                interfaces = self._extract_interfaces(content)
                types = self._extract_types(content)

                for interface in interfaces:
                    result.append(self._format_interface(interface))
                    result.append("")

                for type_def in types:
                    result.append(self._format_type(type_def))
                    result.append("")

            # Extract classes and functions
            classes = self._extract_classes(content)
            functions = self._extract_functions(content)

            for cls in classes:
                result.append(self._format_class(cls))
                result.append("")

            for func in functions:
                result.append(self._format_function(func))
                result.append("")

            return "\n".join(result)

        except Exception as e:
            return f"# Error parsing {filename}: {e}"

    def _format_class(self, class_info: dict[str, Any]) -> str:
        """Format a class for output."""
        result = []

        # Add JSDoc if available
        if class_info.get("jsdoc") and self._should_include_docstring():
            result.append(f"/**\n * {class_info['jsdoc']}\n */")

        # Class declaration
        result.append(f"class {class_info['name']} {{")

        # Add methods
        methods = class_info.get("methods", [])
        if methods:
            for method in methods[:10]:  # Limit methods shown
                method_line = f"  {method['name']}({method['params']})"
                if method.get("return_type"):
                    method_line += f": {method['return_type']}"
                method_line += " { ... }"
                result.append(method_line)

            if len(methods) > 10:
                result.append(f"  // ... and {len(methods) - 10} more methods")
        else:
            result.append("  // No methods extracted")

        result.append("}")

        return "\n".join(result)

    def _format_function(self, func_info: dict[str, Any]) -> str:
        """Format a function for output."""
        result = []

        # Add JSDoc if available
        if func_info.get("jsdoc") and self._should_include_docstring():
            result.append(f"/**\n * {func_info['jsdoc']}\n */")

        # Function signature
        indent = " " * func_info.get("indent", 0)
        func_line = f"{indent}function {func_info['name']}({func_info['params']})"

        if func_info.get("return_type"):
            func_line += f": {func_info['return_type']}"

        func_line += " { ... }"
        result.append(func_line)

        return "\n".join(result)

    def _format_interface(self, interface_info: dict[str, Any]) -> str:
        """Format a TypeScript interface for output."""
        result = []

        # Add JSDoc if available
        if interface_info.get("jsdoc") and self._should_include_docstring():
            result.append(f"/**\n * {interface_info['jsdoc']}\n */")

        result.append(f"interface {interface_info['name']} {{ ... }}")

        return "\n".join(result)

    def _format_type(self, type_info: dict[str, Any]) -> str:
        """Format a TypeScript type definition for output."""
        return f"type {type_info['name']} = ..."
