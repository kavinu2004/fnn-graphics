#!/bin/zsh
# One-time setup: a local venv with Playwright and its headless Chromium.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/playwright install chromium-headless-shell
echo "ready: .venv/bin/python build.py gameweeks/gw9.json"
