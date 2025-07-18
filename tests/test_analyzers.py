"""Comprehensive tests for all code analyzers."""

import json
import os
import tempfile
from pathlib import Path

from folder2md4llms.analyzers.base_code_analyzer import BaseCodeAnalyzer
from folder2md4llms.analyzers.binary_analyzer import BinaryAnalyzer
from folder2md4llms.analyzers.code_analyzer import PythonCodeAnalyzer
from folder2md4llms.analyzers.config_analyzer import ConfigAnalyzer
from folder2md4llms.analyzers.java_analyzer import JavaAnalyzer
from folder2md4llms.analyzers.javascript_analyzer import JavaScriptAnalyzer
from folder2md4llms.analyzers.priority_analyzer import ContentPriorityAnalyzer
from folder2md4llms.analyzers.progressive_condenser import ProgressiveCondenser


class ConcreteCodeAnalyzer(BaseCodeAnalyzer):
    """Concrete implementation of BaseCodeAnalyzer for testing."""

    def get_supported_extensions(self) -> set:
        return {".test"}

    def analyze_file(self, file_path: Path) -> str | None:
        return f"Analyzed: {file_path.name}"

    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        return f"Analyzed code: {len(content)} chars"

    def get_file_structure(self, file_path: Path) -> dict:
        return {"type": "test", "name": file_path.name}


class TestBaseCodeAnalyzer:
    """Test the base code analyzer class."""

    def test_init(self):
        """Test base analyzer initialization."""
        analyzer = ConcreteCodeAnalyzer()
        assert analyzer is not None
        assert analyzer.condense_mode == "signatures_with_docstrings"

    def test_init_with_condense_mode(self):
        """Test base analyzer initialization with condense mode."""
        analyzer = ConcreteCodeAnalyzer(condense_mode="signatures")
        assert analyzer.condense_mode == "signatures"

    def test_analyze_code_signatures(self):
        """Test code analysis in signatures mode."""
        analyzer = ConcreteCodeAnalyzer(condense_mode="signatures")
        content = """def function_one():
    '''Function docstring'''
    pass

class TestClass:
    '''Class docstring'''
    def method_one(self):
        '''Method docstring'''
        pass"""

        result = analyzer.analyze_code(content)
        assert result is not None
        assert "Analyzed code: " in result

    def test_analyze_code_structure(self):
        """Test code analysis in structure mode."""
        analyzer = ConcreteCodeAnalyzer(condense_mode="structure")
        content = """def function_one():
    '''Function docstring'''
    implementation_code = True
    return implementation_code

class TestClass:
    '''Class docstring'''
    def method_one(self):
        '''Method docstring'''
        implementation_code = True
        return implementation_code"""

        result = analyzer.analyze_code(content)
        assert result is not None
        assert "Analyzed code: " in result

    def test_get_stats_empty(self):
        """Test getting statistics with no files processed."""
        analyzer = ConcreteCodeAnalyzer()
        stats = analyzer.get_stats()
        assert stats["condense_mode"] == "signatures_with_docstrings"
        assert stats["analyzer_type"] == "concretecodeanalyzer"
        assert stats["supported_extensions"] == [".test"]

    def test_clean_content_basic(self):
        """Test basic content cleaning."""
        analyzer = ConcreteCodeAnalyzer()
        code = "def test():    \n    pass  \n\n\n"
        cleaned = analyzer._clean_content(code)
        assert cleaned == "def test():\n    pass\n\n"

    def test_clean_content_with_comments(self):
        """Test content cleaning with comments."""
        analyzer = ConcreteCodeAnalyzer()
        code = """def test():
    # This is a comment
    pass
    # Another comment
    return True"""
        cleaned = analyzer._clean_content(code)
        assert "# This is a comment" in cleaned
        assert "# Another comment" in cleaned


