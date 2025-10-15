#!/bin/bash

# Stop Development Servers Script
# This script safely stops various development servers

set -e

echo "🛑 Stopping development servers..."

# Function to stop processes by pattern
stop_processes() {
    local pattern="$1"
    local description="$2"
    
    echo "Looking for $description..."
    
    # Find processes matching the pattern
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "Found processes: $pids"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$remaining" ]; then
            echo "Force killing remaining processes: $remaining"
            echo "$remaining" | xargs kill -KILL 2>/dev/null || true
        fi
        
        echo "✅ Stopped $description"
    else
        echo "ℹ️  No $description found"
    fi
}

# Stop different types of servers
stop_processes "uvicorn.*app.main:app" "FastAPI backend servers"
stop_processes "python.*test_minimal" "minimal test servers"
stop_processes "http.server.*3000" "frontend HTTP servers"
stop_processes "live-server" "frontend live servers"
stop_processes "uvicorn" "any remaining uvicorn servers"

# Check for any remaining processes
echo ""
echo "🔍 Checking for remaining development processes..."
remaining=$(ps aux | grep -E "(uvicorn|live-server|python.*test_minimal|python3.*http.server)" | grep -v grep || true)

if [ -n "$remaining" ]; then
    echo "⚠️  Remaining processes found:"
    echo "$remaining"
else
    echo "✅ All development servers stopped successfully"
fi

echo ""
echo "🎉 Stop operation completed!"
