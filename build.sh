#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Installing Playwright Chromium browser & Linux dependencies..."
playwright install --with-deps chromium || playwright install chromium

echo "==> Build complete!"
