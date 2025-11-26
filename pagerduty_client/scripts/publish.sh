#!/bin/bash
# Publish script for pagerduty-client to Google Artifact Registry
# Usage: ./scripts/publish.sh [VERSION]
# If VERSION is not provided, it will use the version from pyproject.toml

set -e

# Configuration - Update these for your project
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-mai-project-a26f}"
LOCATION="us-central1"
REPOSITORY="mai-python-repo"
PACKAGE_NAME="pagerduty-client"

# Get the version
if [ -n "$1" ]; then
    VERSION="$1"
    # Update version in pyproject.toml
    sed -i.bak "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
    rm pyproject.toml.bak
else
    VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
fi

echo "Publishing ${PACKAGE_NAME} version ${VERSION} to Google Artifact Registry..."

# Navigate to the library directory
cd "$(dirname "$0")/.."

# Build the package
echo "Building package..."
bash scripts/build.sh

# Authenticate with Google Cloud
echo "Authenticating with Google Cloud..."
gcloud auth configure-docker ${LOCATION}-python.pkg.dev

# Upload to Artifact Registry
ARTIFACT_REGISTRY_URL="${LOCATION}-python.pkg.dev/${PROJECT_ID}/${REPOSITORY}"

echo "Uploading to ${ARTIFACT_REGISTRY_URL}..."

# Use twine to upload (install if needed)
pip install --upgrade twine keyring keyrings.google-artifactregistry-auth

# Upload using twine with Artifact Registry authentication
TWINE_REPOSITORY_URL="https://${ARTIFACT_REGISTRY_URL}/simple/"
twine upload \
    --repository-url "${TWINE_REPOSITORY_URL}" \
    --username oauth2accesstoken \
    --password "$(gcloud auth print-access-token)" \
    dist/*

echo "Successfully published ${PACKAGE_NAME} version ${VERSION}!"
echo ""
echo "To install this package, use:"
echo "pip install ${PACKAGE_NAME}==${VERSION} --extra-index-url https://${ARTIFACT_REGISTRY_URL}/simple/"
