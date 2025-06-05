#!/bin/bash
#
# Start Clean WINCASA Q&A Application
# Production-ready Streamlit interface with 3 retrieval modes
#

echo "🚀 Starting WINCASA Clean Q&A Application..."
echo "================================================"

# Activate virtual environment
source .venv/bin/activate

# Check if environment variables are set
if [ -z "$OPENAI_API_KEY" ] && [ ! -f "/home/envs/openai.env" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not found. Please set environment variables."
fi

# Start Streamlit application
echo "🌐 Starting Streamlit server..."
echo "📱 Access at: http://localhost:8501"
echo "📋 Features:"
echo "   ✅ 3 Retrieval modes (Enhanced/FAISS/None)"
echo "   ✅ Clean chat interface"
echo "   ✅ Agent reasoning display"
echo "   ✅ SQL query visualization"
echo "   ✅ Performance metrics"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

streamlit run streamlit_qa_app.py --server.port 8501 --server.address 0.0.0.0