#!/bin/bash

# docs-live.sh - Live Sphinx Documentation Server
# Startet sphinx-autobuild für Live-Dokumentation im Browser

set -e

echo "🚀 Starting WINCASA Live Documentation Server..."

# Activate virtual environment
source venv/bin/activate

# Check if sphinx-autobuild is installed
if ! command -v sphinx-autobuild &> /dev/null; then
    echo "❌ sphinx-autobuild not found. Installing..."
    pip install sphinx-autobuild
fi

# Change to docs directory
cd docs

# Start live documentation server
echo "📚 Starting live documentation server..."
echo "📍 Access at: http://localhost:8000"
echo "🔄 Watches for changes in docs/ directory"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Start sphinx-autobuild
sphinx-autobuild \
    --host 0.0.0.0 \
    --port 8000 \
    --watch ../ARCHITECTURE.md \
    --watch ../API.md \
    --watch ../CHANGELOG.md \
    --watch ../INVENTORY.md \
    --watch ../LOGGING.md \
    --watch ../TESTING.md \
    --watch ../TASKS.md \
    --watch ../SAD.md \
    --watch ../CLAUDE.md \
    --ignore "*.pyc" \
    --ignore "*~" \
    --ignore "*.swp" \
    --ignore "*.swo" \
    . _build/html