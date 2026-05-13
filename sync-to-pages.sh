#!/usr/bin/env bash
# sync-to-pages.sh - Sync latest news JSON to GitHub Pages repo
# Called after collector.py runs to update the web dashboard

set -euo pipefail

SNC_DIR="$HOME/projects/stock-news-collector"
PAGES_DIR="$HOME/projects/cjarvishk.github.io"
JSON_SRC="$SNC_DIR/data.json"
JSON_DST="$PAGES_DIR/snc/data.json"

# Check source exists
if [ ! -f "$JSON_SRC" ]; then
    echo "⚠️  No data.json found at $JSON_SRC"
    exit 1
fi

# Copy JSON to pages repo
cp "$JSON_SRC" "$JSON_DST"

# Commit and push if changed
cd "$PAGES_DIR"
if git diff --quiet HEAD -- snc/data.json; then
    echo "✅ No changes to push"
    exit 0
fi

git add snc/data.json
git commit -m "📰 Auto-update: Stock news $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "✅ Successfully updated GitHub Pages dashboard"
