#!/bin/bash
# WINCASA Layer 4 Streamlit Launcher with Clean Restart
# Usage: ./run_streamlit.sh [port] [address] [--restart] [--debug] [--test] [--dev]
#
# By default runs with nohup in background for production use
# Use --debug or --dev flags to run in foreground for development

# Change to project root directory
cd "$(dirname "$0")/../.."

echo "🏠 Starting WINCASA Layer 4 Streamlit App..."
echo "📂 Working directory: $(pwd)"

# Function for clean restart
clean_restart() {
    echo "🧹 Performing clean restart..."
    
    # Get port from arguments or default
    local RESTART_PORT="${ARGS[0]:-8667}"
    
    # Only stop Streamlit process on specific port
    echo "   Stopping Streamlit process on port $RESTART_PORT..."
    EXISTING_PID=$(lsof -ti:$RESTART_PORT 2>/dev/null)
    if [ ! -z "$EXISTING_PID" ]; then
        echo "   Found process PID: $EXISTING_PID"
        kill $EXISTING_PID 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if kill -0 $EXISTING_PID 2>/dev/null; then
            echo "   Force stopping process..."
            kill -9 $EXISTING_PID 2>/dev/null || true
            sleep 1
        fi
    else
        echo "   No process found on port $RESTART_PORT"
    fi
    
    # Clear any cached Python bytecode
    echo "   Clearing Python cache..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    echo "   ✅ Clean restart completed"
}

# Parse special flags
DEBUG_MODE=false
TEST_MODE=false
DEV_MODE=false

for arg in "$@"; do
    case $arg in
        --restart)
            clean_restart
            ;;
        --debug)
            DEBUG_MODE=true
            echo "🐛 Debug mode enabled"
            ;;
        --test)
            TEST_MODE=true
            echo "🧪 Test mode enabled - running tests first"
            ;;
        --dev)
            DEV_MODE=true
            echo "👨‍💻 Developer mode enabled - verbose logging"
            ;;
    esac
done

# Parse arguments first to get port
ARGS=()
for arg in "$@"; do
    if [[ "$arg" != "--restart" ]] && [[ "$arg" != "--debug" ]] && [[ "$arg" != "--test" ]] && [[ "$arg" != "--dev" ]]; then
        ARGS+=("$arg")
    fi
done

# Get port early for process checking
TARGET_PORT="${ARGS[0]:-$(grep "^STREAMLIT_PORT=" config/.env 2>/dev/null | cut -d'=' -f2 || echo "8667")}"

# If not restart, check for existing processes on specific port
if [[ "$*" != *"--restart"* ]]; then
    # Only check the specific port we're targeting
    EXISTING_PID=$(lsof -ti:$TARGET_PORT 2>/dev/null)
    if [ ! -z "$EXISTING_PID" ]; then
        echo "⚠️  Found existing Streamlit process on port $TARGET_PORT (PID: $EXISTING_PID)"
        echo "   Stopping it first..."
        kill $EXISTING_PID 2>/dev/null || true
        sleep 2
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "venv/installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Set environment variables for new package structure
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check configuration
echo "Checking .env configuration..."
if [ ! -f "config/.env" ]; then
    echo "❌ config/.env file not found!"
    exit 1
fi

# Check API keys file
API_KEYS_FILE=$(grep "^OPENAI_API_KEYS_FILE=" config/.env | cut -d'=' -f2)
if [ ! -f "$API_KEYS_FILE" ]; then
    echo "⚠️  Warning: API keys file not found: $API_KEYS_FILE"
    echo "   App will work but LLM calls will be mocked"
else
    echo "✅ API keys file found: $API_KEYS_FILE"
fi

echo "✅ Configuration loaded"

# Run tests if test mode enabled
if [ "$TEST_MODE" = true ]; then
    echo "🧪 Running quick tests before starting..."
    python tests/unit/test_suite_quick.py
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed! Fix tests before starting server."
        exit 1
    fi
    echo "✅ Tests passed, starting server..."
fi

# Get server configuration from command line, .env, or defaults
# Use TARGET_PORT from earlier parsing
PORT=$TARGET_PORT

if [ -n "${ARGS[1]}" ]; then
    ADDRESS=${ARGS[1]}
else
    ADDRESS=$(grep "^STREAMLIT_ADDRESS=" config/.env | cut -d'=' -f2 2>/dev/null || echo "0.0.0.0")
fi

# Start Streamlit app
if [[ "$ADDRESS" == "0.0.0.0" ]]; then
    echo "🌐 Starting Streamlit accessible from network:"
    echo "   Local:     http://localhost:$PORT"
    echo "   Network:   http://$(hostname -I | awk '{print $1}'):$PORT"
    echo "   External:  http://0.0.0.0:$PORT"
else
    echo "🏠 Starting Streamlit on http://$ADDRESS:$PORT"
fi

echo ""
echo "Press Ctrl+C to stop"

# Set logging level based on mode
if [ "$DEBUG_MODE" = true ] || [ "$DEV_MODE" = true ]; then
    LOG_LEVEL="debug"
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    echo "🔍 Debug environment variables:"
    echo "   PYTHONPATH: $PYTHONPATH" 
    echo "   Working dir: $(pwd)"
else
    LOG_LEVEL="info"
fi

# Special debug instructions
if [ "$DEBUG_MODE" = true ]; then
    echo ""
    echo "🐛 DEBUG MODE INSTRUCTIONS:"
    echo "   1. Set breakpoints with: import pdb; pdb.set_trace()"
    echo "   2. In streamlit_app.py around line 89 (execute_query)"
    echo "   3. In wincasa_query_engine.py around line 45 for Mode 5"
    echo "   4. Check logs in real-time: tail -f logs/layer2.log"
    echo ""
fi

echo "🚀 Starting Streamlit server..."

# Check if we should run in foreground (for debugging)
if [ "$DEBUG_MODE" = true ] || [ "$DEV_MODE" = true ]; then
    echo "🔍 Running in foreground mode (debug/dev)"
    streamlit run src/wincasa/core/streamlit_app.py \
        --server.port $PORT \
        --server.address $ADDRESS \
        --server.enableCORS false \
        --server.enableXsrfProtection false \
        --server.headless true \
        --theme.base light \
        --server.maxUploadSize 10 \
        --logger.level $LOG_LEVEL
else
    # Default: Run with nohup in background
    LOG_FILE="logs/streamlit_$(date +%Y%m%d_%H%M%S).log"
    echo "📝 Server output will be logged to: $LOG_FILE"
    echo "💡 Use 'tail -f $LOG_FILE' to follow the logs"
    
    nohup streamlit run src/wincasa/core/streamlit_app.py \
        --server.port $PORT \
        --server.address $ADDRESS \
        --server.enableCORS false \
        --server.enableXsrfProtection false \
        --server.headless true \
        --theme.base light \
        --server.maxUploadSize 10 \
        --logger.level $LOG_LEVEL > "$LOG_FILE" 2>&1 &
    
    PID=$!
    echo "✅ Server started with PID: $PID"
    echo "🛑 To stop: kill $PID or ./tools/scripts/run_streamlit.sh --restart"
fi