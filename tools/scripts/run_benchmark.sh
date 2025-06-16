#!/bin/bash
# Run WINCASA Benchmark UI

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/src"

# Activate virtual environment if exists
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# Run benchmark UI
echo "🔬 Starting WINCASA Benchmark UI..."
echo "📍 URL: http://localhost:8668"
echo ""

# Run on different port to avoid conflict with main app
# Bind to 0.0.0.0 to allow external access
streamlit run "${PROJECT_ROOT}/src/wincasa/core/benchmark_ui.py" \
    --server.port 8668 \
    --server.address 0.0.0.0 \
    --server.headless true