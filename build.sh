#!/usr/bin/env bash
set -e

echo "=== Building Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Syncing Frontend Build to Backend Static ==="
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "=== Installing Backend Dependencies ==="
pip install -r backend/requirements.txt

echo "=== Build Complete ==="
