#!/bin/bash
set -e

# Semantic release preparation script
# This script is called by semantic-release to prepare a new release

echo "🧹 Cleaning old build artifacts..."
rm -rf dist/ build/ *.egg-info/

echo "📝 Updating version in pyproject.toml..."
sed -i "s/version = \".*\"/version = \"${1}\"/" pyproject.toml

echo "📝 Updating version in __init__.py..."
sed -i "s/__version__ = \".*\"/__version__ = \"${1}\"/" src/dosctl/__init__.py

echo "📦 Building package..."
python -m build

echo "✅ Build complete! Version ${1} ready for release."
