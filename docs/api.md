# CLI Reference

This page provides a complete reference for the `folder2md4llms` command-line interface.

## Usage

```bash
folder2md [OPTIONS] [PATH]
```

## Arguments

- `[PATH]`: The path to the directory you want to process. Defaults to the current directory (`.`).

## Options

| Option | Short | Description |
|---|---|---|
| `--output <file>` | `-o` | Specifies the path for the output Markdown file. Defaults to `output.md`. |
| `--limit <size>` | | Sets a size limit for the output and automatically enables smart condensing. Use `t` for tokens and `c` for characters (e.g., `80000t`, `200000c`). |
| `--condense` | | Enables code condensing for supported languages, using the default settings from your configuration file. |
| `--config <file>` | `-c` | Specifies the path to a custom configuration file. |
| `--clipboard` | | Copies the final output to the system clipboard. |
| `--init-ignore` | | Generates a `.folder2md_ignore` template file in the target directory. |
| `--disable-update-check` | | Disables the automatic check for new versions. |
| `--verbose` | `-v` | Enables verbose logging, providing more detailed output during processing. |
| `--version` | | Shows the installed version of `folder2md4llms`. |
| `--help` | `-h` | Displays the help message. |

## Examples

### Basic Operations

**Process the current directory:**

```bash
folder2md .
```

**Process a specific directory and save to a custom file:**

```bash
folder2md /path/to/my-project -o my-project-analysis.md
```

### Condensing and Limits

**Set a token limit to automatically condense files:**

```bash
folder2md . --limit 80000t
```

**Set a character limit:**

```bash
folder2md . --limit 250000c
```

**Enable default code condensing:**

```bash
folder2md . --condense
```

### Utility

**Copy the output to the clipboard:**

```bash
folder2md . --clipboard
```

**Generate an ignore file:**

```bash
folder2md --init-ignore
```

## Configuration

For more advanced customization, you can create a `folder2md.yaml` file in your project's root directory. This allows you to control ignore patterns, file size limits, and more.

**Example `folder2md.yaml`:**

```yaml
# Set the default output file name
output_file: "project_summary.md"

# Always include the folder structure tree
include_tree: true

# Set a default token limit
token_limit: 100000

# Customize code condensing
condense_code: true
code_condense_mode: "signatures"
condense_languages:
  - "python"
  - "javascript"
```
