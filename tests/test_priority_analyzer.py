"""Tests for the priority analyzer functionality."""

import tempfile
from pathlib import Path

from folder2md4llms.analyzers.priority_analyzer import (
    ContentPriorityAnalyzer,
    PriorityLevel,
)


class TestContentPriorityAnalyzer:
    """Test the ContentPriorityAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ContentPriorityAnalyzer()

    def test_framework_detection_django(self):
        """Test that Django framework detection works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "manage.py").touch()
            Path(tmpdir, "settings.py").touch()
            framework = self.analyzer.detect_framework(Path(tmpdir))
            assert framework == "django"

    def test_framework_detection_flask(self):
        """Test that Flask framework detection works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create requirements.txt with flask
            requirements = Path(tmpdir, "requirements.txt")
            requirements.write_text("flask>=2.0.0\nclick>=8.0.0")
            framework = self.analyzer.detect_framework(Path(tmpdir))
            assert framework == "flask"

    def test_framework_detection_react(self):
        """Test that React framework detection works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json with react
            package_json = Path(tmpdir, "package.json")
            package_json.write_text('{"dependencies": {"react": "^18.0.0"}}')
            framework = self.analyzer.detect_framework(Path(tmpdir))
            assert framework == "react"

    def test_framework_detection_nextjs(self):
        """Test that Next.js framework detection works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create next.config.js to detect Next.js
            next_config = Path(tmpdir, "next.config.js")
            next_config.write_text("module.exports = {}")
            framework = self.analyzer.detect_framework(Path(tmpdir))
            assert framework == "nextjs"

    def test_critical_file_patterns(self):
        """Test that critical file patterns are detected correctly."""
        critical_files = [
            "main.py",
            "app.py",
            "__main__.py",
            "server.py",
            "index.js",
            "Main.java",
        ]

        for filename in critical_files:
            file_path = Path(filename)
            priority = self.analyzer.analyze_file_priority(file_path)
            assert priority == PriorityLevel.CRITICAL, f"Failed for {filename}"

    def test_high_priority_patterns(self):
        """Test that high priority file patterns are detected correctly."""
        high_priority_files = [
            "__init__.py",
            "config.py",
            "settings.py",
            "constants.py",
            "user_controller.py",
            "api_service.js",
        ]

        for filename in high_priority_files:
            file_path = Path(filename)
            priority = self.analyzer.analyze_file_priority(file_path)
            assert priority == PriorityLevel.HIGH, f"Failed for {filename}"

    def test_entry_point_content_detection(self):
        """Test that entry point patterns in content are detected."""
        content_with_main = """
if __name__ == "__main__":
    app.run(debug=True)
"""
        priority = self.analyzer._analyze_python_content(content_with_main)
        assert priority == PriorityLevel.CRITICAL

    def test_api_endpoint_detection(self):
        """Test that API endpoint patterns are detected."""
        flask_content = """
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users)
"""
        priority = self.analyzer._analyze_python_content(flask_content)
        assert priority == PriorityLevel.CRITICAL

        fastapi_content = """
@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
"""
        priority = self.analyzer._analyze_python_content(fastapi_content)
        assert priority == PriorityLevel.CRITICAL

    def test_configuration_patterns(self):
        """Test that configuration patterns are detected."""
        config_content = """
DATABASE_URL = os.environ.get("DATABASE_URL")
API_KEY = config["api_key"]
SECRET_KEY = settings.SECRET_KEY
"""
        priority = self.analyzer._analyze_python_content(config_content)
        assert priority == PriorityLevel.HIGH

    def test_contextual_priority_adjustment(self):
        """Test that file context affects priority correctly."""
        # Test files in 'core' directory get upgraded
        core_file = Path("src/core/utils.py")
        base_priority = PriorityLevel.MEDIUM
        adjusted = self.analyzer.adjust_priority_by_context(core_file, base_priority)
        assert adjusted == PriorityLevel.HIGH

    def test_import_frequency_analysis(self):
        """Test import frequency scoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create test files with known import patterns
            (repo_path / "utils.py").write_text("def helper(): pass")
            (repo_path / "main.py").write_text("from utils import helper")
            (repo_path / "app.py").write_text("from utils import helper")

            import_scores = self.analyzer.analyze_import_frequency(repo_path)

            # utils.py should have a high score since it's imported by multiple files
            utils_path = repo_path / "utils.py"
            assert utils_path in import_scores
            assert import_scores[utils_path] > 0

    def test_javascript_content_analysis(self):
        """Test JavaScript/TypeScript content analysis."""
        # Test Express.js route detection
        express_content = """
app.get('/api/users', (req, res) => {
    res.json(users);
});
"""
        priority = self.analyzer._analyze_js_content(express_content)
        assert priority == PriorityLevel.CRITICAL

        # Test React component detection
        react_content = """
export default function App() {
    return <div>Hello World</div>;
}
"""
        priority = self.analyzer._analyze_js_content(react_content)
        assert priority == PriorityLevel.HIGH  # Default export gets HIGH priority

        # Test Next.js page detection
        nextjs_content = """
export default function HomePage() {
    return <div>Home</div>;
}

export async function getServerSideProps() {
    return { props: {} };
}
"""
        priority = self.analyzer._analyze_js_content(nextjs_content)
        assert priority == PriorityLevel.HIGH

    def test_java_content_analysis(self):
        """Test Java content analysis."""
        # Test main method detection
        java_main = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
