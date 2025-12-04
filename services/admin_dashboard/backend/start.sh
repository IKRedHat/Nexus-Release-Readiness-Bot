#!/usr/bin/env bash
# Render Start Script for Nexus Admin Dashboard Backend
# This script is executed when the service starts

set -e

echo "🚀 Starting Nexus Admin Dashboard Backend..."
echo "============================================"

# Navigate to backend directory
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:/opt/render/project/src/shared:$(pwd)/../../../shared"

# Set default port if not provided
PORT=${PORT:-8088}

echo "📡 Starting server on port ${PORT}..."
echo "🌐 Environment: ${NEXUS_ENV:-development}"
echo "🔐 RBAC Enabled: ${NEXUS_RBAC_ENABLED:-false}"

# Start uvicorn
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --log-level info

