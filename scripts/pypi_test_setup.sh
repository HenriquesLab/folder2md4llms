#!/bin/bash

# PyPI Test Setup Script for folder2md4llms
# This script helps set up and test PyPI Test publishing

set -e

echo "🔧 PyPI Test Setup for folder2md4llms"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we have the required credentials
if [[ -z "$HATCH_INDEX_USER" || -z "$HATCH_INDEX_AUTH" ]]; then
    echo "❌ Missing PyPI Test credentials!"
    echo ""
    echo "Please set the following environment variables:"
    echo "  export HATCH_INDEX_USER=__token__"
    echo "  export HATCH_INDEX_AUTH=your-pypi-token-here"
    echo ""
    echo "To get a PyPI Test token:"
    echo "  1. Go to https://test.pypi.org/"
    echo "  2. Register/login"
    echo "  3. Go to Account Settings -> API tokens"
    echo "  4. Create a new token with 'Entire account' scope"
    echo "  5. Copy the token (starts with 'pypi-')"
    echo ""
    exit 1
fi

echo "✅ Credentials found!"
echo ""

# Build the package
echo "📦 Building package..."
make clean
make build

echo ""
echo "📋 Package information:"
echo "  Version: $(uv run hatch version)"
echo "  Files built:"
ls -la dist/

echo ""
echo "🚀 Publishing to PyPI Test..."
echo "  Repository: https://test.pypi.org/"
echo "  User: $HATCH_INDEX_USER"
echo ""

# Publish to test PyPI
uv run hatch publish --repo https://test.pypi.org/legacy/

echo ""
echo "🎉 Package published successfully!"
echo ""
echo "📦 Your package is now available at:"
echo "  https://test.pypi.org/project/folder2md4llms/"
echo ""
echo "🧪 To test installation:"
echo "  pip install -i https://test.pypi.org/simple/ folder2md4llms"
echo ""
echo "✅ PyPI Test setup complete!"
