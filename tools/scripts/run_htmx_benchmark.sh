#!/bin/bash
# Run WINCASA HTMX Benchmark Server

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/src"

# Create logs directory if needed
mkdir -p "${PROJECT_ROOT}/logs"

echo "🔬 Starting WINCASA HTMX Benchmark Server..."
echo "📍 URL: http://localhost:8669"
echo "📍 Network: http://192.168.178.4:8669"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the HTMX server
cd "${PROJECT_ROOT}/htmx"
python3 server.py