"""
        priority = self.analyzer._analyze_java_content(java_main)
        assert priority == PriorityLevel.CRITICAL

        # Test Spring Boot annotations
        spring_content = """
@RestController
@RequestMapping("/api")
public class UserController {
    @GetMapping("/users")
    public List<User> getUsers() {
        return userService.findAll();
    }
}
"""
        priority = self.analyzer._analyze_java_content(spring_content)
        assert priority == PriorityLevel.CRITICAL

        # Test JAX-RS annotations
        jaxrs_content = """
@Path("/users")
public class UserResource {
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response getUsers() {
        return Response.ok().build();
    }
}
"""
        priority = self.analyzer._analyze_java_content(jaxrs_content)
        assert priority == PriorityLevel.CRITICAL

    def test_code_complexity_analysis(self):
        """Test code complexity scoring."""
        simple_content = """
def simple_function():
    return "hello"
"""
        complexity = self.analyzer.analyze_code_complexity(
            simple_content, Path("test.py")
        )
        assert 0.0 <= complexity <= 1.0

        complex_content = """
class ComplexClass:
    @decorator
    def method1(self):
        pass

    @another_decorator
    async def method2(self):
        pass

class AnotherClass:
    def __init__(self):
        pass
"""
        complexity = self.analyzer.analyze_code_complexity(
            complex_content, Path("test.py")
        )
        assert complexity > 0.3  # Should be higher for complex code

    def test_framework_pattern_application(self):
        """Test that framework-specific patterns are applied correctly."""
        # Test Django patterns
        django_file = Path("views.py")
        priority = self.analyzer._apply_framework_patterns(django_file, "django")
        assert priority == PriorityLevel.HIGH

        django_critical = Path("settings.py")
        priority = self.analyzer._apply_framework_patterns(django_critical, "django")
        assert priority == PriorityLevel.CRITICAL

        # Test Flask patterns
        flask_file = Path("app.py")
        priority = self.analyzer._apply_framework_patterns(flask_file, "flask")
        assert priority == PriorityLevel.CRITICAL

    def test_priority_upgrade(self):
        """Test priority upgrade functionality."""
        assert (
            self.analyzer._upgrade_priority(PriorityLevel.MINIMAL) == PriorityLevel.LOW
        )
        assert (
            self.analyzer._upgrade_priority(PriorityLevel.LOW) == PriorityLevel.MEDIUM
        )
        assert (
            self.analyzer._upgrade_priority(PriorityLevel.MEDIUM) == PriorityLevel.HIGH
        )
        assert (
            self.analyzer._upgrade_priority(PriorityLevel.HIGH)
            == PriorityLevel.CRITICAL
        )
        assert (
            self.analyzer._upgrade_priority(PriorityLevel.CRITICAL)
            == PriorityLevel.CRITICAL
        )

    def test_directory_based_priorities(self):
        """Test that directory structure affects priority."""
        # Test critical directories - routes.py is critical due to filename pattern
        api_file = Path("src/api/routes.py")
        priority = self.analyzer.analyze_file_priority(api_file)
        assert priority == PriorityLevel.CRITICAL

        # Test low priority directories
        test_file = Path("tests/test_something.py")
        priority = self.analyzer.analyze_file_priority(test_file)
        assert priority == PriorityLevel.LOW

        # Test minimal priority directories
        # Test .git directory file
        git_file = Path(".git/config")
        priority = self.analyzer.analyze_file_priority(git_file)
        assert priority == PriorityLevel.MINIMAL

    def test_function_priority_analysis(self):
        """Test function-level priority analysis."""
        # Test critical function patterns
        main_function = '''
def main():
    """Main entry point."""
    app.run()
'''
        priority = self.analyzer.analyze_function_priority(main_function)
        assert priority == PriorityLevel.CRITICAL

        # Test decorated function
        decorated_function = """
@app.route('/test')
def test_endpoint():
    return "test"
"""
        priority = self.analyzer.analyze_function_priority(decorated_function)
        assert priority == PriorityLevel.CRITICAL

        # Test simple getter - matches minimal priority pattern
        simple_getter = """
def get_name(self):
    return self._name
"""
        priority = self.analyzer.analyze_function_priority(simple_getter)
        assert priority == PriorityLevel.MINIMAL  # Matches getter pattern

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with invalid file path
        invalid_path = Path("nonexistent/file.py")
        priority = self.analyzer.analyze_file_priority(invalid_path)
        assert priority in [PriorityLevel.MEDIUM]  # Should have default behavior

        # Test with empty content
        priority = self.analyzer._analyze_python_content("")
        assert priority == PriorityLevel.MEDIUM

        # Test with invalid Python syntax
        invalid_content = "def invalid( syntax"
        priority = self.analyzer._analyze_python_content(invalid_content)
        assert priority == PriorityLevel.MEDIUM  # Should handle gracefully

    def test_analyze_file_priority_with_content(self):
        """Test full file priority analysis with content."""
        content = '''
"""Main application module."""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(debug=True)
'''
        file_path = Path("app.py")
        priority = self.analyzer.analyze_file_priority(file_path, content)
        assert priority == PriorityLevel.CRITICAL  # Critical file with critical content
