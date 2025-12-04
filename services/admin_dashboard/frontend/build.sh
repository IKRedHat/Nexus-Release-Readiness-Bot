#!/bin/bash
# Custom build script for Vercel that avoids TypeScript compiler issues

echo "=== Nexus Admin Dashboard Build ==="
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"

# Remove typescript if it somehow got installed (peer dep)
echo "Removing any typescript installation..."
rm -rf node_modules/typescript 2>/dev/null || true

# Run Vite build directly
echo "Running Vite build..."
./node_modules/.bin/vite build

echo "=== Build Complete ==="

