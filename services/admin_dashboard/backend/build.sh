#!/usr/bin/env bash
# Render Build Script for Nexus Admin Dashboard Backend
# This script is executed during the Render build phase

set -e

echo "🔧 Nexus Admin Dashboard - Build Script"
echo "========================================"

# Navigate to project root (Render clones the entire repo)
cd "$(dirname "$0")/../../.."

# Set up Python path to include shared library
export PYTHONPATH="${PYTHONPATH}:$(pwd)/shared"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r services/admin_dashboard/backend/requirements.txt

# Copy shared library to accessible location
echo "📂 Setting up shared library..."
mkdir -p /opt/render/project/src/shared
cp -r shared/* /opt/render/project/src/shared/ 2>/dev/null || true

echo "✅ Build complete!"

