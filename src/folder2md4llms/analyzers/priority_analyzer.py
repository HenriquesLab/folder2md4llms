"""Content priority analyzer for smart anti-truncation engine."""

import ast
import re
from collections import defaultdict
from enum import Enum
from pathlib import Path

from ..utils.file_utils import get_language_from_extension


class PriorityLevel(Enum):
    """Priority levels for content classification."""

    CRITICAL = 0  # Core business logic, main classes, entry points, APIs
    HIGH = 1  # Important functions, configuration, error handling
    MEDIUM = 2  # Utility functions, helpers, tests
    LOW = 3  # Documentation, comments, examples
    MINIMAL = 4  # Generated code, boilerplate, trivial getters/setters


class ContentPriorityAnalyzer:
    """Analyzes content to determine priority levels for smart condensing."""

    def __init__(self):
        """Initialize the priority analyzer."""
        # Enhanced file patterns for different priority levels
        self.critical_file_patterns = {
            r"main\.py$",
            r"app\.py$",
            r"__main__\.py$",
            r"server\.py$",
            r"api\.py$",
            r"routes\.py$",
            r"views\.py$",
            r"models\.py$",
            r"index\.(js|ts)$",
            r"main\.(js|ts)$",
            r"app\.(js|ts)$",
            r"Application\.(java|kt)$",
            r"Main\.(java|kt)$",
            # Framework-specific entry points
            r"wsgi\.py$",
            r"asgi\.py$",
            r"manage\.py$",
            r"_app\.(js|tsx?)$",
            r"layout\.(js|tsx?)$",
        }

        # Entry point indicators for deep content analysis
        self.entry_point_indicators = {
            # Python
            r"if\s+__name__\s*==\s*['\"]__main__['\"]:",
            r"\.run\(\s*debug\s*=",
            r"app\.run\(",
            r"uvicorn\.run\(",
            r"gunicorn",
            # JavaScript/TypeScript
            r"app\.listen\(",
            r"createServer\(",
            r"new\s+Server\(",
            # Config files that define entry points
            r"\"main\":\s*\"",
            r"\"start\":\s*\"",
            r"\"serve\":\s*\"",
        }

        self.api_endpoint_patterns = {
            r"@(app|router)\.(get|post|put|delete|patch)",
            r"\.route\(['\"][^'\"]+['\"]",
            r"@RequestMapping",
            r"@GetMapping",
            r"@PostMapping",
            r"@RestController",
            r"@Controller",
            r"@app\.(get|post|put|delete)",
            r"router\.(get|post|put|delete)",
        }

        self.configuration_patterns = {
            r"(DATABASE_URL|API_KEY|SECRET_KEY|TOKEN|CONFIG)",
            r"\.env\.",
            r"config\[",
            r"settings\.",
            r"process\.env\.",
            r"os\.environ",
            r"getenv\(",
        }

        self.high_priority_patterns = {
            r"__init__\.py$",
            r"config\.py$",
            r"settings\.py$",
            r"constants\.py$",
            r".*controller\.(py|js|ts|java)$",
            r".*service\.(py|js|ts|java)$",
            r".*manager\.(py|js|ts)$",
            r".*handler\.(py|js|ts|java)$",
            r".*error.*\.(py|js|ts|java)$",
            r".*exception.*\.(py|js|ts|java)$",
        }

        self.medium_priority_patterns = {
            r".*util.*\.(py|js|ts|java)$",
            r".*helper.*\.(py|js|ts|java)$",
            r".*tool.*\.(py|js|ts|java)$",
            r".*lib.*\.(py|js|ts|java)$",
        }

        self.low_priority_patterns = {
            r".*test.*\.(py|js|ts|java)$",
            r".*spec\.(js|ts)$",
            r".*example.*\.(py|js|ts|java)$",
            r".*demo.*\.(py|js|ts|java)$",
            r"README.*",
            r".*\.md$",
            r".*\.txt$",
            r".*\.rst$",
        }

        self.minimal_priority_patterns = {
            r".*_pb2\.py$",
            r".*\.pb\.go$",  # Generated protobuf files
            r".*_generated\.(py|js|ts|java)$",
            r".*\.g\.(py|js|ts|java)$",
            r"migrations/.*\.py$",
            r".*migration.*\.(py|js|ts|java)$",
        }

        # Enhanced function/class priority indicators
        self.critical_function_indicators = {
            # Python decorators that indicate critical functions
            r"@app\.route",
            r"@api\.route",
            r"@flask\.route",
            r"@fastapi\.",
            r"@click\.command",
            r"@asyncio\.",
            r"@pytest\.main",
            r"@celery\.task",
            r"@periodic_task",
            # Function names that are typically critical
            r"def main\(",
            r"def run\(",
            r"def start\(",
            r"def serve\(",
            r"def handle\(",
            r"def process\(",
            r"def execute\(",
            r"def create_app\(",
            r"def setup\(",
            r"def initialize\(",
            # Class names that are typically critical
            r"class.*Application",
            r"class.*Server",
            r"class.*API",
            r"class.*Controller",
            r"class.*Manager",
            r"class.*Service",
            r"class.*Handler",
            r"class.*Processor",
            r"class.*Router",
            # Async patterns
            r"async def",
            r"await ",
        }

        self.high_priority_indicators = {
            r"def __init__",
            r"def __new__",
            r"def __enter__",
            r"def __exit__",
            r"def setUp",
            r"def tearDown",
            r"def configure",
            r"def initialize",
            r"class.*Config",
            r"class.*Settings",
            r"class.*Error",
            r"class.*Exception",
        }

        self.minimal_priority_indicators = {
            r"def get_\w+\(self\):\s*return self\._\w+",  # Simple getters
            r"def set_\w+\(self, \w+\):\s*self\._\w+ = \w+",  # Simple setters
            r"def __str__\(self\):",
            r"def __repr__\(self\):",
            r"# Generated by",
            r"# Auto-generated",
            r"# DO NOT EDIT",
        }

        # Framework-specific patterns for enhanced detection
        self.framework_patterns = {
            "django": {
                "critical": ["settings.py", "wsgi.py", "asgi.py", "urls.py"],
                "high": ["models.py", "views.py", "serializers.py"],
                "medium": ["forms.py", "admin.py", "middleware.py"],
            },
            "flask": {
                "critical": ["app.py", "application.py", "__init__.py"],
                "high": ["routes.py", "models.py", "config.py"],
                "medium": ["forms.py", "utils.py"],
            },
            "fastapi": {
                "critical": ["main.py", "app.py"],
                "high": ["routers/*.py", "models.py", "schemas.py"],
                "medium": ["dependencies.py", "utils.py"],
            },
            "react": {
                "critical": ["index.js", "index.tsx", "App.js", "App.tsx"],
                "high": ["**/components/index.*", "routes.*", "store.*"],
                "medium": ["**/hooks/*.js", "**/utils/*.js"],
            },
            "nextjs": {
                "critical": ["pages/_app.*", "pages/index.*", "app/layout.*"],
                "high": ["pages/api/*", "app/**/page.*"],
                "medium": ["components/*", "lib/*"],
            },
        }

    def analyze_file_priority(
        self, file_path: Path, content: str | None = None
    ) -> PriorityLevel:
        """Analyze a file to determine its priority level for smart condensing.

        This method uses multiple heuristics to determine file importance:
        - File naming patterns (main.py, app.py, etc.)
        - Content analysis (entry points, API routes, critical functions)
        - Import frequency analysis
        - Directory context
        - Code complexity metrics

        Args:
            file_path: Path to the file being analyzed
            content: Optional file content for deep analysis. If not provided,
                    only path-based analysis is performed.

        Returns:
            PriorityLevel: The determined priority level (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)

        Example:
            >>> analyzer = ContentPriorityAnalyzer()
            >>> priority = analyzer.analyze_file_priority(Path("src/main.py"))
            >>> print(priority)
            PriorityLevel.CRITICAL
        """
        file_path_str = str(file_path).lower()

        # Detect framework and apply framework-specific patterns
        framework = self.detect_framework(file_path.parent)
        if framework:
            framework_priority = self._apply_framework_patterns(file_path, framework)
            if framework_priority != PriorityLevel.MEDIUM:
                return framework_priority

        # Check against file patterns
        if self._matches_patterns(file_path_str, self.critical_file_patterns):
            return PriorityLevel.CRITICAL
        if self._matches_patterns(file_path_str, self.high_priority_patterns):
            return PriorityLevel.HIGH
        if self._matches_patterns(file_path_str, self.medium_priority_patterns):
            return PriorityLevel.MEDIUM
        if self._matches_patterns(file_path_str, self.low_priority_patterns):
            return PriorityLevel.LOW
        if self._matches_patterns(file_path_str, self.minimal_priority_patterns):
            return PriorityLevel.MINIMAL

        # If content is available, analyze it for priority indicators
        if content:
            content_priority = self._analyze_content_priority(content, file_path)
            if content_priority != PriorityLevel.MEDIUM:  # Medium is default
                # Adjust priority based on context
                return self.adjust_priority_by_context(file_path, content_priority)

        # Path-based heuristics
        path_parts = file_path.parts

        # Check directory structure
        if any(
            part in ["src", "lib", "core", "main", "api", "app"] for part in path_parts
        ):
            return PriorityLevel.HIGH
        if any(
            part in ["test", "tests", "spec", "specs", "examples", "docs"]
            for part in path_parts
        ):
            return PriorityLevel.LOW
        if any(
            part in ["vendor", "third_party", "node_modules", ".git"]
            for part in path_parts
        ):
            return PriorityLevel.MINIMAL

        # Default to medium priority
        return PriorityLevel.MEDIUM

    def analyze_function_priority(
        self, function_content: str, context: str = ""
    ) -> PriorityLevel:
        """Analyze a function or method to determine its priority level.

        Args:
            function_content: The function's source code
            context: Additional context (class name, file path, etc.)

        Returns:
            Priority level for the function
        """
        combined_content = context + "\n" + function_content

        # Check for critical indicators
        if self._matches_patterns(combined_content, self.critical_function_indicators):
            return PriorityLevel.CRITICAL

        # Check for high priority indicators
        if self._matches_patterns(combined_content, self.high_priority_indicators):
            return PriorityLevel.HIGH

        # Check for minimal priority indicators
        if self._matches_patterns(combined_content, self.minimal_priority_indicators):
            return PriorityLevel.MINIMAL

        # Function length and complexity heuristics
        lines = function_content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Very short functions are often trivial
        if len(non_empty_lines) <= 3:
            return PriorityLevel.LOW

        # Very long functions are often important
        if len(non_empty_lines) > 50:
            return PriorityLevel.HIGH

        return PriorityLevel.MEDIUM

    def analyze_import_frequency(self, repo_path: Path) -> dict[Path, float]:
        """Analyze how frequently files are imported to determine importance.

        Args:
            repo_path: Path to the repository root

        Returns:
            Dictionary mapping file paths to normalized importance scores (0.0 to 1.0)
        """
        import_counts: dict[Path, int] = defaultdict(int)

        # Build reverse import graph - who imports what
        for file_path in repo_path.rglob("*.py"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                imports = self._extract_imports(content, file_path, repo_path)
                for imported in imports:
                    import_counts[imported] += 1
            except (OSError, UnicodeDecodeError):
                continue

        # Normalize scores
        max_imports = max(import_counts.values()) if import_counts else 1
        return {path: count / max_imports for path, count in import_counts.items()}

    def analyze_import_graph(self, repo_path: Path) -> dict[Path, float]:
        """Analyze import relationships to determine file importance.

        Args:
            repo_path: Path to the repository root

        Returns:
            Dictionary mapping file paths to importance scores (0.0 to 1.0)
        """
        return self.analyze_import_frequency(repo_path)

    def get_priority_weights(self) -> dict[PriorityLevel, float]:
        """Get default weights for different priority levels.

        Returns:
            Dictionary mapping priority levels to weight multipliers
        """
        return {
            PriorityLevel.CRITICAL: 1.0,  # Always preserve fully
            PriorityLevel.HIGH: 0.8,  # Minimal condensing
            PriorityLevel.MEDIUM: 0.6,  # Moderate condensing
            PriorityLevel.LOW: 0.3,  # Heavy condensing
            PriorityLevel.MINIMAL: 0.1,  # Maximum condensing
        }

    def _matches_patterns(self, text: str, patterns: set[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def _analyze_content_priority(self, content: str, file_path: Path) -> PriorityLevel:
        """Analyze file content to determine priority level."""
        language = get_language_from_extension(file_path.suffix.lower())

        if language == "python":
            return self._analyze_python_content(content)
        elif language in ["javascript", "typescript"]:
            return self._analyze_js_content(content)
        elif language == "java":
            return self._analyze_java_content(content)
        else:
            return self._analyze_generic_content(content)

    def _analyze_python_content(self, content: str) -> PriorityLevel:
        """Analyze Python content for priority indicators."""
        # Check for entry point patterns first
        if self._matches_patterns(content, self.entry_point_indicators):
            return PriorityLevel.CRITICAL

        # Check for API endpoint patterns
        if self._matches_patterns(content, self.api_endpoint_patterns):
            return PriorityLevel.CRITICAL

        # Check for configuration patterns
        if self._matches_patterns(content, self.configuration_patterns):
            return PriorityLevel.HIGH

        try:
            tree = ast.parse(content)

            # Look for critical patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for main function
                    if node.name == "main":
                        return PriorityLevel.CRITICAL

                    # Check for decorators indicating web routes, CLI commands, etc.
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Attribute):
                            attr_path = self._get_attr_path(decorator)
                            if any(
                                pattern in attr_path
                                for pattern in [
                                    "route",
                                    "command",
                                    "task",
                                    "api",
                                    "endpoint",
                                ]
                            ):
                                return PriorityLevel.CRITICAL

                elif isinstance(node, ast.ClassDef):
                    # Important class types
                    class_name = node.name.lower()
                    if any(
                        keyword in class_name
                        for keyword in [
                            "application",
                            "server",
                            "api",
                            "controller",
                            "manager",
                            "service",
                            "router",
                            "handler",
                            "processor",
                        ]
                    ):
                        return PriorityLevel.CRITICAL
                    if any(
                        keyword in class_name
                        for keyword in ["config", "settings", "error", "exception"]
                    ):
                        return PriorityLevel.HIGH

        except SyntaxError:
            pass

        return PriorityLevel.MEDIUM

    def _analyze_js_content(self, content: str) -> PriorityLevel:
        """Analyze JavaScript/TypeScript content for priority indicators."""
        # Check for API endpoint patterns
        if self._matches_patterns(content, self.api_endpoint_patterns):
            return PriorityLevel.CRITICAL

        # Check for entry point patterns
        if self._matches_patterns(content, self.entry_point_indicators):
            return PriorityLevel.CRITICAL

        # Look for export patterns that indicate main modules
        if re.search(r"export\s+default\s+", content):
            return PriorityLevel.HIGH

        # Look for Express routes, React components, etc.
        if re.search(r"app\.(get|post|put|delete|use)", content):
            return PriorityLevel.CRITICAL
        if re.search(r"export\s+(function|class|const)\s+\w*App", content):
            return PriorityLevel.CRITICAL

        # React/Next.js specific patterns
        if re.search(r"export\s+default\s+function\s+\w*Page", content):
            return PriorityLevel.HIGH
        if re.search(r"getServerSideProps|getStaticProps", content):
            return PriorityLevel.HIGH

        return PriorityLevel.MEDIUM

    def _analyze_java_content(self, content: str) -> PriorityLevel:
        """Analyze Java content for priority indicators."""
        # Check for API endpoint patterns
        if self._matches_patterns(content, self.api_endpoint_patterns):
            return PriorityLevel.CRITICAL

        # Look for main method
        if re.search(r"public\s+static\s+void\s+main", content):
            return PriorityLevel.CRITICAL

        # Look for Spring Boot annotations
        if re.search(
            r"@(RestController|Controller|Service|Repository|Component|Configuration)",
            content,
        ):
            return PriorityLevel.CRITICAL

        # Look for JAX-RS annotations
        if re.search(r"@(Path|GET|POST|PUT|DELETE)", content):
            return PriorityLevel.CRITICAL

        return PriorityLevel.MEDIUM

    def _analyze_generic_content(self, content: str) -> PriorityLevel:
        """Analyze generic content for priority indicators."""
        # Check for entry point patterns
        if self._matches_patterns(content, self.entry_point_indicators):
            return PriorityLevel.CRITICAL

        # Check for configuration patterns
        if self._matches_patterns(content, self.configuration_patterns):
            return PriorityLevel.HIGH

        # Look for configuration patterns
        if re.search(r"(config|settings|constants)", content, re.IGNORECASE):
            return PriorityLevel.HIGH

        # Look for main/entry point patterns
        if re.search(r"(main|entry|start|run)", content, re.IGNORECASE):
            return PriorityLevel.CRITICAL

        return PriorityLevel.MEDIUM

    def _extract_imports(
        self, content: str, file_path: Path, repo_path: Path
    ) -> list[Path]:
        """Extract import dependencies from file content."""
        imports = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    # Try to resolve import to actual file
                    import_path = self._resolve_import_path(node, file_path, repo_path)
                    if import_path:
                        imports.append(import_path)
        except SyntaxError:
            pass

        return imports

    def _resolve_import_path(
        self, import_node: ast.AST, current_file: Path, repo_path: Path
    ) -> Path | None:
        """Resolve an import statement to an actual file path."""
        # This is a simplified version - a full implementation would handle
        # complex import resolution, virtual environments, etc.

        if isinstance(import_node, ast.ImportFrom):
            if import_node.module:
                # Convert module path to file path
                module_parts = import_node.module.split(".")
                potential_path = repo_path
                for part in module_parts:
                    potential_path = potential_path / part

                # Try .py file
                py_file = potential_path.with_suffix(".py")
                if py_file.exists():
                    return py_file

                # Try __init__.py in directory
                init_file = potential_path / "__init__.py"
                if init_file.exists():
                    return init_file

        return None

    def detect_framework(self, repo_path: Path) -> str | None:
        """Detect the primary framework used in the repository."""
        # Skip framework detection if path doesn't exist or isn't accessible
        if not repo_path.exists() or not repo_path.is_dir():
            return None

        try:
            # Check for framework-specific files
            indicators = {
                "django": ["manage.py", "django.po"],
                "flask": ["flask.py", "flask_app.py"],
                "fastapi": ["fastapi", "uvicorn"],
                "react": ["package.json", "react"],
                "nextjs": ["next.config.js", "next.config.mjs"],
            }

            for framework, files in indicators.items():
                for indicator in files:
                    if list(repo_path.rglob(indicator)):
                        return framework
        except (OSError, PermissionError):
            # Return None if directory is inaccessible
            return None

        # Check package files for dependencies
        return self._check_dependencies(repo_path)

    def _check_dependencies(self, repo_path: Path) -> str | None:
        """Check package files for framework dependencies."""
        # Skip if path doesn't exist
        if not repo_path.exists():
            return None

        # Check package.json for JS frameworks
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                import json

                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }
                    if "next" in deps:
                        return "nextjs"
                    elif "react" in deps:
                        return "react"
            except (OSError, json.JSONDecodeError):
                pass

        # Check requirements.txt for Python frameworks
        requirements = repo_path / "requirements.txt"
        if requirements.exists():
            try:
                with open(requirements, encoding="utf-8") as f:
                    content = f.read().lower()
                    if "django" in content:
                        return "django"
                    elif "flask" in content:
                        return "flask"
                    elif "fastapi" in content:
                        return "fastapi"
            except OSError:
                pass

        return None

    def _apply_framework_patterns(
        self, file_path: Path, framework: str
    ) -> PriorityLevel:
        """Apply framework-specific patterns to determine priority."""
        patterns = self.framework_patterns.get(framework, {})
        file_name = file_path.name

        # Check critical patterns
        if file_name in patterns.get("critical", []):
            return PriorityLevel.CRITICAL

        # Check high priority patterns
        if file_name in patterns.get("high", []):
            return PriorityLevel.HIGH

        # Check medium priority patterns
        if file_name in patterns.get("medium", []):
            return PriorityLevel.MEDIUM

        return PriorityLevel.MEDIUM

    def adjust_priority_by_context(
        self, file_path: Path, base_priority: PriorityLevel
    ) -> PriorityLevel:
        """Adjust priority based on file context and neighbors."""

        # Check if file is in a critical directory
        critical_dirs = {"core", "main", "src/api", "src/models", "app", "lib"}
        for part in file_path.parts:
            if part.lower() in critical_dirs:
                return self._upgrade_priority(base_priority)

        # Check if surrounded by test files (might be code being tested)
        try:
            siblings = list(file_path.parent.glob("*"))
            test_files = [f for f in siblings if "test" in f.name.lower()]
            if len(test_files) > len(siblings) / 2:
                # This is likely important code being tested
                return self._upgrade_priority(base_priority)

            # Check for documentation proximity
            doc_indicators = ["README", "CONTRIBUTING", "docs"]
            for sibling in siblings:
                if any(indicator in sibling.name for indicator in doc_indicators):
                    # Files near documentation might be examples or important APIs
                    return self._upgrade_priority(base_priority)
        except OSError:
            pass

        return base_priority

    def _upgrade_priority(self, priority: PriorityLevel) -> PriorityLevel:
        """Upgrade priority level by one step."""
        if priority == PriorityLevel.MINIMAL:
            return PriorityLevel.LOW
        elif priority == PriorityLevel.LOW:
            return PriorityLevel.MEDIUM
        elif priority == PriorityLevel.MEDIUM:
            return PriorityLevel.HIGH
        elif priority == PriorityLevel.HIGH:
            return PriorityLevel.CRITICAL
        else:
            return priority

    def analyze_code_complexity(self, content: str, file_path: Path) -> float:
        """Analyze code complexity to adjust priority."""
        complexity_score = 0.0

        # Check for complex patterns
        if file_path.suffix == ".py":
            try:
                tree = ast.parse(content)
                # Count classes, functions, decorators
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        complexity_score += 2.0
                    elif isinstance(node, ast.FunctionDef):
                        complexity_score += 1.0
                        # Bonus for decorated functions
                        if node.decorator_list:
                            complexity_score += 0.5 * len(node.decorator_list)
                    elif isinstance(node, ast.AsyncFunctionDef):
                        complexity_score += 1.5  # Async functions are often important
            except SyntaxError:
                pass

        lines = content.split("\n")
        # Adjust for file size - larger files might be more important
        if len(lines) > 500:
            complexity_score *= 1.2
        elif len(lines) < 50:
            complexity_score *= 0.8

        return min(complexity_score / 10.0, 1.0)  # Normalize to 0-1

    def _get_attr_path(self, node: ast.Attribute) -> str:
        """Get the full attribute path from an AST node."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attr_path(node.value)}.{node.attr}"
        else:
            return node.attr
