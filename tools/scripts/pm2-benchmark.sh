#!/bin/bash
# PM2 management script for WINCASA Benchmark UI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROCESS_NAME="wincasa-benchmark"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

case "$1" in
    start)
        echo -e "${BLUE}🔬 Starting WINCASA Benchmark UI with PM2...${NC}"
        
        # Stop any existing instance
        pm2 stop $PROCESS_NAME 2>/dev/null || true
        pm2 delete $PROCESS_NAME 2>/dev/null || true
        
        # Set Python path
        export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/src"
        
        # Create PM2 config
        cat > "${PROJECT_ROOT}/benchmark.ecosystem.config.js" << EOF
module.exports = {
  apps: [{
    name: '${PROCESS_NAME}',
    script: 'streamlit',
    args: 'run src/wincasa/core/benchmark_ui.py --server.port 8668 --server.address 0.0.0.0 --server.headless true',
    cwd: '${PROJECT_ROOT}',
    env: {
      PYTHONPATH: '${PROJECT_ROOT}/src',
      PYTHONUNBUFFERED: '1'
    },
    interpreter: 'python3',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    log_date_format: 'YYYY-MM-DD HH:mm:ss.SSS'
  }]
};
EOF
        
        # Start with PM2
        cd "$PROJECT_ROOT"
        pm2 start benchmark.ecosystem.config.js
        
        echo -e "${GREEN}✅ Benchmark UI started!${NC}"
        echo -e "${BLUE}📍 Local URL: http://localhost:8668${NC}"
        echo -e "${BLUE}📍 Network URL: http://192.168.178.4:8668${NC}"
        echo ""
        echo "Use 'pm2 logs $PROCESS_NAME' to see logs"
        echo "Use 'pm2 monit' for live monitoring"
        ;;
        
    stop)
        echo -e "${RED}🛑 Stopping WINCASA Benchmark UI...${NC}"
        pm2 stop $PROCESS_NAME
        ;;
        
    restart)
        echo -e "${BLUE}🔄 Restarting WINCASA Benchmark UI...${NC}"
        pm2 restart $PROCESS_NAME
        ;;
        
    logs)
        echo -e "${BLUE}📜 Showing logs for WINCASA Benchmark UI...${NC}"
        pm2 logs $PROCESS_NAME --lines 50
        ;;
        
    status)
        echo -e "${BLUE}📊 Status of WINCASA Benchmark UI:${NC}"
        pm2 show $PROCESS_NAME
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|logs|status}"
        exit 1
        ;;
esac