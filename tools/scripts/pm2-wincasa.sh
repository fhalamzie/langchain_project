#!/bin/bash
# WINCASA PM2 Management Script
# Provides easy PM2 operations with proper logging

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/../.." || exit 1

# PM2 process name
APP_NAME="wincasa"

# Start the application
start() {
    echo "🚀 Starting WINCASA with PM2..."
    
    # Check if already running
    if pm2 list | grep -q "$APP_NAME.*online"; then
        echo -e "${YELLOW}⚠️  WINCASA already running${NC}"
        echo "Use 'restart' to restart or 'logs' to view logs"
        return
    fi
    
    # Start with PM2
    pm2 start ecosystem.config.js
    
    # Wait a moment for startup
    sleep 3
    
    # Show status
    status
    
    echo ""
    echo -e "${GREEN}✅ WINCASA started successfully${NC}"
    echo ""
    echo "📝 View logs with: $0 logs"
    echo "📊 Monitor with: pm2 monit"
    echo "🌐 Access at: http://localhost:8667"
}

# Stop the application
stop() {
    echo "🛑 Stopping WINCASA..."
    pm2 stop $APP_NAME
    echo -e "${GREEN}✅ WINCASA stopped${NC}"
}

# Restart the application
restart() {
    echo "🔄 Restarting WINCASA..."
    pm2 restart $APP_NAME
    sleep 2
    status
}

# Delete from PM2
delete() {
    echo "🗑️  Removing WINCASA from PM2..."
    pm2 delete $APP_NAME
    echo -e "${GREEN}✅ WINCASA removed from PM2${NC}"
}

# Show status
status() {
    echo "📊 WINCASA Status:"
    echo "─────────────────"
    pm2 show $APP_NAME 2>/dev/null || echo -e "${RED}Not running${NC}"
}

# Show logs
logs() {
    echo "📋 WINCASA Logs (Press Ctrl+C to exit):"
    echo "───────────────────────────────────────"
    # Using --lines to show recent history and then follow
    pm2 logs $APP_NAME --lines 50
}

# Show only error logs
errors() {
    echo "❌ WINCASA Error Logs:"
    echo "─────────────────────"
    pm2 logs $APP_NAME --err --lines 50
}

# Flush logs
flush() {
    echo "🧹 Flushing WINCASA logs..."
    pm2 flush $APP_NAME
    echo -e "${GREEN}✅ Logs flushed${NC}"
}

# Save PM2 process list
save() {
    echo "💾 Saving PM2 process list..."
    pm2 save
    echo -e "${GREEN}✅ PM2 process list saved${NC}"
}

# Quick info
info() {
    echo -e "${BLUE}WINCASA PM2 Info:${NC}"
    echo "────────────────"
    echo "Process name: $APP_NAME"
    echo "Config file: ecosystem.config.js"
    echo "Log files:"
    echo "  - Combined: logs/pm2/wincasa-combined.log"
    echo "  - Output: logs/pm2/wincasa-out.log"
    echo "  - Error: logs/pm2/wincasa-error.log"
    echo ""
    echo "Useful PM2 commands:"
    echo "  - pm2 monit          # Live monitoring dashboard"
    echo "  - pm2 logs           # All logs"
    echo "  - pm2 list           # Process list"
    echo "  - pm2 describe $APP_NAME  # Detailed info"
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
    delete)
        delete
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    errors)
        errors
        ;;
    flush)
        flush
        ;;
    save)
        save
        ;;
    info)
        info
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|delete|status|logs|errors|flush|save|info}"
        echo ""
        echo "Commands:"
        echo "  start    - Start WINCASA server"
        echo "  stop     - Stop WINCASA server"
        echo "  restart  - Restart WINCASA server"
        echo "  delete   - Remove from PM2 process list"
        echo "  status   - Show detailed status"
        echo "  logs     - Stream application logs"
        echo "  errors   - Show error logs only"
        echo "  flush    - Clear all logs"
        echo "  save     - Save PM2 process list"
        echo "  info     - Show configuration info"
        exit 1
        ;;
esac