#!/usr/bin/env bash
# Render build script — installs backend deps and builds frontend
set -e

echo "=== Installing backend dependencies ==="
pip install -r backend/requirements-deploy.txt

echo "=== Installing frontend dependencies ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Build complete ==="
