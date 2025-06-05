#!/bin/bash
# Firebird Server Startup Script for LangChain Integration
# This script ensures Firebird server runs on localhost:3050 for LangChain SQL Database Agent

set -e

# Configuration
DB_PATH="/home/projects/langchain_project/WINCASA2022.FDB"
FB_PORT="3050"
FB_USER="sysdba"
FB_PASSWORD="masterkey"

echo "🔥 Starting Firebird Server for LangChain Integration..."

# Check if Firebird server is already running
if netstat -ln | grep -q ":${FB_PORT} "; then
    echo "✅ Firebird server already running on port ${FB_PORT}"
    exit 0
fi

# Function to start Firebird server
start_firebird() {
    echo "🚀 Starting Firebird server on port ${FB_PORT}..."
    
    # Try different Firebird server binaries
    FB_BINARIES=(
        "/opt/firebird/bin/fbserver"
        "/usr/bin/fbserver" 
        "/usr/local/firebird/bin/fbserver"
        "fbserver"
        "/opt/firebird/bin/firebird"
        "/usr/bin/firebird"
        "firebird"
    )
    
    for fb_bin in "${FB_BINARIES[@]}"; do
        if command -v "$fb_bin" >/dev/null 2>&1; then
            echo "📍 Found Firebird binary: $fb_bin"
            
            # Start server in background
            nohup "$fb_bin" -daemon -port "$FB_PORT" > /tmp/firebird.log 2>&1 &
            FB_PID=$!
            
            # Wait a moment for startup
            sleep 3
            
            # Check if server started successfully
            if netstat -ln | grep -q ":${FB_PORT} "; then
                echo "✅ Firebird server started successfully (PID: $FB_PID)"
                echo "📝 Server log: /tmp/firebird.log"
                return 0
            else
                echo "❌ Failed to start with $fb_bin"
                kill $FB_PID 2>/dev/null || true
            fi
        fi
    done
    
    echo "❌ No working Firebird server binary found"
    return 1
}

# Function to install Firebird if not found
install_firebird() {
    echo "📦 Firebird not found. Attempting installation..."
    
    if command -v apt-get >/dev/null 2>&1; then
        echo "🔧 Installing Firebird via apt-get..."
        sudo apt-get update
        sudo apt-get install -y firebird3.0-server firebird3.0-utils
    elif command -v yum >/dev/null 2>&1; then
        echo "🔧 Installing Firebird via yum..."
        sudo yum install -y firebird firebird-utils
    elif command -v zypper >/dev/null 2>&1; then
        echo "🔧 Installing Firebird via zypper..."
        sudo zypper install -y firebird firebird-utils
    else
        echo "❌ No supported package manager found"
        echo "Please install Firebird server manually:"
        echo "  - Ubuntu/Debian: sudo apt-get install firebird3.0-server"
        echo "  - CentOS/RHEL: sudo yum install firebird"
        echo "  - openSUSE: sudo zypper install firebird"
        return 1
    fi
}

# Main execution
if ! start_firebird; then
    echo "🔄 Attempting Firebird installation..."
    if install_firebird; then
        echo "🔄 Retrying server startup..."
        if ! start_firebird; then
            echo "❌ Failed to start Firebird server after installation"
            exit 1
        fi
    else
        echo "❌ Firebird installation failed"
        exit 1
    fi
fi

# Verify database accessibility
echo "🔍 Testing database connection..."
if command -v isql >/dev/null 2>&1; then
    echo "SELECT COUNT(*) FROM RDB\$RELATIONS;" | isql -u "$FB_USER" -p "$FB_PASSWORD" "localhost:${FB_PORT}/$DB_PATH" > /tmp/fb_test.out 2>&1
    
    if grep -q "COUNT" /tmp/fb_test.out; then
        echo "✅ Database connection test successful"
    else
        echo "⚠️ Database connection test failed, but server is running"
        echo "📝 Test output: /tmp/fb_test.out"
    fi
else
    echo "⚠️ isql not available for connection testing"
fi

echo "🎯 Firebird server ready for LangChain SQL Database Agent"
echo "📊 Connection string: firebird+fdb://${FB_USER}:${FB_PASSWORD}@localhost:${FB_PORT}/${DB_PATH}"