#!/bin/bash

# Redis Startup Script
# Starts Redis server if not already running

set -e

REDIS_DIR="/tmp/redis-stable"
REDIS_SERVER="$REDIS_DIR/src/redis-server"
REDIS_CLI="$REDIS_DIR/src/redis-cli"
PORT=6379

echo "🔴 Starting Redis Server..."
echo "=========================="

# Check if Redis is already running
if ps aux | grep -v grep | grep -q "redis-server.*:$PORT"; then
    echo "✅ Redis is already running on port $PORT"
    $REDIS_CLI ping > /dev/null 2>&1 && echo "✅ Redis connection test: PASSED"
    exit 0
fi

# Check if Redis binaries exist
if [ ! -f "$REDIS_SERVER" ]; then
    echo "⚠️  Redis server binary not found at $REDIS_SERVER"
    echo "📥 Downloading and compiling Redis..."
    
    cd /tmp
    if [ ! -d "redis-stable" ]; then
        curl -s https://download.redis.io/redis-stable.tar.gz -o redis-stable.tar.gz
        tar -xzf redis-stable.tar.gz
    fi
    
    cd redis-stable
    if [ ! -f "src/redis-server" ]; then
        echo "🔨 Compiling Redis (this may take a few minutes)..."
        make > /dev/null 2>&1
    fi
    
    echo "✅ Redis compiled successfully"
fi

# Start Redis server
echo "🚀 Starting Redis server on port $PORT..."
$REDIS_SERVER --daemonize yes --port $PORT

# Wait for Redis to start
sleep 2

# Test connection
if $REDIS_CLI ping > /dev/null 2>&1; then
    echo "✅ Redis server started successfully"
    echo "   Port: $PORT"
    echo "   PID: $(ps aux | grep -v grep | grep "redis-server.*:$PORT" | awk '{print $2}')"
    echo ""
    echo "📝 To stop Redis: pkill -f 'redis-server.*:$PORT'"
    echo "📝 To test connection: $REDIS_CLI ping"
else
    echo "❌ Failed to start Redis server"
    exit 1
fi

