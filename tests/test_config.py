"""Tests for configuration management."""

import yaml

from folder2md4llms.utils.config import Config, ConfigValidationError


class TestConfig:
    """Test the Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.output_format == "markdown"
        assert config.include_tree is True
        assert config.include_stats is True
        assert config.convert_docs is True
        assert config.describe_binaries is True
        assert config.max_file_size == 100 * 1024 * 1024  # 100MB default
        assert config.verbose is False

    def test_load_config_from_file(self, temp_dir):
        """Test loading configuration from YAML file."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "output_format": "html",
            "include_tree": False,
            "max_file_size": 2048,
            "verbose": True,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = Config.load(config_path=config_file)

        assert config.output_format == "html"
        assert config.include_tree is False
        assert config.max_file_size == 2048
        assert config.verbose is True
        # Unchanged values should remain default
        assert config.include_stats is True

    def test_load_config_nonexistent_file(self, temp_dir):
        """Test loading configuration from nonexistent file."""
        config_file = temp_dir / "nonexistent.yaml"
        config = Config.load(config_path=config_file)

        # Should use defaults
        assert config.output_format == "markdown"
        assert config.include_tree is True

    def test_load_config_from_repo_directory(self, temp_dir):
        """Test loading configuration from repository directory."""
        repo_dir = temp_dir / "repo"
        repo_dir.mkdir()

        config_file = repo_dir / "folder2md.yaml"
        config_data = {"output_format": "plain", "max_file_size": 2048}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = Config.load(repo_path=repo_dir)

        assert config.output_format == "plain"
        assert config.max_file_size == 2048

    def test_save_config(self, temp_dir):
        """Test saving configuration to file."""
        config = Config()
        config.output_format = "html"
        config.verbose = True

        config_file = temp_dir / "saved_config.yaml"
        config.save(config_file)

        assert config_file.exists()

        # Load and verify
        with open(config_file) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["output_format"] == "html"
        assert saved_data["verbose"] is True

    def test_create_default_config(self, temp_dir):
        """Test creating default configuration file."""
        config = Config()
        config_file = temp_dir / "default_config.yaml"

        config.create_default_config(config_file)

        assert config_file.exists()
        content = config_file.read_text(encoding="utf-8")
        assert "output_format: markdown" in content
        assert "include_tree: true" in content
        assert "# folder2md4llms configuration file" in content

    def test_config_validation_errors(self):
        """Test configuration validation with invalid values."""
        import pytest

        config = Config()

        # Test invalid numeric constraints
        with pytest.raises(ConfigValidationError, match="token_limit must be between"):
            config._validate_config({"token_limit": 50})  # Below minimum

        with pytest.raises(ConfigValidationError, match="max_workers must be between"):
            config._validate_config({"max_workers": 100})  # Above maximum

        # Test invalid strategy
        with pytest.raises(
            ConfigValidationError, match="token_budget_strategy must be one of"
        ):
            config._validate_config({"token_budget_strategy": "invalid_strategy"})

        # Test invalid boolean
        with pytest.raises(
            ConfigValidationError, match="include_tree must be a boolean"
        ):
            config._validate_config({"include_tree": "not_a_boolean"})

        # Test invalid list
        with pytest.raises(
            ConfigValidationError, match="condense_languages must be a list"
        ):
            config._validate_config({"condense_languages": "not_a_list"})
