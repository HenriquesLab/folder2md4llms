"""Configuration file analyzer for JSON, YAML, and other structured data formats."""

import json
from pathlib import Path
from typing import Any

import yaml

from .base_code_analyzer import BaseCodeAnalyzer


class ConfigAnalyzer(BaseCodeAnalyzer):
    """Analyzer for configuration files (JSON, YAML, TOML, etc.)."""

    def __init__(self, condense_mode: str = "structure"):
        super().__init__(condense_mode)

    def get_supported_extensions(self) -> set[str]:
        """Get supported file extensions."""
        return {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}

    def analyze_file(self, file_path: Path) -> str | None:
        """Analyze a configuration file and return condensed content."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return self.analyze_code(content, str(file_path))
        except (OSError, UnicodeDecodeError) as e:
            return f"# Error reading file: {e}"

    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        """Analyze configuration content and return condensed version."""
        try:
            file_path = Path(filename)
            extension = file_path.suffix.lower()

            if extension == ".json":
                return self._analyze_json(content, file_path)
            elif extension in [".yaml", ".yml"]:
                return self._analyze_yaml(content, file_path)
            elif extension == ".toml":
                return self._analyze_toml(content, file_path)
            elif extension in [".ini", ".cfg", ".conf"]:
                return self._analyze_ini(content, file_path)
            else:
                return self._analyze_generic_config(content, file_path)

        except Exception as e:
            return f"# Error parsing {filename}: {e}"

    def _analyze_json(self, content: str, file_path: Path) -> str:
        """Analyze JSON configuration file."""
        try:
            data = json.loads(content)
            result = []

            # Add header
            result.append(f"# JSON Configuration Analysis: {file_path.name}")
            result.append(f"# Condensed using mode: {self.condense_mode}")
            result.append(f"# Original file: {file_path}")
            result.append("")

            # Analyze structure
            result.append("## Structure Overview")
            result.append(f"- **Type**: {type(data).__name__}")

            if isinstance(data, dict):
                result.append(f"- **Top-level keys**: {len(data)}")
                result.append("")
                result.extend(self._format_dict_structure(data, max_depth=3))
            elif isinstance(data, list):
                result.append(f"- **Array length**: {len(data)}")
                result.append("")
                result.extend(self._format_array_structure(data, max_depth=2))
            else:
                result.append(f"- **Value**: {str(data)[:100]}...")

            return "\n".join(result)

        except json.JSONDecodeError as e:
            return f"# Invalid JSON: {e}"

    def _analyze_yaml(self, content: str, file_path: Path) -> str:
        """Analyze YAML configuration file."""
        try:
            # Handle multiple documents
            documents = list(yaml.safe_load_all(content))
            result = []

            # Add header
            result.append(f"# YAML Configuration Analysis: {file_path.name}")
            result.append(f"# Condensed using mode: {self.condense_mode}")
            result.append(f"# Original file: {file_path}")
            result.append("")

            if len(documents) > 1:
                result.append(f"## Multiple Documents ({len(documents)} documents)")
                result.append("")

                for i, doc in enumerate(documents[:5]):  # Limit to first 5 docs
                    result.append(f"### Document {i + 1}")
                    if isinstance(doc, dict):
                        result.extend(self._format_dict_structure(doc, max_depth=2))
                    else:
                        result.append(f"- **Type**: {type(doc).__name__}")
                        result.append(f"- **Value**: {str(doc)[:100]}...")
                    result.append("")

                if len(documents) > 5:
                    result.append(f"... and {len(documents) - 5} more documents")
            else:
                data = documents[0] if documents else None

                if data is None:
                    result.append("## Empty Document")
                elif isinstance(data, dict):
                    result.append("## Structure Overview")
                    result.append(f"- **Top-level keys**: {len(data)}")
                    result.append("")
                    result.extend(self._format_dict_structure(data, max_depth=3))
                elif isinstance(data, list):
                    result.append("## Array Structure")
                    result.append(f"- **Array length**: {len(data)}")
                    result.append("")
                    result.extend(self._format_array_structure(data, max_depth=2))
                else:
                    result.append("## Simple Value")
                    result.append(f"- **Type**: {type(data).__name__}")
                    result.append(f"- **Value**: {str(data)[:100]}...")

            return "\n".join(result)

        except yaml.YAMLError as e:
            return f"# Invalid YAML: {e}"

    def _analyze_toml(self, content: str, file_path: Path) -> str:
        """Analyze TOML configuration file."""
        # Basic TOML analysis without importing toml library
        result = []

        # Add header
        result.append(f"# TOML Configuration Analysis: {file_path.name}")
        result.append(f"# Condensed using mode: {self.condense_mode}")
        result.append(f"# Original file: {file_path}")
        result.append("")

        # Extract sections and key-value pairs
        sections: list[tuple[str, list[str]]] = []
        current_section = None
        key_value_pairs: list[str] = []

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Section headers
            if line.startswith("[") and line.endswith("]"):
                if current_section:
                    sections.append((current_section, key_value_pairs[:]))
                current_section = line[1:-1]
                key_value_pairs = []
            # Key-value pairs
            elif "=" in line:
                key = line.split("=")[0].strip()
                key_value_pairs.append(key)

        # Add final section
        if current_section:
            sections.append((current_section, key_value_pairs))

        result.append("## Structure Overview")
        result.append(f"- **Sections**: {len(sections)}")
        result.append("")

        for section_name, keys in sections[:10]:  # Limit sections shown
            result.append(f"### [{section_name}]")
            if keys:
                result.append(f"- **Keys**: {', '.join(keys[:10])}")
                if len(keys) > 10:
                    result.append(f"- **... and {len(keys) - 10} more keys**")
            else:
                result.append("- **No keys found**")
            result.append("")

        if len(sections) > 10:
            result.append(f"... and {len(sections) - 10} more sections")

        return "\n".join(result)

    def _analyze_ini(self, content: str, file_path: Path) -> str:
        """Analyze INI-style configuration file."""
        result = []

        # Add header
        result.append(f"# INI Configuration Analysis: {file_path.name}")
        result.append(f"# Condensed using mode: {self.condense_mode}")
        result.append(f"# Original file: {file_path}")
        result.append("")

        # Parse INI structure
        sections: dict[str, list[str]] = {}
        current_section = "DEFAULT"

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            # Section headers
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                sections[current_section] = []
            # Key-value pairs
            elif "=" in line or ":" in line:
                delimiter = "=" if "=" in line else ":"
                key = line.split(delimiter)[0].strip()
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(key)

        result.append("## Structure Overview")
        result.append(f"- **Sections**: {len(sections)}")
        result.append("")

        for section_name, keys in list(sections.items())[:10]:
            result.append(f"### [{section_name}]")
            if keys:
                result.append(f"- **Keys ({len(keys)})**: {', '.join(keys[:10])}")
                if len(keys) > 10:
                    result.append(f"- **... and {len(keys) - 10} more keys**")
            else:
                result.append("- **No keys found**")
            result.append("")

        if len(sections) > 10:
            result.append(f"... and {len(sections) - 10} more sections")

        return "\n".join(result)

    def _analyze_generic_config(self, content: str, file_path: Path) -> str:
        """Analyze generic configuration file."""
        result = []

        # Add header
        result.append(f"# Configuration Analysis: {file_path.name}")
        result.append(f"# Condensed using mode: {self.condense_mode}")
        result.append(f"# Original file: {file_path}")
        result.append("")

        lines = content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        comment_lines = [
            line
            for line in non_empty_lines
            if line.strip().startswith(("#", "//", ";"))
        ]

        result.append("## File Overview")
        result.append(f"- **Total lines**: {len(lines)}")
        result.append(f"- **Non-empty lines**: {len(non_empty_lines)}")
        result.append(f"- **Comment lines**: {len(comment_lines)}")
        result.append("")

        # Show first few lines as sample
        result.append("## Sample Content (first 10 lines)")
        result.append("```")
        for line in lines[:10]:
            result.append(line)
        result.append("```")

        if len(lines) > 10:
            result.append(f"\n... and {len(lines) - 10} more lines")

        return "\n".join(result)

    def _format_dict_structure(
        self,
        data: dict[str, Any],
        max_depth: int = 3,
        current_depth: int = 0,
        prefix: str = "",
    ) -> list[str]:
        """Format dictionary structure for display."""
        result = []

        if current_depth >= max_depth:
            return [f"{prefix}- **... (max depth reached)**"]

        # Sort keys for consistent output
        sorted_keys = sorted(data.keys()) if isinstance(data, dict) else []

        for _i, key in enumerate(sorted_keys[:20]):  # Limit keys shown
            value = data[key]
            bullet = f"{prefix}- **{key}**"

            if isinstance(value, dict):
                result.append(f"{bullet}: Object with {len(value)} keys")
                if self.condense_mode == "structure" and len(value) <= 5:
                    # Show nested structure for small objects
                    nested = self._format_dict_structure(
                        value, max_depth, current_depth + 1, prefix + "  "
                    )
                    result.extend(nested)
            elif isinstance(value, list):
                result.append(f"{bullet}: Array[{len(value)}]")
                if self.condense_mode == "structure" and len(value) <= 3:
                    # Show array sample for small arrays
                    sample = self._format_array_sample(value, max_items=3)
                    if sample:
                        result.append(f"{prefix}  - Sample: {sample}")
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                result.append(f"{bullet}: {type(value).__name__} = {value_str}")

        if len(sorted_keys) > 20:
            result.append(f"{prefix}- **... and {len(sorted_keys) - 20} more keys**")

        return result

    def _format_array_structure(
        self, data: list[Any], max_depth: int = 2, current_depth: int = 0
    ) -> list[str]:
        """Format array structure for display."""
        result = []

        if not data:
            return ["- **Empty array**"]

        # Analyze array content types
        type_counts: dict[str, int] = {}
        for item in data[:100]:  # Sample first 100 items
            type_name = type(item).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        result.append("### Array Content Types")
        for type_name, count in sorted(type_counts.items()):
            percentage = (count / min(len(data), 100)) * 100
            result.append(f"- **{type_name}**: {count} items ({percentage:.1f}%)")

        # Show samples of different types
        if self.condense_mode == "structure":
            result.append("")
            result.append("### Samples")
            shown_types = set()
            for item in data[:10]:
                type_name = type(item).__name__
                if type_name not in shown_types:
                    sample = self._format_value_sample(item)
                    result.append(f"- **{type_name} example**: {sample}")
                    shown_types.add(type_name)
                    if len(shown_types) >= 5:  # Limit types shown
                        break

        return result

    def _format_array_sample(self, data: list[Any], max_items: int = 3) -> str:
        """Format a sample of array items."""
        if not data:
            return "[]"

        samples = []
        for item in data[:max_items]:
            sample = self._format_value_sample(item)
            samples.append(sample)

        if len(data) > max_items:
            samples.append("...")

        return f"[{', '.join(samples)}]"

    def _format_value_sample(self, value: Any) -> str:
        """Format a single value as a sample."""
        if isinstance(value, str):
            if len(value) > 30:
                return f'"{value[:27]}..."'
            return f'"{value}"'
        elif isinstance(value, int | float | bool):
            return str(value)
        elif isinstance(value, dict):
            return f"{{...}} ({len(value)} keys)"
        elif isinstance(value, list):
            return f"[...] ({len(value)} items)"
        elif value is None:
            return "null"
        else:
            return f"{type(value).__name__}(...)"
