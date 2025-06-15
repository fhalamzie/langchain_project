#!/bin/bash
# WINCASA Server Management Script using supervisord
# Provides consistent start/stop/restart/status operations

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
SUPERVISORD_CONF="$PROJECT_ROOT/supervisord.conf"
SUPERVISORD_PID="$PROJECT_ROOT/supervisord.pid"
SUPERVISORD_SOCK="$PROJECT_ROOT/supervisor.sock"

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
        echo "Please create it first with: python3 -m venv venv"
        exit 1
    fi
}

# Install supervisord if not present
install_supervisord() {
    echo "🔍 Checking for supervisord..."
    if ! "$VENV_PATH/bin/pip" show supervisor &>/dev/null; then
        echo "📦 Installing supervisord..."
        "$VENV_PATH/bin/pip" install supervisor
    else
        echo "✅ Supervisord already installed"
    fi
}

# Start supervisord and WINCASA
start() {
    check_venv
    install_supervisord
    
    # Check if supervisord is already running
    if [ -f "$SUPERVISORD_PID" ] && kill -0 $(cat "$SUPERVISORD_PID") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Supervisord already running${NC}"
        # Just ensure WINCASA is started
        "$VENV_PATH/bin/supervisorctl" -c "$SUPERVISORD_CONF" start wincasa
    else
        echo "🚀 Starting supervisord..."
        # Clean up old socket if exists
        rm -f "$SUPERVISORD_SOCK"
        
        # Start supervisord
        "$VENV_PATH/bin/supervisord" -c "$SUPERVISORD_CONF"
        
        # Wait for supervisord to start
        sleep 2
        
        if [ -f "$SUPERVISORD_PID" ] && kill -0 $(cat "$SUPERVISORD_PID") 2>/dev/null; then
            echo -e "${GREEN}✅ Supervisord started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start supervisord${NC}"
            exit 1
        fi
    fi
    
    # Check WINCASA status
    sleep 3
    status
}

# Stop WINCASA and supervisord
stop() {
    if [ -f "$SUPERVISORD_PID" ] && kill -0 $(cat "$SUPERVISORD_PID") 2>/dev/null; then
        echo "🛑 Stopping WINCASA..."
        "$VENV_PATH/bin/supervisorctl" -c "$SUPERVISORD_CONF" stop wincasa
        
        echo "🛑 Stopping supervisord..."
        "$VENV_PATH/bin/supervisorctl" -c "$SUPERVISORD_CONF" shutdown
        
        # Wait for shutdown
        sleep 2
        
        # Clean up
        rm -f "$SUPERVISORD_PID" "$SUPERVISORD_SOCK"
        echo -e "${GREEN}✅ All services stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  No services running${NC}"
    fi
}

# Restart WINCASA
restart() {
    if [ -f "$SUPERVISORD_PID" ] && kill -0 $(cat "$SUPERVISORD_PID") 2>/dev/null; then
        echo "🔄 Restarting WINCASA..."
        "$VENV_PATH/bin/supervisorctl" -c "$SUPERVISORD_CONF" restart wincasa
    else
        echo "⚠️  Supervisord not running, starting fresh..."
        start
    fi
}

# Show status
status() {
    echo "📊 Service Status:"
    echo "────────────────"
    
    if [ -f "$SUPERVISORD_PID" ] && kill -0 $(cat "$SUPERVISORD_PID") 2>/dev/null; then
        echo -e "Supervisord: ${GREEN}Running${NC} (PID: $(cat $SUPERVISORD_PID))"
        
        # Get WINCASA status
        WINCASA_STATUS=$("$VENV_PATH/bin/supervisorctl" -c "$SUPERVISORD_CONF" status wincasa 2>/dev/null)
        if echo "$WINCASA_STATUS" | grep -q "RUNNING"; then
            echo -e "WINCASA:     ${GREEN}Running${NC}"
            echo ""
            echo "🌐 Access URL: http://localhost:8667"
            echo "📝 Logs:"
            echo "   - Application: tail -f $PROJECT_ROOT/logs/wincasa_stdout.log"
            echo "   - Errors: tail -f $PROJECT_ROOT/logs/wincasa_stderr.log"
            echo "   - Supervisor: tail -f $PROJECT_ROOT/logs/supervisord.log"
        else
            echo -e "WINCASA:     ${RED}Not Running${NC}"
            echo ""
            echo "Check logs for errors:"
            echo "   tail -f $PROJECT_ROOT/logs/wincasa_stderr.log"
        fi
    else
        echo -e "Supervisord: ${RED}Not Running${NC}"
        echo -e "WINCASA:     ${RED}Not Running${NC}"
    fi
}

# Show logs
logs() {
    if [ -f "$PROJECT_ROOT/logs/wincasa_stdout.log" ]; then
        echo "📋 Recent WINCASA logs:"
        echo "──────────────────────"
        tail -20 "$PROJECT_ROOT/logs/wincasa_stdout.log"
        echo ""
        echo "For live logs: tail -f $PROJECT_ROOT/logs/wincasa_stdout.log"
    else
        echo "No logs found yet"
    fi
}

# Main command handler
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start supervisord and WINCASA server"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart WINCASA server"
        echo "  status   - Show service status"
        echo "  logs     - Show recent logs"
        exit 1
        ;;
esac