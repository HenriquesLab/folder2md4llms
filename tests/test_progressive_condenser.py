"""Tests for the progressive condenser functionality."""

from pathlib import Path

from folder2md4llms.analyzers.priority_analyzer import PriorityLevel
from folder2md4llms.analyzers.progressive_condenser import (
    CondensingLevel,
    ProgressiveCondenser,
    PythonCodeAnalyzer,
)


class TestPythonCodeAnalyzer:
    """Test the PythonCodeAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PythonCodeAnalyzer()

    def test_extract_class_hierarchy(self):
        """Test class hierarchy extraction."""
        content = """
class BaseClass:
    def base_method(self):
        pass

class DerivedClass(BaseClass):
    def __init__(self):
        super().__init__()

    def derived_method(self):
        pass

@dataclass
class DataClass:
    name: str
"""
        import ast

        tree = ast.parse(content)
        hierarchy = self.analyzer.extract_class_hierarchy(tree)

        assert "BaseClass" in hierarchy
        assert "DerivedClass" in hierarchy
        assert "DataClass" in hierarchy

        assert hierarchy["DerivedClass"]["bases"] == ["BaseClass"]
        assert hierarchy["DerivedClass"]["has_init"] is True
        assert "derived_method" in hierarchy["DerivedClass"]["methods"]
        assert "dataclass" in hierarchy["DataClass"]["decorators"]

    def test_identify_design_patterns(self):
        """Test design pattern identification."""
        singleton_content = """
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
        import ast

        tree = ast.parse(singleton_content)
        patterns = self.analyzer.identify_design_patterns(tree)

        assert any("Singleton" in pattern for pattern in patterns)


class TestProgressiveCondenser:
    """Test the ProgressiveCondenser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.condenser = ProgressiveCondenser()

    def test_condense_with_budget_no_condensing_needed(self):
        """Test when no condensing is needed (enough budget)."""
        content = "def simple_function():\n    return 'hello'"
        file_path = Path("test.py")
        available_tokens = 1000  # More than enough
        priority = PriorityLevel.MEDIUM

        condensed, info = self.condenser.condense_with_budget(
            content, file_path, available_tokens, priority
        )

        assert condensed == content
        assert info["level"] == CondensingLevel.NONE

    def test_condense_with_budget_light_condensing(self):
        """Test light condensing when slightly over budget."""
        content = """
# This is a comment
def function():
    # Another comment
    return "hello"


# More comments
def another_function():
    return "world"
"""
        file_path = Path("test.py")
        available_tokens = 10  # Very limited budget to force condensing
        priority = (
            PriorityLevel.LOW
        )  # Low priority to enable more aggressive condensing

        condensed, info = self.condenser.condense_with_budget(
            content, file_path, available_tokens, priority
        )

        # Should do some level of condensing when budget is very limited
        assert info["level"] != CondensingLevel.NONE
        assert len(condensed) <= len(content)  # Should be same or smaller

    def test_detect_repetitive_patterns(self):
        """Test repetitive pattern detection."""
        content = """
def get_user(id):
    pass

def get_post(id):
    pass

def get_comment(id):
    pass

def get_item(id):
    pass

def set_user(data):
    pass

def set_post(data):
    pass

def set_comment(data):
    pass
"""
        patterns = self.condenser.detect_repetitive_patterns(content, ".py")

        # Should detect get_* and set_* patterns (each appears 3+ times)
        assert len(patterns) >= 1
        pattern_names = [p[0] for p in patterns]
        assert any("ACTION" in name for name in pattern_names)

    def test_create_pattern_summary(self):
        """Test pattern summary creation."""
        patterns = [("get_ACTION_item", 3), ("set_ACTION_item", 2)]
        summary = self.condenser.create_pattern_summary(patterns)

        assert "Pattern Summary:" in summary
        assert "get_ACTION_item pattern repeated 3 times" in summary
        assert "set_ACTION_item pattern repeated 2 times" in summary

    def test_remove_obvious_comments(self):
        """Test obvious comment removal."""
        content = """
# This is an obvious comment
def function():
    # TODO: implement this
    # FIXME: this is broken
    # This is another obvious comment
    return "hello"
"""
        result = self.condenser._remove_obvious_comments(content)

        # Should keep TODO and FIXME comments
        assert "TODO" in result
        assert "FIXME" in result
        # Should remove obvious comments
        assert "obvious comment" not in result

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        content = """
def function():
    pass



def another_function():
    pass
"""
        result = self.condenser._normalize_whitespace(content)

        # Should reduce multiple empty lines to single
        assert "\n\n\n\n" not in result
        # Should remove trailing whitespace
        assert not any(line.endswith(" ") for line in result.split("\n"))

    def test_preserve_api_signatures(self):
        """Test API signature preservation."""
        content = '''
def public_function(arg1, arg2):
    """This is a public function."""
    # Implementation details
    result = arg1 + arg2
    return result

def _private_function():
    """This is private."""
    return "private"

def another_public(data):
    """Another public function."""
    return process(data)
'''
        result = self.condenser._preserve_api_signatures(content)

        # Should preserve public function signatures
        assert "def public_function(arg1, arg2):" in result
        assert "def another_public(data):" in result
        # Should not preserve private functions
        assert "_private_function" not in result

    def test_extract_python_public_api(self):
        """Test Python public API extraction."""
        content = """
class PublicClass:
    def __init__(self):
        pass

    def public_method(self, arg):
        return arg

    def _private_method(self):
        return "private"

def public_function():
    return "public"

def _private_function():
    return "private"