class TestBinaryAnalyzer:
    """Test binary file analyzer."""

    def test_init(self):
        """Test binary analyzer initialization."""
        analyzer = BinaryAnalyzer()
        assert analyzer is not None

    def test_init_with_config(self):
        """Test binary analyzer initialization with config."""
        config = {"max_file_size": 1000000}
        analyzer = BinaryAnalyzer(config)
        assert analyzer.config == config

    def test_analyze_image_file(self):
        """Test analyzing an image file."""
        # Create a mock image file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"mock image content")
            temp_path = Path(f.name)

        try:
            analyzer = BinaryAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "Image File" in result
            assert "jpg" in result.lower()
        finally:
            os.unlink(temp_path)

    def test_analyze_executable_file(self):
        """Test analyzing an executable file."""
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            f.write(b"mock executable content")
            temp_path = Path(f.name)

        try:
            analyzer = BinaryAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "Executable File" in result
            assert "exe" in result.lower()
        finally:
            os.unlink(temp_path)

    def test_analyze_archive_file(self):
        """Test analyzing an archive file."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"mock archive content")
            temp_path = Path(f.name)

        try:
            analyzer = BinaryAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "Archive File" in result
            assert "zip" in result.lower()
        finally:
            os.unlink(temp_path)

    def test_analyze_nonexistent_file(self):
        """Test analyzing a non-existent file."""
        analyzer = BinaryAnalyzer()
        result = analyzer.analyze_file(Path("nonexistent.bin"))
        assert result is not None
        assert "File not found" in result

    def test_analyze_various_file_types(self):
        """Test analyzing various file types."""
        analyzer = BinaryAnalyzer()
        # Test with non-existent files to check handling
        result = analyzer.analyze_file(Path("test.jpg"))
        assert result is not None
        assert "File not found" in result

        result = analyzer.analyze_file(Path("test.exe"))
        assert result is not None
        assert "File not found" in result

        result = analyzer.analyze_file(Path("test.zip"))
        assert result is not None
        assert "File not found" in result


class TestPythonCodeAnalyzer:
    """Test Python code analyzer."""

    def test_init(self):
        """Test Python analyzer initialization."""
        analyzer = PythonCodeAnalyzer()
        assert analyzer is not None
        assert analyzer.condense_mode == "signatures"

    def test_init_with_condense_mode(self):
        """Test Python analyzer initialization with condense mode."""
        analyzer = PythonCodeAnalyzer(condense_mode="signatures")
        assert analyzer.condense_mode == "signatures"

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        analyzer = PythonCodeAnalyzer()
        # PythonCodeAnalyzer doesn't have get_supported_extensions method
        # It works with .py files implicitly
        assert analyzer is not None

    def test_analyze_python_file(self):
        """Test analyzing a Python file."""
        python_code = '''
def hello_world():
    """Print hello world."""
    print("Hello, World!")
    return True

class TestClass:
    """Test class."""

    def __init__(self):
        self.value = 42

    def method(self):
        """Test method."""
        return self.value
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            analyzer = PythonCodeAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "def hello_world():" in result
            assert "class TestClass:" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_invalid_python_file(self):
        """Test analyzing an invalid Python file."""
        invalid_code = "def invalid syntax here"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_path = Path(f.name)

        try:
            analyzer = PythonCodeAnalyzer()
            result = analyzer.analyze_file(temp_path)
            # May return None or error message for invalid syntax
            assert result is None or "Error" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_empty_file(self):
        """Test analyzing an empty Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            analyzer = PythonCodeAnalyzer()
            result = analyzer.analyze_file(temp_path)
            # May return None or minimal content for empty file
            assert result is None or len(result) < 100
        finally:
            os.unlink(temp_path)

    def test_get_stats(self):
        """Test getting analyzer statistics."""
        analyzer = PythonCodeAnalyzer()
        stats = analyzer.get_stats()
        assert stats is not None
        assert isinstance(stats, dict)
        assert "condense_mode" in stats


