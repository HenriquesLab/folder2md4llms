"""Java code analyzer for extracting class and method signatures."""

import re
from pathlib import Path
from typing import Any

from .base_code_analyzer import RegexBasedAnalyzer


class JavaAnalyzer(RegexBasedAnalyzer):
    """Analyzer for Java source files."""

    def __init__(self, condense_mode: str = "signatures_with_docstrings"):
        super().__init__(condense_mode)
        self._compile_patterns()

    def get_supported_extensions(self) -> set[str]:
        """Get supported file extensions."""
        return {".java"}

    def _compile_patterns(self) -> None:
        """Compile regex patterns for Java."""
        # Package declaration
        self.package_pattern = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)

        # Import statements
        self.import_pattern = re.compile(
            r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;", re.MULTILINE
        )

        # Class declarations (including interfaces, enums, records)
        self.class_pattern = re.compile(
            r"(?:^|\n)\s*(?:(?:public|private|protected|static|final|abstract)\s+)*"
            r"(class|interface|enum|record)\s+(\w+)"
            r"(?:\s+extends\s+[\w<>.,\s]+)?"
            r"(?:\s+implements\s+[\w<>.,\s]+)?\s*\{",
            re.MULTILINE,
        )

        # Method declarations
        self.method_pattern = re.compile(
            r"(?:^|\n)(\s*)(?:(?:public|private|protected|static|final|abstract|synchronized|native)\s+)*"
            r"(?:<[^>]+>\s+)?"  # Generic type parameters
            r"([\w<>[\].,\s]+)\s+"  # Return type
            r"(\w+)\s*"  # Method name
            r"\(([^)]*)\)"  # Parameters
            r"(?:\s+throws\s+[\w.,\s]+)?"  # Throws clause
            r"\s*(?:\{|;)",  # Method body start or abstract method
            re.MULTILINE,
        )

        # Field declarations
        self.field_pattern = re.compile(
            r"(?:^|\n)(\s*)(?:(?:public|private|protected|static|final|volatile|transient)\s+)*"
            r"([\w<>[\].,\s]+)\s+"  # Type
            r"(\w+)"  # Field name
            r"(?:\s*=\s*[^;]+)?"  # Optional initialization
            r"\s*;",
            re.MULTILINE,
        )

        # Annotation declarations
        self.annotation_pattern = re.compile(
            r"(?:^|\n)\s*@(\w+)(?:\([^)]*\))?", re.MULTILINE
        )

        # Javadoc comments
        self.javadoc_pattern = re.compile(
            r"/\*\*\s*\n((?:\s*\*.*\n)*)\s*\*/", re.MULTILINE
        )

    def _extract_package(self, content: str) -> str | None:
        """Extract package declaration."""
        if self.package_pattern:
            match = self.package_pattern.search(content)
            if match:
                return f"package {match.group(1)};"
        return None

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements."""
        imports = []

        if self.import_pattern:
            for match in self.import_pattern.finditer(content):
                import_stmt = f"import {match.group(1)};"
                imports.append(import_stmt)

        return imports[:20]  # Limit to first 20 imports

    def _extract_classes(self, content: str) -> list[dict[str, Any]]:
        """Extract class, interface, enum, and record definitions."""
        classes = []

        if self.class_pattern:
            for match in self.class_pattern.finditer(content):
                class_type = match.group(1)  # class, interface, enum, record
                class_name = match.group(2)
                start_pos = match.start()

                # Extract Javadoc if available
                preceding_content = content[:start_pos]
                javadoc = self._extract_preceding_javadoc(preceding_content)

                # Extract annotations
                annotations = self._extract_preceding_annotations(preceding_content)

                # Find class body
                class_start = match.end()
                class_end = self._find_matching_brace(content, class_start - 1)
                class_body = content[class_start:class_end] if class_end else ""

                # Extract methods and fields from class body
                methods = self._extract_methods_from_body(class_body)
                fields = self._extract_fields_from_body(class_body)

                classes.append(
                    {
                        "type": class_type,
                        "name": class_name,
                        "javadoc": javadoc,
                        "annotations": annotations,
                        "methods": methods,
                        "fields": fields,
                        "line": content[:start_pos].count("\n") + 1,
                    }
                )

        return classes

    def _extract_methods_from_body(self, class_body: str) -> list[dict[str, Any]]:
        """Extract method definitions from class body."""
        methods = []

        if self.method_pattern:
            for match in self.method_pattern.finditer(class_body):
                indent = match.group(1)
                return_type = match.group(2).strip()
                method_name = match.group(3)
                parameters = match.group(4).strip()

                # Extract preceding Javadoc
                start_pos = match.start()
                preceding_content = class_body[:start_pos]
                javadoc = self._extract_preceding_javadoc(preceding_content)

                # Extract annotations
                annotations = self._extract_preceding_annotations(preceding_content)

                methods.append(
                    {
                        "name": method_name,
                        "return_type": return_type,
                        "parameters": parameters,
                        "javadoc": javadoc,
                        "annotations": annotations,
                        "indent": len(indent),
                    }
                )

        return methods

    def _extract_fields_from_body(self, class_body: str) -> list[dict[str, Any]]:
        """Extract field declarations from class body."""
        fields = []

        if self.field_pattern:
            for match in self.field_pattern.finditer(class_body):
                indent = match.group(1)
                field_type = match.group(2).strip()
                field_name = match.group(3)

                # Extract preceding annotations
                start_pos = match.start()
                preceding_content = class_body[:start_pos]
                annotations = self._extract_preceding_annotations(preceding_content)

                fields.append(
                    {
                        "name": field_name,
                        "type": field_type,
                        "annotations": annotations,
                        "indent": len(indent),
                    }
                )

        return fields[:10]  # Limit fields shown

    def _extract_preceding_javadoc(self, preceding_content: str) -> str | None:
        """Extract Javadoc comment that precedes the current position."""
        if not self.javadoc_pattern or not self._should_include_docstring():
            return None

        # Look for Javadoc in the last few lines before the current position
        lines = preceding_content.split("\n")

        # Work backwards to find Javadoc
        javadoc_lines: list[str] = []
        in_javadoc = False

        for line in reversed(lines[-15:]):  # Check last 15 lines
            line = line.strip()
            if line.endswith("*/"):
                in_javadoc = True
                javadoc_lines.insert(0, line)
            elif in_javadoc:
                javadoc_lines.insert(0, line)
                if line.startswith("/**"):
                    break
            elif line and not line.startswith("//") and not line.startswith("@"):
                # Hit non-comment, non-annotation line, stop looking
                break

        if javadoc_lines and javadoc_lines[0].startswith("/**"):
            # Clean up Javadoc
            cleaned = []
            for line in javadoc_lines[1:-1]:  # Skip /** and */
                line = re.sub(r"^\s*\*\s?", "", line)
                if line.strip():
                    cleaned.append(line.strip())
            return "\n".join(cleaned) if cleaned else None

        return None

    def _extract_preceding_annotations(self, preceding_content: str) -> list[str]:
        """Extract annotations that precede the current position."""
        annotations: list[str] = []

        if not self.annotation_pattern:
            return annotations

        # Look for annotations in the last few lines
        lines = preceding_content.split("\n")

        for line in reversed(lines[-10:]):  # Check last 10 lines
            line = line.strip()
            if line.startswith("@"):
                annotations.insert(0, line)
            elif line and not line.startswith("//") and not line.startswith("/*"):
                # Hit non-comment line that's not an annotation, stop
                break

        return annotations

    def _find_matching_brace(self, content: str, start_pos: int) -> int | None:
        """Find the matching closing brace for an opening brace."""
        if start_pos >= len(content) or content[start_pos] != "{":
            return None

        brace_count = 1
        pos = start_pos + 1
        in_string = False
        in_char = False
        escape_next = False

        while pos < len(content) and brace_count > 0:
            char = content[pos]

            if escape_next:
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif char == '"' and not in_char:
                in_string = not in_string
            elif char == "'" and not in_string:
                in_char = not in_char
            elif not in_string and not in_char:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1

            pos += 1

        return pos - 1 if brace_count == 0 else None

    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        """Analyze Java code and return condensed version."""
        try:
            content = self._clean_content(content)
            result = []

            # Add header
            result.append(self._format_header(Path(filename), "Java"))

            # Extract package
            package = self._extract_package(content)
            if package:
                result.append(package)
                result.append("")

            # Extract imports
            imports = self._extract_imports(content)
            if imports:
                result.extend(self._truncate_list(imports, 15, "imports"))
                result.append("")

            # Extract classes
            classes = self._extract_classes(content)
            for cls in classes:
                result.append(self._format_class(cls))
                result.append("")

            return "\n".join(result)

        except Exception as e:
            return f"# Error parsing {filename}: {e}"

    def _format_class(self, class_info: dict[str, Any]) -> str:
        """Format a class for output."""
        result = []

        # Add Javadoc if available
        if class_info.get("javadoc") and self._should_include_docstring():
            javadoc_lines = class_info["javadoc"].split("\n")
            result.append("/**")
            for line in javadoc_lines:
                result.append(f" * {line}")
            result.append(" */")

        # Add annotations
        for annotation in class_info.get("annotations", []):
            result.append(annotation)

        # Class declaration
        class_type = class_info.get("type", "class")
        result.append(f"public {class_type} {class_info['name']} {{")

        # Add fields
        fields = class_info.get("fields", [])
        if fields:
            result.append("    // Fields")
            for field in fields:
                field_line = "    "
                # Add field annotations
                for annotation in field.get("annotations", []):
                    result.append(f"    {annotation}")

                field_line += f"{field['type']} {field['name']};"
                result.append(field_line)
            result.append("")

        # Add methods
        methods = class_info.get("methods", [])
        if methods:
            result.append("    // Methods")
            for method in methods[:10]:  # Limit methods shown
                # Add method annotations
                for annotation in method.get("annotations", []):
                    result.append(f"    {annotation}")

                # Add method Javadoc if available
                if method.get("javadoc") and self._should_include_docstring():
                    javadoc_lines = method["javadoc"].split("\n")
                    result.append("    /**")
                    for line in javadoc_lines:
                        result.append(f"     * {line}")
                    result.append("     */")

                method_line = f"    {method['return_type']} {method['name']}({method['parameters']})"
                if self.condense_mode == "signatures":
                    method_line += ";"
                else:
                    method_line += " { ... }"

                result.append(method_line)
                result.append("")

            if len(methods) > 10:
                result.append(f"    // ... and {len(methods) - 10} more methods")

        result.append("}")

        return "\n".join(result)
