#!/bin/bash
# Build script for pagerduty-client
# Usage: ./scripts/build.sh

set -e

cd "$(dirname "$0")/.."

echo "Building pagerduty-client package..."

# Install build tools
pip install --upgrade build wheel

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

echo "Build complete! Artifacts in dist/:"
ls -lh dist/