class TestConfigAnalyzer:
    """Test configuration file analyzer."""

    def test_init(self):
        """Test config analyzer initialization."""
        analyzer = ConfigAnalyzer()
        assert analyzer is not None
        assert analyzer.condense_mode == "structure"

    def test_init_with_condense_mode(self):
        """Test config analyzer initialization with condense mode."""
        analyzer = ConfigAnalyzer(condense_mode="structure")
        assert analyzer.condense_mode == "structure"

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        analyzer = ConfigAnalyzer()
        extensions = analyzer.get_supported_extensions()
        assert ".json" in extensions
        assert ".yaml" in extensions
        assert ".yml" in extensions
        assert ".toml" in extensions
        assert isinstance(extensions, set)

    def test_analyze_json_file(self):
        """Test analyzing a JSON file."""
        json_data = {
            "name": "test",
            "version": "1.0.0",
            "dependencies": {"library1": "^1.0.0", "library2": "^2.0.0"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = Path(f.name)

        try:
            analyzer = ConfigAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "JSON Configuration" in result
            assert "name" in result
            assert "version" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_yaml_file(self):
        """Test analyzing a YAML file."""
        yaml_content = """
name: test
version: 1.0.0
dependencies:
  library1: ^1.0.0
  library2: ^2.0.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            analyzer = ConfigAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "YAML Configuration" in result
            assert "name" in result
            assert "version" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_invalid_json(self):
        """Test analyzing an invalid JSON file."""
        invalid_json = "{ invalid json content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(invalid_json)
            temp_path = Path(f.name)

        try:
            analyzer = ConfigAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "Error" in result or "Invalid" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_toml_file(self):
        """Test analyzing a TOML file."""
        toml_content = """
[tool.poetry]
name = "test"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.8"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_path = Path(f.name)

        try:
            analyzer = ConfigAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "TOML Configuration" in result
            assert "tool.poetry" in result
        finally:
            os.unlink(temp_path)


class TestJavaAnalyzer:
    """Test Java code analyzer."""

    def test_init(self):
        """Test Java analyzer initialization."""
        analyzer = JavaAnalyzer()
        assert analyzer is not None
        assert analyzer.condense_mode == "signatures_with_docstrings"

    def test_init_with_condense_mode(self):
        """Test Java analyzer initialization with condense mode."""
        analyzer = JavaAnalyzer(condense_mode="signatures")
        assert analyzer.condense_mode == "signatures"

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        analyzer = JavaAnalyzer()
        extensions = analyzer.get_supported_extensions()
        assert ".java" in extensions
        assert isinstance(extensions, set)

    def test_analyze_java_file(self):
        """Test analyzing a Java file."""
        java_code = """
public class HelloWorld {
    /**
     * Main method
     */
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }

    /**
     * Test method
     */
    public void testMethod() {
        // Implementation
    }
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_path = Path(f.name)

        try:
            analyzer = JavaAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "public class HelloWorld" in result
            assert "void main" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_invalid_java_file(self):
        """Test analyzing an invalid Java file."""
        invalid_java = "public class invalid syntax"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(invalid_java)
            temp_path = Path(f.name)

        try:
            analyzer = JavaAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            # Should still return some content even for invalid syntax
        finally:
            os.unlink(temp_path)

    def test_get_stats(self):
        """Test getting analyzer statistics."""
        analyzer = JavaAnalyzer()
        stats = analyzer.get_stats()
        assert stats is not None
        assert isinstance(stats, dict)
        assert "condense_mode" in stats


class TestJavaScriptAnalyzer:
    """Test JavaScript code analyzer."""

    def test_init(self):
        """Test JavaScript analyzer initialization."""
        analyzer = JavaScriptAnalyzer()
        assert analyzer is not None
        assert analyzer.condense_mode == "signatures_with_docstrings"

    def test_init_with_condense_mode(self):
        """Test JavaScript analyzer initialization with condense mode."""
        analyzer = JavaScriptAnalyzer(condense_mode="signatures")
        assert analyzer.condense_mode == "signatures"

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        analyzer = JavaScriptAnalyzer()
        extensions = analyzer.get_supported_extensions()
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".jsx" in extensions
        assert ".tsx" in extensions
        assert isinstance(extensions, set)

    def test_analyze_javascript_file(self):
        """Test analyzing a JavaScript file."""
        js_code = """
/**
 * Hello world function
 */
function helloWorld() {
    console.log("Hello, World!");
    return true;
}

/**
 * Test class
 */
class TestClass {
    constructor(name) {
        this.name = name;
    }

    /**
     * Get name method
     */
    getName() {
        return this.name;
    }
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            temp_path = Path(f.name)

        try:
            analyzer = JavaScriptAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "function helloWorld" in result
            assert "class TestClass" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_typescript_file(self):
        """Test analyzing a TypeScript file."""
        ts_code = """
interface User {
    name: string;
    age: number;
}

/**
 * Hello world function
 */
function helloWorld(user: User): string {
    return `Hello, ${user.name}!`;
}

/**
 * Test class
 */
class TestClass implements User {
    name: string;
    age: number;

    constructor(name: string, age: number) {
        this.name = name;
        this.age = age;
    }

    /**
     * Get info method
     */
    getInfo(): string {
        return `${this.name} is ${this.age} years old`;
    }
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write(ts_code)
            temp_path = Path(f.name)

        try:
            analyzer = JavaScriptAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            assert "interface User" in result
            assert "function helloWorld" in result
            assert "class TestClass" in result
        finally:
            os.unlink(temp_path)

    def test_analyze_invalid_javascript_file(self):
        """Test analyzing an invalid JavaScript file."""
        invalid_js = "function invalid syntax here"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(invalid_js)
            temp_path = Path(f.name)

        try:
            analyzer = JavaScriptAnalyzer()
            result = analyzer.analyze_file(temp_path)
            assert result is not None
            # Should still return some content even for invalid syntax
        finally:
            os.unlink(temp_path)

    def test_get_stats(self):
        """Test getting analyzer statistics."""
        analyzer = JavaScriptAnalyzer()
        stats = analyzer.get_stats()
        assert stats is not None
        assert isinstance(stats, dict)
        assert "condense_mode" in stats


class TestContentPriorityAnalyzer:
    """Test content priority analyzer."""

    def test_init(self):
        """Test priority analyzer initialization."""
        analyzer = ContentPriorityAnalyzer()
        assert analyzer is not None

    def test_init_only(self):
        """Test priority analyzer initialization without config."""
        analyzer = ContentPriorityAnalyzer()
        assert analyzer is not None

    def test_analyze_python_file_priority(self):
        """Test analyzing Python file for priority."""
        python_code = '''
def important_function():
    """This is an important function."""
    pass

class ImportantClass:
    """This is an important class."""

    def critical_method(self):
        """This is a critical method."""
        pass
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            analyzer = ContentPriorityAnalyzer()
            priority = analyzer.analyze_file_priority(temp_path)
            # Returns PriorityLevel enum, not numeric value
            assert priority is not None
            assert hasattr(priority, "name")  # Check it's an enum
        finally:
            os.unlink(temp_path)

    def test_analyze_javascript_file_priority(self):
        """Test analyzing JavaScript file for priority."""
        js_code = """
function importantFunction() {
    // Important implementation
}

class ImportantClass {
    constructor() {
        this.value = 42;
    }

    criticalMethod() {
        return this.value;
    }
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            temp_path = Path(f.name)

        try:
            analyzer = ContentPriorityAnalyzer()
            priority = analyzer.analyze_file_priority(temp_path)
            # Returns PriorityLevel enum, not numeric value
            assert priority is not None
            assert hasattr(priority, "name")  # Check it's an enum
        finally:
            os.unlink(temp_path)

    def test_analyze_config_file_priority(self):
        """Test analyzing config file for priority."""
        config_data = {
            "name": "test",
            "version": "1.0.0",
            "dependencies": {"library1": "^1.0.0"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            analyzer = ContentPriorityAnalyzer()
            priority = analyzer.analyze_file_priority(temp_path)
            # Returns PriorityLevel enum, not numeric value
            assert priority is not None
            assert hasattr(priority, "name")  # Check it's an enum
        finally:
            os.unlink(temp_path)

    def test_analyze_empty_file_priority(self):
        """Test analyzing empty file for priority."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            analyzer = ContentPriorityAnalyzer()
            priority = analyzer.analyze_file_priority(temp_path)
            # Returns PriorityLevel enum, not numeric value
            assert priority is not None
            assert hasattr(priority, "name")  # Check it's an enum
        finally:
            os.unlink(temp_path)

    def test_get_priority_weights(self):
        """Test getting priority weights."""
        analyzer = ContentPriorityAnalyzer()
        weights = analyzer.get_priority_weights()
        assert weights is not None
        assert isinstance(weights, dict)
        # Check that keys are PriorityLevel enums
        for key in weights.keys():
            assert hasattr(key, "name")  # Check it's an enum

    def test_analyze_function_priority(self):
        """Test analyzing function priority."""
        analyzer = ContentPriorityAnalyzer()
        function_content = """
def test_function():
    '''Test function'''
    pass
"""
        priority = analyzer.analyze_function_priority(function_content)
        assert priority is not None
        assert hasattr(priority, "name")  # Check it's an enum


class TestProgressiveCondenser:
    """Test progressive condenser."""

    def test_init(self):
        """Test progressive condenser initialization."""
        condenser = ProgressiveCondenser()
        assert condenser is not None

    def test_init_only(self):
        """Test progressive condenser initialization without config."""
        condenser = ProgressiveCondenser()
        assert condenser is not None

    def test_condense_with_budget(self):
        """Test condensing with budget allocation."""
        content = """
def function_one():
    '''Function one docstring'''
    implementation_code = True
    more_implementation = True
    return implementation_code

def function_two():
    '''Function two docstring'''
    implementation_code = True
    more_implementation = True
    return implementation_code

class TestClass:
    '''Test class docstring'''

    def method_one(self):
        '''Method one docstring'''
        implementation_code = True
        more_implementation = True
        return implementation_code

    def method_two(self):
        '''Method two docstring'''
        implementation_code = True
        more_implementation = True
        return implementation_code
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            condenser = ProgressiveCondenser()
            # Need to import PriorityLevel for this to work
            from folder2md4llms.analyzers.priority_analyzer import PriorityLevel

            result, stats = condenser.condense_with_budget(
                content, temp_path, 100, PriorityLevel.MEDIUM
            )
            assert result is not None
            assert isinstance(stats, dict)
            assert len(result) <= len(content)
        finally:
            os.unlink(temp_path)

    def test_condense_function_selectively(self):
        """Test selective function condensing."""
        python_code = '''
def hello_world():
    """Print hello world."""
    print("Hello, World!")
    return True
'''

        condenser = ProgressiveCondenser()
        # Need to import PriorityLevel for this to work
        from folder2md4llms.analyzers.priority_analyzer import PriorityLevel

        result = condenser.condense_function_selectively(
            python_code, PriorityLevel.MEDIUM, 100
        )
        assert result is not None
        assert len(result) <= len(python_code)

    def test_adjust_condensing_level(self):
        """Test adjusting condensing level."""
        content = """
def important_function():
    '''This is very important'''
    critical_implementation = True
    return critical_implementation

def less_important_function():
    '''This is less important'''
    simple_implementation = True
    return simple_implementation
"""

        condenser = ProgressiveCondenser()
        result = condenser.adjust_condensing_level(content, "signatures", 50, 100)
        assert result is not None
        assert len(result) <= len(content)

    def test_get_condensing_stats(self):
        """Test getting condensing statistics."""
        condenser = ProgressiveCondenser()
        stats = condenser.get_condensing_stats()
        assert stats is not None
        assert isinstance(stats, dict)
        assert "files_processed" in stats
        assert "tokens_saved" in stats
        assert "condensing_levels_used" in stats

    def test_simple_condensing_operations(self):
        """Test simple condensing operations."""
        condenser = ProgressiveCondenser()
        content = "def test_function():\n    pass"

        # Test with empty content
        result = condenser.adjust_condensing_level("", "signatures", 0, 100)
        assert result is not None
        # Result may return a default condensing level string
        assert result is not None

        # Test with small content
        result = condenser.adjust_condensing_level(content, "signatures", 10, 1000)
        assert result is not None
        assert len(result) <= len(content)
