#!/usr/bin/env bash
set -e

echo "=== Installing Python Dependencies ==="
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
fi

echo "=== Build Complete ==="
