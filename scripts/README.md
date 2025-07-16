# Scripts Directory

This directory contains utility scripts for the folder2md4llms project.

## Available Scripts

### `pypi_test_setup.sh`

A guided script to help set up and publish the package to PyPI Test.

**Usage:**
```bash
# Set up your credentials first
export HATCH_INDEX_USER=__token__
export HATCH_INDEX_AUTH=your-pypi-token-here

# Run the setup script
./scripts/pypi_test_setup.sh

# Or use the Makefile command
make setup-pypi-test
```

**What it does:**
- Checks for required PyPI Test credentials
- Builds the package
- Publishes to PyPI Test
- Provides next steps for testing

**Prerequisites:**
- PyPI Test account: https://test.pypi.org/
- API token from PyPI Test account settings
- Environment variables set with credentials

**Getting PyPI Test Token:**
1. Go to https://test.pypi.org/
2. Register/login to your account
3. Go to Account Settings → API tokens
4. Create a new token with "Entire account" scope
5. Copy the token (starts with `pypi-`)
6. Set environment variables:
   ```bash
   export HATCH_INDEX_USER=__token__
   export HATCH_INDEX_AUTH=your-copied-token
   ```

## Security Notes

- Never commit API tokens to version control
- Use environment variables for credentials
- Test tokens are separate from production PyPI tokens
- Tokens can be regenerated if compromised