"""
        result = self.condenser._extract_python_public_api(content)

        assert "class PublicClass:" in result
        assert "def public_method(self, arg): ..." in result
        assert "def public_function(): ..." in result
        assert "_private" not in result

    def test_extract_js_public_api(self):
        """Test JavaScript public API extraction."""
        content = """
export function publicFunction() {
    return "public";
}

export const API_KEY = "key";

export default class App {
    render() {
        return "app";
    }
}

function privateFunction() {
    return "private";
}
"""
        result = self.condenser._extract_js_public_api(content)

        assert "export function publicFunction" in result
        assert "export const API_KEY" in result
        assert "export default class App" in result

    def test_extract_java_public_api(self):
        """Test Java public API extraction."""
        content = """
public class UserService {
    public User findById(Long id) {
        return repository.findById(id);
    }

    private void validateUser(User user) {
        // validation logic
    }

    public static List<User> findAll() {
        return repository.findAll();
    }
}
"""
        result = self.condenser._extract_java_public_api(content)

        assert "public class UserService" in result
        assert "public User findById(Long id)" in result
        assert "public static List<User> findAll()" in result
        assert "private void validateUser" not in result

    def test_semantic_condensing_levels(self):
        """Test different levels of semantic condensing."""
        content = '''
def important_function():
    """Important function with documentation."""
    # This is a comment
    result = complex_calculation()
    return result

def _helper_function():
    """Private helper."""
    return "helper"
'''
        file_path = Path("test.py")
        priority = PriorityLevel.HIGH

        # Test light condensing
        light_result = self.condenser._apply_semantic_condensing(
            content, CondensingLevel.LIGHT, file_path, priority
        )
        assert len(light_result) < len(content)

        # Test moderate condensing
        moderate_result = self.condenser._apply_semantic_condensing(
            content, CondensingLevel.MODERATE, file_path, priority
        )
        assert len(moderate_result) < len(light_result)

        # Test heavy condensing
        heavy_result = self.condenser._apply_semantic_condensing(
            content, CondensingLevel.HEAVY, file_path, priority
        )
        assert len(heavy_result) < len(moderate_result)

    def test_condense_function_selectively(self):
        """Test selective function condensing."""
        function_content = '''
def important_function(arg1, arg2):
    """This is an important function.

    Args:
        arg1: First argument
        arg2: Second argument

    Returns:
        Processed result
    """
    # Validate inputs
    if not arg1:
        raise ValueError("arg1 is required")

    # Process data
    result = process_data(arg1, arg2)

    # Return result
    return result
'''

        # Test with high priority - should preserve structure
        high_priority_result = self.condenser.condense_function_selectively(
            function_content, PriorityLevel.HIGH, 100
        )
        assert "def important_function" in high_priority_result
        assert "This is an important function" in high_priority_result

        # Test with low priority - should be more aggressive
        low_priority_result = self.condenser.condense_function_selectively(
            function_content, PriorityLevel.LOW, 100
        )
        assert len(low_priority_result) < len(high_priority_result)

    def test_adjust_condensing_level(self):
        """Test dynamic condensing level adjustment."""
        current_content = "some content"

        # High budget usage should increase condensing
        new_level = self.condenser.adjust_condensing_level(
            current_content, CondensingLevel.LIGHT, 850, 1000
        )
        assert new_level == CondensingLevel.MODERATE

        # Low budget usage should decrease condensing
        new_level = self.condenser.adjust_condensing_level(
            current_content, CondensingLevel.MODERATE, 400, 1000
        )
        assert new_level == CondensingLevel.LIGHT

    def test_generate_smart_statistics(self):
        """Test smart statistics generation."""
        processing_results = {
            "files": [
                {
                    "condensed": True,
                    "compression_ratio": 0.8,
                    "tokens_saved": 100,
                    "priority": "HIGH",
                },
                {
                    "condensed": True,
                    "compression_ratio": 0.6,
                    "tokens_saved": 200,
                    "priority": "MEDIUM",
                },
                {"condensed": False, "priority": "CRITICAL"},
            ]
        }

        stats = self.condenser.generate_smart_statistics(processing_results)

        assert stats["condensing_effectiveness"]["files_condensed"] == 2
        assert stats["condensing_effectiveness"]["tokens_saved"] == 300
        assert stats["condensing_effectiveness"]["average_compression"] == 0.7
        assert stats["priority_distribution"]["HIGH"] == 1
        assert stats["priority_distribution"]["MEDIUM"] == 1
        assert stats["priority_distribution"]["CRITICAL"] == 1

    def test_condensing_stats_tracking(self):
        """Test that condensing statistics are properly tracked."""
        content = "def test(): pass"
        file_path = Path("test.py")

        # Perform condensing operation
        self.condenser.condense_with_budget(
            content, file_path, 50, PriorityLevel.MEDIUM
        )

        stats = self.condenser.get_condensing_stats()

        assert stats["files_processed"] == 1
        assert "condensing_levels_used" in stats
        assert stats["tokens_saved"] >= 0

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty content
        empty_result, info = self.condenser.condense_with_budget(
            "", Path("empty.py"), 100, PriorityLevel.MEDIUM
        )
        assert empty_result == ""
        assert info["level"] == CondensingLevel.NONE

        # Test with very small budget
        tiny_budget_result, info = self.condenser.condense_with_budget(
            "def function(): pass", Path("test.py"), 1, PriorityLevel.LOW
        )
        assert info["level"] == CondensingLevel.MAXIMUM

        # Test with invalid file extension
        result = self.condenser._extract_public_api("content", ".unknown")
        assert isinstance(result, str)  # Should handle gracefully
