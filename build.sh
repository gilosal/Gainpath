#!/usr/bin/env bash
set -e

echo "==> Installing backend dependencies"
cd /app/backend
pip install --no-cache-dir -r requirements.txt

echo "==> Installing frontend dependencies"
cd /app/frontend
npm ci

echo "==> Building frontend"
NEXT_OUTPUT=standalone npm run build

echo "==> Build complete"
