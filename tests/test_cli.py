"""Tests for CLI functionality."""

from pathlib import Path

from click.testing import CliRunner

from folder2md4llms.cli import main


class TestCLI:
    """Test the CLI interface."""

    def test_cli_basic_usage(self, sample_repo):
        """Test basic CLI usage."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo)])

            assert result.exit_code == 0
            assert "Repository processed successfully" in result.output

            # Check output file exists
            output_file = Path("output.md")
            assert output_file.exists()

    def test_cli_with_custom_output(self, sample_repo):
        """Test CLI with custom output file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--output", "custom.md"])

            assert result.exit_code == 0
            assert "custom.md" in result.output

            # Check custom output file exists
            output_file = Path("custom.md")
            assert output_file.exists()

    def test_cli_verbose_mode(self, sample_repo):
        """Test CLI with verbose output."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--verbose"])

            assert result.exit_code == 0
            # Verbose mode should show success message
            assert "Repository processed successfully" in result.output

    def test_cli_no_tree_option(self, sample_repo):
        """Test CLI with --no-tree option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--no-tree"])

            assert result.exit_code == 0

            # Check that output file doesn't contain tree
            output_file = Path("output.md")
            content = output_file.read_text()
            assert "📁 Folder Structure" not in content

    def test_cli_no_stats_option(self, sample_repo):
        """Test CLI with --no-stats option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--no-stats"])

            assert result.exit_code == 0

            # Check that output file doesn't contain stats
            output_file = Path("output.md")
            content = output_file.read_text()
            assert "📊 Repository Statistics" not in content

    def test_cli_no_convert_docs_option(self, sample_repo):
        """Test CLI with --no-convert-docs option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--no-convert-docs"])

            assert result.exit_code == 0
            # Should still process successfully

    def test_cli_no_describe_binaries_option(self, sample_repo):
        """Test CLI with --no-describe-binaries option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--no-describe-binaries"])

            assert result.exit_code == 0
            # Should still process successfully

    def test_cli_max_file_size_option(self, sample_repo):
        """Test CLI with --max-file-size option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--max-file-size", "1024"])

            assert result.exit_code == 0

    def test_cli_format_option(self, sample_repo):
        """Test CLI with --format option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--format", "markdown"])

            assert result.exit_code == 0

    def test_cli_nonexistent_directory(self):
        """Test CLI with nonexistent directory."""
        runner = CliRunner()

        result = runner.invoke(main, ["/nonexistent/directory"])

        assert result.exit_code != 0
        assert "Error" in result.output

    def test_cli_current_directory(self, sample_repo):
        """Test CLI with current directory."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Copy sample repo to current directory
            import shutil

            shutil.copytree(sample_repo, ".", dirs_exist_ok=True)

            result = runner.invoke(main, ["."])

            assert result.exit_code == 0

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()

        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Convert a folder structure to markdown" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()

        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower() or "0.1.0" in result.output
