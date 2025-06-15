#!/bin/bash
# Simple server control script

PIDFILE="streamlit.pid"
LOGFILE="streamlit_output.log"
PORT=8667

start() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Server already running with PID: $PID"
            return
        fi
    fi
    
    echo "🚀 Starting WINCASA server..."
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
    nohup streamlit run src/wincasa/core/streamlit_app.py \
        --server.port $PORT \
        --server.address 0.0.0.0 \
        --server.enableCORS false \
        --server.enableXsrfProtection false \
        --server.headless true \
        > "$LOGFILE" 2>&1 &
    
    PID=$!
    echo $PID > "$PIDFILE"
    
    sleep 3
    if ps -p $PID > /dev/null; then
        echo "✅ Server started successfully with PID: $PID"
        echo "📝 Logs: tail -f $LOGFILE"
        echo "🌐 URL: http://localhost:$PORT"
    else
        echo "❌ Server failed to start. Check $LOGFILE"
        rm -f "$PIDFILE"
    fi
}

stop() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null; then
            echo "🛑 Stopping server (PID: $PID)..."
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null; then
                echo "⚠️  Force stopping..."
                kill -9 $PID
            fi
            rm -f "$PIDFILE"
            echo "✅ Server stopped"
        else
            echo "⚠️  Server not running (stale PID file)"
            rm -f "$PIDFILE"
        fi
    else
        echo "⚠️  No server running"
    fi
}

status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Server running with PID: $PID"
            echo "🌐 URL: http://localhost:$PORT"
            echo "📝 Logs: tail -f $LOGFILE"
        else
            echo "❌ Server not running (stale PID file)"
            rm -f "$PIDFILE"
        fi
    else
        echo "❌ Server not running"
    fi
}

restart() {
    stop
    sleep 1
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac